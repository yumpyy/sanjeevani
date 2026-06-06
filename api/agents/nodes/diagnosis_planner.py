"""Diagnosis planner node: produces a differential diagnosis list."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm
from doctors.models import DiagnosisPlan


class DiagnosisPlannerNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.output_parser = StrOutputParser()

    def plan_diagnosis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        patient_details = state.get("patient_details", {})
        symptoms = state.get("symptoms", [])
        history = state.get("conversation_history", [])
        visual_analysis = state.get("visual_analysis", "")

        history_text = self._format_history(history)

        prompt = ChatPromptTemplate.from_template(
            """You are an AI medical diagnostician. Based on the patient information and history, create a differential diagnosis plan.

Patient Information:
- Age: {age}
- Sex: {sex}
- Chief Complaint: {chief_complaint}
- Extracted Symptoms: {symptoms}

Visual Analysis: {visual_analysis}

Conversation History (Q&A):
{history}

Your task:
1. Analyze the symptoms, history, and visual analysis
2. Generate a list of 3-5 potential diagnoses (differential diagnoses)
3. Provide reasoning for why each diagnosis is considered
4. Note any recommended diagnostic tests if applicable

Output as JSON with:
- "potential_diagnoses": List of 3-5 conditions
- "reasoning": Brief explanation for the differential
- "recommended_tests": Any tests to consider (optional)
"""
        )

        chain = prompt | self.llm.with_structured_output(DiagnosisPlan)

        try:
            result = chain.invoke(
                {
                    "age": patient_details.get("age", "unknown"),
                    "sex": patient_details.get("sex", "unknown"),
                    "chief_complaint": patient_details.get("symptoms", ""),
                    "symptoms": ", ".join(symptoms) if symptoms else "None extracted",
                    "visual_analysis": visual_analysis or "None",
                    "history": history_text,
                }
            )

            return {
                "potential_diagnoses": result.potential_diagnoses,
                "diagnosis_reasoning": result.reasoning,
                "recommended_tests": result.recommended_tests,
            }
        except Exception as e:
            print(f"Diagnosis planning error: {e}")
            return {
                "potential_diagnoses": [
                    "Unable to determine - please consult a doctor"
                ],
                "diagnosis_reasoning": f"Error: {str(e)}",
                "recommended_tests": [],
                "error": str(e),
            }

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No conversation history available."

        formatted: List[str] = []
        for item in history:
            if item.get("role") == "user":
                formatted.append(f"Patient: {item.get('content', '')}")
            elif item.get("role") == "assistant":
                formatted.append(f"Doctor: {item.get('content', '')}")

        return "\n\n".join(formatted)


diagnosis_planner = DiagnosisPlannerNode()
