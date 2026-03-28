import argparse
import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

import requests


def _snapshot(base_url: str) -> Dict[str, Any]:
    response = requests.get(f"{base_url}/chat/metrics", timeout=20)
    response.raise_for_status()
    return response.json()


def _reset_metrics(base_url: str) -> None:
    response = requests.post(f"{base_url}/chat/metrics/reset", timeout=20)
    response.raise_for_status()


def _extract(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "total_turns": metrics.get("total_turns", 0),
        "avg_latency_ms": metrics.get("avg_latency_ms", 0.0),
        "clarify_rate": metrics.get("clarify_rate", 0.0),
        "add_intent_success_rate": metrics.get("add_intent_success_rate", 0.0),
        "redundant_followup_suspected_rate": metrics.get("redundant_followup_suspected_rate", 0.0),
        "action_counts": metrics.get("action_counts", {}),
    }


def _build_delta(v2_on: Dict[str, Any], v2_off: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "clarify_rate": round(v2_on.get("clarify_rate", 0.0) - v2_off.get("clarify_rate", 0.0), 4),
        "add_intent_success_rate": round(
            v2_on.get("add_intent_success_rate", 0.0) - v2_off.get("add_intent_success_rate", 0.0), 4
        ),
        "redundant_followup_suspected_rate": round(
            v2_on.get("redundant_followup_suspected_rate", 0.0)
            - v2_off.get("redundant_followup_suspected_rate", 0.0),
            4,
        ),
        "avg_latency_ms": round(v2_on.get("avg_latency_ms", 0.0) - v2_off.get("avg_latency_ms", 0.0), 2),
    }


def monitor(
    on_url: str,
    off_url: str,
    interval_seconds: int,
    cycles: int,
    output_file: str,
    save_each_cycle: bool,
    reset_at_start: bool,
) -> None:
    records: List[Dict[str, Any]] = []

    def _write_summary() -> None:
        summary = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "config": {
                "v2_on_url": on_url,
                "v2_off_url": off_url,
                "interval_seconds": interval_seconds,
                "cycles": cycles,
            },
            "records": records,
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)

    if reset_at_start:
        _reset_metrics(on_url)
        _reset_metrics(off_url)
        print("Reset /chat/metrics on both rollout instances before sampling.")

    for idx in range(cycles):
        now = datetime.now(timezone.utc).isoformat()

        on_raw = _snapshot(on_url)
        off_raw = _snapshot(off_url)
        on_metrics = _extract(on_raw)
        off_metrics = _extract(off_raw)

        record = {
            "cycle": idx + 1,
            "timestamp_utc": now,
            "v2_on": on_metrics,
            "v2_off": off_metrics,
            "delta": _build_delta(on_metrics, off_metrics),
        }
        records.append(record)

        print(
            f"[{idx + 1}/{cycles}] {now} | "
            f"delta_latency_ms={record['delta']['avg_latency_ms']} "
            f"delta_clarify_rate={record['delta']['clarify_rate']} "
            f"delta_add_success={record['delta']['add_intent_success_rate']}"
        )

        if save_each_cycle:
            _write_summary()

        if idx < cycles - 1:
            time.sleep(interval_seconds)

    _write_summary()

    print(f"Saved rollout monitor report to: {output_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor feature-flag rollout metrics over time.")
    parser.add_argument("--on-url", default="http://127.0.0.1:8000", help="Base URL for v2-on instance")
    parser.add_argument("--off-url", default="http://127.0.0.1:8001", help="Base URL for v2-off instance")
    parser.add_argument("--interval-seconds", type=int, default=300, help="Sampling interval in seconds")
    parser.add_argument("--cycles", type=int, default=12, help="How many samples to capture")
    parser.add_argument(
        "--output-file",
        default="logs/rollout_monitor_latest.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--save-each-cycle",
        choices=["true", "false"],
        default="true",
        help="Persist output after each sample cycle (default: true)",
    )
    parser.add_argument(
        "--reset-at-start",
        choices=["true", "false"],
        default="true",
        help="Reset /chat/metrics on both instances before sampling (default: true)",
    )
    args = parser.parse_args()

    monitor(
        on_url=args.on_url,
        off_url=args.off_url,
        interval_seconds=max(1, args.interval_seconds),
        cycles=max(1, args.cycles),
        output_file=args.output_file,
        save_each_cycle=args.save_each_cycle.strip().lower() == "true",
        reset_at_start=args.reset_at_start.strip().lower() == "true",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
