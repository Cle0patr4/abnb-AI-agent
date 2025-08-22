#!/usr/bin/env python3
"""
Script to clean Pinecone examples and add relevant English examples
"""
import os
from pinecone_client import get_pinecone_manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clean_and_add_examples():
    """Clean existing examples and add relevant English examples"""
    try:
        print("🧹 Cleaning and adding examples...")
        
        pinecone_manager = get_pinecone_manager()
        
        # Get all existing examples
        examples = pinecone_manager.get_all_examples(limit=20)
        
        # Delete all existing examples
        print(f"🗑️ Deleting {len(examples)} existing examples...")
        for example in examples:
            pinecone_manager.delete_example(example['id'])
        
        # Add relevant English examples
        print("➕ Adding relevant English examples...")
        
        # Example 1: Bathroom question
        success1 = pinecone_manager.add_example(
            query="Hello. Your listing says 3.5 baths but I only saw 2 full baths pictured. Did I miss it?",
            response="You're absolutely right to double-check! The property actually has 3 full bathrooms plus a half bath (powder room). The third full bathroom is located on the second floor and might not be as prominently featured in the photos. All bathrooms are fully equipped and ready for your stay.",
            user_feedback="Clear explanation of bathroom count and location"
        )
        
        # Example 2: General inquiry
        success2 = pinecone_manager.add_example(
            query="Hi, I'm interested in booking your property for next month. What's the check-in process like?",
            response="Great choice! Check-in is super easy - you'll receive detailed instructions and access codes 24 hours before arrival. We offer self check-in starting at 3 PM, and I'm always available if you need anything during your stay.",
            user_feedback="Friendly, informative response about check-in process"
        )
        
        # Example 3: Amenity question
        success3 = pinecone_manager.add_example(
            query="Do you have a coffee maker in the kitchen?",
            response="Yes! The kitchen is fully equipped with a Keurig coffee maker, plus we provide coffee pods to get you started. There's also a traditional coffee pot if you prefer ground coffee.",
            user_feedback="Specific answer about coffee maker and coffee provided"
        )
        
        # Example 4: Location question
        success4 = pinecone_manager.add_example(
            query="How far is the property from downtown?",
            response="We're just a 10-minute drive from downtown, or about 15 minutes by public transit. The location is perfect for exploring the city while still being in a quiet, residential area.",
            user_feedback="Clear distance information with multiple transport options"
        )
        
        print(f"✅ Added examples: {success1}, {success2}, {success3}, {success4}")
        
        # Verify new examples
        new_examples = pinecone_manager.get_all_examples(limit=10)
        print(f"\n📚 Now have {len(new_examples)} examples in English")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_and_add_examples()
