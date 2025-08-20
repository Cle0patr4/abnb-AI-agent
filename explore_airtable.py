#!/usr/bin/env python3
"""
Script para explorar la estructura de las tablas de Airtable
"""
from dotenv import load_dotenv
load_dotenv()

from pyairtable import Base
import os

def explore_airtable():
    print("🔍 Explorando estructura de Airtable...")
    
    api_key = os.environ.get("AIRTABLE_API_KEY")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    
    base = Base(api_key, base_id)
    
    # Obtener todas las tablas
    print("\n📋 Tablas disponibles:")
    tables = base.tables()
    for table in tables:
        print(f"   - {table.name}")
    
    # Explorar cada tabla
    for table in tables:
        print(f"\n🔍 Explorando tabla: {table.name}")
        
        try:
            # Obtener algunos registros
            records = table.all(max_records=3)
            
            if records:
                print(f"   ✅ Encontrados {len(records)} registros")
                
                # Mostrar campos del primer registro
                first_record = records[0]
                fields = first_record.get('fields', {})
                
                print(f"   📝 Campos disponibles:")
                for field_name, field_value in fields.items():
                    field_type = type(field_value).__name__
                    if isinstance(field_value, str) and len(field_value) > 50:
                        field_value = field_value[:50] + "..."
                    print(f"      • {field_name} ({field_type}): {field_value}")
            else:
                print("   ⚠️  No se encontraron registros")
                
        except Exception as e:
            print(f"   ❌ Error accediendo a la tabla: {e}")

if __name__ == "__main__":
    explore_airtable()
