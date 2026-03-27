import os
from typing import List, Dict

import requests
from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_reply(
    action: str,
    user_message: str,
    recommendations: List[Dict],
    calendar: List[Dict],
    context: Dict,
    fallback: str,
) -> str:
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

    full_prompt = f"{system_prompt}\n\n{user_prompt}"

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
        )
        text = response.text.strip()
        return text if text else fallback

    except Exception as e:
        print("GEMINI ERROR:", e)
        return fallback


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
                "type": "personal",
            }
        ]
    return []


def get_user_profile(user_id: str) -> Dict:
    """Fetch profile from our own API."""
    try:
        resp = requests.get(f"http://localhost:8000/profile/{user_id}")
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

    # ── Confirmation branch ──────────────────────────────────────────────────
    if message.startswith("yes ") or message.startswith("confirm "):
        parts = message.split()
        if len(parts) >= 2:
            event_id = parts[1]
            for ev in events:
                if str(ev.get("id")) == event_id:
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