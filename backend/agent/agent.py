import os
from typing import List, Dict
from pathlib import Path
from datetime import datetime, timedelta
import re
import time

import requests

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

_ENV_LOADED = False
_DISCOVERED_MODELS_CACHE: List[str] = []
_DISCOVERED_MODELS_CACHE_TS = 0.0

MISTRAL_MODEL_FALLBACKS = [
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
    return os.getenv("MISTRAL_MODEL", "mistralai/mistral-7b-instruct-v0.1")


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
    raw = os.getenv("OPENROUTER_ENABLE_MODEL_DISCOVERY", "false").strip().lower()
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
        return fallback

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
                return fallback

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
        return fallback

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
            "Write a single warm, upbeat confirmation sentence (max 20 words). "
            "Do not ask further questions."
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


def normalize_calendar_entries(calendar: List[Dict]) -> List[Dict]:
    normalized = []
    for entry in calendar:
        if entry.get("start_time") and entry.get("end_time"):
            normalized.append(entry)
            continue

        time_parts = _split_time_range(entry.get("time", ""))
        normalized.append(
            {
                "title": entry.get("title", "Untitled"),
                "date": entry.get("date"),
                "start_time": time_parts["start_time"],
                "end_time": time_parts["end_time"],
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


def _extract_personal_event_request(user_id: str, message: str) -> Dict:
    lowered = message.lower()
    is_calendar_intent = any(term in lowered for term in ["calendar", "add", "schedule", "put"])
    extracted = _extract_date_time(message)
    draft = PERSONAL_EVENT_DRAFTS.get(user_id, {})
    title_from_message = _extract_personal_event_title(message)
    title = title_from_message or draft.get("title", "")
    inherited_calendar_intent = bool(draft.get("calendar_intent", False))
    calendar_intent = is_calendar_intent or inherited_calendar_intent

    if title and extracted:
        PERSONAL_EVENT_DRAFTS.pop(user_id, None)
        return {
            "title": title,
            "date": extracted["date"],
            "start_time": extracted["start_time"],
            "end_time": extracted["end_time"],
            "type": "personal",
            "calendar_intent": calendar_intent,
        }

    # Only create a new draft if we have a valid title (not empty)
    if title and not extracted:
        PERSONAL_EVENT_DRAFTS[user_id] = {
            "title": title,
            "calendar_intent": calendar_intent,
        }
        return {"pending": True, "title": title, "calendar_intent": is_calendar_intent}

    if draft and extracted:
        PERSONAL_EVENT_DRAFTS.pop(user_id, None)
        return {
            "title": draft.get("title", "Personal Event"),
            "date": extracted["date"],
            "start_time": extracted["start_time"],
            "end_time": extracted["end_time"],
            "type": "personal",
            "calendar_intent": True,
        }

    return {}


def _store_pending_personal_event(user_id: str, event: Dict) -> None:
    PENDING_PERSONAL_EVENTS[user_id] = event


def _get_pending_personal_event(user_id: str) -> Dict:
    return PENDING_PERSONAL_EVENTS.get(user_id, {})


def _clear_pending_personal_event(user_id: str) -> None:
    PENDING_PERSONAL_EVENTS.pop(user_id, None)


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
            if event["date"] == entry["date"]:
                if time_overlap(
                    event["start_time"], event["end_time"],
                    entry["start_time"], entry["end_time"],
                ):
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
        if event["date"] == entry["date"]:
            if time_overlap(
                event["start_time"], event["end_time"],
                entry["start_time"], entry["end_time"],
            ):
                score -= 3

    return max(0, min(10, score))


def simple_agent(
    user_id: str, user_message: str, events: List[Dict], calendar: List[Dict]
) -> Dict:
    """Main agent logic. Returns dict matching ChatResponse format."""
    message = user_message.lower()
    profile = get_user_profile(user_id)
    calendar = normalize_calendar_entries(calendar)

    # If a personal event is already pending and user repeats a date/time,
    # treat it as confirmation data instead of re-entering clarification loops.
    pending_personal_event = _get_pending_personal_event(user_id)
    repeated_datetime = _extract_date_time(user_message)
    if pending_personal_event and repeated_datetime and not _extract_personal_event_title(user_message):
        merged_event = {
            **pending_personal_event,
            "date": repeated_datetime["date"],
            "start_time": repeated_datetime["start_time"],
            "end_time": repeated_datetime["end_time"],
            "calendar_intent": True,
        }
        _clear_pending_personal_event(user_id)
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

    personal_event = _extract_personal_event_request(user_id, user_message)
    if personal_event.get("pending"):
        fallback = f"I have the title '{personal_event.get('title')}'. What exact date and time should I put on your calendar?"
        return {
            "reply": fallback,
            "action": "clarify",
            "recommended_event": None,
        }

    if personal_event.get("title") and personal_event.get("date"):
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
        # User is confirming the pending personal event - add it
        _clear_pending_personal_event(user_id)
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
            for entry in calendar_with_pending_event:
                if ev.get("date") == entry.get("date") and time_overlap(
                    ev.get("start_time"), ev.get("end_time"),
                    entry.get("start_time"), entry.get("end_time"),
                ):
                    has_conflict = True
                    break
            recommendations.append(
                {
                    "event": ev,
                    "score": score,
                    "reason": "Potential conflict" if has_conflict else "No schedule conflicts",
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
            for entry in calendar:
                if event.get("date") == entry.get("date"):
                    if time_overlap(
                        event.get("start_time"), event.get("end_time"),
                        entry.get("start_time"), entry.get("end_time"),
                    ):
                        conflict = True
                        break
            if not conflict:
                reasons.append("No schedule conflicts")

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

        # Detect conflict for the best event
        has_conflict = False
        conflict_with = None
        for entry in calendar:
            if best_event.get("date") == entry.get("date"):
                if time_overlap(
                    best_event.get("start_time"), best_event.get("end_time"),
                    entry.get("start_time"), entry.get("end_time"),
                ):
                    has_conflict = True
                    conflict_with = entry
                    break

        if has_conflict:
            # Find the best conflict-free alternative among top picks
            alternative_event = None
            for score, ev in top_events:
                conflict = False
                for entry in calendar:
                    if ev.get("date") == entry.get("date"):
                        if time_overlap(
                            ev.get("start_time"), ev.get("end_time"),
                            entry.get("start_time"), entry.get("end_time"),
                        ):
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