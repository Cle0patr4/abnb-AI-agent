#!/usr/bin/env python3
"""
Script para crear un nuevo índice de Pinecone con las dimensiones correctas
"""
import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

def create_pinecone_index():
    load_dotenv()
    
    api_key = os.environ.get("PINECONE_API_KEY")
    environment = os.environ.get("PINECONE_ENVIRONMENT")
    index_name = "abnb-agent-examples-v2"  # Nuevo nombre para evitar conflictos
    
    if not api_key:
        print("❌ PINECONE_API_KEY no encontrado en .env")
        return
    
    try:
        # Inicializar Pinecone
        pc = Pinecone(api_key=api_key)
        
        # Listar índices existentes
        print("📋 Índices existentes:")
        indexes = pc.list_indexes()
        for index in indexes:
            print(f"   • {index.name} (dimension: {index.dimension})")
        
        # Verificar si el índice ya existe
        if index_name in indexes.names():
            print(f"⚠️  El índice '{index_name}' ya existe")
            return
        
        # Crear nuevo índice
        print(f"\n🔨 Creando nuevo índice: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=1536,  # Dimensiones para text-embedding-ada-002
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'  # Región soportada en plan gratuito
            )
        )
        
        print(f"✅ Índice '{index_name}' creado exitosamente")
        print(f"📝 Actualiza tu .env con:")
        print(f"   PINECONE_INDEX_NAME={index_name}")
        
    except Exception as e:
        print(f"❌ Error creando índice: {e}")

if __name__ == "__main__":
    create_pinecone_index()
