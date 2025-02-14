# standard lib imports
from typing import List, Optional

# langchain imports
# from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# data validation
from pydantic import BaseModel, Field

# env management
from dotenv import load_dotenv

load_dotenv()

import db

# pydantic base model for llm responses
class MedicalConsultation(BaseModel):
    clarification_question: str = Field(
        description="Specific question to understand patient's condition better"
    )
    stop_questioning: bool = Field(
        description="Set to True when enough information has been gathered or an emergency is detected, stopping further questions."
    )
    reason_for_stopping: str = Field(
        description="Explanation for why questioning has stopped, such as 'All key details covered' or 'Possible emergency detected'.",
        default=""
    )

class MedicinePrescription(BaseModel):
    recommend_medicines: List[str] = Field(
        description="List of recommended medicines based on symptoms and patient details"
    )
    dosage: Optional[str] = Field(
        description="Precise dosage and administration guidelines, including frequency and special instructions"
    )
    potential_side_effects: Optional[List[str]] = Field(
        description="List of possible side effects, including common and severe reactions"
    )
    contraindications: Optional[List[str]] = Field(
        description="Conditions, medications, or allergies that may interact negatively with the recommended treatment"
    )
    alternative_treatments: Optional[List[str]] = Field(
        description="Non-pharmaceutical or supportive treatments, such as lifestyle changes or dietary adjustments"
    )
    emergency_advice: Optional[str] = Field(
        description="Guidance on whether symptoms require urgent medical attention instead of self-medication"
    )
    consultation_required: bool = Field(
        description="True if professional medical consultation is necessary before taking any recommended medication"
    )


class Physician:
    def __init__(
            self
    ) -> None:
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            # model="deepseek-r1-distill-llama-70b",
            temperature=0.2,
            max_retries=2,
        )
        self.db = db.VectorDB("./vectordb/")

    def generate_clarification_question(
            self,
            patient_details,
            intial_symptoms,
            qna,
    ):
        """
        based on the user's symptoms, generate clarification_question for better results

        args:
            initial_symptoms 
        """
        clarification_prompt = ChatPromptTemplate.from_template(
            """
            You are a professional medical assistant conducting a structured clarification process to gather precise medical information.
            
            **Context:**  
            - Patient Details: {patient_details}  
            - Initial Symptoms: {symptoms}  
            - Previous Q&A History: {qna}  
            
            **Your Task:**  
            1. Analyze the Q&A history to determine what has already been covered.  
            2. Identify any missing critical details necessary for an accurate medical assessment.  
            3. **Before asking a new question, check if the previous answer directly addressed the last question.**  
            4. **If the user’s response does not fully answer the previous question or shows confusion, clarify first rather than moving to a new question.**  
            5. **If the symptoms indicate a possible emergency, stop questioning immediately.**  
            
            **Rules for Handling Incomplete or Unclear Answers:**  
            - If the user's response does not answer the question, politely clarify its meaning before asking again.  
            - If the user asks what a term means (e.g., "What does onset mean?"), provide a simple definition before asking them to answer.  
            - If the user gives a vague or incomplete answer, prompt them for more detail before moving forward.  
            - Do not assume an answer if the response is ambiguous.  
            
            **Strict Rules for Generating New Questions:**  
            - **No Repetition:** Do NOT ask any question that is identical or similar to a previously asked one.  
            - **Ensure Uniqueness:** The next question must introduce **new** information not yet explored.  
            - **Logical Progression:** The new question must logically build on what is already known, ensuring meaningful clarification.  
            - **Avoid Redundancy:** If the information in previous answers already provides clarity, do NOT ask additional questions.  
            - **Precise Focus:** Only ask about missing medical details. Do not ask about actions (e.g., "Would you like to see a doctor?").  
            
            **When to Stop Asking Questions:**  
            1. **If the symptoms suggest a potential medical emergency, stop questioning immediately.**  
               - Examples of emergency symptoms include:  
                 - Severe chest pain  
                 - Difficulty breathing  
                 - Loss of consciousness or confusion  
                 - Uncontrolled bleeding  
                 - Severe allergic reaction (swelling, trouble breathing)  
                 - Stroke symptoms (slurred speech, weakness on one side)  
                 - Extreme pain or sudden loss of vision  
                 - Heartattack
            2. **If all necessary details are collected, stop questioning.**  
               - All key symptom details have been covered, including **onset, duration, intensity, triggers, and progression**.  
               - The patient's **medical history, including past conditions, surgeries, and allergies, has been addressed**.  
               - Information about **medications (prescriptions, over-the-counter drugs, and supplements) has been gathered**.  
               - No **critical gaps remain** in the patient's responses.  
            
            **How to Ensure Stopping Works:**  
            - If an emergency symptom is detected, return **an empty clarification question** and indicate that questioning has stopped due to a possible emergency.  
            - If all relevant information is gathered, return **an empty clarification question** and indicate that questioning is complete.  
            """
        )

        clarification_chain = clarification_prompt | self.llm.with_structured_output(
            MedicalConsultation
        )

        return clarification_chain.invoke(
            {
                "patient_details": patient_details,
                "symptoms": intial_symptoms,
                "qna": qna,
            }
        )

    def generate_prescription(self, patient_details):
        """
        generate medical prescription using rag with structured query analysis.
        """
        print(type(patient_details))

        medical_docs = ""
        # medical_docs = self.db.retrieve_docs(patient_details)

        prescription_prompt = ChatPromptTemplate.from_template(
        """
        You are a professional medical assistant responsible for generating safe, precise, and well-informed standard treatment.  

        **Patient Information:**  
        - **Patient Medical Details:** {patient_details}  
        - **Relevant Medical Documentation & Guidelines:** {medical_docs}  

        **Your Objective:**  
        Based on the patient's symptoms, medical history, and relevant documentation, provide a **comprehensive and medically sound prescription recommendation** that includes:  

        1. **Recommended Medications** – Identify the most appropriate medicines based on the symptoms, patient details, and medical references.  
        2. **Precise Dosage & Administration Guidelines** – Provide clear and accurate dosage instructions, including frequency, duration, and any special considerations (e.g., take with food, avoid alcohol).  
        3. **Potential Side Effects & Risks** – List common and severe side effects to inform the patient of possible reactions.  
        4. **Contraindications & Drug Interactions** – Highlight potential conflicts with existing medications, medical conditions, or allergies.  
        5. **Alternative Treatments (if applicable)** – Suggest non-pharmaceutical or alternative medical interventions if relevant (e.g., lifestyle changes, dietary adjustments).  
        6. **Urgency & Escalation Guidance** – If symptoms indicate a possible serious condition, recommend seeking immediate medical attention.  

        **Critical Safety Guidelines:**  
        - **DO NOT assume a diagnosis.** Base recommendations solely on reported symptoms and available patient information.  
        - **ALWAYS emphasize the importance of consulting a licensed medical professional** before taking any medication.  
        - **If symptoms suggest a severe or emergency condition (e.g., difficulty breathing, severe chest pain, stroke-like symptoms), prioritize advising immediate medical care over medication recommendations.**  
        - **Ensure compliance with standard medical guidelines and avoid recommending off-label or experimental treatments unless explicitly backed by medical literature.**
        """
        )

        prescription_chain = prescription_prompt | self.llm.with_structured_output(
            MedicinePrescription
        )

        response = prescription_chain.invoke(
            {
                "patient_details": patient_details,
                "medical_docs": medical_docs,
            }
        )

        return response
