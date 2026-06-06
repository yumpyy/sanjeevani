"""SOAP note generator node: produces a clinical-style summary."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm


class SOAPNoteGeneratorNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.output_parser = StrOutputParser()

    def generate_soap_note(self, state: Dict[str, Any]) -> Dict[str, Any]:
        patient_details = state.get("patient_details", {})
        symptoms = state.get("symptoms", [])
        history = state.get("conversation_history", [])
        potential_diagnoses = state.get("potential_diagnoses", [])
        diagnosis = state.get("diagnosis", "")
        prescription = state.get("prescription", {})
        visual_analysis = state.get("visual_analysis", "")

        history_text = self._format_history(history)

        prompt = ChatPromptTemplate.from_template(
            """Generate a structured SOAP note for the patient encounter.

Patient Information:
- Age: {age}
- Sex: {sex}
- Chief Complaint: {chief_complaint}

Extracted Symptoms: {symptoms}

Visual Analysis: {visual_analysis}

Conversation History (Q&A):
{history}

Differential Diagnoses:
{diagnoses}

Diagnosis: {diagnosis}

Prescription/Treatment Plan:
{prescription}

Generate a professional SOAP note with:

S - Subjective:
- Chief Complaint
- History of Present Illness (from conversation)
- Past Medical History
- Medications
- Allergies
- Family History
- Social History

O - Objective:
- Physical Exam Findings (noted from conversation)
- Vital Signs (if mentioned)
- Visual Analysis Results

A - Assessment:
- Primary Diagnosis
- Differential Diagnoses

P - Plan:
- Treatment Plan
- Medications prescribed
- Patient Education
- Follow-up recommendations
- Consultation notes

Note: This is an AI-generated preliminary assessment and should be reviewed by a healthcare professional.
"""
        )

        chain = prompt | self.llm | self.output_parser

        try:
            soap_note = chain.invoke(
                {
                    "age": patient_details.get("age", "unknown"),
                    "sex": patient_details.get("sex", "unknown"),
                    "chief_complaint": patient_details.get("symptoms", ""),
                    "symptoms": ", ".join(symptoms) if symptoms else "None",
                    "visual_analysis": visual_analysis or "None",
                    "history": history_text,
                    "diagnoses": ", ".join(potential_diagnoses)
                    if potential_diagnoses
                    else "None",
                    "diagnosis": diagnosis or "Pending",
                    "prescription": str(prescription) if prescription else "None",
                }
            )

            return {"soap_note": soap_note}
        except Exception as e:
            print(f"SOAP note generation error: {e}")
            return {
                "soap_note": f"Error generating SOAP note: {str(e)}",
                "error": str(e),
            }

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No conversation history."

        formatted: List[str] = []
        for item in history:
            if item.get("role") == "user":
                formatted.append(f"Patient: {item.get('content', '')}")
            elif item.get("role") == "assistant":
                formatted.append(f"Doctor: {item.get('content', '')}")

        return "\n\n".join(formatted)


soap_note_generator = SOAPNoteGeneratorNode()
