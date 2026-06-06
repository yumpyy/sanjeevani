from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DosageDetails(BaseModel):
    medicine_name: str
    strength: Optional[str] = ""
    frequency: str
    duration: str
    special_instructions: Optional[str] = ""


class MedicinePrescription(BaseModel):
    diagnosis: Optional[str] = None
    medications: List[DosageDetails] = []
    side_effects: List[str] = []
    contraindications: List[str] = []
    alternative_treatments: List[str] = []
    emergency_steps: Optional[List[str]] = None
    consultation_required: bool = True
    potential_diagnoses_list: Optional[List[str]] = None


class ExtractedSymptoms(BaseModel):
    symptoms: List[str]
    chief_complaint: str


class RetrievedMedicalInfo(BaseModel):
    potential_diagnosis: str
    diagnostic_info: Optional[str] = None
    treatment_overview: Optional[str] = None
    red_flags: List[str] = []
    general_info_summary: str


class MedicalConsultation(BaseModel):
    clarification_question: str
    stop_questioning: bool
    reason_for_stopping: str = ""


class HistoryQuestionResponse(BaseModel):
    question: str
    stop_questioning: bool
    reason: str
    area_covered: str = ""


class DiagnosisPlan(BaseModel):
    potential_diagnoses: List[str]
    reasoning: str
    recommended_tests: List[str] = []


class PrescriptionResponse(BaseModel):
    diagnosis: str
    medications: List[DosageDetails] = []
    side_effects: List[str] = []
    contraindications: List[str] = []
    alternative_treatments: List[str] = []
    emergency_steps: List[str] = []
    consultation_required: bool = True


class SOAPNote(BaseModel):
    patient_age: int
    patient_sex: str
    chief_complaint: str
    history_of_present_illness: str
    past_medical_history: Optional[str] = None
    surgical_history: Optional[str] = None
    family_history: Optional[str] = None
    social_history: Optional[str] = None
    review_of_systems: Optional[str] = None
    vital_signs: Optional[str] = None
    physical_exam: Optional[str] = None
    lab_results: Optional[str] = None
    imaging_results: Optional[str] = None
    visual_medical_analysis: Optional[str] = None
    primary_diagnosis: str
    differential_diagnosis: List[str]
    reasoning: Optional[str] = None
    potential_diagnoses_considered: Optional[List[str]] = None
    prescription_summary: str
    additional_tests: List[str] = []
    specialist_referral: List[str] = []
    patient_education: Optional[str] = None
    follow_up_plan: Optional[str] = None
    emergency_aid_steps_in_plan: Optional[List[str]] = None
    consultation_required_in_plan: bool = True


class TherapyResponse(BaseModel):
    therapist_reply: str
    coping_strategy: str
    stop_questioning: bool
    reason_for_stopping: str = ""


class PatientDetails(BaseModel):
    age: int
    sex: str
    symptoms: str
    image_data: str = ""


class ClarificationAnswers(BaseModel):
    clarification_questions: Dict[str, str]
