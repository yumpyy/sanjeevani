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

class MedicinePrescription(BaseModel):    
    """
    model for generating a structured medical prescription, including diagnosis,
    recommended medicines, dosage, side effects, and contraindications.
    """

    diagnosis: Optional[str] = Field(
        default=None,
        description="Possible medical condition(s) based on symptoms and available data, including visual medical analysis if provided"
    )
    recommend_medicines: list[str] = Field(
        description="List of recommended medicines based on symptoms and patient details"
    )
    dosage: Optional[str] = Field(
        default=[],
        description="Precise dosage and administration guidelines, including frequency and special instructions"
    )
    potential_side_effects: list[str] = Field(
        description="List of possible side effects, including common and severe reactions"
    )
    contraindications: list[str] = Field(
        description="Conditions, medications, or allergies that may interact negatively with the recommended treatment"
    )
    alternative_treatments: list[str] = Field(
        description="Non-pharmaceutical or supportive treatments, such as lifestyle changes or dietary adjustments"
    )
    emergency_aid: Optional[str] = Field(
        default=None, description="First aid or emergency steps if the symptoms indicate a potentially life-threatening condition"
    )
    consultation_required: bool = Field(
        default=False, description="True if professional medical consultation is necessary before taking any recommended medication"
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
        You are a **professional medical assistant** responsible for generating **safe, precise, and well-informed medical assessments, prescriptions, and emergency guidance** based on patient data, medical documentation, and visual medical analysis.  
        
         **Patient Information**  
        - **Patient Medical Details:** {patient_details}  
        - **Relevant Medical Documentation & Guidelines:** {medical_docs}  
        - **Visual Medical Analysis (If Available):** {visual_medical_analysis} _(Description of medical images or scans related to the patient’s condition, may be empty)_  
        
         **Your Objective**  
        Using the patient's **symptoms, medical history, medical guidelines, and visual medical analysis**, provide a **structured and medically sound response** that includes:  
        
         **1. Preliminary Diagnosis (If Possible & Safe)**  
           - If symptoms and available data **strongly indicate a condition**, provide a **preliminary assessment**.  
           - If a **visual medical analysis** is available, use it to **support or refine** the diagnosis.  
           - **DO NOT assume a definitive diagnosis**—present possible conditions with reasoning.  
        
         **2. Recommended Medications**  
           - Provide **only the names** of the medications based on medical references.  
           - DO NOT include dosage or administration instructions in this section.  
        
         **3. Dosage & Administration Guidelines**  
           - Provide **precise dosage instructions**, including frequency, duration, and special considerations (e.g., "Take with food," "Avoid alcohol").  
        
         **4. Potential Side Effects & Risks**  
           - List **common and severe** side effects that the patient should be aware of.  
        
         **5. Contraindications & Drug Interactions**  
           - Highlight **potential conflicts** with existing medical conditions, medications, or allergies.  
        
         **6. Alternative Treatments (If Applicable)**  
           - Suggest **non-pharmaceutical treatments** like lifestyle modifications, physiotherapy, or dietary changes.  
        
         **7. Emergency Aid & First Response**  
           - If symptoms suggest an **urgent medical condition**, provide **first aid or emergency response steps** (e.g., “Lie down and elevate legs if feeling faint,” “Use an epinephrine injection for severe allergic reactions”).  
           - Clearly state if **immediate professional medical intervention** is required.  
        
         **8. Consultation Recommendation**  
           - Indicate whether a **professional medical consultation is necessary** before taking the recommended medications.  
        
         **Critical Safety Guidelines**  
        - **DO NOT assume a final diagnosis**—only suggest possible conditions based on evidence.  
        - **ALWAYS emphasize** the importance of consulting a licensed medical professional before starting medication.  
        - **If symptoms suggest a medical emergency**, prioritize first aid recommendations and urge **immediate medical attention** instead of self-medication.  
        - **Ensure compliance** with standard medical guidelines and DO NOT recommend off-label or experimental treatments unless explicitly supported by medical references.
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
