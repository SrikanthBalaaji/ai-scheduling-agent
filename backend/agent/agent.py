from datetime import datetime

# TEMP mock calendar (later this comes from DB)
USER_CALENDAR = [
    {
        "title": "Math Test",
        "date": "2026-03-30",
        "start_time": "10:00",
        "end_time": "12:00",
        "type": "personal"
    }
]


def time_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or end2 <= start1)


def detect_conflicts(events, calendar):
    conflicts = []

    for event in events:
        for entry in calendar:
            if event["date"] == entry["date"]:
                if time_overlap(
                    event["start_time"], event["end_time"],
                    entry["start_time"], entry["end_time"]
                ):
                    conflicts.append((event, entry))

    return conflicts


def simple_agent(user_message, events):

    message = user_message.lower()

    # 1. Check schedule
    if "schedule" in message:
        return {
            "reply": f"You have {len(USER_CALENDAR)} planned items.",
            "action": "show_schedule"
        }

    # 2. Check conflicts
    if "conflict" in message or "attend" in message:
        conflicts = detect_conflicts(events, USER_CALENDAR)

        if conflicts:
            event, entry = conflicts[0]
            return {
                "reply": f"You have a conflict between '{event['title']}' and your '{entry['title']}'. I recommend prioritizing your {entry['title']}.",
                "action": "conflict_detected"
            }
        else:
            return {
                "reply": "No conflicts detected. You can attend available events.",
                "action": "no_conflict"
            }

    return {
        "reply": "I'm not sure. Try asking about your schedule or events.",
        "action": None
    }