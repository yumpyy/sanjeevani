"""Graph state TypedDicts for the Sanjeevani LangGraph backend.

These TypedDicts are the single source of truth for the data that flows
through each LangGraph graph. Nodes return partial patches; the framework
merges them into the running state.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict


class PhysicianState(TypedDict, total=False):
    """State carried by the physician sub-graph."""

    patient_details: Dict[str, Any]
    visual_analysis: str

    symptoms: List[str]
    chief_complaint: str

    conversation_history: List[Dict[str, str]]

    potential_diagnoses: List[str]
    diagnosis_reasoning: str
    diagnosis: str

    prescription: Dict[str, Any]
    soap_note: str
    sources: List[Dict[str, Any]]

    clarification_question: str
    stop_questioning: bool
    reason_for_stopping: str

    is_emergency: bool
    emergency_message: str

    current_step: str
    last_pending_question: str


class TherapyState(TypedDict, total=False):
    """State carried by the therapist sub-graph."""

    patient_details: Dict[str, Any]
    symptoms: str
    conversation_history: List[Dict[str, str]]

    therapist_reply: str
    coping_strategy: str

    stop_questioning: bool
    reason_for_stopping: str

    current_step: str
    last_pending_question: str
    recommendation: str


class SupervisorState(TypedDict, total=False):
    """Top-level state that orchestrates physician vs. therapist sub-graphs."""

    patient_details: Dict[str, Any]
    visual_analysis: str

    doctor_type: Literal["physician", "therapist"]

    physician: PhysicianState
    therapy: TherapyState

    final_recommendation: Dict[str, Any]

    is_emergency: bool
    emergency_message: str

    current_step: str


def make_initial_physician_state(
    patient_details: Dict[str, Any],
    visual_analysis: str = "",
) -> PhysicianState:
    """Build the initial physician state for a new session."""
    return {
        "patient_details": patient_details,
        "visual_analysis": visual_analysis,
        "symptoms": [],
        "chief_complaint": patient_details.get("symptoms", ""),
        "conversation_history": [],
        "potential_diagnoses": [],
        "diagnosis_reasoning": "",
        "diagnosis": "",
        "prescription": {},
        "soap_note": "",
        "sources": [],
        "clarification_question": "",
        "stop_questioning": False,
        "reason_for_stopping": "",
        "is_emergency": False,
        "emergency_message": "",
        "current_step": "initial",
        "last_pending_question": "",
    }


def make_initial_therapy_state(
    patient_details: Dict[str, Any],
) -> TherapyState:
    """Build the initial therapist state for a new session."""
    return {
        "patient_details": patient_details,
        "symptoms": patient_details.get("symptoms", ""),
        "conversation_history": [],
        "therapist_reply": "",
        "coping_strategy": "",
        "stop_questioning": False,
        "reason_for_stopping": "",
        "current_step": "initial",
        "last_pending_question": "",
        "recommendation": "",
    }


def make_initial_supervisor_state(
    patient_details: Dict[str, Any],
    visual_analysis: str = "",
    doctor_type: Optional[Literal["physician", "therapist"]] = None,
) -> SupervisorState:
    """Build the initial supervisor state for a new session."""
    return {
        "patient_details": patient_details,
        "visual_analysis": visual_analysis,
        "doctor_type": doctor_type or "",  # type: ignore[typeddict-item]
        "physician": make_initial_physician_state(patient_details, visual_analysis),
        "therapy": make_initial_therapy_state(patient_details),
        "final_recommendation": {},
        "is_emergency": False,
        "emergency_message": "",
        "current_step": "initial",
    }
