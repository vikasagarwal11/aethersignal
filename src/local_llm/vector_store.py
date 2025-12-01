"""
Local Vector Store - FAISS/Chroma for semantic search
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalVectorStore:
    """Local vector store for semantic search."""
    
    def __init__(self, store_path: str = "data/vector_store"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Initialize vector store."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            self.client = chromadb.PersistentClient(path=str(self.store_path))
            
            # Use sentence transformers for embeddings
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"  # Lightweight, fast model
            )
            
            self.collection = self.client.get_or_create_collection(
                name="intelligence_store",
                embedding_function=self.embedding_fn
            )
            
            logger.info("Vector store initialized successfully")
            
        except ImportError:
            logger.warning("ChromaDB not available. Vector store disabled.")
            self.collection = None
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            self.collection = None
    
    def add(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        """
        Add a document to the vector store.
        
        Args:
            doc_id: Unique document identifier
            text: Document text
            metadata: Document metadata
        """
        if not self.collection:
            logger.warning("Vector store not initialized")
            return
        
        try:
            self.collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[metadata]
            )
            logger.debug(f"Added document {doc_id} to vector store")
        except Exception as e:
            logger.error(f"Error adding document: {e}")
    
    def search(self, query: str, n: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            n: Number of results
            filters: Optional metadata filters
        
        Returns:
            Search results dictionary
        """
        if not self.collection:
            logger.warning("Vector store not initialized")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
        
        try:
            where = filters if filters else None
            results = self.collection.query(
                query_texts=[query],
                n_results=n,
                where=where
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }

