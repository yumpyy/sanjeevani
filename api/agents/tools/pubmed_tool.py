"""LangChain tool wrapper around the NCBI E-utilities PubMed client."""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from Bio import Entrez
from langchain_core.tools import BaseTool, tool
from pydantic import BaseModel, Field

from config import config


Entrez.email = "sanjeevani@healthai.local"


@dataclass
class PubMedDocument:
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    mesh_terms: List[str]
    doi: Optional[str] = None

    def to_text(self) -> str:
        return f"""Title: {self.title}
Authors: {", ".join(self.authors)}
Journal: {self.journal} ({self.pub_date})
PMID: {self.pmid}
DOI: {self.doi or "N/A"}

Abstract: {self.abstract}

MeSH Terms: {", ".join(self.mesh_terms) if self.mesh_terms else "None"}
"""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pmid": self.pmid,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "journal": self.journal,
            "pub_date": self.pub_date,
            "mesh_terms": self.mesh_terms,
            "doi": self.doi,
        }


class _PubMedClient:
    """Internal helper. The LangChain tool is the public surface."""

    def __init__(self, max_results: int = 8) -> None:
        self.max_results = max_results

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        sort: str = "relevance",
    ) -> List[str]:
        max_results = max_results or self.max_results
        try:
            handle = Entrez.esearch(
                db="pubmed",
                term=query,
                retmax=max_results,
                sort=sort,
                retmode="xml",
            )
            results = Entrez.read(handle)
            handle.close()
            return list(results.get("IdList", []))
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def fetch_abstracts(self, pmids: List[str]) -> List[PubMedDocument]:
        if not pmids:
            return []
        try:
            handle = Entrez.efetch(
                db="pubmed",
                id=",".join(pmids),
                rettype="abstract",
                retmode="xml",
            )
            records = Entrez.parse(handle)
            handle.close()

            documents: List[PubMedDocument] = []
            for record in records:
                try:
                    doc = self._parse_record(record)
                    if doc:
                        documents.append(doc)
                except Exception as e:
                    print(f"Error parsing record: {e}")
                    continue
            return documents
        except Exception as e:
            print(f"PubMed fetch error: {e}")
            return []

    def _parse_record(self, record: dict) -> Optional[PubMedDocument]:
        try:
            pmid = str(record.get("PMID", ""))
            title = record.get("Article", {}).get("ArticleTitle", "")

            abstract_parts = (
                record.get("Article", {}).get("Abstract", {}).get("AbstractText", [])
            )
            if isinstance(abstract_parts, list):
                abstract = " ".join(str(p) for p in abstract_parts)
            else:
                abstract = str(abstract_parts or "")

            authors: List[str] = []
            for author in record.get("Article", {}).get("AuthorList", []):
                if isinstance(author, dict):
                    last = author.get("LastName", "")
                    fore = author.get("ForeName", "")
                    if last:
                        full_name = f"{fore} {last}".strip() if fore else last
                        authors.append(full_name)

            journal = record.get("Journal", {}).get("Title", "")
            journal_date = record.get("Journal", {}).get("JournalIssue", {})
            year = journal_date.get("PubDate", {}).get("Year", "")
            month = journal_date.get("PubDate", {}).get("Month", "")
            pub_date = f"{month} {year}".strip() if month and year else year

            mesh_terms: List[str] = []
            for mesh in record.get("MeshHeadingList", []):
                if isinstance(mesh, dict):
                    desc = mesh.get("DescriptorName", "")
                    if desc:
                        mesh_terms.append(desc)

            doi: Optional[str] = None
            for art_id in record.get("ArticleIdList", []):
                if isinstance(art_id, dict) and art_id.get("IdType") == "doi":
                    doi = str(art_id)
                    break

            return PubMedDocument(
                pmid=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                journal=journal,
                pub_date=pub_date,
                mesh_terms=mesh_terms,
                doi=doi,
            )
        except Exception as e:
            print(f"Error parsing PubMed record: {e}")
            return None

    def search_and_fetch(
        self,
        query: str,
        max_results: Optional[int] = None,
    ) -> List[PubMedDocument]:
        pmids = self.search(query, max_results)
        if not pmids:
            return []
        time.sleep(0.5)
        return self.fetch_abstracts(pmids)


_pubmed_client = _PubMedClient(max_results=config.max_pubmed_results)


class PubMedSearchInput(BaseModel):
    query: str = Field(description="PubMed search query string.")
    max_results: int = Field(
        default=8,
        description="Maximum number of abstracts to return (1-20).",
    )


@tool("pubmed_search", args_schema=PubMedSearchInput)
def pubmed_search_tool(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """Search PubMed and return a list of documents (title, abstract, etc).

    Use this tool when the physician needs up-to-date evidence from the
    medical literature. Returns a list of ``PubMedDocument`` dicts.
    """
    docs = _pubmed_client.search_and_fetch(query, max_results=max_results)
    return [d.to_dict() for d in docs]
