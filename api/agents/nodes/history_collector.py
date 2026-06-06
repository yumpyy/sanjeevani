"""History collector node: asks the next OLDCARTS question.

Hard rule: the node itself enforces a max-turns guard (``max_history_turns``)
so the LangGraph loop terminates deterministically. The graph uses an
``interrupt_before`` on this node to pause for the human answer.
"""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm
from doctors.models import HistoryQuestionResponse


HISTORY_AREAS = [
    "Onset - When did symptoms start?",
    "Location - Where is the pain/discomfort?",
    "Duration - How long does it last?",
    "Character - Describe the sensation (sharp, dull, throbbing)?",
    "Aggravating/Alleviating - What makes it better/worse?",
    "Radiation - Does the pain spread anywhere?",
    "Timing - Is it constant or intermittent?",
    "Severity - Rate pain on 1-10 scale",
    "Associated symptoms - Fever, nausea, fatigue, etc.",
    "Past medical history - Existing conditions, surgeries",
    "Medications - Current prescriptions, OTC drugs",
    "Allergies - Drug, food, environmental",
    "Family history - Hereditary conditions",
    "Social history - Smoking, alcohol, occupation",
]

MAX_HISTORY_TURNS = 8


class HistoryCollectorNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.output_parser = StrOutputParser()
        self.max_history_turns = MAX_HISTORY_TURNS

    def should_continue(self, state: Dict[str, Any]) -> bool:
        history = state.get("conversation_history", [])
        turns = len([h for h in history if h.get("role") == "assistant"])
        return turns < self.max_history_turns

    def collect_next_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        history = state.get("conversation_history", [])
        turns = len([h for h in history if h.get("role") == "assistant"])

        if turns >= self.max_history_turns:
            return {
                "clarification_question": "",
                "stop_questioning": True,
                "reason_for_stopping": (
                    f"Max history turns reached ({self.max_history_turns})"
                ),
            }

        patient_details = state.get("patient_details", {})
        symptoms = state.get("symptoms", [])
        visual_analysis = state.get("visual_analysis", "")

        history_text = self._format_history(history)

        prompt = ChatPromptTemplate.from_template(
            """You are an AI medical assistant conducting a patient interview.
Your goal is to gather a comprehensive medical history using the OLDCARTS method.

Patient Information:
- Age: {age}
- Sex: {sex}
- Chief Complaint: {chief_complaint}
- Extracted Symptoms: {symptoms}

Visual Analysis: {visual_analysis}

Conversation History:
{history}

History Areas to Cover (choose the most important next area):
{history_areas}

Instructions:
1. Review the conversation history - if the patient's last answer was unclear, ask for clarification FIRST
2. Choose the next most important area from the history areas list that hasn't been covered
3. Ask ONE clear, patient-friendly question
4. If you have gathered sufficient history (covered at least 6 areas), set stop_questioning to true

Output as JSON with:
- "question": The next question to ask
- "stop_questioning": true if enough history gathered, false otherwise
- "reason": Brief explanation
- "area_covered": Which history area this question covers
"""
        )

        chain = prompt | self.llm.with_structured_output(HistoryQuestionResponse)

        try:
            result = chain.invoke(
                {
                    "age": patient_details.get("age", "unknown"),
                    "sex": patient_details.get("sex", "unknown"),
                    "chief_complaint": patient_details.get("symptoms", ""),
                    "symptoms": ", ".join(symptoms) if symptoms else "None extracted",
                    "visual_analysis": visual_analysis or "None",
                    "history": history_text or "No previous questions asked yet.",
                    "history_areas": "\n".join(f"- {area}" for area in HISTORY_AREAS),
                }
            )

            return {
                "clarification_question": result.question,
                "stop_questioning": result.stop_questioning,
                "reason_for_stopping": result.reason if result.stop_questioning else "",
                "history_area_current": result.area_covered,
            }
        except Exception as e:
            print(f"History collection error: {e}")
            return {
                "clarification_question": "Can you tell me more about your symptoms?",
                "stop_questioning": False,
                "reason_for_stopping": "",
                "error": str(e),
            }

    def _format_history(self, history: List[Dict]) -> str:
        if not history:
            return "No previous questions asked yet."

        formatted: List[str] = []
        for item in history:
            if item.get("role") == "user":
                formatted.append(f"Patient: {item.get('content', '')}")
            elif item.get("role") == "assistant":
                formatted.append(f"Doctor: {item.get('content', '')}")

        return "\n\n".join(formatted)


history_collector = HistoryCollectorNode()
