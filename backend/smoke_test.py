#!/usr/bin/env python3
"""
Smoke test / checklist script for AI Scheduling Agent backend.

Validates:
- Backend startup and import integrity
- Core API endpoint availability and contract correctness
- Essential flow: suggest → confirm → calendar integration

Usage:
    python smoke_test.py [--verbose] [--base-url http://localhost:8000]

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any


class SmokeTestRunner:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.errors: List[str] = []

    def log(self, message: str, error: bool = False):
        """Log a message with optional error prefix."""
        prefix = "ERROR" if error else "OK"
        print(f"[{prefix}] {message}")

    def validate_chat_contract(self, payload: Dict[str, Any], context: str) -> bool:
        """Validate strict chat response contract for required and optional fields."""
        is_valid = True

        if not isinstance(payload, dict):
            return self.check(f"{context}: response is object", False, f"Got {type(payload)}")

        is_valid &= self.check(f"{context}: has reply", "reply" in payload)
        is_valid &= self.check(f"{context}: has action", "action" in payload)
        is_valid &= self.check(
            f"{context}: reply is string",
            isinstance(payload.get("reply"), str),
            f"Got {type(payload.get('reply'))}",
        )
        is_valid &= self.check(
            f"{context}: action is string",
            isinstance(payload.get("action"), str),
            f"Got {type(payload.get('action'))}",
        )

        optional_specs = {
            "recommendations": list,
            "requires_confirmation": bool,
            "event_to_add": dict,
        }
        for key, expected_type in optional_specs.items():
            if key in payload:
                is_valid &= self.check(
                    f"{context}: {key} type",
                    isinstance(payload[key], expected_type),
                    f"Expected {expected_type}, got {type(payload[key])}",
                )

        if "confirmation_token" in payload and payload.get("confirmation_token") is not None:
            is_valid &= self.check(
                f"{context}: confirmation_token scalar",
                isinstance(payload["confirmation_token"], (str, int)),
                f"Got {type(payload['confirmation_token'])}",
            )

        return is_valid

    def log_verbose(self, message: str):
        """Log only if verbose mode is enabled."""
        if self.verbose:
            print(f"    {message}")

    def check(self, name: str, condition: bool, error_msg: str = "") -> bool:
        """Record a test result."""
        if condition:
            self.passed += 1
            self.log(f"{name}")
            return True
        else:
            self.failed += 1
            self.log(f"{name}{': ' + error_msg if error_msg else ''}", error=True)
            self.errors.append(f"{name}: {error_msg}")
            return False

    def test_backend_startup(self) -> bool:
        """Test 1: Backend startup and root endpoint."""
        print("\n[Test 1] Backend Startup")
        try:
            resp = requests.get(f"{self.base_url}/", timeout=5)
            if resp.status_code != 200:
                self.check("Root endpoint responds", False, f"HTTP {resp.status_code}")
                return False
            
            data = resp.json()
            self.check("Root endpoint responds", resp.status_code == 200)
            self.check("Root returns 'message' field", "message" in data)
            self.log_verbose(f"Root response: {data}")
            return True
        except Exception as e:
            self.check("Backend accessible", False, str(e))
            return False

    def test_events_endpoint(self) -> bool:
        """Test 2: /events endpoint."""
        print("\n[Test 2] Events Endpoint")
        try:
            resp = requests.get(f"{self.base_url}/events", timeout=5)
            self.check("GET /events responds", resp.status_code == 200, f"HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                events = resp.json()
                if isinstance(events, list):
                    self.check("GET /events returns list", True)
                    self.log_verbose(f"Events count: {len(events)}")
                    if events:
                        event = events[0]
                        has_required = all(k in event for k in ["id", "title"])
                        self.check("Events have required fields (id, title)", has_required)
                        self.log_verbose(f"Sample event: {event}")
                else:
                    self.check("GET /events returns list", False, f"Got {type(events)}")
            return resp.status_code == 200
        except Exception as e:
            self.check("GET /events endpoint", False, str(e))
            return False

    def test_profile_endpoint(self) -> bool:
        """Test 3: /profile/{user_id} endpoint."""
        print("\n[Test 3] Profile Endpoint")
        user_id = "smoke-test-user"
        try:
            resp = requests.get(f"{self.base_url}/profile/{user_id}", timeout=5)
            self.check("GET /profile/{user_id} responds", resp.status_code == 200, f"HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                profile = resp.json()
                self.check("Profile is dict", isinstance(profile, dict))
                self.log_verbose(f"Profile: {profile}")
            return resp.status_code == 200
        except Exception as e:
            self.check("GET /profile endpoint", False, str(e))
            return False

    def test_chat_suggest_flow(self) -> bool:
        """Test 4: POST /chat with suggest message."""
        print("\n[Test 4] Chat Suggest Flow")
        user_id = "smoke-test-suggest"
        try:
            payload = {
                "user_id": user_id,
                "message": "suggest events"
            }
            resp = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            self.check("POST /chat responds", resp.status_code == 200, f"HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                response = resp.json()
                self.validate_chat_contract(response, "Suggest contract")
                self.check("Chat response has 'action'", "action" in response)
                self.check("Chat response has 'reply'", "reply" in response)
                self.check("Chat response has 'recommendations'", "recommendations" in response)
                
                if "recommendations" in response and response["recommendations"]:
                    recs = response["recommendations"]
                    self.check("Recommendations is list", isinstance(recs, list))
                    if recs:
                        rec = recs[0]
                        self.check("Recommendation has 'event'", "event" in rec)
                        self.log_verbose(f"Recommendation count: {len(recs)}")
                
                self.log_verbose(f"Chat action: {response.get('action')}")
                self.log_verbose(f"Chat confirmation_token: {response.get('confirmation_token')}")
            return resp.status_code == 200
        except Exception as e:
            self.check("POST /chat suggest flow", False, str(e))
            return False

    def test_chat_confirm_flow(self) -> bool:
        """Test 5: POST /chat with confirm message."""
        print("\n[Test 5] Chat Confirm Flow")
        user_id = "smoke-test-confirm"
        
        # First, get a suggestion
        try:
            payload = {
                "user_id": user_id,
                "message": "suggest events"
            }
            resp1 = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if resp1.status_code != 200:
                self.check("Initial suggest request", False, f"HTTP {resp1.status_code}")
                return False
            
            response1 = resp1.json()
            token = response1.get("confirmation_token", "1")
            
            # Then confirm
            payload2 = {
                "user_id": user_id,
                "message": f"yes {token}"
            }
            resp2 = requests.post(
                f"{self.base_url}/chat",
                json=payload2,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            self.check("POST /chat confirm responds", resp2.status_code == 200, f"HTTP {resp2.status_code}")
            
            if resp2.status_code == 200:
                response2 = resp2.json()
                self.validate_chat_contract(response2, "Confirm contract")
                self.check("Confirm response has 'action'", "action" in response2)
                self.check("Confirm action is 'add_to_calendar'", 
                           response2.get("action") == "add_to_calendar")
                self.log_verbose(f"Confirm action: {response2.get('action')}")
            
            return resp2.status_code == 200
        except Exception as e:
            self.check("POST /chat confirm flow", False, str(e))
            return False

    def test_calendar_endpoint(self) -> bool:
        """Test 6: GET /calendar/{user_id} endpoint."""
        print("\n[Test 6] Calendar Endpoint")
        user_id = "smoke-test-calendar"
        
        try:
            # Get initial calendar state
            resp = requests.get(f"{self.base_url}/calendar/{user_id}", timeout=5)
            self.check("GET /calendar/{user_id} responds", resp.status_code == 200, f"HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                calendar = resp.json()
                self.check("Calendar is list", isinstance(calendar, list))
                initial_count = len(calendar) if isinstance(calendar, list) else 0
                self.log_verbose(f"Initial calendar count: {initial_count}")
                
                # Try to add an event
                if isinstance(calendar, list):
                    event_payload = {
                        "title": "Smoke Test Event",
                        "time": "14:00-16:00"
                    }
                    resp_add = requests.post(
                        f"{self.base_url}/calendar/{user_id}",
                        json=event_payload,
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )
                    self.check("POST /calendar/{user_id} responds", 
                               resp_add.status_code == 200, f"HTTP {resp_add.status_code}")
                    
                    if resp_add.status_code == 200:
                        # Verify event was added
                        resp_check = requests.get(f"{self.base_url}/calendar/{user_id}", timeout=5)
                        if resp_check.status_code == 200:
                            updated_calendar = resp_check.json()
                            new_count = len(updated_calendar) if isinstance(updated_calendar, list) else 0
                            self.check("Calendar reflects added event", new_count > initial_count)
                            if new_count > initial_count:
                                last_event = updated_calendar[-1]
                                self.check("Added event has 'title'", "title" in last_event)
                                self.check("Added event has 'time'", "time" in last_event)
                                self.log_verbose(f"Added event: {last_event}")
            
            return resp.status_code == 200
        except Exception as e:
            self.check("GET /calendar endpoint", False, str(e))
            return False

    def test_chat_clarify_contract(self) -> bool:
        """Test 7: contract check for non-recommendation path."""
        print("\n[Test 7] Chat Clarify Contract")
        try:
            payload = {
                "user_id": "smoke-test-clarify",
                "message": "hello there"
            }
            resp = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            self.check("POST /chat clarify responds", resp.status_code == 200, f"HTTP {resp.status_code}")
            if resp.status_code == 200:
                response = resp.json()
                self.validate_chat_contract(response, "Clarify contract")
            return resp.status_code == 200
        except Exception as e:
            self.check("POST /chat clarify flow", False, str(e))
            return False

    def test_architecture_guards(self) -> bool:
        """Test 8: architecture guardrails for side effects and data boundaries."""
        print("\n[Test 8] Architecture Guards")
        base = Path(__file__).resolve().parent
        agent_file = base / "agent" / "agent.py"
        graph_file = base / "agent" / "graph.py"
        chat_route_file = base / "routes" / "chat.py"

        try:
            agent_text = agent_file.read_text(encoding="utf-8")
            graph_text = graph_file.read_text(encoding="utf-8")
            chat_text = chat_route_file.read_text(encoding="utf-8")
        except Exception as e:
            self.check("Read architecture files", False, str(e))
            return False

        # Agent should not directly access DB modules/cursors.
        self.check("Agent has no sqlite import", "sqlite3" not in agent_text)
        self.check("Agent has no db.database import", "db.database" not in agent_text)
        self.check("Agent has no direct cursor usage", "cursor" not in agent_text)

        # Chat route should not perform calendar side effects directly.
        self.check("Chat route does not import add_calendar_event", "add_calendar_event" not in chat_text)
        self.check("Chat route does not touch calendar_storage", "calendar_storage" not in chat_text)

        # Graph should keep side-effect function in action node only.
        self.check("Graph action node uses add_calendar_event", "def _calendar_action_node" in graph_text and "add_calendar_event" in graph_text)

        return True

    def run_all(self) -> int:
        """Run all smoke tests."""
        print("=" * 60)
        print("Backend Smoke Test Suite")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Run all test suites
        self.test_backend_startup()
        self.test_events_endpoint()
        self.test_profile_endpoint()
        self.test_chat_suggest_flow()
        self.test_chat_confirm_flow()
        self.test_calendar_endpoint()
        self.test_chat_clarify_contract()
        self.test_architecture_guards()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 60)
        
        if self.errors:
            print("\nFailed checks:")
            for error in self.errors:
                print(f"  - {error}")
        
        return 0 if self.failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Smoke test suite for AI Scheduling Agent backend"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend base URL (default: http://127.0.0.1:8000)"
    )
    
    args = parser.parse_args()
    
    runner = SmokeTestRunner(base_url=args.base_url, verbose=args.verbose)
    exit_code = runner.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
