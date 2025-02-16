import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()


class TherapyAnalysis(BaseModel):
    """Model for structuring therapy responses."""

    clarification_question: str = Field(
        description="A short and concise supportive opinion on the user input and A thoughtful follow-up question to encourage deeper introspection and discussion."
    )
    stop_questioning: bool = Field(
        description="Indicates whether the user has given enough information about himself."
    )
    coping_strategy: str = Field(
        description="A gentle, practical coping strategy based on the user's emotional state."
    )


class Therapist:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")

        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            # model="deepseek-r1-distill-llama-70b",
            temperature=0.7,
            max_retries=2,
        )

    def generate_clarification_question(
        self, patient_details: dict, symptoms: str, clarification_history: dict
    ):
        """
        Generates a follow-up question and coping strategy based on user input.
        """
        therapy_prompt = ChatPromptTemplate.from_template(
            """
            You are a professional therapist guiding a patient through introspection and emotional support.
            
            **Patient Details:** {patient_details}
            **Symptoms:** {symptoms}
            **Clarification History:** {clarification_history}
            
            **Your Response Should Include:**
            1. **Consolation**: A short and concise supportive opinion on the user input.
            2. **Clarification Question**: A question that encourages deeper self-reflection or something a therapist would ask.
            3. **Stop Questioning**: Whether the user has given enough information about his issue.
            4. **Coping Strategy**: A gentle way to manage emotions (e.g., mindfulness, journaling, breathing exercises).
            
            **Guidelines:**
            - Be warm, non-judgmental, and patient.
            - Avoid diagnosing; instead, help the user explore their feelings.
            - Keep responses concise but meaningful.
            """
        )

        therapy_chain = therapy_prompt | self.llm.with_structured_output(
            TherapyAnalysis
        )

        return therapy_chain.invoke(
            {
                "patient_details": patient_details,
                "symptoms": symptoms,
                "clarification_history": clarification_history,
            }
        )

    def generate_prescription(self, patient_details: dict):
        """
        Generates a personalized therapy recommendation or coping plan.
        """
        prescription_prompt = ChatPromptTemplate.from_template(
            """
            Based on the patient's details and emotional state, provide a supportive and personalized therapy recommendation.
            
            **Patient Details:** {patient_details}
            
            **Your Response Should Include:**
            - A brief, supportive summary of the patient's emotional well-being.
            - A few actionable coping strategies for emotional regulation.
            - A reminder to seek professional help if needed.
            """
        )

        prescription_chain = prescription_prompt | self.llm.with_structured_output(str)

        return prescription_chain.invoke({"patient_details": patient_details})
