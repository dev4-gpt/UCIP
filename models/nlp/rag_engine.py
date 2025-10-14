"""RAG (Retrieval-Augmented Generation) engine for policy Q&A."""
import os
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class RAGEngine:
    """RAG engine for semantic search and Q&A over policy documents."""

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        index_type: str = "flat",
    ):
        """Initialize RAG engine.
        
        Args:
            embedding_model: Sentence transformer model name
            index_type: FAISS index type ('flat', 'ivf')
        """
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index_type = index_type
        self.index = None
        self.documents = []
        self.metadata = []
        
        logger.info(f"RAG engine initialized with {embedding_model}")

    def build_index(
        self,
        documents: List[str],
        metadata: Optional[List[Dict]] = None,
    ) -> None:
        """Build FAISS index from documents.
        
        Args:
            documents: List of document chunks
            metadata: Optional metadata for each document
        """
        logger.info(f"Building index for {len(documents)} documents...")
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(
            documents,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        
        if self.index_type == "flat":
            self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, min(100, len(documents) // 10))
            self.index.train(embeddings)
        
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents = documents
        self.metadata = metadata or [{} for _ in documents]
        
        logger.info(f"Index built with {self.index.ntotal} vectors")

    def search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of result dictionaries
        """
        if self.index is None:
            logger.error("Index not built. Call build_index() first.")
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, k)
        
        # Format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    'document': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score),
                    'index': int(idx)
                })
        
        logger.info(f"Found {len(results)} results for query")
        return results

    def generate_answer(
        self,
        query: str,
        context_docs: List[str],
        max_context_length: int = 2000,
    ) -> str:
        """Generate answer using retrieved context.
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            max_context_length: Maximum context length
            
        Returns:
            Generated answer
        """
        # Combine context
        context = "\n\n".join(context_docs)
        if len(context) > max_context_length:
            context = context[:max_context_length]
        
        # In production, use OpenAI API or local LLM
        # For now, return a simple response
        answer = f"Based on the policy documents, regarding '{query}': {context[:200]}..."
        
        return answer

    def query(
        self,
        question: str,
        k: int = 3,
    ) -> Dict:
        """Query the RAG system.
        
        Args:
            question: User question
            k: Number of context documents to retrieve
            
        Returns:
            Dictionary with answer and sources
        """
        # Retrieve relevant documents
        results = self.search(question, k=k)
        
        if not results:
            return {
                'answer': "I couldn't find relevant information in the policy documents.",
                'sources': [],
                'confidence': 0.0
            }
        
        # Extract context
        context_docs = [r['document'] for r in results]
        
        # Generate answer
        answer = self.generate_answer(question, context_docs)
        
        # Calculate confidence based on top score
        confidence = results[0]['score'] if results else 0.0
        
        return {
            'answer': answer,
            'sources': results,
            'confidence': float(confidence)
        }

    def save_index(self, path: str) -> None:
        """Save FAISS index to disk.
        
        Args:
            path: Path to save index
        """
        if self.index is not None:
            faiss.write_index(self.index, path)
            logger.info(f"Index saved to {path}")

    def load_index(self, path: str) -> None:
        """Load FAISS index from disk.
        
        Args:
            path: Path to index file
        """
        if os.path.exists(path):
            self.index = faiss.read_index(path)
            logger.info(f"Index loaded from {path}")
        else:
            logger.error(f"Index file not found: {path}")


def main():
    """Example usage."""
    rag = RAGEngine()
    
    # Sample policy documents
    documents = [
        "The university commits to 50% emissions reduction by 2030.",
        "All buildings must undergo energy efficiency retrofits by 2025.",
        "Solar panels will be installed on 80% of suitable rooftops by 2028.",
        "The campus will transition to 100% electric vehicle fleet by 2030.",
        "Natural gas heating will be phased out by December 31, 2035.",
        "New construction must meet LEED Gold standards.",
        "Green space and tree canopy will expand by 25% by 2027.",
    ]
    
    metadata = [
        {'source': 'Climate Action Plan', 'section': 'Goals'},
        {'source': 'Climate Action Plan', 'section': 'Buildings'},
        {'source': 'Climate Action Plan', 'section': 'Energy'},
        {'source': 'Climate Action Plan', 'section': 'Transportation'},
        {'source': 'Climate Action Plan', 'section': 'Energy'},
        {'source': 'Climate Action Plan', 'section': 'Buildings'},
        {'source': 'Climate Action Plan', 'section': 'Green Infrastructure'},
    ]
    
    # Build index
    rag.build_index(documents, metadata)
    
    # Query the system
    questions = [
        "What is the emissions reduction target?",
        "When will solar panels be installed?",
        "What are the requirements for new buildings?",
    ]
    
    for question in questions:
        result = rag.query(question)
        logger.info(f"\nQ: {question}")
        logger.info(f"A: {result['answer']}")
        logger.info(f"Confidence: {result['confidence']:.2f}")


if __name__ == "__main__":
    main()

