#!/usr/bin/env python3
"""
Script to check Pinecone examples
"""
import os
from pinecone_client import get_pinecone_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_examples():
    """Check all examples stored in Pinecone"""
    try:
        print("🔍 Checking Pinecone examples...")
        
        pinecone_manager = get_pinecone_manager()
        examples = pinecone_manager.get_all_examples(limit=20)
        
        print(f"\n📚 Found {len(examples)} examples:")
        print("=" * 80)
        
        for i, example in enumerate(examples, 1):
            print(f"\n**Example {i}** (ID: {example['id']})")
            print(f"Question: {example['query']}")
            print(f"Response: {example['response']}")
            print(f"User feedback: {example['user_feedback']}")
            print(f"Created: {example['created_at']}")
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error checking examples: {e}")

if __name__ == "__main__":
    check_examples()
