"""End-to-end HTTP smoke test of the FastAPI app.

Stub out LLM-touching nodes, then start uvicorn in a background thread
and exercise the public endpoints with the requests library.
"""
import os
import sys
import threading
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Stub LLM-touching nodes BEFORE importing main / building the graph.
from agents.nodes import (
    diagnosis_planner,
    history_collector,
    prescription_generator,
    soap_note_generator,
    symptom_extractor,
)


# Stateful history stub: first call asks a question (not done yet),
# second call says we're done. This mirrors a real multi-turn consult.
_call_count = {"n": 0}


def _stub_history(_state):
    _call_count["n"] += 1
    if _call_count["n"] == 1:
        return {
            "clarification_question": "How long have you had the headache?",
            "stop_questioning": False,
            "reason_for_stopping": "",
            "history_area_current": "duration",
        }
    return {
        "clarification_question": "Any other symptoms?",
        "stop_questioning": True,
        "reason_for_stopping": "ok",
        "history_area_current": "associated",
    }

symptom_extractor.extract = lambda *a, **k: {
    "symptoms": ["headache", "nausea"],
    "chief_complaint": "headache and nausea",
}
diagnosis_planner.plan_diagnosis = lambda s: {
    "potential_diagnoses": ["migraine"],
    "diagnosis_reasoning": "classic",
    "recommended_tests": [],
}
history_collector.collect_next_question = _stub_history
prescription_generator.generate_prescription = lambda s: {
    "diagnosis": "migraine",
    "medications": [],
    "side_effects": [],
    "contraindications": [],
    "alternative_treatments": ["rest"],
    "emergency_steps": [],
    "consultation_required": True,
    "sources": [],
}
soap_note_generator.generate_soap_note = lambda s: {
    "soap_note": "S: Patient reports headache. O: N/A. A: Migraine. P: Rest."
}

import uvicorn  # noqa: E402
import main  # noqa: E402


def _run_server():
    uvicorn.run(main.app, host="127.0.0.1", port=8001, log_level="error")


t = threading.Thread(target=_run_server, daemon=True)
t.start()
time.sleep(3)

BASE = "http://127.0.0.1:8001"

try:
    r = requests.get(f"{BASE}/doctors/")
    print("/doctors/  ->", r.status_code, r.json())
    assert r.status_code == 200
    assert "physician" in r.json()["available_doctors"]

    r = requests.get(f"{BASE}/health")
    print("/health    ->", r.status_code, r.json())
    assert r.status_code == 200

    r = requests.post(
        f"{BASE}/diagnosis/physician/",
        json={"age": 30, "sex": "male", "symptoms": "I have a severe headache"},
    )
    print("POST start ->", r.status_code, r.json())
    assert r.status_code == 200
    body = r.json()
    session_id = body["session_id"]
    # Graph is paused at collect_history (interrupt_before). diagnosis_complete
    # is False and the response is the fallback acknowledgement.
    assert body["diagnosis_complete"] is False, body

    # First /continue: triggers the stubbed history collector (which sets
    # stop_questioning=True), so the graph runs to completion in this call.
    # First /continue: append user answer, graph resumes. The stub is
    # called a second time and returns stop_questioning=True, so the
    # graph advances all the way to SOAP-note_generated in this call.
    r = requests.post(
        f"{BASE}/diagnosis/{session_id}/continue",
        json={"clarification_questions": {"How long have you had the headache?": "3 days"}},
    )
    print("POST cont1->", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["diagnosis_complete"] is True, r.json()
    assert r.json()["recommendation_summary"] == "migraine"

    r = requests.get(f"{BASE}/diagnosis/{session_id}/history")
    print("GET hist   ->", r.status_code, r.json())
    assert len(r.json()["conversation_history"]) >= 1

    r = requests.get(f"{BASE}/diagnosis/{session_id}/recommendation")
    print("GET rec    ->", r.status_code, r.json())
    assert r.json()["recommendation_summary"] == "migraine"
    assert "migraine" in r.json()["soap_note"].lower()

    r = requests.get(f"{BASE}/diagnosis/{session_id}/state")
    print("GET state  ->", r.status_code, "current_step=",
          r.json().get("current_step"))
    assert r.json()["current_step"] == "soap_note_generated"

    # --- Therapist flow ---
    print()
    print("=== Therapist flow ===")
    # Reset stub state and re-bind
    _call_count["n"] = 0
    therapist_calls = {"n": 0}

    def stub_respond(_state):
        therapist_calls["n"] += 1
        if therapist_calls["n"] == 1:
            return {
                "therapist_reply": "How are you feeling today?",
                "coping_strategy": "Take a deep breath.",
                "stop_questioning": False,
                "reason_for_stopping": "",
                "conversation_history": [
                    {"role": "assistant", "content": "How are you feeling today?"}
                ],
            }
        return {
            "therapist_reply": "Thank you for sharing.",
            "coping_strategy": "Stay mindful.",
            "stop_questioning": True,
            "reason_for_stopping": "ok",
            "conversation_history": [
                {"role": "assistant", "content": "Thank you for sharing."}
            ],
        }

    from agents.nodes import therapist_recommend, therapist_respond

    # The therapist_respond / therapist_recommend exports are the
    # singleton instances, not the classes.
    therapist_respond.respond = stub_respond
    therapist_recommend.recommend = lambda s: {"recommendation": "Take care."}

    r = requests.post(
        f"{BASE}/diagnosis/therapist/",
        json={"age": 25, "sex": "female", "symptoms": "feeling anxious"},
    )
    print("T-POST start->", r.status_code, r.json())
    assert r.status_code == 200
    body = r.json()
    t_session_id = body["session_id"]
    assert body["diagnosis_complete"] is False

    r = requests.post(
        f"{BASE}/diagnosis/{t_session_id}/continue",
        json={"clarification_questions": {"How are you feeling today?": "ok"}},
    )
    print("T-POST cont1->", r.status_code, r.json())
    assert r.status_code == 200
    assert r.json()["diagnosis_complete"] is True

    r = requests.get(f"{BASE}/diagnosis/{t_session_id}/recommendation")
    print("T-GET rec   ->", r.status_code, r.json())
    assert "take care" in r.json()["soap_note"].lower()

    print()
    print("E2E SMOKE TEST: PASS")
except Exception as e:
    print("E2E SMOKE TEST: FAIL ->", repr(e))
    raise
finally:
    # uvicorn is in a daemon thread; just exit.
    os._exit(0)
