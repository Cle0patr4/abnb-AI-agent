#!/usr/bin/env python3
"""
Módulo para manejar Pinecone con ejemplos de respuestas exitosas
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
            raise ValueError("PINECONE_API_KEY, PINECONE_ENVIRONMENT y PINECONE_INDEX_NAME deben estar configurados en .env")
        
        # Inicializar Pinecone (nueva API)
        self.pc = Pinecone(api_key=self.api_key)
        
        # Conectar al índice
        self.index = self.pc.Index(self.index_name)
        
        # Cliente OpenAI para embeddings
        self.openai_client = OpenAI()
        
        print(f"✅ Conectado a Pinecone index: {self.index_name}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Crear embedding de un texto usando OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",  # Usar modelo ada-002 para 1536 dimensiones
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creando embedding: {e}")
            return []
    
    def add_example(self, query: str, response: str, user_feedback: str = None, metadata: Dict = None) -> bool:
        """
        Agregar un ejemplo de respuesta exitosa a Pinecone
        
        Args:
            query: La pregunta original del usuario
            response: La respuesta que el usuario considera correcta
            user_feedback: Comentario adicional del usuario (opcional)
            metadata: Metadatos adicionales (opcional)
        """
        try:
            # Crear embedding del query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return False
            
            # Crear ID único
            example_id = f"example_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}"
            
            # Preparar metadatos
            example_metadata = {
                "query": query,
                "response": response,
                "user_feedback": user_feedback or "",
                "created_at": datetime.now().isoformat(),
                "type": "positive_example",
                "query_length": len(query),
                "response_length": len(response)
            }
            
            # Agregar metadatos adicionales si existen
            if metadata:
                example_metadata.update(metadata)
            
            # Insertar en Pinecone
            self.index.upsert(
                vectors=[{
                    "id": example_id,
                    "values": query_embedding,
                    "metadata": example_metadata
                }]
            )
            
            print(f"✅ Ejemplo agregado: {example_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error agregando ejemplo: {e}")
            return False
    
    def search_similar_examples(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Buscar ejemplos similares a una consulta
        
        Args:
            query: La consulta para buscar ejemplos similares
            top_k: Número máximo de ejemplos a retornar
        
        Returns:
            Lista de ejemplos similares con sus metadatos
        """
        try:
            # Crear embedding del query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Buscar en Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Procesar resultados
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
            print(f"❌ Error buscando ejemplos: {e}")
            return []
    
    def get_examples_for_context(self, query: str, top_k: int = 2) -> str:
        """
        Obtener ejemplos similares formateados para usar como contexto
        
        Args:
            query: La consulta actual
            top_k: Número de ejemplos a incluir
        
        Returns:
            String formateado con ejemplos para usar como contexto
        """
        examples = self.search_similar_examples(query, top_k)
        
        if not examples:
            return ""
        
        context = "\n\n📚 **Ejemplos de respuestas exitosas similares:**\n"
        
        for i, example in enumerate(examples, 1):
            context += f"\n**Ejemplo {i}** (similitud: {example['score']:.2f}):\n"
            context += f"**Pregunta:** {example['query']}\n"
            context += f"**Respuesta exitosa:** {example['response']}\n"
            
            if example['user_feedback']:
                context += f"**Feedback del usuario:** {example['user_feedback']}\n"
        
        return context
    
    def get_all_examples(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener todos los ejemplos almacenados (para debugging)"""
        try:
            # Buscar todos los vectores
            results = self.index.query(
                vector=[0] * 1536,  # Vector de ceros para buscar todo (1536 dimensiones)
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
            print(f"❌ Error obteniendo ejemplos: {e}")
            return []
    
    def delete_example(self, example_id: str) -> bool:
        """Eliminar un ejemplo específico"""
        try:
            self.index.delete(ids=[example_id])
            print(f"✅ Ejemplo eliminado: {example_id}")
            return True
        except Exception as e:
            print(f"❌ Error eliminando ejemplo: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del índice"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}

# Instancia global del manager de Pinecone
pinecone_manager = None

def get_pinecone_manager():
    global pinecone_manager
    if pinecone_manager is None:
        pinecone_manager = PineconeExamplesManager()
    return pinecone_manager
