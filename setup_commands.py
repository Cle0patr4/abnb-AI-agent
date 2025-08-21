#!/usr/bin/env python3
"""
Script to configure bot commands with BotFather
"""
import requests
from dotenv import load_dotenv
import os

def setup_bot_commands():
    load_dotenv()
    
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found in .env")
        return
    
    # URL to configure commands
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    
    # Commands we want to configure
    commands = [
        {
            "command": "start",
            "description": "Start the bot and see help"
        },
        {
            "command": "feedback",
            "description": "Give feedback on the last response"
        },
        {
            "command": "stats",
            "description": "View bot usage statistics"
        },
        {
            "command": "help",
            "description": "Show help and available commands"
        }
    ]
    
    # Data to send
    data = {
        "commands": commands
    }
    
    try:
        print("🤖 Configuring bot commands...")
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Commands configured successfully!")
                print("📱 Now when you type '/' in Telegram you should see:")
                for cmd in commands:
                    print(f"   • /{cmd['command']} - {cmd['description']}")
            else:
                print(f"❌ Error: {result.get('description', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error configuring commands: {e}")

def get_bot_info():
    load_dotenv()
    
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found in .env")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                print("🤖 Bot information:")
                print(f"   • Name: {bot_info.get('first_name', 'N/A')}")
                print(f"   • Username: @{bot_info.get('username', 'N/A')}")
                print(f"   • ID: {bot_info.get('id', 'N/A')}")
            else:
                print(f"❌ Error: {result.get('description', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting bot information: {e}")

if __name__ == "__main__":
    print("🔧 Configuring Telegram bot...")
    print()
    
    # Get bot information
    get_bot_info()
    print()
    
    # Configure commands
    setup_bot_commands()
