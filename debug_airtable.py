#!/usr/bin/env python3
"""
Script para debuggear la búsqueda en Airtable
"""
from dotenv import load_dotenv
load_dotenv()

from pyairtable import Base
import os

def debug_airtable():
    print("🔍 Debuggeando búsqueda en Airtable...")
    
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    
    base = Base(api_key, base_id)
    
    # Tabla Items per property
    print("\n📦 Tabla 'Items per property':")
    items_table = base.table("Items per property")
    items_records = items_table.all()
    
    print(f"   Total registros: {len(items_records)}")
    
    for i, record in enumerate(items_records[:3]):  # Solo los primeros 3
        fields = record.get('fields', {})
        print(f"\n   Registro {i+1}:")
        print(f"   ID: {record['id']}")
        
        # Mostrar todos los campos
        for field_name, field_value in fields.items():
            if isinstance(field_value, str) and len(field_value) > 100:
                field_value = field_value[:100] + "..."
            print(f"   • {field_name}: {field_value}")
    
    # Tabla Houses Organization
    print("\n🏠 Tabla 'Houses Organization':")
    houses_table = base.table("Houses Organization")
    houses_records = houses_table.all()
    
    print(f"   Total registros: {len(houses_records)}")
    
    for i, record in enumerate(houses_records[:3]):  # Solo los primeros 3
        fields = record.get('fields', {})
        print(f"\n   Registro {i+1}:")
        print(f"   ID: {record['id']}")
        
        # Mostrar todos los campos
        for field_name, field_value in fields.items():
            if isinstance(field_value, str) and len(field_value) > 100:
                field_value = field_value[:100] + "..."
            print(f"   • {field_name}: {field_value}")
    
    # Probar búsqueda específica
    print("\n🔍 Probando búsquedas específicas:")
    
    # Buscar "mitsubishi" en items
    print("\n   Buscando 'mitsubishi' en items:")
    for record in items_records:
        fields = record.get('fields', {})
        code = fields.get('Code', '').lower()
        make = fields.get('Make (Brand)', '').lower()
        
        if 'mitsubishi' in code or 'mitsubishi' in make:
            print(f"   ✅ Encontrado: {fields.get('Code', 'Sin código')} - {fields.get('Make (Brand)', 'Sin marca')}")
    
    # Buscar "basement" en items
    print("\n   Buscando 'basement' en items:")
    for record in items_records:
        fields = record.get('fields', {})
        level = fields.get('Level of the house', [])
        
        if isinstance(level, list) and any('basement' in str(lvl).lower() for lvl in level):
            print(f"   ✅ Encontrado: {fields.get('Code', 'Sin código')} - Nivel: {level}")

if __name__ == "__main__":
    debug_airtable()
