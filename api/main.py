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
        self.conversation_history = {}
        self.recommendation = None

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

    # Generate the first response to the symptoms
    response = None
    if isinstance(doctor, Therapist):
        response = doctor.respond_to_patient(
            patient_details.model_dump(), patient_details.symptoms, {}
        )
    else:
        response = doctor.generate_clarification_question(
            patient_details.model_dump(), patient_details.symptoms, {}
        )
    

    if response.stop_questioning:
        session.completed = True
        session.recommendation = doctor.provide_recommendations(
            patient_details.model_dump()
        )
        return {
            "session_id": session.session_id,
            "diagnosis_complete": True,
            "recommendation": session.recommendation,
        }


    session.conversation_history[response.therapist_reply if isinstance(doctor, Therapist) else response.clarification_question] = None

    return {
        "session_id": session.session_id,
        "diagnosis_complete": False,
        "response": response.therapist_reply if isinstance(doctor, Therapist) else response.clarification_question,
    }

@app.post("/diagnosis/{session_id}/continue")
async def continue_diagnosis(
    session_id: str, clarification_answers: ClarificationAnswers
):
    """continue the diagnosis process with answers to previous responses."""

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    doctor = DOCTORS[session.doctor_id]

    # Store the answers to previous responses
    for question, answer in clarification_answers.clarification_questions.items():
        session.conversation_history[question] = answer

    response = None
    if isinstance(doctor, Therapist):
        response = doctor.respond_to_patient(
            session.patient_details.model_dump(),
            session.patient_details.symptoms,
            session.conversation_history,
        )
        session.conversation_history[response.therapist_reply] = None
    else:
        response = doctor.generate_clarification_question(
            session.patient_details.model_dump(),
            session.patient_details.symptoms,
            session.conversation_history,
        )
        session.conversation_history[response.clarification_question] = None
    
    if response.stop_questioning:
        session.completed = True

        if isinstance(doctor, Physician):
            session.recommendation = doctor.generate_prescription(
                session.patient_details.model_dump()
            )
        else:
            session.recommendation = doctor.provide_recommendations(
                session.patient_details.model_dump()
            )

        return {
            "diagnosis_complete": True,
            "recommendation": session.recommendation,
        }

    # if isinstance(doctor, Physician):
    #     session.conversation_history[response.clarification_question] = None
    # else:
    #     session.conversation_history[response.therapist_reply] = None


    return {
        "diagnosis_complete": False,
        "response": (
            response.therapist_reply if isinstance(doctor, Therapist)
            else response.clarification_question
        ),
    }

@app.get("/diagnosis/{session_id}/history")
async def get_conversation_history(session_id: str):
    """retrieve all previous therapist responses and user inputs."""

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"conversation_history": sessions[session_id].conversation_history}

@app.get("/diagnosis/{session_id}/recommendation")
async def get_recommendation(session_id: str):
    """retrieve the final therapy recommendation."""

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    if not session.completed:
        raise HTTPException(status_code=400, detail="Diagnosis not complete")

    return {"recommendation": session.recommendation}
