from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class TherapyResponse(BaseModel):
    """Model for structuring therapist responses."""

    therapist_reply: str = Field(
        description="A warm, empathetic response that validates the user's feelings, provides encouragement, and includes a gentle follow-up question when appropriate."
    )
    coping_strategy: str = Field(
        description="A practical coping strategy personalized to the user's emotional state."
    )
    stop_questioning: bool = Field(
        description="Indicates whether the user has provided sufficient information to proceed with coping strategies instead of further questioning."
    )


class Therapist:
    def __init__(self) -> None:
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_retries=2,
        )

    def respond_to_patient(
        self, patient_details: dict, symptoms: str, conversation_history: dict
    ):
        """
        Generates an empathetic and supportive response, resembling a real therapist’s dialogue.
        """
        therapy_prompt = ChatPromptTemplate.from_template(
            """
            You are a professional therapist having a warm and engaging conversation with a patient.
            Your goal is to provide validation, encouragement, and a structured coping strategy while making the conversation feel natural and supportive.
            
            **Patient Details:** {patient_details}
            **Symptoms:** {symptoms}
            **Conversation History:** {conversation_history}
            
            **Your Response Should Include:**
            1. **Therapist Reply**: A warm, empathetic response that reflects real-life therapy conversations. Use gentle affirmations and a natural flow.
               - Validate the patient's feelings (e.g., "That sounds really exhausting. I hear you.").
               - Provide encouragement and normalize their experience.
               - Include a thoughtful follow-up question only if it feels appropriate, rather than forcing one.
            2. **Coping Strategy**: A simple, practical way to manage emotions (e.g., mindfulness, journaling, self-reflection).
            3. **Stop Questioning**: Indicate whether further questioning is necessary, or if the user has provided enough context to shift toward support and guidance.
            
            **Guidelines:**
            - Be warm, non-judgmental, and patient.
            - Avoid sounding robotic or overly clinical—this should feel like a real conversation.
            - If the user expresses hopelessness, provide encouragement without invalidating their feelings.
            - Do not diagnose or suggest medical treatments.
            """
        )

        therapy_chain = therapy_prompt | self.llm.with_structured_output(
            TherapyResponse
        )

        return therapy_chain.invoke(
            {
                "patient_details": patient_details,
                "symptoms": symptoms,
                "conversation_history": conversation_history,
            }
        )

    def provide_recommendations(self, patient_details: dict):
        """
        Provides structured self-care recommendations to improve emotional well-being.
        """
        recommendation_prompt = ChatPromptTemplate.from_template(
            """
            Based on the patient's emotional state, provide a warm and structured therapy recommendation.
            
            **Patient Details:** {patient_details}
            
            **Your Response Should Include:**
            1. **General Suggestions**: Actionable self-care strategies tailored to the patient (e.g., practicing mindfulness, journaling, reaching out to a friend).
            2. **Closing Message**: A short, warm, and encouraging statement that reassures the patient.
            
            **Guidelines:**
            - Be empathetic, encouraging, and uplifting.
            - Offer simple but meaningful advice.
            - Avoid medical prescriptions or clinical diagnoses.
            """
        )

        recommendation_chain = recommendation_prompt | self.llm.with_structured_output(
            TherapyResponse
        )

        return recommendation_chain.invoke({"patient_details": patient_details})
