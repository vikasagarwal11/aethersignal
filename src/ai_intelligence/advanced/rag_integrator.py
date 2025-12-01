"""
RAG Integrator for Copilot
Retrieval-Augmented Generation using vector search and knowledge graphs
"""

import logging
from typing import List, Dict, Any, Optional
from src.local_llm.vector_store import LocalVectorStore

logger = logging.getLogger(__name__)


class RAGIntegrator:
    """Integrates RAG for Safety Copilot."""
    
    def __init__(self):
        self.vector_store = None
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize vector store if available."""
        try:
            self.vector_store = LocalVectorStore()
        except Exception as e:
            logger.warning(f"Vector store not available: {e}")
            self.vector_store = None
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using vector search.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
        
        Returns:
            List of retrieved documents with metadata
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            results = self.vector_store.search(query, n=n_results)
            
            # Format results
            formatted_results = []
            if results and "documents" in results:
                for i, doc in enumerate(results["documents"][0] if results["documents"] else []):
                    metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                    distance = results.get("distances", [[]])[0][i] if results.get("distances") else 1.0
                    
                    formatted_results.append({
                        "document": doc,
                        "metadata": metadata,
                        "similarity": 1.0 - distance,  # Convert distance to similarity
                        "rank": i + 1
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """
        Add a document to the vector store.
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Document metadata
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return
        
        try:
            self.vector_store.add(doc_id, text, metadata)
        except Exception as e:
            logger.error(f"Error adding document: {e}")

