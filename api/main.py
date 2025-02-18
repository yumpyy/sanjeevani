import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from doctors.physician import Physician
from doctors.therapist import Therapist

from utils import image_analysis
from utils import web_search

app = FastAPI()
origins = ["http://127.0.0.1:8001", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    image_data: str

class DiagnosisSession:
    def __init__(self, doctor_id: str, patient_details: PatientDetails):
        self.session_id = str(uuid.uuid4())
        self.doctor_id = doctor_id
        self.patient_details = patient_details
        self.completed = False
        self.summarized_docs = ""
        self.visual_medical_analysis = ""
        self.conversation_history = {}
        self.recommendation = ""
        self.soap_note = ""

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

    # reterive base64 image data, store it in a variable and delete it from user
    image_data = patient_details.image_data
    visual_medical_analysis = ""
    patient_details.image_data = ""

    session = DiagnosisSession(doctor_id, patient_details)
    sessions[session.session_id] = session

    # generate the first response to the symptoms
    response = None
    if isinstance(doctor, Therapist):
        response = doctor.respond_to_patient(
            patient_details.model_dump(), patient_details.symptoms, {}
        )
    elif isinstance(doctor, Physician):
        if image_data != "":
            visual_medical_analysis = image_analysis.create_description(image_data)
        # store visual analysis for future reference
        sessions[session.visual_medical_analysis] = visual_medical_analysis

        response = doctor.generate_clarification_question(
            patient_details.model_dump(), patient_details.symptoms, visual_medical_analysis, {}
        )
    

    if response.stop_questioning:
        session.completed = True
        if isinstance(doctor, Therapist):
            session.recommendation = doctor.provide_recommendations(patient_details.model_dump())
        elif isinstance(doctor, Physician):
            extracted_symptoms = doctor.extract_symptoms(patient_details.symptoms)
            medical_docs = [web_search.retrieve_documents(symptom) for symptom in extracted_symptoms]
            summarized_docs = doctor.summarize_docs(medical_docs)

            prescription_data = doctor.generate_prescription(patient_details.model_dump(), summarized_docs, visual_medical_analysis)
            session.recommendation = doctor.medical_prescription_summary(prescription_data)
            session.soap_note = doctor.generate_soap_note(patient_details.model_dump(), summarized_docs, visual_medical_analysis)
        return {
            "session_id": session.session_id,
            "diagnosis_complete": True,
            "recommendation": session.recommendation,
            "soap_note": session.soap_note
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

    # store the answers to previous responses
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
            session.visual_medical_analysis,
            session.conversation_history,
        )
        session.conversation_history[response.clarification_question] = None
    
    if response.stop_questioning:
        session.completed = True

        if isinstance(doctor, Physician):
            prescription_data = doctor.generate_prescription(session.patient_details.model_dump(), session.summarized_docs, session.visual_medical_analysis)
            session.recommendation = doctor.medical_prescription_summary(prescription_data)
            session.soap_note = doctor.generate_soap_note(session.patient_details, session.summarized_docs, session.visual_medical_analysis)
        else:
            session.recommendation = doctor.provide_recommendations(
                session.patient_details.model_dump()
            )

        return {
            "diagnosis_complete": True
        }

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

    print(session.recommendation)
    return {
        "recommendation": session.recommendation,
        "soap_note": session.soap_note
    }
