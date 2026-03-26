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

def simple_agent(user_id: str, user_message: str, events: List[Dict]) -> Dict:
    """
    Main agent logic. Returns dict matching ChatResponse format.
    """
    message = user_message.lower()
    calendar = get_user_calendar(user_id)
    profile = get_user_profile(user_id)
    
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
        
        scored.sort(reverse=True)
        
        if not scored:
            return {
                "reply": "No events available to recommend.",
                "action": "no_events",
                "recommended_event": None
            }
        
        best_score, best_event = scored[0]
        
        has_conflict = False
        conflict_with = None
        for entry in calendar:
            if best_event["date"] == entry["date"]:
                if time_overlap(
                    best_event["start_time"], best_event["end_time"],
                    entry["start_time"], entry["end_time"]
                ):
                    has_conflict = True
                    conflict_with = entry
                    break
        
        if has_conflict:
            return {
                "reply": f"I recommend '{best_event['title']}' (score: {best_score:.1f}/10), but it conflicts with your '{conflict_with['title']}'. Consider which is more important for your goals.",
                "action": "recommend_with_conflict",
                "recommended_event": best_event
            }
        else:
            return {
                "reply": f"I recommend '{best_event['title']}' (score: {best_score:.1f}/10). No conflicts detected.",
                "action": "recommend",
                "recommended_event": best_event
            }
    
    return {
        "reply": "I can help you find events, check conflicts, or see your schedule. What would you like to know?",
        "action": "clarify",
        "recommended_event": None
    }