#!/usr/bin/env python3
"""
Scripted demo runner for the AI Scheduling Agent.

Flow:
1) Health check
2) Suggest events
3) Confirm first recommendation (yes <event_id>)
4) Verify calendar write

Usage:
    python demo_sequence.py [--base-url http://127.0.0.1:8000] [--user-id demo-script]
"""

import argparse
import sys
from typing import Any, Dict

import requests


def print_step(title: str) -> None:
    print("\n" + "=" * 20 + f" {title} " + "=" * 20)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def post_json(base_url: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(
        f"{base_url}{path}",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=45,
    )
    require(resp.status_code == 200, f"{path} returned HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    require(isinstance(data, dict), f"{path} response must be JSON object")
    require("reply" in data and "action" in data, f"{path} response missing required keys")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scripted demo sequence")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="demo-script")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    user_id = args.user_id

    try:
        print_step("Health")
        health = requests.get(f"{base}/", timeout=10)
        require(health.status_code == 200, f"Health check failed: HTTP {health.status_code}")
        print("Backend:", health.json())

        print_step("Suggest")
        suggest = post_json(base, "/chat", {"user_id": user_id, "message": "suggest events"})
        print("Action:", suggest.get("action"))
        print("Reply:", suggest.get("reply"))

        recommendations = suggest.get("recommendations") or []
        require(len(recommendations) > 0, "No recommendations returned in suggest flow")
        first_event = recommendations[0].get("event", {})
        event_id = str(first_event.get("id") or suggest.get("confirmation_token") or "")
        require(event_id, "Could not determine event_id for confirmation")
        print("Selected event_id:", event_id)

        print_step("Confirm")
        confirm = post_json(base, "/chat", {"user_id": user_id, "message": f"yes {event_id}"})
        print("Action:", confirm.get("action"))
        print("Reply:", confirm.get("reply"))
        require(confirm.get("action") == "add_to_calendar", "Confirm flow did not produce add_to_calendar action")

        print_step("Verify Calendar")
        cal_resp = requests.get(f"{base}/calendar/{user_id}", timeout=10)
        require(cal_resp.status_code == 200, f"Calendar read failed: HTTP {cal_resp.status_code}")
        calendar = cal_resp.json()
        require(isinstance(calendar, list), "Calendar response is not a list")
        require(len(calendar) > 0, "Calendar has no entries after confirmation")

        last = calendar[-1]
        require("title" in last and "time" in last, "Calendar entry missing title/time")
        print("Calendar entries:", len(calendar))
        print("Last entry:", last)

        print("\nDemo sequence PASSED")
        return 0

    except Exception as e:
        print("\nDemo sequence FAILED")
        print(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
