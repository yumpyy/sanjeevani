"""Top-level supervisor.

The supervisor is a plain Python function that decides whether a patient
should see the **physician** or the **therapist** sub-graph. It is
intentionally not a ``StateGraph`` itself — the per-patient state machine
lives entirely in the sub-graph, and the FastAPI layer in ``main.py``
invokes the right sub-graph based on the supervisor's classification.

This is the standard LangGraph pattern for multi-agent orchestration: a
thin orchestrator on top of independent stateful agents, rather than a
deeply-nested graph hierarchy that has to manage sub-graph interrupts.
"""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from agents.physician_graph import build_physician_graph
from agents.state import (
    make_initial_physician_state,
    make_initial_therapy_state,
)
from agents.therapist_graph import build_therapist_graph


PSYCHIATRIC_KEYWORDS = (
    "anxiety",
    "anxious",
    "depress",
    "panic",
    "stress",
    "stressed",
    "lonely",
    "loneliness",
    "hopeless",
    "suicidal",
    "self harm",
    "therapy",
    "therapist",
    "mental",
    "emotional",
    "grief",
    "trauma",
    "ptsd",
    "burnout",
)


DoctorType = Literal["physician", "therapist"]


def classify(
    patient_details: Dict[str, Any],
    explicit: Optional[DoctorType] = None,
) -> DoctorType:
    """Pick the doctor type for a new session.

    Honours an explicit choice (set from the API endpoint) and otherwise
    falls back to a deterministic keyword heuristic. No LLM call: the
    check is cheap and explainable.
    """
    if explicit in ("physician", "therapist"):
        return explicit  # type: ignore[return-value]
    text = (patient_details.get("symptoms") or "").lower()
    if any(kw in text for kw in PSYCHIATRIC_KEYWORDS):
        return "therapist"
    return "physician"


def build_subgraph(doctor_type: DoctorType, checkpointer):
    """Return the compiled sub-graph for a doctor type."""
    if doctor_type == "physician":
        return build_physician_graph(checkpointer)
    return build_therapist_graph(checkpointer)


def make_initial_state(
    doctor_type: DoctorType,
    patient_details: Dict[str, Any],
    visual_analysis: str = "",
) -> Dict[str, Any]:
    """Build the initial state for the chosen sub-graph."""
    if doctor_type == "physician":
        return make_initial_physician_state(patient_details, visual_analysis)
    return make_initial_therapy_state(patient_details)
