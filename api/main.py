import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from doctors.physician import Physician
from doctors.therapist import Therapist

app = FastAPI()

DOCTORS = {
    "physician": Physician(),
    "therapist": Therapist(),
}

sessions = {}

class ClarificationAnswers(BaseModel):
    clarification_questions: dict[str, str]

class PatientDetails(BaseModel):
    age: int
    sex: str
    symptoms: str

class DiagnosisSession:
    def __init__(self, doctor_id: str, patient_details: PatientDetails):
        self.session_id = str(uuid.uuid4())
        self.doctor_id = doctor_id
        self.patient_details = patient_details
        self.completed = False
        self.clarification_history = {}
        self.prescription = None

@app.get("/doctors/")
async def get_doctors():
    """get available doctor types."""
    return {"available_doctors": list(DOCTORS.keys())}

@app.post("/diagnosis/{doctor_id}/")
async def start_diagnosis(doctor_id: str, patient_details: PatientDetails):
    """start a diagnosis session (without expecting clarification questions)."""
    
    if doctor_id not in DOCTORS:
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    doctor = DOCTORS[doctor_id]
    session = DiagnosisSession(doctor_id, patient_details)
    sessions[session.session_id] = session

    # generate the first clarification question
    symptom_analysis = doctor.generate_clarification_question(
        patient_details.model_dump(), patient_details.symptoms, {}
    )

    if symptom_analysis.stop_questioning:
        session.completed = True
        session.prescription = doctor.generate_prescription(patient_details.model_dump())
        return {
            "session_id": session.session_id,
            "diagnosis_complete": True,
            "prescription": session.prescription,
        }

    # store the first question without answer
    session.clarification_history[symptom_analysis.clarification_question] = None

    return {
        "session_id": session.session_id,
        "diagnosis_complete": False,
        "question": symptom_analysis.clarification_question,
    }

@app.post("/diagnosis/{session_id}/continue")
async def continue_diagnosis(session_id: str, clarification_answers: ClarificationAnswers):
    """continue the diagnosis process with answers to previous questions."""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    doctor = DOCTORS[session.doctor_id]

    # store the answers to previous questions
    for question, answer in clarification_answers.clarification_questions.items():
        session.clarification_history[question] = answer

    # generate the next clarification question
    symptom_analysis = doctor.generate_clarification_question(
        session.patient_details.model_dump(), session.patient_details.symptoms, session.clarification_history
    )

    if symptom_analysis.stop_questioning:
        session.completed = True
        session.prescription = doctor.generate_prescription(session.patient_details.model_dump())
        return {
            "diagnosis_complete": True,
            "prescription": session.prescription,
        }

    # store the next question without an answer
    session.clarification_history[symptom_analysis.clarification_question] = None

    return {
        "diagnosis_complete": False,
        "question": symptom_analysis.clarification_question,
    }

@app.get("/diagnosis/{session_id}/history")
async def get_clarification_history(session_id: str):
    """retrieve all previous clarification questions and answers."""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"clarification_history": sessions[session_id].clarification_history}

@app.get("/diagnosis/{session_id}/prescription")
async def get_prescription(session_id: str):
    """retrieve the final prescription."""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session.completed:
        raise HTTPException(status_code=400, detail="Diagnosis not complete")

    return {"prescription": session.prescription}
