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
    
    Only called when agent_response action is "add_to_calendar".
    Calls calendar API-layer function to persist event.
    Stores result in calendar_write_result for response_node context.
    """
    from routes.calendar import add_calendar_event, CalendarEvent
    
    if state.agent_response and state.agent_response.get("action") == "add_to_calendar":
        event_to_add = state.agent_response.get("event_to_add")
        if event_to_add:
            event_obj = CalendarEvent(
                title=event_to_add.get("title"),
                time=f"{event_to_add.get('start_time')}-{event_to_add.get('end_time')}",
                date=event_to_add.get("date"),
            )
            result = add_calendar_event(state.user_id, event_obj)
            state.calendar_write_result = result
            # Update local calendar state for next turn
            state.calendar.append(event_obj.dict())
    
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
    
    state.final_response = final
    return state


def _route_after_decision(state: GraphState) -> str:
    """
    Conditional edge: route to action_node if side effects needed, else to response_node.
    
    Routes to "action" if agent_response action is "add_to_calendar".
    Routes to "response" for all other cases (recommend, clarify, show_schedule, etc).
    """
    action = state.agent_response.get("action") if state.agent_response else None
    
    if action == "add_to_calendar":
        return "action"
    else:
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
