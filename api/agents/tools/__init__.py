"""LangChain tools used by the Sanjeevani LangGraph backend.

Every tool is a ``langchain_core`` ``BaseTool`` (decorated with ``@tool``)
so it can be passed to ``ToolNode`` or used with ``llm.bind_tools``.
"""
from agents.tools.base import JsonSerializableTool, dumps, to_jsonable
from agents.tools.emergency_tool import (
    EmergencyCheckInput,
    EmergencyCheckTool,
    EmergencyResult,
    emergency_check_tool,
)
from agents.tools.pubmed_tool import (
    PubMedDocument,
    PubMedSearchInput,
    pubmed_search_tool,
)
from agents.tools.rag_tool import (
    RagRetrieveInput,
    RetrievedContext,
    rag_retrieve_tool,
)
from agents.tools.vector_store_tool import (
    VectorSearchInput,
    vector_search_tool,
)

ALL_TOOLS = [
    emergency_check_tool,
    pubmed_search_tool,
    vector_search_tool,
    rag_retrieve_tool,
]

__all__ = [
    "ALL_TOOLS",
    "EmergencyCheckInput",
    "EmergencyCheckTool",
    "EmergencyResult",
    "JsonSerializableTool",
    "PubMedDocument",
    "PubMedSearchInput",
    "RagRetrieveInput",
    "RetrievedContext",
    "VectorSearchInput",
    "dumps",
    "emergency_check_tool",
    "pubmed_search_tool",
    "rag_retrieve_tool",
    "to_jsonable",
    "vector_search_tool",
]
