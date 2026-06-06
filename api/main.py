"""FastAPI app for Sanjeevani.

The endpoints below match the previous version so the Next.js frontend
keeps working unchanged. Internally the API:

* Uses ``agents.supervisor.classify`` to pick physician vs. therapist.
* Builds the appropriate sub-graph against a Postgres checkpointer.
* Threads ``{doctor_type}:{session_id}`` as the LangGraph ``thread_id``
  so the two sub-graphs cannot collide on the same session.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.state import (
    make_initial_physician_state,
    make_initial_therapy_state,
)
from agents.supervisor import (
    DoctorType,
    build_subgraph,
    classify,
    make_initial_state,
)
from config import get_checkpointer
from doctors.models import ClarificationAnswers, PatientDetails


load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sanjeevani")


app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Graph bootstrap (singletons, lazy) ---
_physician_graph = None
_therapist_graph = None


def _get_physician_graph():
    global _physician_graph
    if _physician_graph is None:
        _physician_graph = build_subgraph("physician", get_checkpointer())
    return _physician_graph


def _get_therapist_graph():
    global _therapist_graph
    if _therapist_graph is None:
        _therapist_graph = build_subgraph("therapist", get_checkpointer())
    return _therapist_graph


# --- Routes ---


@app.get("/")
async def root():
    return {"message": "Sanjeevani API - AI Healthcare Assistant"}


@app.get("/doctors/")
async def get_doctors():
    return {"available_doctors": ["physician", "therapist"]}


@app.get("/health")
async def health():
    return {"status": "ok"}


def _config_for(session_id: str, doctor_type: Optional[DoctorType] = None) -> Dict[str, Any]:
    """Build a LangGraph config. If ``doctor_type`` is provided, namespace
    the thread_id so the two sub-graphs don't share checkpoint rows."""
    if doctor_type is None:
        return {"configurable": {"thread_id": session_id}}
    return {"configurable": {"thread_id": f"{doctor_type}:{session_id}"}}


def _state_snapshot(graph, session_id: str, doctor_type: DoctorType) -> Dict[str, Any]:
    snap = graph.get_state(_config_for(session_id, doctor_type))
    return dict(snap.values or {})


def _merge_user_answer(
    state_snapshot: Dict[str, Any],
    answers: Dict[str, str],
) -> Dict[str, Any]:
    """Append the latest user message to whichever sub-state is active."""
    answer_text = ""
    if answers:
        for ans in answers.values():
            if ans:
                answer_text = ans
                break

    history = list(state_snapshot.get("conversation_history", []))
    last_q = state_snapshot.get("last_pending_question")

    if last_q and answer_text:
        history.append({"role": "assistant", "content": last_q})
        history.append({"role": "user", "content": answer_text})
        return {
            "conversation_history": history,
            "last_pending_question": "",
        }

    if answer_text:
        # No pending question recorded (graph hasn't asked yet). Just
        # store the answer so the next ask-step can reference it.
        history.append({"role": "user", "content": answer_text})
        return {"conversation_history": history}

    return {}


def _format_physician(state_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if state_snapshot.get("is_emergency"):
        return {
            "diagnosis_complete": True,
            "message": state_snapshot.get("emergency_message", "Emergency detected"),
            "is_emergency": True,
        }
    if state_snapshot.get("current_step") == "soap_note_generated":
        return {
            "diagnosis_complete": True,
            "message": state_snapshot.get("reason_for_stopping", "Assessment complete"),
            "recommendation_summary": state_snapshot.get("diagnosis", ""),
        }
    return {
        "diagnosis_complete": False,
        "response": state_snapshot.get("last_pending_question")
        or state_snapshot.get("clarification_question")
        or "Can you tell me more about your symptoms?",
        "reason": state_snapshot.get("reason_for_stopping", "Gathering medical history"),
    }


def _format_therapist(state_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    if state_snapshot.get("current_step") == "recommended":
        return {
            "diagnosis_complete": True,
            "response": state_snapshot.get("recommendation", ""),
            "reason": state_snapshot.get("reason_for_stopping", "Session concluded"),
        }
    return {
        "diagnosis_complete": False,
        "response": state_snapshot.get("last_pending_question")
        or state_snapshot.get("therapist_reply", ""),
        "reason": state_snapshot.get("reason_for_stopping", "Continuing conversation"),
    }


@app.post("/diagnosis/{doctor_id}/")
async def start_diagnosis(
    doctor_id: str, patient_details: PatientDetails
) -> Dict[str, Any]:
    if doctor_id not in ("physician", "therapist"):
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    session_id = str(uuid.uuid4())
    details = patient_details.model_dump()
    image_data = details.pop("image_data", "")

    # Honour the explicit choice but run it through the classifier for
    # validation / consistency.
    doctor_type: DoctorType = classify(details, doctor_id)  # type: ignore[arg-type]

    visual_analysis = ""
    if doctor_type == "physician" and image_data:
        try:
            from utils import image_analysis

            visual_analysis = image_analysis.create_description(image_data)
        except Exception as e:
            log.warning("Image analysis error: %s", e)
            visual_analysis = ""

    graph = (
        _get_physician_graph() if doctor_type == "physician" else _get_therapist_graph()
    )
    initial_state = make_initial_state(doctor_type, details, visual_analysis)
    graph.invoke(initial_state, config=_config_for(session_id, doctor_type))

    snapshot = _state_snapshot(graph, session_id, doctor_type)
    if doctor_type == "physician":
        return {"session_id": session_id, **_format_physician(snapshot)}
    return {"session_id": session_id, **_format_therapist(snapshot)}


@app.post("/diagnosis/{session_id}/continue")
async def continue_diagnosis(
    session_id: str, clarification_answers: ClarificationAnswers
) -> Dict[str, Any]:
    # Try physician first, then therapist. Both thread_ids are
    # namespaced per doctor_type, so a session can only exist on one.
    snapshot: Dict[str, Any] = {}
    graph = None
    doctor_type: Optional[DoctorType] = None
    for candidate, g in (
        ("physician", _get_physician_graph()),
        ("therapist", _get_therapist_graph()),
    ):
        snap = _state_snapshot(g, session_id, candidate)  # type: ignore[arg-type]
        if snap.get("patient_details"):
            snapshot = snap
            graph = g
            doctor_type = candidate  # type: ignore[assignment]
            break

    if not snapshot or graph is None or doctor_type is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if (
        snapshot.get("is_emergency")
        or snapshot.get("current_step") == "soap_note_generated"
        or snapshot.get("current_step") == "recommended"
    ):
        raise HTTPException(status_code=400, detail="Diagnosis already complete")

    state_updates = _merge_user_answer(
        snapshot, clarification_answers.clarification_questions
    )

    # With `interrupt_after`, each pause requires (a) feeding any new state
    # in, which re-runs the paused node with the updated state, then
    # (b) advancing past the next pause. We do both in this endpoint.
    if state_updates:
        graph.invoke(state_updates, config=_config_for(session_id, doctor_type))

    snap = _state_snapshot(graph, session_id, doctor_type)
    # If the graph is still paused (the conditional edge produced a new
    # next node), one more invoke advances it. We detect "still paused"
    # by checking that current_step is anything other than a terminal
    # state. Both sub-graphs share the same terminal set: emergency,
    # soap_note_generated, recommended.
    terminal = {"soap_note_generated", "recommended"}
    is_paused = (
        not snap.get("is_emergency")
        and snap.get("current_step") not in terminal
    )
    if is_paused:
        graph.invoke(None, config=_config_for(session_id, doctor_type))

    snapshot = _state_snapshot(graph, session_id, doctor_type)
    if doctor_type == "physician":
        return _format_physician(snapshot)
    return _format_therapist(snapshot)


@app.get("/diagnosis/{session_id}/history")
async def get_conversation_history(session_id: str) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    for candidate, g in (
        ("physician", _get_physician_graph()),
        ("therapist", _get_therapist_graph()),
    ):
        snap = _state_snapshot(g, session_id, candidate)  # type: ignore[arg-type]
        if snap.get("patient_details"):
            snapshot = snap
            break
    if not snapshot:
        raise HTTPException(status_code=404, detail="Session not found")

    history: List[Dict[str, str]] = snapshot.get("conversation_history", [])
    pairs: List[Dict[str, str]] = []
    pending_q: Optional[str] = None
    for item in history:
        role = item.get("role")
        content = item.get("content", "")
        if role == "assistant":
            pending_q = content
        elif role == "user" and pending_q is not None:
            pairs.append({"question": pending_q, "answer": content})
            pending_q = None
    return {"conversation_history": pairs}


@app.get("/diagnosis/{session_id}/recommendation")
async def get_recommendation(session_id: str) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {}
    for candidate, g in (
        ("physician", _get_physician_graph()),
        ("therapist", _get_therapist_graph()),
    ):
        snap = _state_snapshot(g, session_id, candidate)  # type: ignore[arg-type]
        if snap.get("patient_details"):
            snapshot = snap
            break
    if not snapshot:
        raise HTTPException(status_code=404, detail="Session not found")

    if snapshot.get("is_emergency"):
        return {
            "recommendation_summary": snapshot.get("emergency_message", ""),
            "prescription": {},
            "soap_note": "",
            "sources": [],
            "is_emergency": True,
            "emergency_message": snapshot.get("emergency_message", ""),
        }
    if snapshot.get("current_step") == "soap_note_generated":
        return {
            "recommendation_summary": snapshot.get("diagnosis", ""),
            "prescription": snapshot.get("prescription", {}),
            "soap_note": snapshot.get("soap_note", ""),
            "sources": snapshot.get("sources", []),
            "is_emergency": False,
            "emergency_message": "",
        }
    if snapshot.get("current_step") == "recommended":
        rec = snapshot.get("recommendation", "")
        return {
            "recommendation_summary": rec,
            "prescription": {},
            "soap_note": f"Therapist Session Summary\n\n{rec}",
            "sources": [],
            "is_emergency": False,
            "emergency_message": "",
        }
    raise HTTPException(status_code=400, detail="Diagnosis not complete")


@app.get("/diagnosis/{session_id}/state")
async def get_state(session_id: str) -> Dict[str, Any]:
    for candidate, g in (
        ("physician", _get_physician_graph()),
        ("therapist", _get_therapist_graph()),
    ):
        snap = _state_snapshot(g, session_id, candidate)  # type: ignore[arg-type]
        if snap.get("patient_details"):
            return snap
    raise HTTPException(status_code=404, detail="Session not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
