#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de feedback
"""
from database import db

def test_database():
    print("🧪 Probando sistema de feedback...")
    
    # Test 1: Log de conversación
    print("\n1. Probando log de conversación...")
    conv_id = db.log_conversation(
        user_id="test_user_123",
        query="¿Qué electrodomésticos tiene la cocina?",
        response="La cocina cuenta con nevera Samsung, horno LG y microondas.",
        response_time=2.5,
        used_rag=True,
        used_airtable=False
    )
    print(f"✅ Conversación registrada con ID: {conv_id}")
    
    # Test 2: Agregar feedback
    print("\n2. Probando agregar feedback...")
    feedback_id = db.add_feedback(
        user_id="test_user_123",
        original_query="¿Qué electrodomésticos tiene la cocina?",
        original_response="La cocina cuenta con nevera Samsung, horno LG y microondas.",
        feedback_type="positive",
        feedback_text="Excelente respuesta, muy clara",
        conversation_id=conv_id
    )
    print(f"✅ Feedback registrado con ID: {feedback_id}")
    
    # Test 3: Obtener última conversación
    print("\n3. Probando obtener última conversación...")
    last_conv = db.get_last_conversation("test_user_123")
    if last_conv:
        print(f"✅ Última conversación encontrada:")
        print(f"   Query: {last_conv['query']}")
        print(f"   Response: {last_conv['response']}")
    else:
        print("❌ No se encontró conversación")
    
    # Test 4: Estadísticas
    print("\n4. Probando estadísticas...")
    stats = db.get_feedback_stats()
    print(f"✅ Estadísticas obtenidas:")
    print(f"   Total conversaciones: {stats['total_conversations']}")
    print(f"   Conversaciones con feedback: {stats['conversations_with_feedback']}")
    print(f"   Tasa de feedback: {stats['feedback_rate']:.1f}%")
    print(f"   Tipos de feedback: {stats['feedback_types']}")
    
    # Test 5: Feedback no procesado
    print("\n5. Probando feedback no procesado...")
    unprocessed = db.get_unprocessed_feedback()
    print(f"✅ Feedback no procesado: {len(unprocessed)} elementos")
    for feedback in unprocessed:
        print(f"   - {feedback['feedback_type']}: {feedback['feedback_text']}")
    
    print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")

if __name__ == "__main__":
    test_database()
