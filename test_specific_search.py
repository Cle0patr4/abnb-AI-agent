#!/usr/bin/env python3
"""
Script para probar búsquedas específicas en Airtable
"""
from dotenv import load_dotenv
load_dotenv()

from airtable_client import airtable_client

def test_specific_search():
    print("🔍 Probando búsquedas específicas...")
    
    # Test 1: Búsqueda de "cocina"
    print("\n1. Buscando 'cocina':")
    items = airtable_client.search_items("cocina")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:
        fields = item.get('fields', {})
        code = fields.get('Code', 'Sin código')
        print(f"   - {code}")
    
    # Test 2: Búsqueda de "basement"
    print("\n2. Buscando 'basement':")
    items = airtable_client.search_items("basement")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:
        fields = item.get('fields', {})
        code = fields.get('Code', 'Sin código')
        print(f"   - {code}")
    
    # Test 3: Búsqueda de "tv"
    print("\n3. Buscando 'tv':")
    items = airtable_client.search_items("tv")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:
        fields = item.get('fields', {})
        code = fields.get('Code', 'Sin código')
        print(f"   - {code}")
    
    # Test 4: Búsqueda de "stony"
    print("\n4. Buscando 'stony':")
    items = airtable_client.search_items("stony")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:
        fields = item.get('fields', {})
        code = fields.get('Code', 'Sin código')
        print(f"   - {code}")
    
    # Test 5: Búsqueda de "mitsubishi"
    print("\n5. Buscando 'mitsubishi':")
    items = airtable_client.search_items("mitsubishi")
    print(f"   Items encontrados: {len(items)}")
    for item in items[:3]:
        fields = item.get('fields', {})
        code = fields.get('Code', 'Sin código')
        print(f"   - {code}")

if __name__ == "__main__":
    test_specific_search()
