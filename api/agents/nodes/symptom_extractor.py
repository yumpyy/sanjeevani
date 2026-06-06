"""Symptom extractor node for the physician graph."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm
from doctors.models import ExtractedSymptoms


class SymptomExtractorNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.output_parser = StrOutputParser()

    def extract(
        self, patient_text: str, visual_analysis: str = ""
    ) -> Dict[str, Any]:
        visual_context = (
            f"Visual observation: {visual_analysis}" if visual_analysis else ""
        )

        prompt = ChatPromptTemplate.from_template(
            """You are a medical symptom extractor. Analyze the patient description and extract structured symptom information.

Patient Description:
{patient_text}

{visual_context}

Extract the following:
1. Chief complaint (brief summary in 1-2 sentences)
2. Key symptoms (medical terms, e.g., "throbbing headache", "dry cough", "abdominal pain")

Output as a structured JSON with:
- "chief_complaint": Brief summary
- "symptoms": List of symptom keywords/phrases
"""
        )

        chain = prompt | self.llm.with_structured_output(ExtractedSymptoms)
        try:
            result = chain.invoke(
                {
                    "patient_text": patient_text,
                    "visual_context": visual_context,
                }
            )
            return {
                "chief_complaint": result.chief_complaint,
                "symptoms": result.symptoms,
                "extraction_complete": True,
            }
        except Exception as e:
            print(f"Symptom extraction error: {e}")
            return {
                "chief_complaint": patient_text[:100],
                "symptoms": [patient_text] if patient_text else [],
                "extraction_complete": False,
                "error": str(e),
            }


symptom_extractor = SymptomExtractorNode()
