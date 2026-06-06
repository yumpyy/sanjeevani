"""Therapist recommend node: produces the final self-care summary."""
from __future__ import annotations

from typing import Any, Dict

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm


class TherapistRecommendNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.string_parser = StrOutputParser()

    def recommend(self, state: Dict[str, Any]) -> Dict[str, Any]:
        patient_details = state.get("patient_details", {})

        prompt = ChatPromptTemplate.from_template(
            """
            **Role:** You are a professional therapist providing final self-care recommendations and closing remarks based on a patient's general context from a chat session.
            **Objective:** Generate a warm, structured text summary of actionable self-care strategies and a supportive concluding message for the patient.

            **Patient Details (General context from session start):** {patient_details}

            **Your Task:**
            Based on the general information available about the patient, suggest broadly applicable self-care strategies and provide a warm closing.

            **Output Structure Requirements:**
            - Opening: warm concluding statement
            - Self-Care Suggestions: 2-3 simple, actionable self-care strategies
            - Coping Strategy Reminder: mention a quick coping strategy
            - Seeking Professional Help: strongly encourage the patient to seek support from a qualified mental health professional
            - Closing Message: short, warm, encouraging statement

            Avoid medical or diagnostic language. Focus on self-care and emotional support.
            """
        )

        chain = prompt | self.llm | self.string_parser

        try:
            text = chain.invoke({"patient_details": patient_details})
        except Exception as e:
            print(f"Therapist recommend error: {e}")
            text = (
                "I'm sorry, I couldn't generate a full recommendation summary due to "
                f"an internal error: {e}. Please remember to seek professional help if "
                "you need it."
            )

        return {"recommendation": text}


therapist_recommend = TherapistRecommendNode()
