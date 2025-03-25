import json
import chromadb
from typing import List, Dict, Any
import os

class SpectraKnowledgeManager:
    def __init__(self, knowledge_file: str = "knowledge_base.json", persist_directory: str = "knowledge_store"):
        # Initialize ChromaDB with new configuration
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )
        
        # Load knowledge base
        with open(knowledge_file, 'r') as f:
            self.knowledge = json.load(f)
        
        # Create or get collections
        self.services_collection = self.client.get_or_create_collection("services")
        self.faqs_collection = self.client.get_or_create_collection("faqs")
        self.company_collection = self.client.get_or_create_collection("company")
        
        # Initialize collections
        self._initialize_collections()
    
    def _initialize_collections(self):
        # Clear existing data
        self.services_collection.delete(where={"source": "init"})
        self.faqs_collection.delete(where={"source": "init"})
        self.company_collection.delete(where={"source": "init"})
        
        # Add services
        services_docs = []
        services_metadatas = []
        services_ids = []
        
        for idx, service in enumerate(self.knowledge["services"]):
            doc = f"{service['name']}: {service['description']}. Features: {', '.join(service['features'])}."
            services_docs.append(doc)
            services_metadatas.append({
                "name": service["name"],
                "source": "init",
                "type": "service"
            })
            services_ids.append(f"service_{idx}")
        
        if services_docs:
            self.services_collection.add(
                documents=services_docs,
                metadatas=services_metadatas,
                ids=services_ids
            )
        
        # Add FAQs
        faq_docs = []
        faq_metadatas = []
        faq_ids = []
        
        for idx, faq in enumerate(self.knowledge["faqs"]):
            doc = f"Q: {faq['question']} A: {faq['answer']}"
            faq_docs.append(doc)
            faq_metadatas.append({
                "source": "init",
                "type": "faq"
            })
            faq_ids.append(f"faq_{idx}")
        
        if faq_docs:
            self.faqs_collection.add(
                documents=faq_docs,
                metadatas=faq_metadatas,
                ids=faq_ids
            )
        
        # Add company info
        company_info = self.knowledge["company_info"]
        doc = f"{company_info['name']}: {company_info['description']} Values: {', '.join(company_info['values'])}"
        
        self.company_collection.add(
            documents=[doc],
            metadatas=[{"source": "init", "type": "company_info"}],
            ids=["company_main"]
        )
    
    def query_knowledge(self, query: str, n_results: int = 2) -> Dict[str, Any]:
        """Query all collections and return relevant information."""
        results = {
            "services": self.services_collection.query(
                query_texts=[query],
                n_results=n_results
            ),
            "faqs": self.faqs_collection.query(
                query_texts=[query],
                n_results=n_results
            ),
            "company": self.company_collection.query(
                query_texts=[query],
                n_results=1
            )
        }
        return results

    def get_service_by_name(self, service_name: str) -> Dict[str, Any]:
        """Get specific service details by name."""
        for service in self.knowledge["services"]:
            if service["name"].lower() == service_name.lower():
                return service
        return None

    def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all services."""
        return self.knowledge["services"]

    def get_company_info(self) -> Dict[str, Any]:
        """Get company information."""
        return self.knowledge["company_info"] 