"""Smoke tests for the physician sub-graph."""
from __future__ import annotations

from agents.state import make_initial_physician_state
from agents.physician_graph import build_physician_graph
from agents.nodes import (
    diagnosis_planner,
    history_collector,
    prescription_generator,
    soap_note_generator,
    symptom_extractor,
)
from langgraph.checkpoint.memory import MemorySaver


def test_physician_compiles(graph_factory):
    graph = graph_factory(use_memory=True)
    assert graph["physician"] is not None


def test_physician_runs_to_completion(graph_factory, monkeypatch):
    monkeypatch.setattr(
        symptom_extractor,
        "extract",
        lambda *_a, **_k: {
            "symptoms": ["headache", "nausea"],
            "chief_complaint": "headache and nausea",
        },
    )
    monkeypatch.setattr(
        diagnosis_planner,
        "plan_diagnosis",
        lambda _s: {
            "potential_diagnoses": ["migraine"],
            "diagnosis_reasoning": "classic presentation",
            "recommended_tests": [],
        },
    )
    monkeypatch.setattr(
        prescription_generator,
        "generate_prescription",
        lambda _s: {
            "diagnosis": "migraine",
            "medications": [],
            "side_effects": [],
            "contraindications": [],
            "alternative_treatments": ["rest"],
            "emergency_steps": [],
            "consultation_required": True,
            "sources": [],
        },
    )
    monkeypatch.setattr(
        soap_note_generator,
        "generate_soap_note",
        lambda _s: {"soap_note": "S: ... O: ... A: ... P: ..."},
    )

    class _Stop:
        def __init__(self):
            self.calls = 0

        def invoke(self, *_a, **_k):
            self.calls += 1
            return {
                "clarification_question": "q",
                "stop_questioning": True,
                "reason_for_stopping": "ok",
                "history_area_current": "a",
            }

    history_stub = _Stop()
    monkeypatch.setattr(history_collector, "collect_next_question", lambda _s: history_stub.invoke())

    graph = build_physician_graph(MemorySaver())
    state = make_initial_physician_state(
        {"age": 30, "sex": "male", "symptoms": "headache and nausea"},
        visual_analysis="",
    )

    thread_id = "test-thread-1"
    config = {"configurable": {"thread_id": thread_id}}

    # First invoke: collect_history runs (interrupt_after), then graph pauses.
    graph.invoke(state, config=config)
    snap1 = graph.get_state(config)
    phys = snap1.values
    # The history-collector ran and stored its pending question.
    assert phys.get("last_pending_question") == "q"
    assert phys.get("stop_questioning") is True

    # Resume with None — graph continues past the pause and runs the rest.
    graph.invoke(None, config=config)
    snap2 = graph.get_state(config)
    phys = snap2.values
    assert phys.get("current_step") == "soap_note_generated"
    assert phys.get("diagnosis") == "migraine"
    assert phys.get("soap_note", "").startswith("S:")


def test_emergency_short_circuits(graph_factory, monkeypatch):
    """Cardiac keyword input should set is_emergency on the first invoke."""
    monkeypatch.setattr(
        symptom_extractor,
        "extract",
        lambda *_a, **_k: {"symptoms": ["chest pain"], "chief_complaint": "chest pain"},
    )

    graph = build_physician_graph(MemorySaver())
    state = make_initial_physician_state(
        {
            "age": 60,
            "sex": "male",
            "symptoms": "severe crushing chest pain and pain in jaw and arm",
        },
        visual_analysis="",
    )
    config = {"configurable": {"thread_id": "test-emergency"}}
    graph.invoke(state, config=config)
    snap = graph.get_state(config)
    phys = snap.values
    assert phys.get("is_emergency") is True
    assert phys.get("stop_questioning") is True
    assert "emergency" in (phys.get("reason_for_stopping") or "").lower()
