"""Smoke tests for the therapist sub-graph."""
from __future__ import annotations

from agents.therapist_graph import build_therapist_graph
from agents.nodes import therapist_recommend, therapist_respond
from agents.state import make_initial_therapy_state
from langgraph.checkpoint.memory import MemorySaver


def test_therapist_compiles(graph_factory):
    graph = graph_factory(use_memory=True)
    assert graph["therapist"] is not None


def test_therapist_runs_to_recommendation(monkeypatch):
    def fake_respond(_state):
        return {
            "therapist_reply": "I hear you.",
            "coping_strategy": "Take 3 deep breaths.",
            "stop_questioning": True,
            "reason_for_stopping": "ok",
            "conversation_history": [
                {"role": "assistant", "content": "I hear you."}
            ],
        }

    def fake_recommend(_state):
        return {"recommendation": "Warm summary."}

    monkeypatch.setattr(therapist_respond, "respond", fake_respond)
    monkeypatch.setattr(therapist_recommend, "recommend", fake_recommend)

    graph = build_therapist_graph(MemorySaver())
    state = make_initial_therapy_state(
        {"age": 25, "sex": "female", "symptoms": "feeling anxious"}
    )
    config = {"configurable": {"thread_id": "t1"}}

    # First invoke: respond runs (interrupt_after), then graph pauses.
    graph.invoke(state, config=config)
    snap1 = graph.get_state(config)
    ther1 = snap1.values
    assert ther1.get("therapist_reply") == "I hear you."
    assert ther1.get("stop_questioning") is True

    # Resume — the graph jumps to recommend and ends.
    graph.invoke(None, config=config)
    snap = graph.get_state(config)
    ther = snap.values
    assert ther.get("therapist_reply") == "I hear you."
    assert ther.get("stop_questioning") is True
    assert ther.get("current_step") == "recommended"
    assert ther.get("recommendation") == "Warm summary."
