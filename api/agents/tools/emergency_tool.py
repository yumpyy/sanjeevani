"""LangChain tool wrapper around the regex-based emergency checker."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Type

from langchain_community.tools import tool
from pydantic import BaseModel, Field


@dataclass
class EmergencyResult:
    is_emergency: bool
    emergency_type: Optional[str]
    description: str
    urgency_level: str


class EmergencyCheckInput(BaseModel):
    patient_text: str = Field(description="Free-text complaint or recent answer from the patient.")
    symptoms: str = Field(default="", description="Structured symptom text from history.")
    visual_analysis: Optional[str] = Field(
        default=None,
        description="Optional image analysis summary to scan for emergency cues.",
    )


class EmergencyCheckTool:
    """Regex-based emergency detector.

    Kept in pure Python so the check is deterministic and free. The same
    logic that lived in ``agents/tools/emergency_checker.py`` is preserved
    verbatim — only the wrapping changes.
    """

    EMERGENCY_KEYWORDS: Dict[str, List[str]] = {
        "cardiac": [
            r"chest pain.*tight",
            r"crushing.*chest",
            r"heart attack",
            r"myocardial infarction",
            r"cardiac arrest",
            r"severe chest pressure",
            r"pain.*jaw.*arm",
        ],
        "respiratory": [
            r"can't breathe",
            r"difficulty breathing",
            r"shortness of breath.*severe",
            r"choking",
            r"asthma.*attack",
            r"stopped breathing",
            r"blue lips",
            r"cyanosis",
        ],
        "neurological": [
            r"stroke",
            r"can't speak",
            r"face.*droop",
            r"arm.*weak",
            r"confusion.*sudden",
            r"loss of consciousness",
            r"seizure",
            r"fitting",
            r"unresponsive",
        ],
        "bleeding": [
            r"severe bleeding",
            r"can't stop bleeding",
            r"blood.*pressure.*low",
            r"shock",
            r"internal bleeding",
        ],
        "allergic": [
            r"anaphylaxis",
            r"throat.*swell",
            r"allergic reaction.*severe",
            r"hives.*trouble breathing",
        ],
        "poisoning": [
            r"poison",
            r"overdose",
            r"ingested.*toxic",
            r"drug.*too much",
        ],
        "psychiatric": [
            r"suicide",
            r"kill myself",
            r"self harm",
            r"harm.*others",
            r"psychotic",
        ],
        "trauma": [
            r"broken bone.*visible",
            r"head injury.*lost consciousness",
            r"car accident",
            r"fall.*unconscious",
            r"burn.*severe",
        ],
    }

    URGENT_SYMPTOMS: List[str] = [
        "high fever",
        "stiff neck",
        "severe headache",
        "confusion",
        "persistent vomiting",
        "dehydration",
        "severe pain",
        "bleeding",
    ]

    DESCRIPTIONS: Dict[str, str] = {
        "cardiac": "Possible heart attack. Call emergency services immediately.",
        "respiratory": "Severe breathing difficulty. Seek immediate medical attention.",
        "neurological": "Possible stroke. Time is critical - call emergency services.",
        "bleeding": "Severe bleeding detected. Apply pressure and seek immediate help.",
        "allergic": "Severe allergic reaction (anaphylaxis). Use epinephrine if available and call emergency.",
        "poisoning": "Possible poisoning/overdose. Call poison control or emergency services.",
        "psychiatric": "Mental health crisis. Please contact emergency services or a crisis hotline.",
        "trauma": "Severe injury detected. Do not move the person and call emergency services.",
    }

    def check(self, text: str) -> EmergencyResult:
        text_lower = text.lower()
        for emergency_type, patterns in self.EMERGENCY_KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return EmergencyResult(
                        is_emergency=True,
                        emergency_type=emergency_type,
                        description=self.DESCRIPTIONS.get(
                            emergency_type,
                            "Medical emergency detected. Call emergency services.",
                        ),
                        urgency_level="critical",
                    )

        urgent_count = sum(
            1 for symptom in self.URGENT_SYMPTOMS if symptom in text_lower
        )
        if urgent_count >= 2:
            return EmergencyResult(
                is_emergency=False,
                emergency_type="potentially_urgent",
                description="Multiple urgent symptoms detected. Please seek medical attention soon.",
                urgency_level="high",
            )

        return EmergencyResult(
            is_emergency=False,
            emergency_type=None,
            description="No immediate emergency detected.",
            urgency_level="normal",
        )

    def check_patient_input(
        self,
        patient_text: str,
        symptoms: str,
        visual_analysis: Optional[str] = None,
    ) -> EmergencyResult:
        combined = f"{patient_text} {symptoms}"
        if visual_analysis:
            combined += f" {visual_analysis}"
        return self.check(combined)


emergency_checker = EmergencyCheckTool()


@tool("emergency_check", args_schema=EmergencyCheckInput)
def emergency_check_tool(
    patient_text: str,
    symptoms: str = "",
    visual_analysis: Optional[str] = None,
) -> Dict[str, Any]:
    """Scan a patient message for medical emergency signals.

    Returns a dict with ``is_emergency``, ``emergency_type``, ``description``,
    and ``urgency_level``. The physician graph calls this once at session
    start and again whenever a new user message hints at escalation.
    """
    result = emergency_checker.check_patient_input(patient_text, symptoms, visual_analysis)
    return asdict(result)
