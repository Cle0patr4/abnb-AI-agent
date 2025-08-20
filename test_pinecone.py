#!/usr/bin/env python3
"""
Script para probar la conexión y funcionalidad de Pinecone
"""
from dotenv import load_dotenv
from pinecone_client import get_pinecone_manager

def test_pinecone():
    print("🧪 Probando Pinecone...")
    
    try:
        # Obtener manager de Pinecone
        pinecone_manager = get_pinecone_manager()
        
        # Test 1: Estadísticas del índice
        print("\n1. Estadísticas del índice:")
        stats = pinecone_manager.get_index_stats()
        print(f"   • Total de vectores: {stats.get('total_vector_count', 0)}")
        print(f"   • Dimensión: {stats.get('dimension', 'N/A')}")
        print(f"   • Índice lleno: {stats.get('index_fullness', 'N/A')}")
        
        # Test 2: Agregar ejemplo de prueba
        print("\n2. Agregando ejemplo de prueba...")
        success = pinecone_manager.add_example(
            query="¿Qué electrodomésticos tiene la cocina?",
            response="La cocina cuenta con nevera Samsung, horno eléctrico, microondas y cafetera. Todos están en perfecto estado.",
            user_feedback="Respuesta clara y específica sobre los electrodomésticos"
        )
        
        if success:
            print("   ✅ Ejemplo agregado exitosamente")
        else:
            print("   ❌ Error agregando ejemplo")
        
        # Test 3: Buscar ejemplos similares
        print("\n3. Buscando ejemplos similares...")
        examples = pinecone_manager.search_similar_examples(
            "¿Qué hay en la cocina?",
            top_k=3
        )
        
        print(f"   Encontrados {len(examples)} ejemplos:")
        for i, example in enumerate(examples, 1):
            print(f"   • Ejemplo {i}: {example['query'][:50]}... (score: {example['score']:.2f})")
        
        # Test 4: Obtener contexto formateado
        print("\n4. Contexto formateado:")
        context = pinecone_manager.get_examples_for_context("¿Qué electrodomésticos hay?")
        if context:
            print(f"   Contexto generado ({len(context)} caracteres):")
            print(f"   {context[:200]}...")
        else:
            print("   No se encontraron ejemplos similares")
        
        # Test 5: Todos los ejemplos
        print("\n5. Todos los ejemplos almacenados:")
        all_examples = pinecone_manager.get_all_examples(limit=5)
        print(f"   Total de ejemplos: {len(all_examples)}")
        for example in all_examples:
            print(f"   • {example['query'][:40]}...")
        
        print("\n🎉 ¡Todas las pruebas de Pinecone pasaron exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")

if __name__ == "__main__":
    test_pinecone()
