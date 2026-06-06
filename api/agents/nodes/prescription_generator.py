"""Prescription generator node: produces a preliminary Rx + RAG evidence.

Uses the ``rag_retrieve`` LangChain tool to fetch relevant literature and
feeds the result into a structured LLM call. Falls back gracefully if the
tool or LLM fails.
"""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate

from agents.tools.rag_tool import _retrieve_with_rag
from config import get_llm
from doctors.models import PrescriptionResponse


class PrescriptionGeneratorNode:
    def __init__(self) -> None:
        self.llm = get_llm()

    def generate_prescription(self, state: Dict[str, Any]) -> Dict[str, Any]:
        patient_details = state.get("patient_details", {})
        symptoms = state.get("symptoms", [])
        history = state.get("conversation_history", [])
        potential_diagnoses = state.get("potential_diagnoses", [])
        visual_analysis = state.get("visual_analysis", "")

        try:
            context = _retrieve_with_rag(
                query=patient_details.get("symptoms", ""),
                diagnoses=potential_diagnoses,
            )
        except Exception as e:
            print(f"RAG retrieval error: {e}")
            context = type("EmptyContext", (), {"documents": [], "sources": []})()

        history_text = self._format_history(history)

        context_text = (
            "\n\n".join(
                doc.page_content[:500] for doc in getattr(context, "documents", [])
            )
            or "No literature retrieved."
        )

        prompt = ChatPromptTemplate.from_template(
            """You are an AI medical prescriber. Based on the patient information and retrieved medical literature, generate a preliminary prescription and treatment plan.

Patient Information:
- Age: {age}
- Sex: {sex}
- Chief Complaint: {symptoms}
- Extracted Symptoms: {symptoms_list}
- Visual Analysis: {visual_analysis}

Conversation History:
{history}

Potential Diagnoses Considered:
{diagnoses}

Retrieved Medical Literature:
{context}

IMPORTANT INSTRUCTIONS:
1. The retrieved literature may not be directly applicable. Use your medical knowledge.
2. If the diagnosis is uncertain, state that clearly.
3. Only prescribe medications if strongly supported by the literature or standard medical practice.
4. Always recommend professional consultation.
5. Include relevant emergency warning signs.
6. Note: This is a PRELIMINARY assessment only.

Output as JSON with:
- "diagnosis": The most likely preliminary diagnosis (or "Inconclusive - requires professional evaluation")
- "medications": List of medications with dosage (or empty list if none recommended)
- "side_effects": Common side effects for prescribed medications
- "contraindications": Any contraindications based on patient history
- "alternative_treatments": Non-pharmaceutical treatments
- "emergency_steps": Warning signs requiring immediate attention
- "consultation_required": Always true
"""
        )

        chain = prompt | self.llm.with_structured_output(PrescriptionResponse)

        try:
            result = chain.invoke(
                {
                    "age": patient_details.get("age", "unknown"),
                    "sex": patient_details.get("sex", "unknown"),
                    "symptoms": patient_details.get("symptoms", ""),
                    "symptoms_list": ", ".join(symptoms) if symptoms else "None",
                    "visual_analysis": visual_analysis or "None",
                    "history": history_text,
                    "diagnoses": ", ".join(potential_diagnoses)
                    if potential_diagnoses
                    else "None",
                    "context": context_text,
                }
            )

            return {
                "diagnosis": result.diagnosis,
                "medications": [m.model_dump() for m in result.medications],
                "side_effects": result.side_effects,
                "contraindications": result.contraindications,
                "alternative_treatments": result.alternative_treatments,
                "emergency_steps": result.emergency_steps,
                "consultation_required": result.consultation_required,
                "sources": getattr(context, "sources", []),
            }
        except Exception as e:
            print(f"Prescription generation error: {e}")
            return {
                "diagnosis": "Unable to generate - please consult a medical professional",
                "medications": [],
                "side_effects": [],
                "contraindications": [],
                "alternative_treatments": [
                    "Rest",
                    "Hydration",
                    "Consult a doctor",
                ],
                "emergency_steps": [],
                "consultation_required": True,
                "sources": getattr(context, "sources", []),
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


prescription_generator = PrescriptionGeneratorNode()
