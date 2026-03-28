from fastapi import APIRouter
from pydantic import BaseModel
from time import perf_counter

from agent.graph import invoke_graph
from routes.events import get_events
from routes.calendar import get_calendar
from routes.chat_metrics import chat_metrics_store

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
    start = perf_counter()
    response = invoke_graph(
        user_id=request.user_id,
        message=request.message,
        events=events,
        calendar=calendar
    )
    trace = response.pop("_trace", None) if isinstance(response, dict) else None

    latency_ms = (perf_counter() - start) * 1000
    chat_metrics_store.record_turn(
        user_id=request.user_id,
        message=request.message,
        response=response,
        latency_ms=latency_ms,
        trace=trace,
    )
    
    return response


@router.get("/chat/metrics")
def get_chat_metrics():
    """Runtime baseline metrics for chat responsiveness and redundancy tracking."""
    return chat_metrics_store.snapshot()


@router.get("/chat/metrics/prompts")
def get_chat_prompt_corpus():
    """Collected prompt corpus used for parser/regression tuning."""
    fixed = chat_metrics_store.fixed_prompt_corpus()
    observed = chat_metrics_store.prompt_corpus()
    return {
        "fixed_count": len(fixed),
        "fixed_prompts": fixed,
        "observed_count": len(observed),
        "observed_prompts": observed,
    }


@router.post("/chat/metrics/reset")
def reset_chat_metrics():
    """Reset in-memory metrics and prompt corpus baseline."""
    chat_metrics_store.reset()
    return {"message": "Chat metrics reset"}