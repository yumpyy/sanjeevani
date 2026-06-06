"""LangChain tool wrapper around the ChromaDB-backed medical vector store."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_chroma import Chroma
from pydantic import BaseModel, Field

from agents.tools.pubmed_tool import PubMedDocument
from config import config, get_embeddings


class _MedicalVectorStore:
    """Same behaviour as the previous free-standing module."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "medical_docs",
    ) -> None:
        self.persist_directory = persist_directory or config.chroma_persist_directory
        self.collection_name = collection_name
        self._embeddings = None
        self._vectorstore = None
        self._cache: Dict[str, tuple] = {}

    @property
    def embeddings(self):
        if self._embeddings is None:
            self._embeddings = get_embeddings()
        return self._embeddings

    @property
    def vectorstore(self) -> Chroma:
        if self._vectorstore is None:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name=self.collection_name,
            )
        return self._vectorstore

    def add_documents(self, documents: List[PubMedDocument]) -> None:
        if not documents:
            return
        docs = [
            Document(
                page_content=doc.to_text(),
                metadata={
                    "pmid": doc.pmid,
                    "title": doc.title,
                    "journal": doc.journal,
                    "pub_date": doc.pub_date,
                    "doi": doc.doi,
                    "type": "pubmed",
                },
            )
            for doc in documents
        ]
        self.vectorstore.add_documents(docs)
        print(f"Added {len(docs)} documents to vector store")

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=k, filter=filter_metadata)

    def _cache_key(self, query: str, diagnoses: List[str]) -> str:
        key_data = {"query": query, "diagnoses": sorted(diagnoses)}
        return hashlib.sha256(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()

    def get_cached(
        self, query: str, diagnoses: List[str]
    ) -> Optional[List[Document]]:
        key = self._cache_key(query, diagnoses)
        if key in self._cache:
            docs, ts = self._cache[key]
            if datetime.now() - ts < timedelta(days=config.cache_ttl_days):
                print(f"Cache hit for key: {key[:16]}...")
                return docs
            else:
                del self._cache[key]

        try:
            results = self.vectorstore.get(
                where={"diagnoses_hash": key},
                include=["documents", "metadatas"],
            )
            if results["documents"]:
                docs = [
                    Document(page_content=doc, metadata=meta)
                    for doc, meta in zip(results["documents"], results["metadatas"])
                ]
                self._cache[key] = (docs, datetime.now())
                return docs
        except Exception as e:
            print(f"Error checking vector store cache: {e}")
        return None

    def cache_result(
        self,
        query: str,
        diagnoses: List[str],
        documents: List[Document],
    ) -> None:
        key = self._cache_key(query, diagnoses)
        for doc in documents:
            doc.metadata["diagnoses_hash"] = key
            doc.metadata["cached_at"] = datetime.now().isoformat()
        if documents:
            self.vectorstore.add_documents(documents)
        self._cache[key] = (documents, datetime.now())
        print(f"Cached {len(documents)} documents for key: {key[:16]}...")

    def search_with_rag_context(
        self,
        query: str,
        diagnoses: List[str],
        k: int = 5,
    ) -> List[Document]:
        cached = self.get_cached(query, diagnoses)
        if cached:
            return cached[:k]
        combined_query = f"{query} {' '.join(diagnoses)}"
        results = self.similarity_search(combined_query, k=k)
        if results:
            self.cache_result(query, diagnoses, results)
        return results


vector_store = _MedicalVectorStore()


class VectorSearchInput(BaseModel):
    query: str = Field(description="Search query for the medical vector store.")
    diagnoses: List[str] = Field(
        default_factory=list,
        description="Differential diagnoses to bias the cache key.",
    )
    k: int = Field(default=5, description="Top-k documents to return.")


@tool("vector_search", args_schema=VectorSearchInput)
def vector_search_tool(
    query: str,
    diagnoses: List[str] = [],
    k: int = 5,
) -> List[Dict[str, Any]]:
    """Semantic search over the cached medical literature.

    Use this when the diagnosis is already narrowing down and we want
    targeted evidence for a particular condition. Returns a list of dicts
    with ``page_content`` and ``metadata``.
    """
    docs = vector_store.search_with_rag_context(query, diagnoses, k=k)
    return [{"page_content": d.page_content, "metadata": d.metadata} for d in docs]
