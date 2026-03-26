from fastapi import APIRouter
from pydantic import BaseModel

class CalendarEvent(BaseModel):
    title: str
    time: str

router = APIRouter()

calendar_storage = {}

@router.get("/calendar/{user_id}")
def get_calendar(user_id: str):
    return calendar_storage.get(user_id, [])

@router.post("/calendar/{user_id}")
def add_event(user_id: str, event: CalendarEvent):
    if user_id not in calendar_storage:
        calendar_storage[user_id] = []
    calendar_storage[user_id].append(event.dict())
    return {"message": "Event added"}