#!/usr/bin/env python3
"""
Script de prueba para verificar la conexión con Airtable
"""
from dotenv import load_dotenv
load_dotenv()  # Cargar variables antes de importar

from airtable_client import airtable_client

def test_airtable_connection():
    print("🧪 Probando conexión con Airtable...")
    
    # Test 1: Conexión básica
    print("\n1. Probando conexión básica...")
    if airtable_client.test_connection():
        print("✅ Conexión exitosa")
    else:
        print("❌ Error en la conexión")
        return
    
    # Test 2: Análisis de consultas
    print("\n2. Probando análisis de consultas...")
    test_queries = [
        "¿Qué electrodomésticos tiene la cocina?",
        "¿Cuántas habitaciones tiene la casa?",
        "¿Dónde está la piscina?",
        "¿Qué hay en el primer piso?",
        "Hola, ¿cómo estás?"
    ]
    
    for query in test_queries:
        analysis = airtable_client.analyze_query(query)
        print(f"   '{query}' → {analysis['query_type']} (usar Airtable: {analysis['should_use_airtable']})")
    
    # Test 3: Búsqueda de items
    print("\n3. Probando búsqueda de items...")
    items = airtable_client.search_items("cocina")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:  # Mostrar solo los primeros 3
        fields = item.get('fields', {})
        name = fields.get('Name', fields.get('Item', 'Sin nombre'))
        print(f"   - {name}")
    
    # Test 4: Búsqueda de houses
    print("\n4. Probando búsqueda de houses...")
    houses = airtable_client.search_houses("habitación")
    print(f"   Houses encontrados: {len(houses)}")
    for house in houses[:3]:  # Mostrar solo los primeros 3
        fields = house.get('fields', {})
        room = fields.get('Room', fields.get('Habitación', 'Sin especificar'))
        print(f"   - {room}")
    
    # Test 5: Información completa de propiedad
    print("\n5. Probando información completa...")
    property_info = airtable_client.get_property_info("casa")
    print(f"   Items: {len(property_info['items'])}")
    print(f"   Houses: {len(property_info['houses'])}")
    
    # Test 6: Formateo de respuesta
    print("\n6. Probando formateo de respuesta...")
    response = airtable_client.format_response(property_info, "¿Qué tiene la casa?")
    print("   Respuesta formateada:")
    print(f"   {response[:200]}...")  # Mostrar solo los primeros 200 caracteres
    
    print("\n🎉 ¡Todas las pruebas de Airtable pasaron exitosamente!")

if __name__ == "__main__":
    load_dotenv()
    test_airtable_connection()
