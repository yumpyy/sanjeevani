from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class Therapist:
    def __init__(self) -> None:
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            # model="deepseek-r1-distill-llama-70b",
            temperature=0.2,
            max_retries=2,
        )
