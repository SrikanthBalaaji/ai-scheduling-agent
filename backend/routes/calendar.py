from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

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


@router.get("/calendar/{user_id}")
def read_calendar(user_id: str):
    """Read user calendar. Returns list of CalendarEvent objects."""
    return get_calendar(user_id)


@router.post("/calendar/{user_id}")
def write_calendar(user_id: str, event: CalendarEvent):
    """Add event to user calendar. Unified contract with agent write flow."""
    return add_calendar_event(user_id, event)
