#!/usr/bin/env python3
"""
Module to handle Pinecone with successful response examples
"""
import os
from pinecone import Pinecone
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class PineconeExamplesManager:
    def __init__(self):
        self.api_key = os.environ.get("PINECONE_API_KEY")
        self.environment = os.environ.get("PINECONE_ENVIRONMENT")
        self.index_name = os.environ.get("PINECONE_INDEX_NAME")
        
        if not all([self.api_key, self.environment, self.index_name]):
            raise ValueError("PINECONE_API_KEY, PINECONE_ENVIRONMENT and PINECONE_INDEX_NAME must be configured in .env")
        
        # Initialize Pinecone (new API)
        self.pc = Pinecone(api_key=self.api_key)
        
        # Connect to index
        self.index = self.pc.Index(self.index_name)
        
        # OpenAI client for embeddings
        self.openai_client = OpenAI()
        
        print(f"✅ Connected to Pinecone index: {self.index_name}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding of text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",  # Use ada-002 model for 1536 dimensions
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            return []
    
    def add_example(self, query: str, response: str, user_feedback: str = None, metadata: Dict = None) -> bool:
        """
        Add a successful response example to Pinecone
        
        Args:
            query: The user's original question
            response: The response the user considers correct
            user_feedback: Additional user comment (optional)
            metadata: Additional metadata (optional)
        """
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return False
            
            # Create unique ID
            example_id = f"example_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"
            
            # Prepare metadata
            example_metadata = {
                "query": query,
                "response": response,
                "user_feedback": user_feedback or "",
                "created_at": datetime.now().isoformat(),
                "type": "positive_example",
                "query_length": len(query),
                "response_length": len(response)
            }
            
            # Add additional metadata if exists
            if metadata:
                example_metadata.update(metadata)
            
            # Insert into Pinecone
            self.index.upsert(
                vectors=[{
                    "id": example_id,
                    "values": query_embedding,
                    "metadata": example_metadata
                }]
            )
            
            print(f"✅ Example added: {example_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding example: {e}")
            return False
    
    def search_similar_examples(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for examples similar to a query
        
        Args:
            query: The query to search for similar examples
            top_k: Maximum number of examples to return
        
        Returns:
            List of similar examples with their metadata
        """
        try:
            # Create query embedding
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Search in Pinecone with more results to allow for reordering
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k * 2,  # Get more results to allow for reordering
                include_metadata=True
            )
            
            # Process results and add recency boost
            examples = []
            for match in results.matches:
                if match.metadata:
                    created_at = match.metadata.get("created_at", "")
                    
                    # Calculate recency boost (newer examples get higher priority)
                    recency_boost = 0.0
                    if created_at:
                        try:
                            from datetime import datetime
                            created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            now = datetime.now(created_time.tzinfo)
                            hours_old = (now - created_time).total_seconds() / 3600
                            # Boost newer examples (within last 24 hours get +0.1, older get +0.05)
                            recency_boost = 0.1 if hours_old < 24 else 0.05
                        except:
                            recency_boost = 0.05
                    
                    # Adjust score with recency boost
                    adjusted_score = match.score + recency_boost
                    
                    examples.append({
                        "id": match.id,
                        "score": adjusted_score,
                        "original_score": match.score,
                        "recency_boost": recency_boost,
                        "query": match.metadata.get("query", ""),
                        "response": match.metadata.get("response", ""),
                        "user_feedback": match.metadata.get("user_feedback", ""),
                        "created_at": created_at
                    })
            
            # Sort by adjusted score (highest first) and return top_k
            examples.sort(key=lambda x: x['score'], reverse=True)
            return examples[:top_k]
            
        except Exception as e:
            print(f"❌ Error searching examples: {e}")
            return []
    
    def get_examples_for_context(self, query: str, top_k: int = 2) -> str:
        """
        Get similar examples formatted for use as context
        
        Args:
            query: The current query
            top_k: Number of examples to include
        
        Returns:
            Formatted string with examples to use as context
        """
        examples = self.search_similar_examples(query, top_k)
        
        if not examples:
            return ""
        
        context = "\n\n📚 **Similar successful response examples:**\n"
        
        for i, example in enumerate(examples, 1):
            # Add recency indicator
            recency_indicator = "🆕" if example.get('recency_boost', 0) >= 0.1 else "📝"
            context += f"\n{recency_indicator} **Example {i}** (similarity: {example['score']:.2f}):\n"
            context += f"**Question:** {example['query']}\n"
            context += f"**Successful response:** {example['response']}\n"
            
            if example['user_feedback']:
                context += f"**User feedback:** {example['user_feedback']}\n"
        
        return context
    
    def get_all_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all stored examples (for debugging)"""
        try:
            # Search all vectors
            results = self.index.query(
                vector=[0] * 1536,  # Zero vector to search everything (1536 dimensions)
                top_k=limit,
                include_metadata=True
            )
            
            examples = []
            for match in results.matches:
                if match.metadata:
                    examples.append({
                        "id": match.id,
                        "score": match.score,
                        "query": match.metadata.get("query", ""),
                        "response": match.metadata.get("response", ""),
                        "user_feedback": match.metadata.get("user_feedback", ""),
                        "created_at": match.metadata.get("created_at", "")
                    })
            
            return examples
            
        except Exception as e:
            print(f"❌ Error getting examples: {e}")
            return []
    
    def delete_example(self, example_id: str) -> bool:
        """Delete a specific example"""
        try:
            self.index.delete(ids=[example_id])
            print(f"✅ Example deleted: {example_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting example: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}

# Global Pinecone manager instance
pinecone_manager = None

def get_pinecone_manager():
    global pinecone_manager
    if pinecone_manager is None:
        pinecone_manager = PineconeExamplesManager()
    return pinecone_manager
