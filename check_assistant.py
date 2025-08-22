#!/usr/bin/env python3
"""
Script to check OpenAI Assistant configuration
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_KEY = os.environ["OPENAI_API_KEY"]
ASSISTANT_ID = os.environ["ASSISTANT_ID"]

client = OpenAI()

def check_assistant():
    """Check the OpenAI Assistant configuration"""
    try:
        print("🔍 Checking OpenAI Assistant configuration...")
        print(f"🧠 Assistant ID: {ASSISTANT_ID}")
        
        # Get assistant details
        assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
        
        print("\n📋 Assistant Details:")
        print(f"   • Name: {assistant.name}")
        print(f"   • Model: {assistant.model}")
        print(f"   • Created: {assistant.created_at}")
        
        print("\n📝 Instructions/Prompt:")
        print("=" * 50)
        print(assistant.instructions)
        print("=" * 50)
        
        print(f"\n📁 Files attached: {len(assistant.file_ids)}")
        if assistant.file_ids:
            for file_id in assistant.file_ids:
                print(f"   • {file_id}")
        
        print(f"\n🛠️ Tools: {len(assistant.tools)}")
        for tool in assistant.tools:
            print(f"   • {tool.type}")
        
    except Exception as e:
        print(f"❌ Error checking assistant: {e}")

if __name__ == "__main__":
    check_assistant()
