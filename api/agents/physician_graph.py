"""Physician sub-graph (LangGraph).

Flow::

    START
      -> check_emergency
      -> extract_symptoms
      -> collect_history        (interrupt_before; pauses for human)
      -> plan_diagnosis         (only if stop_questioning is true)
      -> generate_prescription
      -> generate_soap_note
      -> END

The graph compiles with ``interrupt_before=["collect_history"]`` and a
Postgres-backed ``checkpointer``. On each ``/continue`` call the API
layer re-invokes the graph with the same ``thread_id`` and LangGraph
resumes from the paused node.
"""
from __future__ import annotations

from typing import Any, Dict, Literal

from langgraph.graph import END, START, StateGraph

from agents.nodes.diagnosis_planner import diagnosis_planner
from agents.nodes.history_collector import history_collector
from agents.nodes.prescription_generator import prescription_generator
from agents.nodes.soap_note_generator import soap_note_generator
from agents.nodes.symptom_extractor import symptom_extractor
from agents.state import PhysicianState
from agents.tools.emergency_tool import emergency_check_tool


def _format_history(history: list) -> str:
    if not history:
        return "No previous questions asked yet."
    parts = []
    for item in history:
        if item.get("role") == "user":
            parts.append(f"Patient: {item.get('content', '')}")
        elif item.get("role") == "assistant":
            parts.append(f"Doctor: {item.get('content', '')}")
    return "\n\n".join(parts) or "No previous questions asked yet."


def check_emergency_node(state: PhysicianState) -> Dict[str, Any]:
    """Run the regex emergency detector once at the start of a session."""
    patient_details = state.get("patient_details", {}) or {}
    patient_text = patient_details.get("symptoms", "")
    visual = state.get("visual_analysis", "")

    try:
        result = emergency_check_tool.invoke(
            {
                "patient_text": patient_text,
                "symptoms": patient_text,
                "visual_analysis": visual or None,
            }
        )
        is_emergency = bool(result.get("is_emergency"))
        urgency = result.get("urgency_level", "normal")
        emergency_type = result.get("emergency_type")
        description = result.get("description", "")
    except Exception as e:
        print(f"Emergency check error: {e}")
        is_emergency = False
        urgency = "normal"
        emergency_type = None
        description = ""

    if is_emergency or urgency == "critical":
        return {
            "is_emergency": True,
            "emergency_message": description,
            "stop_questioning": True,
            "reason_for_stopping": f"Emergency detected: {emergency_type}",
            "current_step": "emergency_detected",
        }

    return {
        "is_emergency": False,
        "current_step": "symptom_extraction",
    }


def extract_symptoms_node(state: PhysicianState) -> Dict[str, Any]:
    patient_text = (state.get("patient_details") or {}).get("symptoms", "")
    visual = state.get("visual_analysis", "")
    result = symptom_extractor.extract(patient_text, visual)
    return {
        "symptoms": result.get("symptoms", []),
        "chief_complaint": result.get("chief_complaint", state.get("chief_complaint", "")),
        "current_step": "symptoms_extracted",
    }


def collect_history_node(state: PhysicianState) -> Dict[str, Any]:
    result = history_collector.collect_next_question(state)
    return {
        "clarification_question": result.get("clarification_question", ""),
        "stop_questioning": result.get("stop_questioning", False),
        "reason_for_stopping": result.get("reason_for_stopping", ""),
        "current_step": "history_collected"
        if result.get("stop_questioning")
        else "awaiting_answer",
        "last_pending_question": result.get("clarification_question", ""),
    }


def plan_diagnosis_node(state: PhysicianState) -> Dict[str, Any]:
    result = diagnosis_planner.plan_diagnosis(state)
    return {
        "potential_diagnoses": result.get("potential_diagnoses", []),
        "diagnosis_reasoning": result.get("diagnosis_reasoning", ""),
        "current_step": "diagnosis_planned",
    }


def generate_prescription_node(state: PhysicianState) -> Dict[str, Any]:
    result = prescription_generator.generate_prescription(state)
    return {
        "diagnosis": result.get("diagnosis", ""),
        "prescription": {
            "medications": result.get("medications", []),
            "side_effects": result.get("side_effects", []),
            "contraindications": result.get("contraindications", []),
            "alternative_treatments": result.get("alternative_treatments", []),
            "emergency_steps": result.get("emergency_steps", []),
            "consultation_required": result.get("consultation_required", True),
        },
        "sources": result.get("sources", []),
        "current_step": "prescription_generated",
    }


def generate_soap_note_node(state: PhysicianState) -> Dict[str, Any]:
    result = soap_note_generator.generate_soap_note(state)
    return {
        "soap_note": result.get("soap_note", ""),
        "current_step": "soap_note_generated",
    }


def route_after_history(
    state: PhysicianState,
) -> Literal["plan_diagnosis", "await_user"]:
    if state.get("stop_questioning"):
        return "plan_diagnosis"
    return "await_user"


def route_after_emergency(
    state: PhysicianState,
) -> Literal["emergency_exit", "extract_symptoms"]:
    if state.get("is_emergency"):
        return "emergency_exit"
    return "extract_symptoms"


def build_physician_graph(checkpointer):
    g = StateGraph(PhysicianState)

    g.add_node("check_emergency", check_emergency_node)
    g.add_node("extract_symptoms", extract_symptoms_node)
    g.add_node("collect_history", collect_history_node)
    g.add_node("plan_diagnosis", plan_diagnosis_node)
    g.add_node("generate_prescription", generate_prescription_node)
    g.add_node("generate_soap_note", generate_soap_note_node)

    g.add_edge(START, "check_emergency")
    g.add_conditional_edges(
        "check_emergency",
        route_after_emergency,
        {
            "emergency_exit": END,
            "extract_symptoms": "extract_symptoms",
        },
    )
    g.add_edge("extract_symptoms", "collect_history")

    g.add_conditional_edges(
        "collect_history",
        route_after_history,
        {
            "plan_diagnosis": "plan_diagnosis",
            "await_user": END,  # re-entry resumes at collect_history
        },
    )
    g.add_edge("plan_diagnosis", "generate_prescription")
    g.add_edge("generate_prescription", "generate_soap_note")
    g.add_edge("generate_soap_note", END)

    return g.compile(
        checkpointer=checkpointer,
        interrupt_after=["collect_history"],
    )
