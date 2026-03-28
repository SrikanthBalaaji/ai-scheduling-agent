import os
from typing import List, Dict
from pathlib import Path
from datetime import datetime, timedelta
import re
import time
import json

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

_ENV_LOADED = False
_DISCOVERED_MODELS_CACHE: List[str] = []
_DISCOVERED_MODELS_CACHE_TS = 0.0

MISTRAL_MODEL_FALLBACKS = [
    "openrouter/auto",
    "mistralai/mistral-7b-instruct-v0.1",
    "mistralai/mistral-7b-instruct",
    "mistralai/mistral-7b-instruct-v0.2",
    "mistralai/mistral-7b-instruct-v0.3",
    "mistralai/mistral-7b-instruct:free",
    "mistralai/mistral-nemo:free",
    "mistralai/mistral-small-3.2-24b-instruct:free",
]

DEFAULT_OPENROUTER_DISCOVERY_TIMEOUT_SECONDS = 4
DEFAULT_OPENROUTER_REQUEST_TIMEOUT_SECONDS = 12
DEFAULT_OPENROUTER_MAX_MODEL_ATTEMPTS = 2
DEFAULT_DISCOVERY_CACHE_TTL_SECONDS = 600
DEFAULT_PROFILE_REQUEST_TIMEOUT_SECONDS = 2

PERSONAL_EVENT_DRAFTS: Dict[str, Dict] = {}
PENDING_PERSONAL_EVENTS: Dict[str, Dict] = {}
PENDING_PERSONAL_CONFLICT_CHOICES: Dict[str, Dict] = {}
CLARIFICATION_STATE: Dict[str, Dict] = {}  # Tracks which fields were already asked per user
MONTH_NAME_TO_NUMBER = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

MONTH_TOKEN_TO_NUMBER = {
    **MONTH_NAME_TO_NUMBER,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

INTEREST_ALIASES = {
    "hackathon": ["hackathon", "tech", "competition"],
    "guest talk": ["guest talk", "talk", "career"],
    "culturals": ["culturals", "cultural", "music", "drama"],
    "workshop": ["workshop", "tech", "ai"],
    "expo": ["expo", "career", "tech"],
    "competition": ["competition", "hackathon", "sports"],
    "career": ["career", "guest talk", "expo"],
}


def _load_env_once(force: bool = False) -> None:
    global _ENV_LOADED
    if _ENV_LOADED and not force:
        return

    agent_dir = Path(__file__).resolve().parent
    backend_dir = agent_dir.parent
    repo_dir = backend_dir.parent
    candidates = [backend_dir / ".env", repo_dir / ".env"]

    for env_path in candidates:
        if not env_path.exists():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception:
            # Keep startup resilient even if .env parsing fails.
            pass

    _ENV_LOADED = True


def _get_openrouter_api_key() -> str:
    _load_env_once()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if api_key:
        return api_key
    # Retry once in case .env was added after process startup.
    _load_env_once(force=True)
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def _get_mistral_model() -> str:
    _load_env_once()
    # Use OpenRouter auto-routing by default so an available model is selected.
    return os.getenv("MISTRAL_MODEL", "openrouter/auto")


def _get_env_int(name: str, default: int) -> int:
    _load_env_once()
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except Exception:
        return default


def _is_discovery_enabled() -> bool:
    _load_env_once()
    raw = os.getenv("OPENROUTER_ENABLE_MODEL_DISCOVERY", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _is_fast_local_responses_enabled() -> bool:
    """Use deterministic local replies for high-frequency simple actions."""
    _load_env_once()
    # Default to LLM-backed response generation unless explicitly overridden.
    raw = os.getenv("FAST_LOCAL_RESPONSES_ENABLED", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _is_prompt_sensitivity_v2_enabled() -> bool:
    """Feature flag for phased rollout of slot-based parsing and clarification policy."""
    _load_env_once()
    raw = os.getenv("PROMPT_SENSITIVITY_V2_ENABLED", "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _is_slot_llm_fallback_enabled() -> bool:
    """Enable bounded LLM slot extraction only for low-confidence parses."""
    _load_env_once()
    raw = os.getenv("SLOT_LLM_FALLBACK_ENABLED", "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _discover_openrouter_mistral_candidates(headers: Dict[str, str]) -> List[str]:
    global _DISCOVERED_MODELS_CACHE_TS, _DISCOVERED_MODELS_CACHE
    cache_ttl = _get_env_int("OPENROUTER_DISCOVERY_CACHE_TTL_SECONDS", DEFAULT_DISCOVERY_CACHE_TTL_SECONDS)
    if _DISCOVERED_MODELS_CACHE and (time.time() - _DISCOVERED_MODELS_CACHE_TS) < cache_ttl:
        return _DISCOVERED_MODELS_CACHE

    discovery_timeout = _get_env_int(
        "OPENROUTER_DISCOVERY_TIMEOUT_SECONDS",
        DEFAULT_OPENROUTER_DISCOVERY_TIMEOUT_SECONDS,
    )

    try:
        response = requests.get(OPENROUTER_MODELS_URL, headers=headers, timeout=discovery_timeout)
        if response.status_code >= 400:
            return []

        payload = response.json()
        models = payload.get("data", []) if isinstance(payload, dict) else []
        discovered = []
        for model in models:
            model_id = str(model.get("id", "")).strip()
            model_id_lower = model_id.lower()
            if "mistral" not in model_id_lower:
                continue
            # Prefer 7B-ish or instruct variants first.
            if "7b" in model_id_lower or "instruct" in model_id_lower:
                discovered.append(model_id)

        _DISCOVERED_MODELS_CACHE = discovered
        _DISCOVERED_MODELS_CACHE_TS = time.time()
        return discovered
    except Exception:
        return []


def _build_model_candidates() -> List[str]:
    _load_env_once()
    # Environment + static fallbacks are deterministic; dynamic discovery is added later.
    models = [_get_mistral_model()]
    env_candidates = os.getenv("OPENROUTER_MODEL_CANDIDATES", "")
    if env_candidates.strip():
        models.extend([m.strip() for m in env_candidates.split(",") if m.strip()])
    models.extend(MISTRAL_MODEL_FALLBACKS)

    deduped = []
    for model in models:
        if model not in deduped:
            deduped.append(model)
    return deduped


def _generate_mistral_text(system_prompt: str, user_prompt: str, fallback: str) -> str:
    openrouter_api_key = _get_openrouter_api_key()
    if not openrouter_api_key:
        print("OPENROUTER ERROR: OPENROUTER_API_KEY is missing")
        return (
            "I could not reach the LLM because OPENROUTER_API_KEY is missing. "
            "Please set a valid key in backend/.env and retry."
        )

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "ai-scheduling-agent",
    }
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        model_candidates = _build_model_candidates()
        if _is_discovery_enabled():
            discovered_candidates = _discover_openrouter_mistral_candidates(headers)
            if discovered_candidates:
                print(f"OPENROUTER INFO: discovered {len(discovered_candidates)} mistral model ids")
                model_candidates.extend(discovered_candidates)

        deduped_candidates = []
        for model in model_candidates:
            if model not in deduped_candidates:
                deduped_candidates.append(model)

        max_attempts = _get_env_int("OPENROUTER_MAX_MODEL_ATTEMPTS", DEFAULT_OPENROUTER_MAX_MODEL_ATTEMPTS)
        request_timeout = _get_env_int(
            "OPENROUTER_REQUEST_TIMEOUT_SECONDS",
            DEFAULT_OPENROUTER_REQUEST_TIMEOUT_SECONDS,
        )

        tried = 0

        for model_name in deduped_candidates:
            if tried >= max_attempts:
                break
            tried += 1

            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 180,
            }
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=request_timeout,
            )

            if response.status_code == 404:
                print(f"OPENROUTER WARN: model unavailable -> {model_name} | {response.text[:220]}")
                continue

            if response.status_code >= 400:
                print(f"OPENROUTER ERROR: model={model_name} HTTP {response.status_code} - {response.text[:300]}")
                if response.status_code == 401:
                    return (
                        "I could not authenticate with OpenRouter (HTTP 401). "
                        "Please verify OPENROUTER_API_KEY in backend/.env and restart the backend."
                    )
                continue

            data = response.json()
            choices = data.get("choices", []) if isinstance(data, dict) else []

            if choices:
                message = choices[0].get("message", {})
                text = (message.get("content") or "").strip()
                if text:
                    print(f"OPENROUTER INFO: using model {model_name}")
                    return text

            print(f"OPENROUTER WARN: empty response choices for model {model_name}")

        print("OPENROUTER ERROR: No available model endpoints returned usable content")
        return (
            "I could not get a response from the configured LLM models right now. "
            "Please verify your OpenRouter model access and try again."
        )

    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return fallback


def generate_reply(
    action: str,
    user_message: str,
    recommendations: List[Dict],
    calendar: List[Dict],
    context: Dict,
    fallback: str,
) -> str:
    if _is_fast_local_responses_enabled():
        if action == "add_to_calendar":
            event_title = context.get("event_title") or "your event"
            return f"Added '{event_title}' to your calendar."
        if action == "clarify_not_found":
            return "I couldn't find that event id. Please reply with yes <event_id> from the list."
        if action == "no_events":
            return "There are no events to recommend right now."
        if action == "show_schedule":
            count = int(context.get("count", 0) or 0)
            return f"You currently have {count} item(s) in your calendar."
        if action == "recommend_alternative":
            alt = context.get("alternative") or "the alternative option"
            alt_id = context.get("alternative_id") or "?"
            blocked = context.get("blocked") or "that event"
            conflict_with = context.get("conflict_with") or "an existing event"
            return (
                f"'{blocked}' conflicts with '{conflict_with}'. "
                f"Best conflict-free pick: [{alt_id}] {alt}. Reply with yes {alt_id} to add it."
            )
        if action == "recommend_with_conflict":
            blocked = context.get("blocked") or "that event"
            blocked_id = context.get("blocked_id") or "?"
            conflict_with = context.get("conflict_with") or "an existing event"
            return (
                f"'{blocked}' overlaps with '{conflict_with}', and no safer alternative is available. "
                f"Reply with yes {blocked_id} if you still want to add it."
            )
        if action == "recommend_multiple":
            if not recommendations:
                return "I couldn't find suitable recommendations right now."

            top = recommendations[:3]
            parts = []
            for rec in top:
                ev = rec.get("event", {})
                ev_id = ev.get("id", "?")
                title = ev.get("title", "Untitled")
                reason = rec.get("reason", "Recommended")
                parts.append(f"[{ev_id}] {title} ({reason})")

            return (
                "Top options: " + "; ".join(parts) + ". "
                "Reply with yes <event_id> to add one to your calendar."
            )
        if action == "clarify":
            return "Tell me if you want event suggestions, conflict checks, or calendar updates."

    print("DEBUG: calling OpenRouter...")

    calendar_summary = (
        ", ".join(
            f"{e.get('title', 'Unnamed')} on {e.get('date', '?')} "
            f"({e.get('start_time', '?')}–{e.get('end_time', '?')})"
            for e in calendar
        )
        if calendar
        else "no existing events"
    )

    recs_summary = ""
    if recommendations:
        lines = []
        for r in recommendations:
            ev = r["event"]
            lines.append(
                f"  - [{ev['id']}] {ev['title']} on {ev['date']} "
                f"({ev['start_time']}–{ev['end_time']}, tags: {', '.join(ev.get('tags', []))}) "
                f"| score: {r['score']:.1f} | reason: {r['reason']}"
            )
        recs_summary = "\n".join(lines)

    action_instructions = {
        "add_to_calendar": (
            f"The student confirmed they want to add '{context.get('event_title')}' to their calendar. "
            "Write a single warm, upbeat confirmation sentence (max 15 words). "
            "Do NOT ask questions or give instructions—just confirm the action is done."
        ),
        "clarify_not_found": (
            "The student typed 'yes <id>' but the event id wasn't recognised. "
            "Write one friendly sentence asking them to pick a valid id from the list shown (max 25 words)."
        ),
        "show_schedule": (
            f"The student asked about their schedule. They have {context.get('count', 0)} item(s): {calendar_summary}. "
            "Write 1–2 friendly sentences summarising what's on their plate. Max 35 words."
        ),
        "no_events": (
            "There are no events available to recommend right now. "
            "Write one short empathetic sentence letting the student know. Max 20 words."
        ),
        "recommend_alternative": (
            f"The top-ranked event '{context.get('blocked')}' clashes with '{context.get('conflict_with')}' "
            f"already on the student's calendar. "
            f"Suggest '{context.get('alternative')}' (id: {context.get('alternative_id')}) as the best conflict-free option. "
            "Write 2 natural sentences: acknowledge the clash, then recommend the alternative with its id. Max 50 words. "
            "End with: 'Reply with yes <event_id> to confirm.'"
        ),
        "recommend_with_conflict": (
            f"The best event '{context.get('blocked')}' conflicts with '{context.get('conflict_with')}' "
            "and there are no conflict-free alternatives in the top picks. "
            "Write 2 short sentences: acknowledge the problem, then let the student decide whether to proceed anyway. "
            f"Include the event id {context.get('blocked_id')}. Max 50 words."
        ),
        "recommend_multiple": (
            f"Present the following top event recommendations to the student:\n{recs_summary}\n"
            "Write 2–3 natural, enthusiastic sentences highlighting why these events stand out. "
            "List each option by id and title. "
            "End exactly with: 'Reply with yes <event_id> to add one to your calendar.' Max 80 words."
        ),
        "clarify": (
            "The student's message wasn't clearly understood. "
            "Write one friendly sentence offering to help with: finding events, checking conflicts, or viewing their schedule. "
            "Max 25 words."
        ),
    }

    instruction = action_instructions.get(action)
    if not instruction:
        return fallback

    system_prompt = (
        "You are a smart, friendly AI planner assistant for university students. "
        "You help them manage their schedule and discover campus events. "
        "Keep replies concise, warm, and actionable. Never use bullet points or markdown. "
        "Always speak directly to the student."
    )

    user_prompt = (
        f"Student said: \"{user_message}\"\n"
        f"Student's current calendar: {calendar_summary}\n\n"
        f"Your task: {instruction}"
    )

    try:
        return _generate_mistral_text(system_prompt, user_prompt, fallback)
    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return fallback


def time_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or end2 <= start1)


def _split_time_range(time_range: str) -> Dict[str, str]:
    if not time_range or "-" not in time_range:
        return {"start_time": "09:00", "end_time": "10:00"}

    start_time, end_time = time_range.split("-", 1)
    return {
        "start_time": start_time.strip() or "09:00",
        "end_time": end_time.strip() or "10:00",
    }


def _normalize_date(date_value: str) -> str:
    if not date_value:
        return ""

    raw = str(date_value).strip()
    if not raw:
        return ""

    formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%m/%d/%Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return raw


def _time_to_minutes(time_value: str) -> int:
    if time_value is None:
        return -1

    raw = str(time_value).strip().lower().replace(".", "")
    if not raw:
        return -1

    raw = re.sub(r"\s+", " ", raw)

    twelve_hour_match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", raw)
    if twelve_hour_match:
        hour = int(twelve_hour_match.group(1))
        minute = int(twelve_hour_match.group(2) or 0)
        meridiem = twelve_hour_match.group(3)

        if minute < 0 or minute > 59 or hour < 1 or hour > 12:
            return -1

        if meridiem == "pm" and hour != 12:
            hour += 12
        if meridiem == "am" and hour == 12:
            hour = 0

        return hour * 60 + minute

    twenty_four_hour_match = re.match(r"^(\d{1,2})(?::(\d{2}))?$", raw)
    if twenty_four_hour_match:
        hour = int(twenty_four_hour_match.group(1))
        minute = int(twenty_four_hour_match.group(2) or 0)
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return -1
        return hour * 60 + minute

    return -1


def _minutes_to_hhmm(total_minutes: int, fallback: str) -> str:
    if total_minutes < 0:
        return fallback
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def _events_conflict(event: Dict, entry: Dict) -> bool:
    event_date = _normalize_date(event.get("date"))
    entry_date = _normalize_date(entry.get("date"))

    if not event_date or not entry_date or event_date != entry_date:
        return False

    event_start = _time_to_minutes(event.get("start_time"))
    event_end = _time_to_minutes(event.get("end_time"))
    entry_start = _time_to_minutes(entry.get("start_time"))
    entry_end = _time_to_minutes(entry.get("end_time"))

    if min(event_start, event_end, entry_start, entry_end) < 0:
        return False

    if event_end <= event_start:
        event_end += 24 * 60
    if entry_end <= entry_start:
        entry_end += 24 * 60

    return not (event_end <= entry_start or entry_end <= event_start)


def _first_conflict_entry(event: Dict, calendar: List[Dict]) -> Dict:
    for entry in calendar:
        if _events_conflict(event, entry):
            return entry
    return {}


def normalize_calendar_entries(calendar: List[Dict]) -> List[Dict]:
    normalized = []
    for entry in calendar:
        normalized_date = _normalize_date(entry.get("date"))

        if entry.get("start_time") and entry.get("end_time"):
            start_minutes = _time_to_minutes(entry.get("start_time"))
            end_minutes = _time_to_minutes(entry.get("end_time"))
            normalized.append(entry)
            normalized[-1]["date"] = normalized_date
            normalized[-1]["start_time"] = _minutes_to_hhmm(start_minutes, str(entry.get("start_time")))
            normalized[-1]["end_time"] = _minutes_to_hhmm(end_minutes, str(entry.get("end_time")))
            continue

        time_parts = _split_time_range(entry.get("time", ""))
        start_minutes = _time_to_minutes(time_parts["start_time"])
        end_minutes = _time_to_minutes(time_parts["end_time"])
        normalized.append(
            {
                "title": entry.get("title", "Untitled"),
                "date": normalized_date,
                "start_time": _minutes_to_hhmm(start_minutes, "09:00"),
                "end_time": _minutes_to_hhmm(end_minutes, "10:00"),
                "type": entry.get("type", "personal"),
            }
        )
    return normalized


def _extract_personal_event_title(message: str) -> str:
    # Words that should not be treated as event titles
    stop_words = {"it", "that", "this", "them", "these", "those", "what", "which"}
    
    title_patterns = [
        r"(?:i have|i've got)\s+(?:(?:a|an)\s+)?(.+?)\s+(?:at|on)\s+",
        r"(?:add|schedule|put)\s+(?:(?:a|an)\s+)?(.+?)\s+(?:at|on)\s+",
        r"(?:add|schedule|put)\s+(.+?)\s+to my calendar",
    ]

    lowered = message.lower()
    for pattern in title_patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            title = match.group(1).strip(" ,.")
            # Don't use single stop words as titles
            if title.lower() not in stop_words:
                return title.title()
    return ""


def _extract_date_time(message: str) -> Dict[str, str]:
    lowered = message.lower()

    day_first_match = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?(?:\s+of)?\s+(january|february|march|april|may|june|july|august|september|october|november|december)(?:\s*,?\s*(\d{4}))?",
        lowered,
        flags=re.IGNORECASE,
    )
    month_first_match = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?",
        lowered,
        flags=re.IGNORECASE,
    )
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", lowered, flags=re.IGNORECASE)

    if not time_match or (not day_first_match and not month_first_match):
        return {}

    if day_first_match:
        day = int(day_first_match.group(1))
        month = MONTH_NAME_TO_NUMBER[day_first_match.group(2).lower()]
        year = int(day_first_match.group(3)) if day_first_match.group(3) else datetime.now().year
    else:
        month = MONTH_NAME_TO_NUMBER[month_first_match.group(1).lower()]
        day = int(month_first_match.group(2))
        year = int(month_first_match.group(3)) if month_first_match.group(3) else datetime.now().year

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridiem = time_match.group(3).lower()
    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0

    try:
        start_dt = datetime(year, month, day, hour, minute)
    except ValueError:
        return {}
    end_dt = start_dt + timedelta(hours=2)
    return {
        "date": start_dt.strftime("%Y-%m-%d"),
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M"),
    }


def _parse_event_slots(message: str) -> Dict:
    """Tiered slot parser: strict parse -> tolerant parse -> optional LLM fallback."""
    strict = _parse_event_slots_strict(message)
    if strict.get("confidence", 0.0) >= 1.0:
        return strict

    tolerant = _parse_event_slots_tolerant(message, strict)
    best = tolerant if tolerant.get("confidence", 0.0) >= strict.get("confidence", 0.0) else strict

    if _is_slot_llm_fallback_enabled() and best.get("confidence", 0.0) < 1.0:
        llm_slots = _parse_event_slots_with_llm(message)
        if llm_slots:
            candidate = _merge_slot_results(best, llm_slots)
            if candidate.get("confidence", 0.0) > best.get("confidence", 0.0):
                best = candidate

    return best


def _parse_event_slots_strict(message: str) -> Dict:
    """Deterministic parser for well-structured natural language inputs."""
    lowered = message.lower()
    result: Dict = {
        "title": "",
        "date": "",
        "start_time": "",
        "end_time": "",
        "confidence": 0.0,
        "missing_fields": [],
    }

    # ── 1. DATE ─────────────────────────────────────────────────────────────
    day = month = year = None
    date_start = len(lowered)

    day_first = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?(?:\s+of)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)(?:\s*,?\s*(\d{4}))?",
        lowered, re.IGNORECASE,
    )
    month_first = re.search(
        r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?",
        lowered, re.IGNORECASE,
    )
    iso_date = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", lowered)
    numeric_date = re.search(r"\b(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b", lowered)

    if day_first:
        day = int(day_first.group(1))
        month = MONTH_TOKEN_TO_NUMBER[day_first.group(2).lower()]
        year = int(day_first.group(3)) if day_first.group(3) else datetime.now().year
        date_start = day_first.start()
    elif month_first:
        month = MONTH_TOKEN_TO_NUMBER[month_first.group(1).lower()]
        day = int(month_first.group(2))
        year = int(month_first.group(3)) if month_first.group(3) else datetime.now().year
        date_start = month_first.start()
    elif iso_date:
        year = int(iso_date.group(1))
        month = int(iso_date.group(2))
        day = int(iso_date.group(3))
        date_start = iso_date.start()
    elif numeric_date:
        first = int(numeric_date.group(1))
        second = int(numeric_date.group(2))
        year_raw = numeric_date.group(3)
        year = int(year_raw) if year_raw else datetime.now().year
        if year < 100:
            year += 2000

        # Handle both day-first and month-first numeric forms.
        if first > 12 and second <= 12:
            day = first
            month = second
        elif second > 12 and first <= 12:
            month = first
            day = second
        else:
            day = first
            month = second
        date_start = numeric_date.start()
    else:
        today = datetime.now()
        if "today" in lowered:
            day, month, year = today.day, today.month, today.year
            date_start = lowered.index("today")
        elif "tomorrow" in lowered:
            tmrw = today + timedelta(days=1)
            day, month, year = tmrw.day, tmrw.month, tmrw.year
            date_start = lowered.index("tomorrow")

    if day and month and year:
        try:
            result["date"] = datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            day = month = year = None

    if not result["date"]:
        result["missing_fields"].append("date")

    # ── 2. TIME ─────────────────────────────────────────────────────────────
    # Allow 12h, 24h, and words like noon/midnight.
    time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered, re.IGNORECASE)
    time_match_24h = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lowered)
    noon_match = re.search(r"\bnoon\b", lowered)
    midnight_match = re.search(r"\bmidnight\b", lowered)
    time_start = len(lowered)

    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        meridiem = time_match.group(3).lower()
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        base = datetime(
            year or datetime.now().year,
            month or datetime.now().month,
            day or datetime.now().day,
        )
        try:
            start_dt = base.replace(hour=hour, minute=minute)
            end_dt = start_dt + timedelta(hours=2)
            result["start_time"] = start_dt.strftime("%H:%M")
            result["end_time"] = end_dt.strftime("%H:%M")
            time_start = time_match.start()
        except ValueError:
            pass
    elif time_match_24h:
        hour = int(time_match_24h.group(1))
        minute = int(time_match_24h.group(2))
        base = datetime(
            year or datetime.now().year,
            month or datetime.now().month,
            day or datetime.now().day,
        )
        try:
            start_dt = base.replace(hour=hour, minute=minute)
            end_dt = start_dt + timedelta(hours=2)
            result["start_time"] = start_dt.strftime("%H:%M")
            result["end_time"] = end_dt.strftime("%H:%M")
            time_start = time_match_24h.start()
        except ValueError:
            pass
    elif noon_match or midnight_match:
        hour = 12 if noon_match else 0
        minute = 0
        base = datetime(
            year or datetime.now().year,
            month or datetime.now().month,
            day or datetime.now().day,
        )
        start_dt = base.replace(hour=hour, minute=minute)
        end_dt = start_dt + timedelta(hours=2)
        result["start_time"] = start_dt.strftime("%H:%M")
        result["end_time"] = end_dt.strftime("%H:%M")
        time_start = noon_match.start() if noon_match else midnight_match.start()

    if not result["start_time"]:
        result["missing_fields"].append("time")

    # ── 3. TITLE ────────────────────────────────────────────────────────────
    # Clip message at the earliest context boundary so calendar/date/time words
    # are never absorbed into the title.
    context_stops = [s for s in [date_start, time_start] if s < len(lowered)]
    cal_phrase = re.search(r"\s+(?:to|in|on)\s+(?:my\s+)?calendar", lowered)
    if cal_phrase:
        context_stops.append(cal_phrase.start())

    stop_at = min(context_stops) if context_stops else len(lowered)
    clipped = lowered[:stop_at].rstrip(" ,.")

    # Remove leading verb/modal phrases and leading articles
    stripped = re.sub(
        r"^(?:(?:please|pls)\s+)?(?:(?:can|could)\s+(?:you|u)\s+(?:(?:please|pls)\s+)?)?(?:add|schedule|put|create|set\s+up|set|remind\s+me\s+(?:about|of)|i(?:'ve)?\s+(?:have|got))\s+(?:an?\s+|the\s+)?",
        "",
        clipped,
        flags=re.IGNORECASE,
    ).strip(" ,.;:!?")
    # Remove trailing prepositions/connectors left over from clipping (e.g. "yoga class on")
    stripped = re.sub(r"\s+(?:on|at|for|in|from|by|a|an|the)\s*$", "", stripped, flags=re.IGNORECASE).strip(" ,.;:!?")
    # Remove trailing relative date words that may remain in noisy shorthand.
    stripped = re.sub(r"\s+(?:today|tomorrow|tmrw|tom)\s*$", "", stripped, flags=re.IGNORECASE).strip(" ,.;:!?")

    stop_words = {"it", "that", "this", "them", "these", "those", "what", "which"}
    if stripped and stripped.lower() not in stop_words:
        result["title"] = stripped.title()
    else:
        result["missing_fields"].append("title")

    # ── 4. CONFIDENCE ───────────────────────────────────────────────────────
    filled = sum(1 for f in ("title", "date", "start_time") if result.get(f))
    result["confidence"] = round(filled / 3.0, 2)

    return result


def _parse_event_slots_tolerant(message: str, base_slots: Dict) -> Dict:
    """Relaxed parser for noisy shorthand (e.g. 'at 21', 'tmrw', abbreviated months)."""
    lowered = message.lower()
    merged = dict(base_slots)

    # Tolerant date recovery: short relative words.
    if not merged.get("date"):
        today = datetime.now()
        if "tmrw" in lowered or "tom" in lowered:
            target = today + timedelta(days=1)
            merged["date"] = target.strftime("%Y-%m-%d")

    # Tolerant time recovery: "at 21" style without minutes/am-pm.
    if not merged.get("start_time"):
        hour_only = re.search(r"\bat\s+([01]?\d|2[0-3])\b", lowered)
        hour_dot_min = re.search(r"\b([01]?\d|2[0-3])\.(\d{2})\b", lowered)
        if hour_only:
            hour = int(hour_only.group(1))
            merged["start_time"] = f"{hour:02d}:00"
            merged["end_time"] = f"{(hour + 2) % 24:02d}:00"
        elif hour_dot_min:
            hour = int(hour_dot_min.group(1))
            minute = int(hour_dot_min.group(2))
            if 0 <= minute <= 59:
                base_dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                merged["start_time"] = base_dt.strftime("%H:%M")
                merged["end_time"] = (base_dt + timedelta(hours=2)).strftime("%H:%M")

    # Recompute confidence/missing fields from merged state.
    merged["missing_fields"] = []
    if not merged.get("title"):
        merged["missing_fields"].append("title")
    if not merged.get("date"):
        merged["missing_fields"].append("date")
    if not merged.get("start_time"):
        merged["missing_fields"].append("time")

    filled = sum(1 for f in ("title", "date", "start_time") if merged.get(f))
    merged["confidence"] = round(filled / 3.0, 2)
    return merged


def _merge_slot_results(primary: Dict, secondary: Dict) -> Dict:
    merged = dict(primary)
    for field in ("title", "date", "start_time", "end_time"):
        if not merged.get(field) and secondary.get(field):
            merged[field] = secondary[field]

    merged["missing_fields"] = []
    if not merged.get("title"):
        merged["missing_fields"].append("title")
    if not merged.get("date"):
        merged["missing_fields"].append("date")
    if not merged.get("start_time"):
        merged["missing_fields"].append("time")
    filled = sum(1 for f in ("title", "date", "start_time") if merged.get(f))
    merged["confidence"] = round(filled / 3.0, 2)
    return merged


def _validate_llm_slot_payload(payload: Dict) -> Dict:
    validated: Dict = {}

    title = str(payload.get("title", "")).strip()
    if title and 1 <= len(title) <= 120:
        validated["title"] = title.title()

    date_val = str(payload.get("date", "")).strip()
    if date_val:
        try:
            validated["date"] = datetime.strptime(date_val, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            pass

    for field in ("start_time", "end_time"):
        raw = str(payload.get(field, "")).strip()
        if re.match(r"^([01]\d|2[0-3]):[0-5]\d$", raw):
            validated[field] = raw

    return validated


def _parse_event_slots_with_llm(message: str) -> Dict:
    """Bounded LLM fallback for low-confidence parses. Must return schema-validated slots."""
    api_key = _get_openrouter_api_key()
    if not api_key:
        return {}

    system_prompt = (
        "Extract scheduling slots from user text. Return only compact JSON with keys: "
        "title, date, start_time, end_time. date must be YYYY-MM-DD, times must be HH:MM 24-hour. "
        "Use empty strings for unknown values."
    )
    user_prompt = f"Text: {message}"

    raw = _generate_mistral_text(system_prompt, user_prompt, "{}")
    if not raw:
        return {}

    candidate = raw.strip()
    if "{" in candidate and "}" in candidate:
        candidate = candidate[candidate.find("{") : candidate.rfind("}") + 1]

    try:
        payload = json.loads(candidate)
        if not isinstance(payload, dict):
            return {}
    except Exception:
        return {}

    validated = _validate_llm_slot_payload(payload)
    if not validated:
        return {}

    validated["missing_fields"] = []
    if not validated.get("title"):
        validated["missing_fields"].append("title")
    if not validated.get("date"):
        validated["missing_fields"].append("date")
    if not validated.get("start_time"):
        validated["missing_fields"].append("time")
    filled = sum(1 for f in ("title", "date", "start_time") if validated.get(f))
    validated["confidence"] = round(filled / 3.0, 2)
    return validated


def _extract_personal_event_request(user_id: str, message: str) -> Dict:
    """Extract personal event from message using unified slot parser.
    Returns complete event if all slots present, or partial slots if some missing."""
    lowered = message.lower()
    def has_keyword(keyword: str) -> bool:
        if " " in keyword or "'" in keyword:
            return keyword in lowered
        return re.search(rf"\b{re.escape(keyword)}\b", lowered) is not None

    is_calendar_intent = any(term in lowered for term in ["calendar", "add", "schedule", "put"])
    has_personal_signal = any(
        has_keyword(term)
        for term in [
            "calendar",
            "add",
            "schedule",
            "put",
            "i have",
            "i've got",
            "remind me",
            "exam",
            "test",
            "assignment",
            "meeting",
            "appointment",
            "personal",
        ]
    )
    clarify_state = _get_clarification_state(user_id)
    draft = PERSONAL_EVENT_DRAFTS.get(user_id, {})

    # Avoid hijacking recommendation/search prompts when no personal-event flow is active.
    if not has_personal_signal and not draft and not clarify_state:
        return {}

    slots = _parse_event_slots(message)
    has_fresh_full_event = bool(
        slots.get("title") and slots.get("date") and slots.get("start_time")
    )
    
    # Determine the title: prefer draft if filling in missing fields,
    # else use freshly parsed title
    if has_fresh_full_event:
        # Fresh full details from user override stale partial draft values.
        title = slots.get("title", "")
    elif draft and clarify_state:
        # User is filling in missing fields in response to clarification.
        # Preserve draft values for fields already provided
        title = draft.get("title", "") or slots.get("title", "")
    else:
        # First interaction or no clarification state → use parsed or draft
        title = slots.get("title") or draft.get("title", "")
    
    # Update calendar_intent in slots
    calendar_intent = is_calendar_intent or draft.get("calendar_intent", False)
    
    # If we have a complete event (title + date + time), return it
    if title and slots.get("date") and slots.get("start_time"):
        PERSONAL_EVENT_DRAFTS.pop(user_id, None)
        _clear_clarification_state(user_id)  # Clear state on successful full extraction
        return {
            "title": title,
            "date": slots["date"],
            "start_time": slots["start_time"],
            "end_time": slots["end_time"],
            "type": "personal",
            "calendar_intent": calendar_intent,
        }
    
    # Partial extraction - store all available fields in draft
    if title or slots.get("date") or slots.get("start_time"):
        PERSONAL_EVENT_DRAFTS[user_id] = {
            "title": title or draft.get("title", ""),
            "date": slots.get("date", "") or draft.get("date", ""),
            "start_time": slots.get("start_time", "") or draft.get("start_time", ""),
            "end_time": slots.get("end_time", "") or draft.get("end_time", ""),
            "calendar_intent": calendar_intent,
        }
    
    # Compute actual missing fields (excluding those now filled)
    # Include both parsed slots AND draft values
    actual_missing = slots.get("missing_fields", [])
    if title or draft.get("title"):
        actual_missing = [f for f in actual_missing if f != "title"]
    if slots.get("date") or draft.get("date"):
        actual_missing = [f for f in actual_missing if f != "date"]
    if slots.get("start_time") or draft.get("start_time"):
        actual_missing = [f for f in actual_missing if f != "time"]
    
    # Return slots structure for unified clarification to handle
    return {
        "partial": True,
        "title": title or draft.get("title", ""),
        "date": slots.get("date", "") or draft.get("date", ""),
        "start_time": slots.get("start_time", "") or draft.get("start_time", ""),
        "end_time": slots.get("end_time", "") or draft.get("end_time", ""),
        "missing_fields": actual_missing,
        "confidence": slots.get("confidence", 0.0),
        "calendar_intent": calendar_intent,
    }


def _extract_personal_event_request_legacy(user_id: str, message: str) -> Dict:
    """Legacy extractor path used when prompt-sensitivity rollout flag is disabled."""
    lowered = message.lower()
    def has_keyword(keyword: str) -> bool:
        if " " in keyword or "'" in keyword:
            return keyword in lowered
        return re.search(rf"\b{re.escape(keyword)}\b", lowered) is not None

    is_calendar_intent = any(term in lowered for term in ["calendar", "add", "schedule", "put"])
    has_personal_signal = any(
        has_keyword(term)
        for term in [
            "calendar",
            "add",
            "schedule",
            "put",
            "i have",
            "i've got",
            "remind me",
            "exam",
            "test",
            "assignment",
            "meeting",
            "appointment",
            "personal",
        ]
    )

    if not has_personal_signal:
        return {}

    title = _extract_personal_event_title(message)
    parsed_dt = _extract_date_time(message)

    if title and parsed_dt.get("date") and parsed_dt.get("start_time"):
        return {
            "title": title,
            "date": parsed_dt["date"],
            "start_time": parsed_dt["start_time"],
            "end_time": parsed_dt["end_time"],
            "type": "personal",
            "calendar_intent": is_calendar_intent,
        }

    # Legacy path keeps behavior conservative by not entering slot-based clarification state.
    return {}


def _store_pending_personal_event(user_id: str, event: Dict) -> None:
    PENDING_PERSONAL_EVENTS[user_id] = event


def _get_pending_personal_event(user_id: str) -> Dict:
    return PENDING_PERSONAL_EVENTS.get(user_id, {})


def _clear_pending_personal_event(user_id: str) -> None:
    PENDING_PERSONAL_EVENTS.pop(user_id, None)


def _store_pending_personal_conflict_choice(user_id: str, event_to_add: Dict, conflicts: List[Dict]) -> None:
    PENDING_PERSONAL_CONFLICT_CHOICES[user_id] = {
        "event_to_add": event_to_add,
        "conflicts": conflicts,
    }


def _get_pending_personal_conflict_choice(user_id: str) -> Dict:
    return PENDING_PERSONAL_CONFLICT_CHOICES.get(user_id, {})


def _clear_pending_personal_conflict_choice(user_id: str) -> None:
    PENDING_PERSONAL_CONFLICT_CHOICES.pop(user_id, None)


def _store_clarification_state(user_id: str, asked_fields: List[str], slots: Dict) -> None:
    """Track which fields have been asked in clarification for this user."""
    CLARIFICATION_STATE[user_id] = {
        "asked_fields": asked_fields,
        "last_slots": slots,
    }


def _get_clarification_state(user_id: str) -> Dict:
    """Retrieve clarification state for user."""
    return CLARIFICATION_STATE.get(user_id, {})


def _clear_clarification_state(user_id: str) -> None:
    """Clear clarification state when turning completes."""
    CLARIFICATION_STATE.pop(user_id, None)


def _generate_field_specific_clarification_prompt(missing_fields: List[str], slots: Dict) -> str:
    """Generate a minimal, field-aware clarification prompt."""
    # Priority: first ask for title, then date, then time
    for field in ["title", "date", "time"]:
        if field in missing_fields:
            if field == "title":
                return "What should I call this event?"
            elif field == "date":
                captured = []
                if slots.get("title"):
                    captured.append(f"the title '{slots['title']}'")
                if slots.get("start_time"):
                    captured.append(f"the time {slots['start_time']}")
                prefix = f"I captured {' and '.join(captured)}. " if captured else ""
                return prefix + "What date should I put on your calendar?"
            elif field == "time":
                return f"I have {slots.get('title', 'your event')} on {slots.get('date')}. What time should I set?"
    
    # Fallback (shouldn't reach here)
    return "Could you provide the missing details?"


def _handle_unified_clarification(
    user_id: str,
    slots: Dict,
    message: str,
    calendar: List[Dict],
) -> Dict:
    """Unified clarification path that asks for missing fields one at a time."""
    missing = slots.get("missing_fields", [])
    if not missing:
        # All slots filled - this shouldn't be called
        return {}
    
    clarify_state = _get_clarification_state(user_id)
    already_asked = clarify_state.get("asked_fields", [])
    
    # Remove fields that are now filled (even if from draft)
    # These shouldn't be added to "asked" or asked again
    filled_fields = []
    if slots.get("title"):
        filled_fields.append("title")
    if slots.get("date"):
        filled_fields.append("date")
    if slots.get("start_time"):
        filled_fields.append("time")
    
    # Don't ask for fields we've already asked for or fields now filled
    new_missing = [f for f in missing if f not in already_asked and f not in filled_fields]
    
    if not new_missing:
        # We've already asked for all missing fields in this turn sequence
        # or they're now filled. Check if we should escalate (they didn't provide what was asked).
        # Escalation happens when: we asked for something, but it's still missing.
        if already_asked:
            # Find which fields are still missing from the already_asked list
            still_missing_from_asked = [f for f in already_asked if f in missing]
            if still_missing_from_asked:
                # They were asked for at least one field and still haven't provided it
                last_asked_field = still_missing_from_asked[0]  # First still-missing field
                escalation_prompts = {
                    "title": "I need an event title to add it to your calendar. Could you describe what you'd like to schedule?",
                    "date": "I need a date to add your event. Could you provide a specific day or date?",
                    "time": "I need a time to add your event. Could you tell me what time works for you?",
                }
                escalation_msg = escalation_prompts.get(
                    last_asked_field,
                    "Could you provide more details so I can help you better?"
                )
                return {
                    "reply": escalation_msg,
                    "action": "clarify",
                    "recommended_event": None,
                }
        # Fallback if no escalation needed
        return {}
    
    # Update which fields we're asking for in this turn
    updated_asked = already_asked + new_missing
    _store_clarification_state(user_id, updated_asked, slots)
    
    # Generate field-specific prompt
    prompt = _generate_field_specific_clarification_prompt(new_missing, slots)
    
    return {
        "reply": prompt,
        "action": "clarify",
        "recommended_event": None,
    }


def _find_conflicting_entries(event: Dict, calendar: List[Dict]) -> List[Dict]:
    return [entry for entry in calendar if _events_conflict(event, entry)]


def _build_personal_conflict_prompt(event_to_add: Dict, conflicts: List[Dict]) -> str:
    event_title = event_to_add.get("title", "this personal event")
    event_date = event_to_add.get("date", "the same day")
    event_window = f"{event_to_add.get('start_time', '?')}-{event_to_add.get('end_time', '?')}"

    conflict_titles = [entry.get("title", "an existing event") for entry in conflicts]
    primary_conflict_title = conflict_titles[0] if conflict_titles else "an existing event"

    return (
        f"Your personal event '{event_title}' ({event_date} {event_window}) overlaps with '{primary_conflict_title}'. "
        "Reply 'replace' to remove conflicting calendar event(s) and add this personal event, "
        "or reply 'keep' to keep your current calendar unchanged."
    )


def get_user_calendar(user_id: str) -> List[Dict]:
    """
    Fetch calendar for user.
    TODO: Call Person B's /calendar/{user_id} API when ready.
    """
    if user_id == "demo":
        return [
            {
                "title": "Math Test",
                "date": "2026-03-30",
                "start_time": "10:00",
                "end_time": "12:00",
                "type": "personal",
            }
        ]
    return []


def get_user_profile(user_id: str) -> Dict:
    """Fetch profile from our own API."""
    _load_env_once()
    profile_base_url = os.getenv("PROFILE_API_BASE_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    profile_timeout = _get_env_int("PROFILE_API_TIMEOUT_SECONDS", DEFAULT_PROFILE_REQUEST_TIMEOUT_SECONDS)

    try:
        resp = requests.get(f"{profile_base_url}/profile/{user_id}", timeout=profile_timeout)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"interests": [], "career_goals": [], "major": ""}


def detect_conflicts(events: List[Dict], calendar: List[Dict]) -> List[Dict]:
    """Return list of events that conflict with calendar."""
    conflicts = []
    for event in events:
        for entry in calendar:
            if _events_conflict(event, entry):
                conflicts.append({"event": event, "conflicts_with": entry})
    return conflicts


def score_event(event: Dict, calendar: List[Dict], profile: Dict) -> float:
    """Score event 0-10. Higher = better recommendation."""
    score = 5.0

    interests = [i.lower() for i in profile.get("interests", [])]
    tags = [t.lower() for t in event.get("tags", [])]
    title_and_desc = (event.get("title", "") + " " + event.get("description", "")).lower()

    for interest in interests:
        aliases = INTEREST_ALIASES.get(interest, [interest])
        if any(alias in tags for alias in aliases):
            score += 2
        if any(alias in title_and_desc for alias in aliases):
            score += 1.5

    goals = [g.lower() for g in profile.get("career_goals", [])]
    for goal in goals:
        aliases = INTEREST_ALIASES.get(goal, [goal])
        if any(alias in title_and_desc for alias in aliases):
            score += 1.5

    if "tech" in tags:
        score += 1

    if "hackathon" in event.get("title", "").lower():
        score += 0.5

    for entry in calendar:
        if _events_conflict(event, entry):
            score -= 3

    return max(0, min(10, score))


def simple_agent(
    user_id: str, user_message: str, events: List[Dict], calendar: List[Dict]
) -> Dict:
    """Main agent logic. Returns dict matching ChatResponse format."""
    message = user_message.lower()
    profile = get_user_profile(user_id)
    calendar = normalize_calendar_entries(calendar)

    recommendation_intent_terms = ["suggest", "recommend", "attend", "what should"]
    if any(term in message for term in recommendation_intent_terms):
        # Recommendation intent should not be blocked by stale personal-event slot state.
        PERSONAL_EVENT_DRAFTS.pop(user_id, None)
        _clear_pending_personal_event(user_id)
        _clear_clarification_state(user_id)

    pending_conflict_choice = _get_pending_personal_conflict_choice(user_id)
    if pending_conflict_choice:
        replace_keywords = ["replace", "yes", "remove", "swap", "option 1", "1"]
        keep_keywords = ["keep", "no", "cancel", "option 2", "2", "don't replace", "do not replace"]

        if any(keyword in message for keyword in replace_keywords):
            _clear_pending_personal_conflict_choice(user_id)
            _clear_pending_personal_event(user_id)
            _clear_clarification_state(user_id)
            event_to_add = pending_conflict_choice.get("event_to_add", {})
            conflicts = pending_conflict_choice.get("conflicts", [])
            fallback = (
                f"Replacing {len(conflicts)} conflicting event(s) and adding '{event_to_add.get('title', 'your personal event')}'."
            )
            return {
                "reply": fallback,
                "action": "replace_conflicting_with_personal",
                "event_to_add": event_to_add,
                "conflicting_events": conflicts,
            }

        if any(keyword in message for keyword in keep_keywords):
            _clear_pending_personal_conflict_choice(user_id)
            _clear_pending_personal_event(user_id)
            _clear_clarification_state(user_id)
            fallback = (
                "Understood. I kept your existing calendar unchanged and did not add the conflicting personal event. "
                "Share a different time if you want to add it."
            )
            return {
                "reply": fallback,
                "action": "clarify",
                "recommended_event": None,
            }

        event_to_add = pending_conflict_choice.get("event_to_add", {})
        conflicts = pending_conflict_choice.get("conflicts", [])
        return {
            "reply": _build_personal_conflict_prompt(event_to_add, conflicts),
            "action": "clarify",
            "recommended_event": None,
        }

    # If a personal event is already pending and user repeats a date/time,
    # treat it as confirmation data instead of re-entering clarification loops.
    pending_personal_event = _get_pending_personal_event(user_id)
    _follow_up_slots = _parse_event_slots(user_message)
    _follow_up_has_dt = bool(_follow_up_slots.get("date") and _follow_up_slots.get("start_time"))
    if pending_personal_event and _follow_up_has_dt and not _follow_up_slots.get("title"):
        merged_event = {
            **pending_personal_event,
            "date": _follow_up_slots["date"],
            "start_time": _follow_up_slots["start_time"],
            "end_time": _follow_up_slots["end_time"],
            "calendar_intent": True,
        }
        _clear_pending_personal_event(user_id)

        conflicts = _find_conflicting_entries(merged_event, calendar)
        if conflicts:
            _store_pending_personal_conflict_choice(user_id, merged_event, conflicts)
            return {
                "reply": _build_personal_conflict_prompt(merged_event, conflicts),
                "action": "clarify",
                "recommended_event": None,
            }

        fallback = f"Added '{merged_event['title']}' to your calendar for {merged_event['date']} at {merged_event['start_time']}."
        return {
            "reply": generate_reply(
                action="add_to_calendar",
                user_message=user_message,
                recommendations=[],
                calendar=calendar,
                context={"event_title": merged_event.get("title")},
                fallback=fallback,
            ),
            "action": "add_to_calendar",
            "event_to_add": merged_event,
        }

    if _is_prompt_sensitivity_v2_enabled():
        personal_event = _extract_personal_event_request(user_id, user_message)
    else:
        personal_event = _extract_personal_event_request_legacy(user_id, user_message)
    
    # If extraction is partial (missing fields), use unified clarification
    if personal_event.get("partial"):
        clarification_result = _handle_unified_clarification(
            user_id, personal_event, user_message, calendar
        )
        if clarification_result:
            return clarification_result
        # If no clarification was returned (all fields asked), fall through
        # This shouldn't happen in normal flow but handles edge cases
    
    # If we have a complete event (title + date + time)
    if personal_event.get("title") and personal_event.get("date") and personal_event.get("start_time"):
        _store_pending_personal_event(user_id, personal_event)
        fallback = f"Added '{personal_event['title']}' to your calendar for {personal_event['date']} at {personal_event['start_time']}."
        if not personal_event.get("calendar_intent") or any(term in message for term in ["conflict", "clash", "check"]):
            fallback = (
                f"I noted your {personal_event['title']} on {personal_event['date']} at {personal_event['start_time']}. "
                "I can check for conflicts or add it to your calendar."
            )
            return {
                "reply": fallback,
                "action": "clarify",
                "recommended_event": None,
            }

        conflicts = _find_conflicting_entries(personal_event, calendar)
        if conflicts:
            _store_pending_personal_conflict_choice(user_id, personal_event, conflicts)
            return {
                "reply": _build_personal_conflict_prompt(personal_event, conflicts),
                "action": "clarify",
                "recommended_event": None,
            }

        return {
            "reply": generate_reply(
                action="add_to_calendar",
                user_message=user_message,
                recommendations=[],
                calendar=calendar,
                context={"event_title": personal_event.get("title")},
                fallback=fallback,
            ),
            "action": "add_to_calendar",
            "event_to_add": personal_event,
        }

    # ── Confirmation branch ──────────────────────────────────────────────────
    confirmation_match = re.match(r"^(yes|confirm)\s+(\d+)\b", message)
    if confirmation_match:
        event_id = confirmation_match.group(2)
        if event_id:
            for ev in events:
                if str(ev.get("id")) == event_id:
                    _clear_pending_personal_event(user_id)
                    _clear_pending_personal_conflict_choice(user_id)
                    _clear_clarification_state(user_id)
                    fallback = "Adding event to your calendar..."
                    return {
                        "reply": generate_reply(
                            action="add_to_calendar",
                            user_message=user_message,
                            recommendations=[],
                            calendar=calendar,
                            context={"event_title": ev.get("title")},
                            fallback=fallback,
                        ),
                        "action": "add_to_calendar",
                        "event_to_add": ev,
                    }

        fallback = (
            "No event found by that id. "
            "Please use 'yes <event_id>' from the recommendations."
        )
        return {
            "reply": generate_reply(
                action="clarify_not_found",
                user_message=user_message,
                recommendations=[],
                calendar=calendar,
                context={},
                fallback=fallback,
            ),
            "action": "clarify",
            "recommended_event": None,
        }

    # ── Check if user is confirming a pending personal event ─────────────────
    pending_personal_event = _get_pending_personal_event(user_id)
    confirmation_keywords = ["add", "yes", "okay", "ok", "sure", "please", "go", "confirm"]
    is_confirming_event = any(keyword in message for keyword in confirmation_keywords)
    
    if pending_personal_event and is_confirming_event and not any(term in message for term in ["conflict", "clash", "check"]):
        conflicts = _find_conflicting_entries(pending_personal_event, calendar)
        if conflicts:
            _store_pending_personal_conflict_choice(user_id, pending_personal_event, conflicts)
            return {
                "reply": _build_personal_conflict_prompt(pending_personal_event, conflicts),
                "action": "clarify",
                "recommended_event": None,
            }

        # User is confirming the pending personal event - add it
        _clear_pending_personal_event(user_id)
        _clear_clarification_state(user_id)  # Clear clarification state on successful completion
        fallback = f"Added '{pending_personal_event['title']}' to your calendar for {pending_personal_event['date']} at {pending_personal_event['start_time']}."
        return {
            "reply": generate_reply(
                action="add_to_calendar",
                user_message=user_message,
                recommendations=[],
                calendar=calendar,
                context={"event_title": pending_personal_event.get("title")},
                fallback=fallback,
            ),
            "action": "add_to_calendar",
            "event_to_add": pending_personal_event,
        }

    pending_personal_event = _get_pending_personal_event(user_id)
    if pending_personal_event and any(term in message for term in ["conflict", "clash", "check"]):
        calendar_with_pending_event = [*calendar, pending_personal_event]
        scored = []
        for event in events:
            score = score_event(event, calendar_with_pending_event, profile)
            scored.append((score, event))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_events = scored[:3]

        recommendations = []
        for score, ev in top_events:
            has_conflict = False
            conflict_title = ""
            for entry in calendar_with_pending_event:
                if _events_conflict(ev, entry):
                    has_conflict = True
                    conflict_title = entry.get("title", "an existing event")
                    break
            recommendations.append(
                {
                    "event": ev,
                    "score": score,
                    "reason": (
                        f"Conflicts with {conflict_title}" if has_conflict else "No schedule conflicts"
                    ),
                }
            )

        fallback = (
            f"I checked conflicts against your {pending_personal_event['title']} on {pending_personal_event['date']} at {pending_personal_event['start_time']}. "
            "These are the safest options."
        )
        return {
            "reply": generate_reply(
                action="recommend_multiple",
                user_message=user_message,
                recommendations=recommendations,
                calendar=calendar_with_pending_event,
                context={},
                fallback=fallback,
            ),
            "action": "recommend_multiple",
            "recommendations": recommendations,
            "requires_confirmation": True,
            "confirmation_token": recommendations[0]["event"].get("id") if recommendations else None,
        }

    # ── Schedule summary branch ──────────────────────────────────────────────
    if "schedule" in message:
        fallback = f"You have {len(calendar)} items in your calendar."
        return {
            "reply": generate_reply(
                action="show_schedule",
                user_message=user_message,
                recommendations=[],
                calendar=calendar,
                context={"count": len(calendar)},
                fallback=fallback,
            ),
            "action": "show_schedule",
            "recommended_event": None,
        }

    # ── Recommendation / conflict branch ────────────────────────────────────
    if any(
        word in message
        for word in ["conflict", "attend", "recommend", "what should", "suggest"]
    ):
        scored = []
        for event in events:
            s = score_event(event, calendar, profile)
            scored.append((s, event))

        scored.sort(key=lambda x: x[0], reverse=True)

        if not scored:
            fallback = "No events available to recommend."
            return {
                "reply": generate_reply(
                    action="no_events",
                    user_message=user_message,
                    recommendations=[],
                    calendar=calendar,
                    context={},
                    fallback=fallback,
                ),
                "action": "no_events",
                "recommended_event": None,
            }

        top_events = scored[:3]
        best_score, best_event = top_events[0]

        def event_reason(score, event):
            reasons = []
            interests = [i.lower() for i in profile.get("interests", [])]
            tags = [t.lower() for t in event.get("tags", [])]
            if any(interest in tags for interest in interests):
                reasons.append("Matches your interests")

            conflict = False
            conflict_title = ""
            for entry in calendar:
                if _events_conflict(event, entry):
                    conflict = True
                    conflict_title = entry.get("title", "an existing event")
                    break
            if not conflict:
                reasons.append("No schedule conflicts")
            else:
                reasons.append(f"Conflicts with {conflict_title}")

            if score >= 8:
                reasons.append("Highly relevant")

            return reasons[0] if reasons else "Recommended"

        recommendations = []
        for score, ev in top_events:
            recommendations.append(
                {
                    "event": ev,
                    "score": score,
                    "reason": event_reason(score, ev),
                }
            )

        # If conflicts exist but are absent from top 3, surface one conflicting event
        # so users can clearly see conflict detection in recommendations.
        if calendar:
            top_ids = {str(rec["event"].get("id")) for rec in recommendations if rec.get("event")}
            conflict_candidates = []
            for score, ev in scored:
                conflict_entry = _first_conflict_entry(ev, calendar)
                if conflict_entry:
                    conflict_candidates.append((score, ev, conflict_entry))

            if conflict_candidates:
                best_conflict_score, best_conflict_event, conflict_entry = conflict_candidates[0]
                best_conflict_id = str(best_conflict_event.get("id"))
                if best_conflict_id not in top_ids and recommendations:
                    recommendations[-1] = {
                        "event": best_conflict_event,
                        "score": best_conflict_score,
                        "reason": f"Conflicts with {conflict_entry.get('title', 'an existing event')}",
                    }

        # Detect conflict for the best event
        has_conflict = False
        conflict_with = None
        for entry in calendar:
            if _events_conflict(best_event, entry):
                has_conflict = True
                conflict_with = entry
                break

        if has_conflict:
            # Find the best conflict-free alternative among top picks
            alternative_event = None
            for score, ev in top_events:
                conflict = False
                for entry in calendar:
                    if _events_conflict(ev, entry):
                        conflict = True
                        break
                if not conflict:
                    alternative_event = ev
                    break

            if alternative_event:
                fallback = (
                    f"'{best_event['title']}' conflicts with your schedule. "
                    f"You can attend '{alternative_event['title']}' instead."
                )
                return {
                    "reply": generate_reply(
                        action="recommend_alternative",
                        user_message=user_message,
                        recommendations=recommendations,
                        calendar=calendar,
                        context={
                            "blocked": best_event["title"],
                            "conflict_with": conflict_with.get("title", "an existing event"),
                            "alternative": alternative_event["title"],
                            "alternative_id": alternative_event.get("id"),
                        },
                        fallback=fallback,
                    ),
                    "action": "recommend_alternative",
                    "recommended_event": alternative_event,
                    "requires_confirmation": True,
                    "confirmation_token": alternative_event.get("id"),
                }
            else:
                fallback = (
                    f"'{best_event['title']}' conflicts with your schedule. "
                    "No better alternatives found."
                )
                return {
                    "reply": generate_reply(
                        action="recommend_with_conflict",
                        user_message=user_message,
                        recommendations=recommendations,
                        calendar=calendar,
                        context={
                            "blocked": best_event["title"],
                            "blocked_id": best_event.get("id"),
                            "conflict_with": conflict_with.get("title", "an existing event"),
                        },
                        fallback=fallback,
                    ),
                    "action": "recommend_with_conflict",
                    "recommended_event": best_event,
                    "confirmation_token": best_event.get("id"),
                }

        # No conflict — return multiple recommendations
        fallback = "Top recommendations:\n"
        for rec in recommendations:
            ev = rec["event"]
            fallback += f"- [{ev['id']}] {ev['title']} ({rec['reason']})\n"
        fallback += "Say 'yes <event_id>' to add one to your calendar."

        return {
            "reply": generate_reply(
                action="recommend_multiple",
                user_message=user_message,
                recommendations=recommendations,
                calendar=calendar,
                context={},
                fallback=fallback,
            ),
            "action": "recommend_multiple",
            "recommendations": recommendations,
            "requires_confirmation": True,
            "confirmation_token": best_event.get("id"),
        }

    # ── Catch-all clarify branch ─────────────────────────────────────────────
    fallback = (
        "I can help you find events, check conflicts, or see your schedule. "
        "What would you like to know?"
    )
    return {
        "reply": generate_reply(
            action="clarify",
            user_message=user_message,
            recommendations=[],
            calendar=calendar,
            context={},
            fallback=fallback,
        ),
        "action": "clarify",
        "recommended_event": None,
    }