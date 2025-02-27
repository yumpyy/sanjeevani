from typing import Optional

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class MedicalConsultation(BaseModel):
    """
    model for structuring a medical consultation process, including clarification questions
    and stopping conditions.
    """

    clarification_question: str = Field(
        description="Specific question to understand patient's condition better"
    )
    stop_questioning: bool = Field(
        description="Set to True when enough information has been gathered or an emergency is detected, stopping further questions."
    )
    reason_for_stopping: str = Field(
        default="",
        description="Explanation for why questioning has stopped, such as 'All key details covered' or 'Possible emergency detected'."
    )
class DosageDetails(BaseModel):
    """
    model for defining detailed dosage and administration instructions for each medication.
    """
    medicine_name: str = Field(description="Name of the prescribed medicine")
    strength: Optional[str] = Field(default=None, description="Strength of the medication (e.g., 500 mg, 10 mL)")
    frequency: str = Field(description="How often the medication should be taken (e.g., twice daily)")
    duration: str = Field(description="Total duration of the treatment (e.g., 7 days)")
    special_instructions: Optional[str] = Field(default=None, description="Any specific instructions such as 'take with food'")

class MedicinePrescription(BaseModel):
    """
    model for generating a structured medical prescription, including diagnosis,
    recommended medicines, detailed dosage, side effects, and contraindications.
    """
    diagnosis: Optional[str] = Field(
        default=None,
        description="Possible medical condition(s) based on symptoms and available data, including visual medical analysis if provided"
    )
    medications: list[DosageDetails] = Field(
        description="List of prescribed medicines with dosage details"
    )
    side_effects: list[str] = Field(
        default=[], description="List of side effects that may occur"
    )
    contraindications: list[str] = Field(
        description="Conditions, medications, or allergies that may interact negatively with the prescribed treatment"
    )
    alternative_treatments: list[str] = Field(
        description="Non-pharmaceutical or supportive treatments, such as lifestyle changes or dietary adjustments"
    )
    emergency_aid_steps: Optional[list[str]] = Field(
        default=None, description="Step-by-step emergency actions if the symptoms indicate a severe reaction"
    )
    consultation_required: bool = Field(
        default=False, description="True if professional medical consultation is necessary"
    )

class ExtractedSymptoms(BaseModel):
    """
    model for extracting symptoms as keywords from initial symptoms.
    """
    symptoms: list[str] = Field(
        description="List of extracted symptom keywords"
    )

class SummarizedDocs(BaseModel):
    summary: str = Field(
        description="Summary for document"
    )

class SOAPNote(BaseModel):
    """
    Model for generating a structured SOAP note based on patient input,
    clinical observations, visual medical analysis (if applicable),
    and structured prescriptions.
    """
    patient_age: int = Field(description="Patient's age in years")
    patient_sex: str = Field(description="Patient's sex (Male/Female/Other)")
    
    # subjective
    chief_complaint: str = Field(description="Primary reason for the visit, as reported by the patient")
    history_of_present_illness: str = Field(description="Detailed description of the chief complaint using OLDCARTS method")
    past_medical_history: Optional[str] = Field(default=None, description="Pertinent past medical conditions")
    surgical_history: Optional[str] = Field(default=None, description="Past surgical procedures")
    family_history: Optional[str] = Field(default=None, description="Relevant family medical history")
    social_history: Optional[str] = Field(default=None, description="Patient's lifestyle, including smoking, alcohol, occupation, etc.")
    review_of_systems: Optional[str] = Field(default=None, description="System-based symptom checklist")

    # objective
    vital_signs: Optional[str] = Field(default=None, description="Documented vital signs including BP, HR, Temp, RR")
    physical_exam: Optional[str] = Field(default=None, description="Findings from the clinician's physical examination")
    lab_results: Optional[str] = Field(default=None, description="Relevant laboratory test results")
    imaging_results: Optional[str] = Field(default=None, description="Findings from X-ray, MRI, CT scans, or ultrasound")
    visual_medical_analysis: Optional[str] = Field(default=None, description="Findings from image analysis (if applicable)")

    # assessment
    primary_diagnosis: str = Field(description="Most likely diagnosis based on subjective and objective findings")
    differential_diagnosis: list[str] = Field(description="List of alternative possible diagnoses")
    reasoning: Optional[str] = Field(default=None, description="Justification for primary and differential diagnoses")

    # plan
    prescription: MedicinePrescription
    additional_tests: Optional[list[str]] = Field(default=[], description="Any further diagnostic tests recommended")
    specialist_referral: Optional[list[str]] = Field(default=[], description="Recommended specialist consultations")
    patient_education: Optional[str] = Field(default=None, description="Guidance provided to the patient about their condition and treatment")
    follow_up_plan: Optional[str] = Field(default=None, description="Instructions for future visits or check-ups")


class Physician:
    def __init__(self) -> None:
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )
        self.groq = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_retries=2,
        )

    def extract_symptoms(
        self, 
        symptoms_text: str
    ) -> list[str]:
        """
        extract structured symptom keywords from user input.
        """
        prompt = ChatPromptTemplate.from_template(
        """
        Extract the key symptoms from the given patient input as a list of concise medical terms.
        
        **Patient Input:** "{symptoms_text}"
        
        **Output Format:**
        - Provide only relevant medical symptoms, avoiding general descriptions.
        """
        )

        extraction_chain = prompt | self.groq.with_structured_output(ExtractedSymptoms)
        response = extraction_chain.invoke({"symptoms_text": symptoms_text})
        return response.symptoms

    def summarize_docs(
        self, 
        medical_docs
    ):
        """
        summarizes medical documents focusing on critical and actionable details.
        """

        summarization_prompt = ChatPromptTemplate.from_template(
        """
        You are a professional medical document summarizer specializing in clinical workflows. Your task is to extract only the most critical and actionable details from the provided medical document to assist in AI-driven medical consultations.
        
        **Key Extraction Focus Areas:**
        1. **Disease Diagnosis & Symptom Analysis**  
           - Identify key symptoms and diagnostic criteria.  
           - Highlight differentiating factors between similar conditions.  
        
        2. **Treatment Protocols & Standard Procedures**  
           - Summarize recommended clinical workflows and step-by-step treatment procedures.  
           - Include guidelines for acute vs. chronic cases.  
        
        3. **Recommended Medicines & Dosages**  
           - List the primary medications prescribed for treatment.  
           - Specify standard dosages, administration frequency, and duration.  
           - Mention any special considerations (e.g., age-based or condition-specific adjustments).  
        
        4. **Alternative & Supportive Treatments**  
           - Include lifestyle modifications, physical therapies, dietary changes, and home remedies.  
           - Highlight complementary treatments such as physiotherapy, mental health support, or rehabilitation programs.  
        
        5. **Potential Side Effects & Contraindications**  
           - Outline common and severe side effects associated with medications.  
           - List contraindications, including interactions with other drugs, pre-existing conditions, and allergies.  
        
        6. **Emergency Considerations**  
           - Identify symptoms requiring **urgent medical attention** (e.g., heart attack, stroke, anaphylaxis).  
           - Provide immediate first-response actions if applicable.  
        
        **Output Constraints & Formatting:**  
        - Keep the summary structured and **highly actionable** for AI-based consultations.  
        - **Limit output to 3000 tokens maximum.** Prioritize essential information, avoiding unnecessary details.  
        - Maintain clinical accuracy and clarity, ensuring the summary is useful for medical professionals and AI-driven decision-making.  
        
        **Medical Document:**  
        {medical_docs}
        """
        )

        summarization_chain = summarization_prompt | self.gemini.with_structured_output(SummarizedDocs)
        return summarization_chain.invoke({"medical_docs": medical_docs})

    def generate_clarification_question(
        self,
        patient_details,
        intial_symptoms,
        visual_medical_analysis,
        qna
    ):
        """
        generates a clarification question to obtain additional details about the patient's condition.
        """

        clarification_prompt = ChatPromptTemplate.from_template(
        """
         **Context:**  
        - **Patient Details:** {patient_details}  
        - **Initial Symptoms:** {symptoms}  
        - **Previous Q&A History:** {qna}  
        - **Visual Medical Analysis:** {visual_medical_analysis} _(May be empty)_  
        
         **Your Task:**  
        You are conducting a structured medical clarification process to gather precise and complete information for an accurate assessment.  
        
        1. **Analyze Existing Information:**  
           - Review the Q&A history to determine what has already been covered.  
           - Identify missing critical details necessary for an accurate medical evaluation.  
           - If a medical image description is provided, incorporate its details into your reasoning.  
        
        2. **Handle Unclear or Incomplete Answers Before Moving Forward:**  
           - **Verify Completeness:** Before asking a new question, check if the previous response fully answered the last question.  
           - **Clarify When Needed:** If the response is vague, ambiguous, or does not directly answer the question, politely request clarification before proceeding.  
           - **Educate When Necessary:** If the patient asks for clarification on a medical term (e.g., "What does onset mean?"), provide a brief, clear definition before asking them to respond.  
        
        3. **Formulate Precise, Logical, and Non-Repetitive Questions:**  
           - **Avoid Redundancy:** Do NOT ask any question that has already been covered or rephrase previous questions unnecessarily.  
           - **Ensure Logical Progression:** The next question should introduce new information and build meaningfully on existing details.  
           - **Leverage Medical Image Analysis:**  
             - If a medical image description is provided, integrate its insights into your questioning.  
             - Ask about abnormalities, findings, or concerns related to the image.  
             - If the image description contradicts or adds new insights to patient-reported symptoms, seek clarification.  
           - **Stay Medically Relevant:** Only ask about missing medical details—avoid irrelevant or action-based questions (e.g., "Would you like to see a doctor?").  
        
        4. **Recognize When to Stop Asking Questions:**  
           - **Emergency Detection:** Stop questioning immediately if symptoms suggest a potential emergency.  
             - Examples of emergency symptoms include:  
               - Severe chest pain  
               - Difficulty breathing  
               - Loss of consciousness or confusion  
               - Uncontrolled bleeding  
               - Severe allergic reaction (e.g., swelling, trouble breathing)  
               - Stroke symptoms (e.g., slurred speech, weakness on one side)  
               - Sudden extreme pain or vision loss  
           - **Completion of Necessary Details:** If all relevant medical details are collected, stop asking questions.  
             - Ensure all key symptom details are covered (**onset, duration, intensity, triggers, and progression**).  
             - Verify that **medical history, past conditions, surgeries, and allergies** have been addressed.  
             - Confirm that information about **medications (prescription, over-the-counter, and supplements)** has been gathered.  
             - If the visual medical analysis is available, ensure any notable findings are clarified.  
           - **How to Stop Properly:**  
             - If an emergency symptom is detected, return **an empty clarification question** and indicate questioning has stopped due to a possible medical emergency.  
             - If all necessary information has been gathered, return **an empty clarification question** and indicate that questioning is complete.
        """
        )

        clarification_chain = clarification_prompt | self.groq.with_structured_output(MedicalConsultation)
        return clarification_chain.invoke(
            {
                "patient_details": patient_details,
                "symptoms": intial_symptoms,
                "visual_medical_analysis": visual_medical_analysis, 
                "qna": qna
            }
        )

    def generate_prescription(
        self,
        patient_details,
        medical_docs,
        visual_medical_analysis
    ):
        """
        generates a medical prescription with diagnosis, medications, dosage, side effects, 
        contraindications, and emergency aid based on patient data.
        """

        prescription_prompt = ChatPromptTemplate.from_template(
        """
        **Role & Responsibility**  
            You are a **professional medical assistant** responsible for generating **safe, structured, and evidence-based medical assessments, prescriptions, and emergency guidance** based on patient data, standardized medical guidelines, and visual medical analysis (if available).  
        
        **Patient Information**
            - **Patient Medical Details:** {patient_details}
            - **Relevant Medical Documentation & Guidelines:** {medical_docs}
            - **Visual Medical Analysis (If Available):** {visual_medical_analysis} _(Description of medical images or scans related to the patient’s condition, may be empty)_
        
        **Your Objective**
            Using the **patient’s symptoms, medical history, medical guidelines, and visual medical analysis**, generate a structured and **medically accurate response** that strictly adheres to **evidence-based practices** and does NOT recommend **hallucinated, non-standard, or unsafe treatments**.
        
            Your response **MUST follow** the structure below:
        
        **1. Preliminary Diagnosis**
            - Provide a **possible condition(s) based on available medical data**, but **DO NOT assume a definitive diagnosis**.
            - If a **visual medical analysis** is available, use it to **support or refine** the diagnosis. 
            - Clearly state if **further tests or specialist evaluation** are required. 
        
        **2. Recommended Medications**
            - **Only recommend medications that are widely recognized in medical guidelines** for the suspected condition.
            - DO NOT generate **random or hallucinated medication names**.
            - If a condition does not have a clear pharmacological treatment, state **"No medication recommendation based on current medical guidelines."** 
    
        **3. Dosage & Administration Guidelines**
            For each **recommended medication**, provide:  
            - **Precise dosage and strength** (e.g., “500 mg,” “10 mL”).
            - **Route of administration** (e.g., oral, IV, topical).
            - **Frequency & duration** (e.g., “Take twice daily for 7 days”).
            - **Special instructions**, if applicable (e.g., “Take with food,” “Avoid alcohol”).
        
        **4. Potential Side Effects & Risks**
            - **Common side effects** (e.g., nausea, dizziness, headache).
            - **Severe or rare adverse effects** (e.g., risk of liver damage, anaphylaxis). 
            - **Clearly state when medical attention is required** for certain side effects.
        
        **5. Contraindications & Drug Interactions**
            - **Pre-existing conditions** that may conflict with the prescribed medication (e.g., “Not recommended for patients with liver disease”).
            - **Known drug interactions** (e.g., “Avoid if taking blood thinners”). 
            - **Allergy considerations** (e.g., “Do not prescribe if allergic to penicillin”).
    
        **6. Alternative Treatments (If Applicable)**
            - **Non-pharmaceutical interventions** such as dietary adjustments, physical therapy, lifestyle changes, or home remedies supported by medical guidelines.
            - **Clearly indicate if alternative treatments alone are insufficient** for managing the condition. 
    
        **7. Emergency Aid & First Response (IF URGENT SYMPTOMS DETECTED)** 
            - **Provide first aid or emergency response steps** if symptoms indicate a potential medical emergency. 
            - **For critical cases, explicitly state:** “Seek immediate emergency medical care—self-treatment is NOT recommended.”
        **8. Consultation Recommendation**
            - Clearly state whether the patient **must consult a doctor before taking any prescribed medications**. 
            - If a **physical examination, lab test, or specialist referral** is required, provide justification.
        **Failure Criteria (Trigger Safeguards If Any Apply)**
            If any of the following apply, state **"Unable to provide a safe recommendation—consult a licensed medical professional."** 
            1. **Symptoms are vague, unclear, or insufficient for a safe diagnosis.**
            2. **No medication is recognized in standard medical guidelines for the condition.**
            3. **Potential medication risks outweigh benefits.**
            4. **Patient history suggests high-risk contraindications.**
            5. **A medical emergency requires urgent professional intervention.**
        """
        )

        prescription_chain = prescription_prompt | self.groq.with_structured_output(MedicinePrescription)
        response = prescription_chain.invoke(
            {
                "patient_details": patient_details,
                "medical_docs": medical_docs,
                "visual_medical_analysis": visual_medical_analysis
            }
        )
        return response
    
    def medical_prescription_summary(
        self,
        prescription_data: MedicalConsultation
    ):
        """converts structured medical prescription data into a doctor-style, human-readable summary."""

        prompt = ChatPromptTemplate.from_template(
        """
        **Prompt for Human-Readable Doctor’s Summary of Medical Prescription**  

        **Role & Objective:**  
        You are a **highly experienced medical professional** responsible for communicating **precise, structured, and medically sound** treatment plans to patients in a **clear yet professional manner**. Your task is to generate a **concise, human-readable summary** of a medical prescription while maintaining a **doctor’s authoritative and confident tone**.  
        
        **Context:**
        {prescription_data}
        
        **Output Requirements:**  
        Your response should:  
        ✔ **Use a professional doctor’s tone**—precise, confident, and medically authoritative.  
        ✔ **Naturally integrate** all prescription details into a structured yet conversational format.  
        ✔ **Emphasize critical information**, such as dosage instructions, precautions, and follow-up needs.  
        ✔ **Avoid technical jargon** unless necessary—prioritize **patient comprehension**.  
        ✔ **Sound natural and realistic**, as if spoken by a doctor during a consultation.  
        
        **Critical Guidelines for the LLM:**  
        - **DO NOT introduce any new medications or details not in the given prescription.**  
        - **DO NOT make definitive guarantees about recovery—use medical reasoning instead.**  
        - **DO NOT use casual or overly empathetic language—maintain a clinical, professional approach.**  
        - **DO NOT omit safety warnings, potential side effects, or contraindications.**  
        """
        )

        med_summary_chain = prompt | self.groq
        response = med_summary_chain.invoke({"prescription_data": prescription_data})
        return response.content

    def generate_soap_note(
        self,
        patient_details,
        visual_medical_analysis,
        prescription_data
    ):
        prompt = ChatPromptTemplate.from_template(
        """
        **Role & Responsibility**  
        You are a **professional medical assistant** responsible for generating **safe, structured, and medically accurate SOAP notes** based on patient data, medical documentation, visual medical analysis, and any related prescription information.  
        
        **Patient Information**  
        - **Patient Medical Details:** {patient_details}  
        - **Visual Medical Analysis (If Available):** {visual_medical_analysis} _(Description of medical images or scans related to the patient’s condition, may be empty)_  
        - **Prescription Data:** {prescription_data} _(Structured medical prescription including diagnosis, recommended medications, dosage, side effects, contraindications, etc.)_
        
        **Your Objective**  
        Using the patient’s **symptoms, medical history, medical guidelines, visual medical analysis**, and the **prescription data**, generate a **structured SOAP note** with the following sections:
        
        #**1. Subjective (S) - Patient’s Reported Information**  
           - **Chief Complaint (CC):** Short statement of the primary symptom or condition.  
           - **History of Present Illness (HPI):** Detailed description of the CC, structured using the **OLDCARTS** framework:  
             - **Onset:** When did it start?  
             - **Location:** Where is the issue?  
             - **Duration:** How long has it persisted?  
             - **Characterization:** How does the patient describe it?  
             - **Alleviating & Aggravating Factors:** What makes it better or worse?  
             - **Radiation:** Does it spread anywhere?  
             - **Temporal Factors:** Is it worse at specific times?  
             - **Severity:** Pain or symptom severity scale (e.g., 1-10).  
           - **Past Medical History:** Previous diagnoses, conditions, and surgeries.  
           - **Family & Social History:** Relevant hereditary conditions and lifestyle factors.  
           - **Review of Systems (ROS):** Checklist of symptoms related to different organ systems.  
        
        #**2. Objective (O) - Clinical & Diagnostic Findings**  
           - **Vital Signs:** Temperature, heart rate, blood pressure, respiratory rate.  
           - **Physical Exam Findings:** Notable observations from a physical examination.  
           - **Diagnostic Data:** Laboratory results, imaging findings, and other diagnostic reports.  
        
        #**3. Assessment (A) - Diagnosis & Clinical Analysis**  
           - **Problem List:** List the issues based on the subjective and objective information.  
           - **Preliminary Diagnosis:** If symptoms strongly suggest a specific condition, include possible diagnoses, but refrain from definitive conclusions.  
           - **Differential Diagnosis:** Additional potential diagnoses that need to be ruled out, including reasoning.  
        
        #**4. Plan (P) - Treatment & Recommendations**  
           - **Medications:** Based on the prescription data, list the **recommended medications** with emphasis on dosage and administration guidelines.  
           - **Side Effects & Risks:** Include any potential side effects as per the prescription data.  
           - **Contraindications & Interactions:** List any contraindications or interactions with other medications, conditions, or allergies as noted in the prescription data.  
           - **Alternative Treatments:** Suggest non-pharmaceutical approaches if applicable.  
           - **Specialist Referrals & Additional Tests:** Specify any consultations or additional tests required.  
           - **Emergency Response:** Include any emergency steps if the condition is life-threatening or urgent.  
           - **Consultation Requirement:** Indicate if professional consultation is recommended before following the plan.
        
        **Critical Notes**  
        - Ensure the **prescription data** is accurately integrated into the treatment and recommendations sections.  
        - Maintain a **professional tone** throughout, ensuring clarity and accuracy in each section.  
        - Emphasize that **this is a preliminary assessment**, and professional consultation is essential for final diagnosis and treatment decisions.  
        """
        )

        soap_note_chain = prompt | self.groq
        response = soap_note_chain.invoke(
            {
                "patient_details": patient_details,
                "visual_medical_analysis": visual_medical_analysis,
                "prescription_data": prescription_data
            }
        )

        return response.content
