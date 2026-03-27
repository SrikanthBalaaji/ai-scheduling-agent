from fastapi import APIRouter
from pydantic import BaseModel
from agent.agent import simple_agent
from routes.events import get_events
from routes.calendar import get_calendar, calendar_storage

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
def chat(request: ChatRequest):
    events = [e.dict() for e in get_events()]
    calendar = get_calendar(request.user_id)
    response = simple_agent(request.user_id, request.message, events, calendar)
    
    if response.get("action") == "add_to_calendar":
        event_to_add = response.get("event_to_add")
        if request.user_id not in calendar_storage:
            calendar_storage[request.user_id] = []
        calendar_storage[request.user_id].append({
            "title": event_to_add.get("title"),
            "time": f"{event_to_add.get('start_time')}-{event_to_add.get('end_time')}"
        })
        response["reply"] = f"Event '{event_to_add.get('title')}' added to your calendar!"
    
    return response