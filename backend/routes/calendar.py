from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

# Unified in-memory storage (for hackathon)
# Format: { user_id: [{ "title": str, "time": str }, ...] }
calendar_storage = {}


class CalendarEvent(BaseModel):
    """Canonical calendar event shape used across all routes and write flows."""
    title: str
    time: str
    date: Optional[str] = None


def get_calendar(user_id: str):
    """Get all calendar events for a user. Returns list of CalendarEvent-shaped dicts."""
    return calendar_storage.get(user_id, [])


def add_calendar_event(user_id: str, event: CalendarEvent) -> dict:
    """Internal helper to add an event to user's calendar. Used by both route and agent."""
    if user_id not in calendar_storage:
        calendar_storage[user_id] = []
    event_payload = event.model_dump(exclude_none=True)
    calendar_storage[user_id].append(event_payload)
    return {"message": "Event added", "event": event_payload}


def _normalize_date(date_value: Optional[str]) -> str:
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

    return raw


def _time_to_minutes(time_value: Optional[str]) -> int:
    if not time_value:
        return -1

    value = str(time_value).strip()
    if ":" not in value:
        return -1

    parts = value.split(":", 1)
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return -1

    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        return -1
    return hour * 60 + minute


def _split_time_range(time_range: Optional[str]) -> tuple[str, str]:
    if not time_range or "-" not in time_range:
        return "", ""
    start, end = time_range.split("-", 1)
    return start.strip(), end.strip()


def _overlaps(start1: int, end1: int, start2: int, end2: int) -> bool:
    if min(start1, end1, start2, end2) < 0:
        return False
    if end1 <= start1:
        end1 += 24 * 60
    if end2 <= start2:
        end2 += 24 * 60
    return not (end1 <= start2 or end2 <= start1)


def remove_conflicting_calendar_events(
    user_id: str,
    date: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
) -> dict:
    """Remove calendar entries that overlap the provided date/time window."""
    existing = calendar_storage.get(user_id, [])
    if not existing:
        return {"message": "No events removed", "removed_count": 0, "removed": []}

    target_date = _normalize_date(date)
    target_start = _time_to_minutes(start_time)
    target_end = _time_to_minutes(end_time)

    kept = []
    removed = []

    for entry in existing:
        entry_date = _normalize_date(entry.get("date"))
        entry_start_str, entry_end_str = _split_time_range(entry.get("time"))
        entry_start = _time_to_minutes(entry_start_str)
        entry_end = _time_to_minutes(entry_end_str)

        if target_date and entry_date and target_date == entry_date and _overlaps(target_start, target_end, entry_start, entry_end):
            removed.append(entry)
        else:
            kept.append(entry)

    calendar_storage[user_id] = kept
    return {
        "message": "Conflicting events removed",
        "removed_count": len(removed),
        "removed": removed,
    }


@router.get("/calendar/{user_id}")
def read_calendar(user_id: str):
    """Read user calendar. Returns list of CalendarEvent objects."""
    return get_calendar(user_id)


@router.post("/calendar/{user_id}")
def write_calendar(user_id: str, event: CalendarEvent):
    """Add event to user calendar. Unified contract with agent write flow."""
    return add_calendar_event(user_id, event)
