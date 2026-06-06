"""Therapist respond node: writes a single empathetic reply to the patient."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import get_llm
from doctors.models import TherapyResponse


class TherapistRespondNode:
    def __init__(self) -> None:
        self.llm = get_llm()
        self.string_parser = StrOutputParser()

    def respond(self, state: Dict[str, Any]) -> Dict[str, Any]:
        patient_details = state.get("patient_details", {})
        symptoms = state.get("symptoms", "") or patient_details.get("symptoms", "")
        history = state.get("conversation_history", [])

        qna_formatted = "\n".join(
            f"Q: {item.get('question', '')}\nA: {item.get('answer') or '<NO ANSWER>'}"
            for item in history
        )

        therapy_prompt = ChatPromptTemplate.from_template(
            """
            **Role:** You are a professional therapist having a warm, empathetic, and supportive conversation with a patient via text chat.
            **Objective:** Respond to the patient's last message or the current state of the conversation. Your response should acknowledge and validate their feelings, offer encouragement, provide a relevant, simple coping strategy, and gently guide the conversation. Decide if further dialogue is needed or if it's appropriate to conclude and suggest final recommendations.

            **Patient Information:**
            - Patient Details (Age, Sex): {patient_details}
            - Initial Symptoms/Reason for reaching out: {symptoms}
            - Conversation History (Q&A so far):
            {conversation_history}

            **Your Task:**
            Analyze the conversation history and patient details. Generate your response focusing on emotional support and practical coping.

            **Response Structure Requirements (Strictly follow the TherapyResponse model):**
            1. **therapist_reply**: Craft a warm, empathetic message.
               - Start by acknowledging and validating the patient's most recent expressed feeling or situation based on the LAST turn of the conversation. Use phrases like "That sounds really challenging," "I hear you," or "It's understandable you're feeling [emotion]."
               - Provide gentle encouragement or normalize their experience.
               - If the conversation feels like it needs to continue, formulate ONE gentle, open-ended follow-up question.
               - If sufficient context seems gathered, or the patient indicates they are ready to move on, your reply can transition towards a concluding statement.
               - If the user expresses thoughts of harming themselves or others, your reply MUST immediately advise them to seek professional help.
            2. **coping_strategy**: Provide a *specific, simple, and practical* coping strategy relevant to the emotional state or issues discussed.
            3. **stop_questioning**: Set to `True` if sufficient context has been gathered, the patient has nothing more to add, or there is an immediate crisis. Set to `False` if further dialogue is genuinely needed.
            4. **reason_for_stopping**: Briefly explain the reason for setting `stop_questioning`.

            **Output Format:** Return a JSON object strictly conforming to the `TherapyResponse` model.
            """
        )

        chain = therapy_prompt | self.llm.with_structured_output(TherapyResponse)

        try:
            response = chain.invoke(
                {
                    "patient_details": patient_details,
                    "symptoms": symptoms,
                    "conversation_history": qna_formatted or "No prior Q&A.",
                }
            )
        except Exception as e:
            print(f"Therapist respond error: {e}")
            response = TherapyResponse(
                therapist_reply=(
                    "I'm sorry, I'm having trouble responding right now. Please consider "
                    "reaching out to a human therapist or a crisis line for support."
                ),
                coping_strategy="Focus on taking a few slow, deep breaths.",
                stop_questioning=True,
                reason_for_stopping=f"An internal error occurred: {e}",
            )

        if response.stop_questioning:
            if not response.therapist_reply:
                response.therapist_reply = (
                    "Thank you for sharing. Please consider seeking professional help if "
                    "you need further support."
                )
            if not response.reason_for_stopping:
                response.reason_for_stopping = "Session concluded."
        else:
            if not response.therapist_reply:
                response.therapist_reply = (
                    "Can you tell me a little more about that, or how you're feeling right now?"
                )
            if not response.reason_for_stopping:
                response.reason_for_stopping = "Continuing conversation."

        # History in the therapist sub-graph is stored as {role, content} pairs
        # for consistency with the physician sub-graph. Append the reply.
        history = state.get("conversation_history", [])
        history = [
            h
            if isinstance(h, dict) and "role" in h
            else {"role": "user", "content": h.get("answer", "")}
            for h in history
        ]
        history.append({"role": "assistant", "content": response.therapist_reply})

        return {
            "therapist_reply": response.therapist_reply,
            "coping_strategy": response.coping_strategy,
            "stop_questioning": response.stop_questioning,
            "reason_for_stopping": response.reason_for_stopping,
            "conversation_history": history,
        }


therapist_respond = TherapistRespondNode()
