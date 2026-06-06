"""Composite RAG tool combining PubMed search + vector store caching."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from agents.tools.pubmed_tool import PubMedDocument, _pubmed_client
from agents.tools.vector_store_tool import vector_store


@dataclass
class RetrievedContext:
    documents: List[Document]
    sources: List[Dict[str, Any]]
    query_used: str


class RagRetrieveInput(BaseModel):
    query: str = Field(description="Free-text patient complaint or symptom string.")
    diagnoses: List[str] = Field(
        default_factory=list,
        description="Differential diagnoses (top-3) used to bias retrieval.",
    )
    use_cache: bool = Field(
        default=True,
        description="If true, prefer the cached vector store before hitting PubMed.",
    )


def _retrieve_from_pubmed(query: str, diagnoses: List[str]) -> RetrievedContext:
    search_queries: List[str] = [query]
    for diagnosis in diagnoses[:3]:
        search_queries.append(f"{diagnosis} treatment management")

    all_docs: List[PubMedDocument] = []
    seen_pmids: set[str] = set()

    for sq in search_queries:
        for doc in _pubmed_client.search_and_fetch(sq):
            if doc.pmid not in seen_pmids:
                all_docs.append(doc)
                seen_pmids.add(doc.pmid)
        if len(all_docs) >= 8:
            break

    if all_docs:
        vector_store.add_documents(all_docs)

    documents = [
        Document(
            page_content=doc.to_text(),
            metadata={"pmid": doc.pmid, "title": doc.title},
        )
        for doc in all_docs
    ]
    sources = [
        {
            "pmid": doc.pmid,
            "title": doc.title,
            "journal": doc.journal,
            "pub_date": doc.pub_date,
            "doi": doc.doi,
        }
        for doc in all_docs
    ]
    return RetrievedContext(documents=documents, sources=sources, query_used=query)


def _retrieve_with_rag(
    query: str,
    diagnoses: List[str],
    use_cache: bool = True,
) -> RetrievedContext:
    if use_cache:
        cached_docs = vector_store.search_with_rag_context(query, diagnoses, k=5)
        if cached_docs:
            sources = [
                {
                    "pmid": doc.metadata.get("pmid", "unknown"),
                    "title": doc.metadata.get("title", "Unknown"),
                }
                for doc in cached_docs
            ]
            return RetrievedContext(
                documents=cached_docs, sources=sources, query_used=query
            )
    return _retrieve_from_pubmed(query, diagnoses)


@tool("rag_retrieve", args_schema=RagRetrieveInput)
def rag_retrieve_tool(
    query: str,
    diagnoses: List[str] = [],
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Retrieve medical evidence via the RAG pipeline.

    Returns a dict with ``documents`` (list of page_content + metadata),
    ``sources`` (citation dicts), and ``query_used``. The physician graph
    calls this before generating a prescription so the LLM has up-to-date
    evidence in context.
    """
    context = _retrieve_with_rag(query, diagnoses, use_cache=use_cache)
    return {
        "query_used": context.query_used,
        "documents": [
            {"page_content": d.page_content, "metadata": d.metadata}
            for d in context.documents
        ],
        "sources": context.sources,
    }
