"""
LangGraph orchestration for AI Scheduling Agent.

Explicit state-based graph separating decision logic (via simple_agent),
side effects (calendar writes), and response generation into distinct nodes.

State contract: { user_id, message, events, calendar, agent_response,
                  previous_recommendations, pending_confirmation_tokens,
                  calendar_write_result, final_response }

Graph Caching:
- The compiled graph is cached as a singleton to avoid recompilation overhead.
- Per-request state is isolated via GraphState instances (thread-safe).
- Factory functions allow lifecycle management and testing.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from threading import Lock
import re
from langgraph.graph import StateGraph, END
from langgraph.types import Send


# Thread-safe singleton cache for compiled graph
_graph_lock = Lock()
_graph_instance = None


@dataclass
class GraphState:
    """
    Explicit state object for the scheduling agent graph.
    
    Fields:
    - user_id: Student identifier from request.
    - message: Raw user input message.
    - events: List of available events (from /events).
    - calendar: User's current calendar events (from /calendar/{user_id}).
    - agent_response: Structured output from simple_agent (action, recommendations, etc.).
    - previous_recommendations: Cache of recommendations shown in prior turns.
    - pending_confirmation_tokens: Tokens waiting for confirmation (yes <id>).
    - calendar_write_result: Result object from add_to_calendar side effect.
    - final_response: Final response to return to user (reply, action, etc.).
    """
    user_id: str
    message: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    calendar: List[Dict[str, Any]] = field(default_factory=list)
    agent_response: Optional[Dict[str, Any]] = None
    previous_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    pending_confirmation_tokens: List[Union[str, int]] = field(default_factory=list)
    calendar_write_result: Optional[Dict[str, Any]] = None
    final_response: Optional[Dict[str, Any]] = None
    action_path: str = "decision->response"


def _is_calendar_add_like_message(message: str) -> bool:
    lowered = (message or "").lower()
    add_terms = ["add", "schedule", "put", "calendar", "exam", "test", "assignment", "meeting"]
    return any(term in lowered for term in add_terms)


def _derive_observability_payload(state: GraphState) -> Dict[str, Any]:
    response = state.agent_response or {}
    action = str(response.get("action", "unknown"))
    payload: Dict[str, Any] = {
        "action": action,
        "action_path": state.action_path,
        "clarification_reason_tags": [],
    }

    if _is_calendar_add_like_message(state.message):
        try:
            from agent.agent import _parse_event_slots

            slots = _parse_event_slots(state.message)
            missing_fields = list(slots.get("missing_fields", [])) if isinstance(slots, dict) else []
            payload["extraction"] = {
                "confidence": float(slots.get("confidence", 0.0)) if isinstance(slots, dict) else 0.0,
                "missing_fields": missing_fields,
                "is_complete": len(missing_fields) == 0,
            }
        except Exception:
            payload["extraction"] = {
                "confidence": 0.0,
                "missing_fields": ["unavailable"],
                "is_complete": False,
            }

    if action == "clarify":
        reply_text = str(response.get("reply", "")).lower()
        tags: List[str] = []

        if response.get("conflicting_events"):
            tags.append("conflict_overlap_confirmed")
        if "valid id" in reply_text or "no event found by that id" in reply_text:
            tags.append("confirmation_id_not_found")
        if "kept your existing calendar unchanged" in reply_text:
            tags.append("conflict_keep_existing")

        extraction = payload.get("extraction", {})
        if isinstance(extraction, dict):
            for field in extraction.get("missing_fields", []):
                if re.match(r"^[a-z_]+$", str(field)):
                    tags.append(f"missing_{field}")

        if not tags:
            tags.append("generic_clarify")
        payload["clarification_reason_tags"] = tags

    return payload


def _agent_decision_node(state: GraphState) -> GraphState:
    """
    Decision node: invoke simple_agent to classify intent and generate recommendations.
    
    Does NOT mutate calendar. Only produces agent_response with action, recommendations, etc.
    Routes to either action_node (for side effects) or response_node (direct reply).
    """
    from agent.agent import simple_agent
    
    response = simple_agent(
        user_id=state.user_id,
        user_message=state.message,
        events=state.events,
        calendar=state.calendar
    )
    
    # Cache recommendations for next turn
    if "recommendations" in response and response["recommendations"]:
        state.previous_recommendations = response["recommendations"]
    
    state.agent_response = response
    return state


def _calendar_action_node(state: GraphState) -> GraphState:
    """
    Action node: perform side effects (calendar writes) triggered by agent decision.
    
    Called when agent_response action requires calendar side effects.
    Calls calendar API-layer functions to persist event or replace conflicts.
    Stores result in calendar_write_result for response_node context.
    """
    from routes.calendar import add_calendar_event, remove_conflicting_calendar_events, CalendarEvent

    if state.agent_response and state.agent_response.get("action") in {
        "add_to_calendar",
        "replace_conflicting_with_personal",
    }:
        event_to_add = state.agent_response.get("event_to_add")
        if event_to_add:
            action = state.agent_response.get("action")
            replacement_result = None
            if action == "replace_conflicting_with_personal":
                replacement_result = remove_conflicting_calendar_events(
                    state.user_id,
                    event_to_add.get("date"),
                    event_to_add.get("start_time"),
                    event_to_add.get("end_time"),
                )

            event_obj = CalendarEvent(
                title=event_to_add.get("title"),
                time=f"{event_to_add.get('start_time')}-{event_to_add.get('end_time')}",
                date=event_to_add.get("date"),
            )
            add_result = add_calendar_event(state.user_id, event_obj)
            state.calendar_write_result = {
                "replacement": replacement_result,
                "add": add_result,
            }
            # Update local calendar state for next turn
            state.calendar.append(event_obj.model_dump(exclude_none=True))
    
    return state


def _response_node(state: GraphState) -> GraphState:
    """
    Response node: produce final JSON response to return to user.
    
    Transforms agent_response and side effect results into strict output contract:
    { reply, action, recommendations?, requires_confirmation?, confirmation_token?, ... }
    """
    response = state.agent_response or {}
    
    # Build final response with guaranteed fields
    final = {
        "reply": response.get("reply", "I can help you find events and manage your schedule."),
        "action": response.get("action", "clarify"),
    }
    
    # Add optional fields based on action
    if "recommendations" in response:
        final["recommendations"] = response["recommendations"]
    if "requires_confirmation" in response:
        final["requires_confirmation"] = response["requires_confirmation"]
    if "confirmation_token" in response:
        final["confirmation_token"] = response["confirmation_token"]
    if "event_to_add" in response:
        final["event_to_add"] = response["event_to_add"]
    if "conflicting_events" in response:
        final["conflicting_events"] = response["conflicting_events"]

    final["_trace"] = _derive_observability_payload(state)
    
    state.final_response = final
    return state


def _route_after_decision(state: GraphState) -> str:
    """
    Conditional edge: route to action_node if side effects needed, else to response_node.
    
    Routes to "action" if agent_response action mutates calendar state.
    Routes to "response" for all other cases (recommend, clarify, show_schedule, etc).
    """
    action = state.agent_response.get("action") if state.agent_response else None

    if action in {"add_to_calendar", "replace_conflicting_with_personal"}:
        state.action_path = "decision->action->response"
        return "action"
    else:
        state.action_path = "decision->response"
        return "response"


def build_graph() -> StateGraph:
    """
    Build and return the compiled scheduling agent graph.
    
    Nodes:
    - decision: invoke simple_agent, classify intent
    - action: perform side effects (calendar writes)
    - response: produce final JSON response
    
    Edges:
    - decision -> action (if add_to_calendar) or response (otherwise)
    - action -> response (after side effect complete)
    - response -> END
    """
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("decision", _agent_decision_node)
    graph.add_node("action", _calendar_action_node)
    graph.add_node("response", _response_node)
    
    # Add edges
    graph.add_edge("action", "response")
    graph.add_conditional_edges(
        "decision",
        _route_after_decision,
        {
            "action": "action",
            "response": "response"
        }
    )
    graph.add_edge("response", END)
    
    # Set entry point
    graph.set_entry_point("decision")
    
    return graph


# Compiled graph instance (singleton for performance)
_graph_instance = None


def _compile_graph():
    """
    Internal factory: build and compile the graph.
    Called once by get_compiled_graph() to initialize the singleton.
    """
    graph = build_graph().compile()
    return graph


def get_compiled_graph():
    """
    Return compiled graph instance (thread-safe lazy initialization).
    
    This is called per-request, but the graph is compiled only once.
    Per-request state isolation is guaranteed via GraphState instances.
    
    Thread-safe: uses lock to ensure only one compilation even under concurrency.
    
    Returns:
        Compiled LangGraph instance ready for invocation.
    """
    global _graph_instance
    if _graph_instance is None:
        with _graph_lock:
            # Double-check pattern: recheck after acquiring lock
            if _graph_instance is None:
                _graph_instance = _compile_graph()
    return _graph_instance


def reset_graph_cache():
    """
    Reset the compiled graph cache.
    
    Useful for testing or dynamic reloading. In production, this should not be called
    on a running server, as graph compilation is expensive.
    """
    global _graph_instance
    with _graph_lock:
        _graph_instance = None


def get_graph_cache_stats() -> Dict[str, Any]:
    """
    Return cache statistics for monitoring/debugging.
    """
    return {
        "cached": _graph_instance is not None,
        "instance": type(_graph_instance).__name__ if _graph_instance else None,
    }


def invoke_graph(user_id: str, message: str, events: List[Dict], calendar: List[Dict]) -> Dict[str, Any]:
    """
    Invoke the scheduling agent graph for a single request.
    
    Cache behavior:
    - Graph is compiled once and cached globally (expensive operation, done once at startup).
    - State is initialized fresh per request (GraphState instance isolated per call).
    - User data is never shared across requests.
    
    Args:
        user_id: Student identifier
        message: User input message
        events: Available events list
        calendar: User's calendar events
    
    Returns:
        final_response dict containing: reply, action, recommendations, etc.
        
    Thread-safe: Multiple concurrent requests reuse the same compiled graph instance
    with isolated GraphState per request.
    """
    graph = get_compiled_graph()
    
    initial_state = GraphState(
        user_id=user_id,
        message=message,
        events=events,
        calendar=calendar
    )
    
    # Graph.invoke returns a dict (serialized state), not the dataclass object
    final_state_dict = graph.invoke(initial_state.__dict__)
    return final_state_dict.get("final_response", {
        "reply": "Unable to process request",
        "action": "error"
    })
