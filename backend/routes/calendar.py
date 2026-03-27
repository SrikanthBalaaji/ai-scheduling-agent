from fastapi import APIRouter
from datetime import datetime, timedelta

router = APIRouter()

# In-memory storage (for hackathon)
calendar_entries = []


# 🔹 Add event
@router.post("/calendar")
def add_calendar_entry(user_id: int, title: str, time: str, duration: int, priority: int = 3):
    entry = {
        "id": len(calendar_entries) + 1,
        "user_id": user_id,
        "title": title,
        "time": time,
        "duration": duration,
        "priority": priority
    }
    calendar_entries.append(entry)
    return entry


# 🔹 Get user calendar
@router.get("/calendar/{user_id}")
def get_user_calendar(user_id: int):
    return [e for e in calendar_entries if e["user_id"] == user_id]


# 🔹 Delete event
@router.delete("/calendar/{event_id}")
def delete_event(event_id: int):
    global calendar_entries

    before = len(calendar_entries)
    calendar_entries = [e for e in calendar_entries if e["id"] != event_id]

    if before == len(calendar_entries):
        return {"message": "Event not found"}

    return {"message": f"Event {event_id} deleted"}


# 🔹 Conflict detection
@router.get("/conflicts/{user_id}")
def check_conflicts(user_id: int, time: str, duration: int):

    new_start = datetime.strptime(time, "%Y-%m-%d %H:%M")
    new_end = new_start + timedelta(hours=duration)

    user_events = [e for e in calendar_entries if e["user_id"] == user_id]

    conflicts = []

    for event in user_events:
        existing_start = datetime.strptime(event["time"], "%Y-%m-%d %H:%M")
        existing_end = existing_start + timedelta(hours=event["duration"])

        if new_start < existing_end and new_end > existing_start:
            conflicts.append(event)

    return {
        "conflict": len(conflicts) > 0,
        "conflicting_events": conflicts
    }


# 🔹 Smart decision engine
@router.get("/decision/{user_id}")
def decision(user_id: int, time: str, duration: int):

    new_start = datetime.strptime(time, "%Y-%m-%d %H:%M")
    new_end = new_start + timedelta(hours=duration)

    user_events = [e for e in calendar_entries if e["user_id"] == user_id]

    conflicts = []
    suggestions = []

    for event in user_events:
        existing_start = datetime.strptime(event["time"], "%Y-%m-%d %H:%M")
        existing_end = existing_start + timedelta(hours=event["duration"])

        if new_start < existing_end and new_end > existing_start:
            conflicts.append(event)

            overlap_start = max(new_start, existing_start)
            overlap_end = min(new_end, existing_end)
            overlap_duration = (overlap_end - overlap_start).total_seconds() / 3600

            if overlap_duration < duration:
                suggestions.append(
                    f"You can attend part of '{event['title']}' and still manage this event."
                )
            else:
                suggestions.append(
                    f"This fully overlaps with '{event['title']}'. Consider rescheduling."
                )

    if not conflicts:
        return {
            "decision": "attend",
            "reason": "No conflicts in your schedule."
        }

    return {
        "decision": "conflict",
        "reason": "You have overlapping events.",
        "conflicts": conflicts,
        "suggestions": suggestions
    }