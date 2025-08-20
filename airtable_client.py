#!/usr/bin/env python3
"""
Módulo para manejar la conexión y consultas a Airtable
"""
import os
from pyairtable import Api, Base, Table
from typing import List, Dict, Any, Optional
import re

class AirtableClient:
    def __init__(self):
        self.api_key = os.environ.get("AIRTABLE_API_KEY")
        self.base_id = os.environ.get("AIRTABLE_BASE_ID")
        
        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY y AIRTABLE_BASE_ID deben estar configurados en .env")
        
        self.api = Api(self.api_key)
        self.base = Base(self.api_key, self.base_id)
        
        # Nombres de las tablas
        self.items_table = "Items per property"
        self.houses_table = "Houses Organization"
        
        # Cache para mejorar rendimiento
        self._cache = {}
        self._cache_timeout = 300  # 5 minutos
    
    def get_table(self, table_name: str) -> Table:
        """Obtener una tabla específica"""
        return self.base.table(table_name)
    
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Buscar items en la tabla 'Items per property'
        """
        try:
            table = self.get_table(self.items_table)
            
            # Obtener todos los registros
            records = table.all()
            
            # Filtrar basado en la consulta
            query_lower = query.lower()
            matching_records = []
            
            for record in records:
                fields = record.get('fields', {})
                
                # Buscar en campos específicos basados en la estructura real
                searchable_text = ""
                
                # Campo Code (descripción del item)
                code = fields.get('Code', '')
                if isinstance(code, str):
                    searchable_text += f" {code.lower()}"
                
                # Campo Make (Brand) - marca
                make = fields.get('Make (Brand)', '')
                if isinstance(make, str):
                    searchable_text += f" {make.lower()}"
                
                # Campo Model - modelo
                model = fields.get('Model', '')
                if isinstance(model, str):
                    searchable_text += f" {model.lower()}"
                
                # Campo Category - categoría
                category = fields.get('Category', [])
                if isinstance(category, list):
                    searchable_text += f" {' '.join(str(cat).lower() for cat in category)}"
                
                # Campo Level of the house - nivel
                level = fields.get('Level of the house', [])
                if isinstance(level, list):
                    searchable_text += f" {' '.join(str(lvl).lower() for lvl in level)}"
                
                # Verificar si la consulta coincide (búsqueda más flexible)
                query_words = query_lower.split()
                matches = 0
                
                for word in query_words:
                    if len(word) > 2 and word in searchable_text:  # Solo palabras de más de 2 caracteres
                        matches += 1
                
                # Si al menos una palabra coincide, incluir el registro
                if matches > 0:
                    matching_records.append({
                        'id': record['id'],
                        'fields': fields,
                        'match_score': matches
                    })
            
            return matching_records
            
        except Exception as e:
            print(f"❌ Error buscando items en Airtable: {e}")
            return []
    
    def search_houses(self, query: str) -> List[Dict[str, Any]]:
        """
        Buscar información de organización de casas
        """
        try:
            table = self.get_table(self.houses_table)
            
            # Obtener todos los registros
            records = table.all()
            
            # Filtrar basado en la consulta
            query_lower = query.lower()
            matching_records = []
            
            for record in records:
                fields = record.get('fields', {})
                
                # Buscar en campos específicos basados en la estructura real
                searchable_text = ""
                
                # Campo Cod (descripción del espacio)
                cod = fields.get('Cod', '')
                if isinstance(cod, str):
                    searchable_text += f" {cod.lower()}"
                
                # Campo Space (referencias a espacios)
                space = fields.get('Space', [])
                if isinstance(space, list):
                    searchable_text += f" {' '.join(str(sp).lower() for sp in space)}"
                
                # Campo Properties (referencias a propiedades)
                properties = fields.get('Properties', [])
                if isinstance(properties, list):
                    searchable_text += f" {' '.join(str(prop).lower() for prop in properties)}"
                
                # Verificar si la consulta coincide (búsqueda más flexible)
                query_words = query_lower.split()
                matches = 0
                
                for word in query_words:
                    if len(word) > 2 and word in searchable_text:  # Solo palabras de más de 2 caracteres
                        matches += 1
                
                # Si al menos una palabra coincide, incluir el registro
                if matches > 0:
                    matching_records.append({
                        'id': record['id'],
                        'fields': fields,
                        'match_score': matches
                    })
            
            return matching_records
            
        except Exception as e:
            print(f"❌ Error buscando houses en Airtable: {e}")
            return []
    
    def get_property_info(self, property_name: str = None) -> Dict[str, Any]:
        """
        Obtener información completa de una propiedad
        """
        try:
            # Buscar en ambas tablas
            items = self.search_items(property_name or "")
            houses = self.search_houses(property_name or "")
            
            return {
                'items': items,
                'houses': houses,
                'property_name': property_name
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo información de propiedad: {e}")
            return {'items': [], 'houses': [], 'property_name': property_name}
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analizar una consulta para determinar qué tipo de información buscar
        """
        query_lower = query.lower()
        
        # Patrones para identificar tipos de consultas
        patterns = {
            'electrodomesticos': [
                r'electrodomésticos?', r'nevera', r'refrigerador', r'horno', 
                r'microondas', r'lavadora', r'secadora', r'cafetera', r'tostadora'
            ],
            'habitaciones': [
                r'habitaciones?', r'cuartos?', r'dormitorios?', r'baños?', 
                r'cocina', r'sala', r'comedor', r'terraza', r'balcón'
            ],
            'amenidades': [
                r'piscina', r'jacuzzi', r'hot tub', r'gimnasio', r'wifi', 
                r'aire acondicionado', r'calefacción', r'tv', r'televisión'
            ],
            'ubicacion': [
                r'piso', r'nivel', r'planta', r'ubicación', r'localización',
                r'primer', r'segundo', r'tercer', r'cuarto'
            ]
        }
        
        # Determinar qué tipo de información buscar
        query_type = 'general'
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, query_lower):
                    query_type = category
                    break
            if query_type != 'general':
                break
        
        return {
            'query_type': query_type,
            'original_query': query,
            'should_use_airtable': query_type != 'general'
        }
    
    def format_response(self, data: Dict[str, Any], query: str) -> str:
        """
        Formatear la respuesta basada en los datos de Airtable
        """
        items = data.get('items', [])
        houses = data.get('houses', [])
        
        if not items and not houses:
            return "No encontré información específica sobre eso en mi base de datos."
        
        response_parts = []
        
        # Formatear items
        if items:
            response_parts.append("📦 **Items encontrados:**")
            for item in items[:5]:  # Limitar a 5 items
                fields = item.get('fields', {})
                
                # Campos reales de la tabla Items per property
                code = fields.get('Code', 'Sin descripción')
                make = fields.get('Make (Brand)', '')
                model = fields.get('Model', '')
                category = fields.get('Category', [])
                level = fields.get('Level of the house', [])
                status = fields.get('Status', '')
                
                item_text = f"• **{code}**"
                if make:
                    item_text += f" (Marca: {make})"
                if model:
                    item_text += f" (Modelo: {model})"
                if category:
                    item_text += f" (Categoría: {', '.join(category)})"
                if level:
                    item_text += f" (Nivel: {', '.join(level)})"
                if status:
                    item_text += f" (Estado: {status})"
                
                response_parts.append(item_text)
        
        # Formatear información de organización
        if houses:
            response_parts.append("\n🏠 **Organización de la casa:**")
            for house in houses[:3]:  # Limitar a 3 registros
                fields = house.get('fields', {})
                
                # Campos reales de la tabla Houses Organization
                cod = fields.get('Cod', 'Sin especificar')
                space = fields.get('Space', [])
                properties = fields.get('Properties', [])
                
                house_text = f"• **{cod}**"
                if space:
                    house_text += f" (Espacios: {len(space)} referencias)"
                if properties:
                    house_text += f" (Propiedades: {len(properties)} referencias)"
                
                response_parts.append(house_text)
        
        return "\n".join(response_parts)
    
    def test_connection(self) -> bool:
        """
        Probar la conexión con Airtable
        """
        try:
            # Intentar obtener un registro de cada tabla
            items_table = self.get_table(self.items_table)
            houses_table = self.get_table(self.houses_table)
            
            # Obtener un registro de prueba
            items_table.all(max_records=1)
            houses_table.all(max_records=1)
            
            print("✅ Conexión con Airtable exitosa")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando con Airtable: {e}")
            return False

# Instancia global del cliente de Airtable (se inicializará cuando se necesite)
airtable_client = None

def get_airtable_client():
    global airtable_client
    if airtable_client is None:
        airtable_client = AirtableClient()
    return airtable_client
