#!/usr/bin/env python3
"""
Module to handle Airtable connection and queries
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
            raise ValueError("AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be configured in .env")
        
        self.api = Api(self.api_key)
        self.base = Base(self.api_key, self.base_id)
        
        # Table names
        self.items_table = "Items per property"
        self.houses_table = "Houses Organization"
        
        # Cache to improve performance
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    def get_table(self, table_name: str) -> Table:
        """Get a specific table"""
        return self.base.table(table_name)
    
    def search_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Search items in the 'Items per property' table
        """
        try:
            table = self.get_table(self.items_table)
            
            # Get all records
            records = table.all()
            
            # Filter based on query
            query_lower = query.lower()
            matching_records = []
            
            for record in records:
                fields = record.get('fields', {})
                
                # Search in specific fields based on actual structure
                searchable_text = ""
                
                # Code field (item description)
                code = fields.get('Code', '')
                if isinstance(code, str):
                    searchable_text += f" {code.lower()}"
                
                # Make (Brand) field - brand
                make = fields.get('Make (Brand)', '')
                if isinstance(make, str):
                    searchable_text += f" {make.lower()}"
                
                # Model field - model
                model = fields.get('Model', '')
                if isinstance(model, str):
                    searchable_text += f" {model.lower()}"
                
                # Category field - category
                category = fields.get('Category', [])
                if isinstance(category, list):
                    searchable_text += f" {' '.join(str(cat).lower() for cat in category)}"
                
                # Level of the house field - level
                level = fields.get('Level of the house', [])
                if isinstance(level, list):
                    searchable_text += f" {' '.join(str(lvl).lower() for lvl in level)}"
                
                # Check if query matches (more flexible search)
                query_words = query_lower.split()
                matches = 0
                
                for word in query_words:
                    if len(word) > 2 and word in searchable_text:  # Only words longer than 2 characters
                        matches += 1
                
                # If at least one word matches, include the record
                if matches > 0:
                    matching_records.append({
                        'id': record['id'],
                        'fields': fields,
                        'match_score': matches
                    })
            
            return matching_records
            
        except Exception as e:
            print(f"❌ Error searching items in Airtable: {e}")
            return []
    
    def search_houses(self, query: str) -> List[Dict[str, Any]]:
        """
        Search house organization information
        """
        try:
            table = self.get_table(self.houses_table)
            
            # Get all records
            records = table.all()
            
            # Filter based on query
            query_lower = query.lower()
            matching_records = []
            
            for record in records:
                fields = record.get('fields', {})
                
                # Search in specific fields based on actual structure
                searchable_text = ""
                
                # Cod field (space description)
                cod = fields.get('Cod', '')
                if isinstance(cod, str):
                    searchable_text += f" {cod.lower()}"
                
                # Space field (space references)
                space = fields.get('Space', [])
                if isinstance(space, list):
                    searchable_text += f" {' '.join(str(sp).lower() for sp in space)}"
                
                # Properties field (property references)
                properties = fields.get('Properties', [])
                if isinstance(properties, list):
                    searchable_text += f" {' '.join(str(prop).lower() for prop in properties)}"
                
                # Check if query matches (more flexible search)
                query_words = query_lower.split()
                matches = 0
                
                for word in query_words:
                    if len(word) > 2 and word in searchable_text:  # Only words longer than 2 characters
                        matches += 1
                
                # If at least one word matches, include the record
                if matches > 0:
                    matching_records.append({
                        'id': record['id'],
                        'fields': fields,
                        'match_score': matches
                    })
            
            return matching_records
            
        except Exception as e:
            print(f"❌ Error searching houses in Airtable: {e}")
            return []
    
    def get_property_info(self, property_name: str = None) -> Dict[str, Any]:
        """
        Get complete property information
        """
        try:
            # Search in both tables
            items = self.search_items(property_name or "")
            houses = self.search_houses(property_name or "")
            
            return {
                'items': items,
                'houses': houses,
                'property_name': property_name
            }
            
        except Exception as e:
            print(f"❌ Error getting property information: {e}")
            return {'items': [], 'houses': [], 'property_name': property_name}
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to determine what type of information to search for
        """
        query_lower = query.lower()
        
        # Patterns to identify query types
        patterns = {
            'appliances': [
                r'appliances?', r'refrigerator', r'fridge', r'oven', 
                r'microwave', r'washer', r'dryer', r'coffee maker', r'toaster'
            ],
            'rooms': [
                r'rooms?', r'bedrooms?', r'bathrooms?', r'kitchen', 
                r'living room', r'dining room', r'terrace', r'balcony'
            ],
            'amenities': [
                r'pool', r'jacuzzi', r'hot tub', r'gym', r'wifi', 
                r'air conditioning', r'heating', r'tv', r'television'
            ],
            'location': [
                r'floor', r'level', r'story', r'location',
                r'first', r'second', r'third', r'fourth'
            ]
        }
        
        # Determine what type of information to search for
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
        Format response based on Airtable data
        """
        items = data.get('items', [])
        houses = data.get('houses', [])
        
        if not items and not houses:
            return "I didn't find specific information about that in my database."
        
        response_parts = []
        
        # Format items
        if items:
            response_parts.append("📦 **Items found:**")
            for item in items[:5]:  # Limit to 5 items
                fields = item.get('fields', {})
                
                # Real fields from Items per property table
                code = fields.get('Code', 'No description')
                make = fields.get('Make (Brand)', '')
                model = fields.get('Model', '')
                category = fields.get('Category', [])
                level = fields.get('Level of the house', [])
                status = fields.get('Status', '')
                
                item_text = f"• **{code}**"
                if make:
                    item_text += f" (Brand: {make})"
                if model:
                    item_text += f" (Model: {model})"
                if category:
                    item_text += f" (Category: {', '.join(category)})"
                if level:
                    item_text += f" (Level: {', '.join(level)})"
                if status:
                    item_text += f" (Status: {status})"
                
                response_parts.append(item_text)
        
        # Format organization information
        if houses:
            response_parts.append("\n🏠 **House organization:**")
            for house in houses[:3]:  # Limit to 3 records
                fields = house.get('fields', {})
                
                # Real fields from Houses Organization table
                cod = fields.get('Cod', 'Not specified')
                space = fields.get('Space', [])
                properties = fields.get('Properties', [])
                
                house_text = f"• **{cod}**"
                if space:
                    house_text += f" (Spaces: {len(space)} references)"
                if properties:
                    house_text += f" (Properties: {len(properties)} references)"
                
                response_parts.append(house_text)
        
        return "\n".join(response_parts)
    
    def test_connection(self) -> bool:
        """
        Test Airtable connection
        """
        try:
            # Try to get a record from each table
            items_table = self.get_table(self.items_table)
            houses_table = self.get_table(self.houses_table)
            
            # Get a test record
            items_table.all(max_records=1)
            houses_table.all(max_records=1)
            
            print("✅ Airtable connection successful")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Airtable: {e}")
            return False

# Global Airtable client instance (will be initialized when needed)
airtable_client = None

def get_airtable_client():
    global airtable_client
    if airtable_client is None:
        airtable_client = AirtableClient()
    return airtable_client
