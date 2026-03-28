from __future__ import annotations

from collections import defaultdict
from threading import Lock
from time import time
import re
import json
from pathlib import Path
from typing import Dict, List, Any


DEFAULT_SUCCESS_TARGETS = {
    "one_turn_add_success_rate_target": 0.85,
    "clarify_rate_target": 0.25,
    "redundant_followup_suspected_rate_target": 0.05,
    "avg_latency_ms_target": 1500,
}


def _load_success_targets() -> Dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "success_targets.json"
    if not path.exists():
        return dict(DEFAULT_SUCCESS_TARGETS)

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            merged = dict(DEFAULT_SUCCESS_TARGETS)
            merged.update(payload)
            return merged
    except Exception:
        pass

    return dict(DEFAULT_SUCCESS_TARGETS)


def _load_fixed_prompt_corpus() -> List[str]:
    path = Path(__file__).resolve().parent.parent / "prompt_corpus.json"
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            prompts = payload.get("prompts", [])
        else:
            prompts = payload
        if isinstance(prompts, list):
            return [str(prompt).strip() for prompt in prompts if str(prompt).strip()]
    except Exception:
        pass

    return []


class ChatMetricsStore:
    """In-memory baseline metrics for chat quality and responsiveness."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._success_targets = _load_success_targets()
        self._fixed_prompt_corpus = _load_fixed_prompt_corpus()
        self._reset_unlocked()

    def _reset_unlocked(self) -> None:
        self.started_at = time()
        self.total_turns = 0
        self.total_latency_ms = 0.0
        self.action_counts: Dict[str, int] = defaultdict(int)
        self.clarify_turns = 0
        self.consecutive_clarify_turns = 0
        self.repeated_clarify_turns = 0
        self.add_intent_turns = 0
        self.add_intent_success_turns = 0
        self.explicit_datetime_add_intent_turns = 0
        self.redundant_followup_suspected_turns = 0
        self._last_by_user: Dict[str, Dict[str, str]] = {}
        self._prompt_corpus: List[str] = []
        self._prompt_corpus_set = set()
        self.action_path_counts: Dict[str, int] = defaultdict(int)
        self.clarification_reason_tag_counts: Dict[str, int] = defaultdict(int)
        self.extraction_observed_turns = 0
        self.extraction_complete_turns = 0

    def reset(self) -> None:
        with self._lock:
            self._reset_unlocked()

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    def _is_add_intent(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        trigger_terms = (
            "add",
            "schedule",
            "put",
            "calendar",
            "exam",
            "test",
            "assignment",
            "meeting",
        )
        return any(term in normalized for term in trigger_terms)

    def _has_explicit_date(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        date_patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
            r"\b\d{1,2}(?:st|nd|rd|th)?(?:\s+of)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b",
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?\b",
            r"\b(today|tomorrow)\b",
        ]
        return any(re.search(pattern, normalized) for pattern in date_patterns)

    def _has_explicit_time(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        time_patterns = [
            r"\b\d{1,2}:\d{2}\s*(am|pm)?\b",
            r"\b\d{1,2}\s*(am|pm)\b",
        ]
        return any(re.search(pattern, normalized) for pattern in time_patterns)

    def _record_prompt_for_corpus(self, message: str) -> None:
        normalized = self._normalize_text(message)
        if not normalized or normalized in self._prompt_corpus_set:
            return
        if len(self._prompt_corpus) >= 250:
            return
        self._prompt_corpus.append(message.strip())
        self._prompt_corpus_set.add(normalized)

    def record_turn(
        self,
        user_id: str,
        message: str,
        response: Dict[str, Any],
        latency_ms: float,
        trace: Dict[str, Any] | None = None,
    ) -> None:
        action = str(response.get("action", "unknown"))
        reply_text = str(response.get("reply", ""))
        normalized_reply = self._normalize_text(reply_text)
        normalized_message = self._normalize_text(message)

        is_add_intent = self._is_add_intent(message)
        has_date = self._has_explicit_date(message)
        has_time = self._has_explicit_time(message)

        with self._lock:
            self.total_turns += 1
            self.total_latency_ms += max(0.0, float(latency_ms))
            self.action_counts[action] += 1

            if isinstance(trace, dict):
                action_path = str(trace.get("action_path", "")).strip()
                if action_path:
                    self.action_path_counts[action_path] += 1

                extraction = trace.get("extraction")
                if isinstance(extraction, dict):
                    self.extraction_observed_turns += 1
                    if extraction.get("is_complete"):
                        self.extraction_complete_turns += 1

                tags = trace.get("clarification_reason_tags", [])
                if isinstance(tags, list):
                    for tag in tags:
                        normalized_tag = str(tag).strip().lower()
                        if normalized_tag:
                            self.clarification_reason_tag_counts[normalized_tag] += 1

            if is_add_intent:
                self.add_intent_turns += 1
                self._record_prompt_for_corpus(message)

                if action in {"add_to_calendar", "replace_conflicting_with_personal"}:
                    self.add_intent_success_turns += 1

                if has_date and has_time:
                    self.explicit_datetime_add_intent_turns += 1
                    if action == "clarify":
                        self.redundant_followup_suspected_turns += 1

            if action == "clarify":
                self.clarify_turns += 1

                last_state = self._last_by_user.get(user_id, {})
                if last_state.get("action") == "clarify":
                    self.consecutive_clarify_turns += 1
                if (
                    last_state.get("action") == "clarify"
                    and last_state.get("reply") == normalized_reply
                    and last_state.get("message") != normalized_message
                ):
                    self.repeated_clarify_turns += 1

            self._last_by_user[user_id] = {
                "action": action,
                "reply": normalized_reply,
                "message": normalized_message,
            }

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            uptime_seconds = max(0.0, time() - self.started_at)
            avg_latency_ms = self.total_latency_ms / self.total_turns if self.total_turns else 0.0
            clarify_rate = self.clarify_turns / self.total_turns if self.total_turns else 0.0
            add_success_rate = (
                self.add_intent_success_turns / self.add_intent_turns if self.add_intent_turns else 0.0
            )
            redundant_followup_rate = (
                self.redundant_followup_suspected_turns / self.explicit_datetime_add_intent_turns
                if self.explicit_datetime_add_intent_turns
                else 0.0
            )
            extraction_completion_rate = (
                self.extraction_complete_turns / self.extraction_observed_turns
                if self.extraction_observed_turns
                else 0.0
            )

            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "total_turns": self.total_turns,
                "avg_latency_ms": round(avg_latency_ms, 2),
                "clarify_turns": self.clarify_turns,
                "clarify_rate": round(clarify_rate, 4),
                "consecutive_clarify_turns": self.consecutive_clarify_turns,
                "repeated_clarify_turns": self.repeated_clarify_turns,
                "add_intent_turns": self.add_intent_turns,
                "add_intent_success_turns": self.add_intent_success_turns,
                "add_intent_success_rate": round(add_success_rate, 4),
                "explicit_datetime_add_intent_turns": self.explicit_datetime_add_intent_turns,
                "redundant_followup_suspected_turns": self.redundant_followup_suspected_turns,
                "redundant_followup_suspected_rate": round(redundant_followup_rate, 4),
                "action_counts": dict(self.action_counts),
                "action_path_counts": dict(self.action_path_counts),
                "clarification_reason_tag_counts": dict(self.clarification_reason_tag_counts),
                "extraction_observed_turns": self.extraction_observed_turns,
                "extraction_complete_turns": self.extraction_complete_turns,
                "extraction_complete_rate": round(extraction_completion_rate, 4),
                "prompt_corpus_count": len(self._prompt_corpus),
                "fixed_prompt_corpus_count": len(self._fixed_prompt_corpus),
                "success_targets": dict(self._success_targets),
            }

    def prompt_corpus(self) -> List[str]:
        with self._lock:
            return list(self._prompt_corpus)

    def fixed_prompt_corpus(self) -> List[str]:
        with self._lock:
            return list(self._fixed_prompt_corpus)


chat_metrics_store = ChatMetricsStore()
