from fastapi import APIRouter
from pydantic import BaseModel
from agent.graph import invoke_graph
from routes.events import get_events
from routes.calendar import get_calendar

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str

@router.post("/chat")
def chat(request: ChatRequest):
    """
    Chat endpoint orchestrated by LangGraph.
    
    Graph handles:
    - Decision logic (simple_agent)
    - Side effects (calendar writes in action_node only)
    - Response normalization (response_node)
    
    Route no longer mutates calendar directly; graph manages all state transitions.
    """
    events = [e.dict() for e in get_events()]
    calendar = get_calendar(request.user_id)
    
    # Graph invocation: inject state, orchestrate nodes, return final_response
    response = invoke_graph(
        user_id=request.user_id,
        message=request.message,
        events=events,
        calendar=calendar
    )
    
    return response