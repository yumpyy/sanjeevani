"""Therapist sub-graph (LangGraph).

Flow::

    START
      -> respond               (interrupt_before; pauses for human)
      -> recommend              (only if stop_questioning is true)
      -> END
"""
from __future__ import annotations

from typing import Any, Dict, Literal

from langgraph.graph import END, START, StateGraph

from agents.nodes.therapist_recommend import therapist_recommend
from agents.nodes.therapist_respond import therapist_respond
from agents.state import TherapyState


def respond_node(state: TherapyState) -> Dict[str, Any]:
    result = therapist_respond.respond(state)
    return {
        **result,
        "current_step": "responded" if result.get("stop_questioning") else "awaiting_reply",
        "last_pending_question": result.get("therapist_reply", ""),
    }


def recommend_node(state: TherapyState) -> Dict[str, Any]:
    result = therapist_recommend.recommend(state)
    return {
        "recommendation": result.get("recommendation", ""),
        "current_step": "recommended",
    }


def route_after_respond(
    state: TherapyState,
) -> Literal["recommend", "await_user"]:
    if state.get("stop_questioning"):
        return "recommend"
    return "await_user"


def build_therapist_graph(checkpointer):
    g = StateGraph(TherapyState)

    g.add_node("respond", respond_node)
    g.add_node("recommend", recommend_node)

    g.add_edge(START, "respond")
    g.add_conditional_edges(
        "respond",
        route_after_respond,
        {
            "recommend": "recommend",
            "await_user": END,
        },
    )
    g.add_edge("recommend", END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_after=["respond"],
    )
