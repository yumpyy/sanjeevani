import os
import json
from uuid import uuid4
from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma

from langchain import hub
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import CSVLoader, JSONLoader

class VectorDB:
    def __init__(self, vector_store_path) -> None:
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.vector_store = Chroma(
            collection_name="medical_documents",
            embedding_function=self.embeddings,
            persist_directory=vector_store_path,
        )
        self.prompt = hub.pull("rlm/rag-prompt")

    async def index_json_documents(self, data_directory):
        """index documents"""
        for filename in os.listdir(data_directory):
            print(f"Indexing: {filename}")
            path = os.path.join(data_directory, filename)

            # load as a document
            loader = JSONLoader(
                file_path=path,
                jq_schema='.',
                text_content=False
            )

            data = []
            try:
                data_lazy = await loader.load()
                for doc in data_lazy:
                    data.append(doc)
            except Exception as e:
                print(e)

            doc_ids = self.vector_store.add_documents(documents=data)
            print(f"Indexing complete. IDs: {doc_ids}")
            print()

    async def index_csv_documents(self, file_path):
        """index csv files"""
        loader = CSVLoader(
            file_path=file_path,
            csv_args={
                "delimiter": ",",
                "quotechar": '"',
                "fieldnames": [
                    "sub_category",
                    "product_name",
                    "salt_composition",
                    "product_price",
                    "product_manufactured",
                    "medicine_desc",
                    "side_effects",
                    "drug_interactions"
                ]
            }
        )

        data = []
        try:
            data_lazy = await loader.load()
            for doc in data_lazy:
                data.append(doc)
        except Exception as e:
            print(e)

        doc_ids = self.vector_store.add_documents(documents=data)
        print(f"Indexing complete. IDs: {doc_ids}")
        print()

    def retrieve_docs(self, patient_details):
        """
        find relevant documents by analyzing patient symptoms and details.
        """
        structured_query = self.construct_query(patient_details)
        return self.vector_store.similarity_search(structured_query)

    def construct_query(self, patient_details):
        """extract key medical aspects from patient details to create a structured query."""
        symptoms = patient_details['symptom']
        clarifications = patient_details["clarification_questions"]
        
        # extract important information
        symptom_details = " ".join([f"{q}: {a}" for q, a in clarifications.items()])
        
        # construct query medical context
        structured_query = (
            f"Patient presents with {symptoms}. {symptom_details}. "
            "Search for causes, standard treatment workflows, medicines, and risk factors."
        )
        
        return structured_query

    def generate_prompt(self, patient_details, retrieved_docs):
        docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
        structured_query = self.construct_query(patient_details)

        prompt = self.prompt.invoke({
            "question": structured_query, 
            "context": docs_content
        })

        return prompt
