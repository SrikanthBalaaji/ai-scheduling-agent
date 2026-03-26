from datetime import datetime
from typing import List, Dict
import requests

def time_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or end2 <= start1)

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
                "type": "personal"
            }
        ]
    return []

def get_user_profile(user_id: str) -> Dict:
    """Fetch profile from our own API."""
    try:
        resp = requests.get(f"http://localhost:8000/profile/{user_id}")
        if resp.status_code == 200:
            return resp.json()
    except:
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
                    entry["start_time"], entry["end_time"]
                ):
                    conflicts.append({
                        "event": event,
                        "conflicts_with": entry
                    })
    return conflicts

def score_event(event: Dict, calendar: List[Dict], profile: Dict) -> float:
    """
    Score event 0-10. Higher = better recommendation.
    """
    score = 5.0
    
    interests = [i.lower() for i in profile.get("interests", [])]
    tags = [t.lower() for t in event.get("tags", [])]
    
    for interest in interests:
        if interest in tags:
            score += 2
    
    goals = [g.lower() for g in profile.get("career_goals", [])]
    title_and_desc = (event.get("title", "") + " " + event.get("description", "")).lower()
    for goal in goals:
        if goal in title_and_desc:
            score += 1.5
    
    if "tech" in tags:
        score += 1
    
    if "hackathon" in event.get("title", "").lower():
        score += 0.5
    
    for entry in calendar:
        if event["date"] == entry["date"]:
            if time_overlap(
                event["start_time"], event["end_time"],
                entry["start_time"], entry["end_time"]
            ):
                score -= 3
    
    return max(0, min(10, score))

def simple_agent(user_id: str, user_message: str, events: List[Dict], calendar: List[Dict]) -> Dict:
    """
    Main agent logic. Returns dict matching ChatResponse format.
    """
    message = user_message.lower()
    profile = get_user_profile(user_id)
    
    if message.startswith("yes ") or message.startswith("confirm "):
        parts = message.split()
        if len(parts) >= 2:
            event_id = parts[1]
            for ev in events:
                if str(ev.get("id")) == event_id:
                    return {
                        "reply": "Adding event to your calendar...",
                        "action": "add_to_calendar",
                        "event_to_add": ev
                    }
        return {
            "reply": "No event found by that id. Please use 'yes <event_id>' from the recommendations.",
            "action": "clarify",
            "recommended_event": None
        }
    
    if "schedule" in message:
        return {
            "reply": f"You have {len(calendar)} items in your calendar.",
            "action": "show_schedule",
            "recommended_event": None
        }
    
    if any(word in message for word in ["conflict", "attend", "recommend", "what should", "suggest"]):
        
        scored = []
        for event in events:
            s = score_event(event, calendar, profile)
            scored.append((s, event))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        if not scored:
            return {
                "reply": "No events available to recommend.",
                "action": "no_events",
                "recommended_event": None
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
                        entry.get("start_time"), entry.get("end_time")
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
            recommendations.append({
                "event": ev,
                "score": score,
                "reason": event_reason(score, ev)
            })

        has_conflict = False
        conflict_with = None
        for entry in calendar:
            if best_event.get("date") == entry.get("date"):
                if time_overlap(
                    best_event.get("start_time"), best_event.get("end_time"),
                    entry.get("start_time"), entry.get("end_time")
                ):
                    has_conflict = True
                    conflict_with = entry
                    break

        if has_conflict:
            alternative_event = None
            for score, ev in top_events:
                conflict = False
                for entry in calendar:
                    if ev.get("date") == entry.get("date"):
                        if time_overlap(
                            ev.get("start_time"), ev.get("end_time"),
                            entry.get("start_time"), entry.get("end_time")
                        ):
                            conflict = True
                            break
                if not conflict:
                    alternative_event = ev
                    break

            if alternative_event:
                return {
                    "reply": f"'{best_event['title']}' conflicts with your schedule. You can attend '{alternative_event['title']}' instead.",
                    "action": "recommend_alternative",
                    "recommended_event": alternative_event,
                    "requires_confirmation": True,
                    "confirmation_token": alternative_event.get("id")
                }
            else:
                return {
                    "reply": f"'{best_event['title']}' conflicts with your schedule. No better alternatives found.",
                    "action": "recommend_with_conflict",
                    "recommended_event": best_event,
                    "confirmation_token": best_event.get("id")
                }

        reply = "Top recommendations:\n"
        for rec in recommendations:
            ev = rec["event"]
            reply += f"- [{ev['id']}] {ev['title']} ({rec['reason']})\n"
        reply += "Say 'yes <event_id>' to add one to your calendar."

        return {
            "reply": reply,
            "action": "recommend_multiple",
            "recommendations": recommendations,
            "requires_confirmation": True,
            "confirmation_token": best_event.get("id")
        }
    
    return {
        "reply": "I can help you find events, check conflicts, or see your schedule. What would you like to know?",
        "action": "clarify",
        "recommended_event": None
    }