from fastapi import APIRouter
from pydantic import BaseModel
from agent.agent import simple_agent
from routes.events import get_events  # reuse your function

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def chat(request: ChatRequest):
    events = get_events()   # fetch events
    response = simple_agent(request.message, events)
    return response