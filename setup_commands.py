#!/usr/bin/env python3
"""
Script para configurar los comandos del bot con BotFather
"""
import requests
from dotenv import load_dotenv
import os

def setup_bot_commands():
    load_dotenv()
    
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN no encontrado en .env")
        return
    
    # URL para configurar comandos
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands"
    
    # Comandos que queremos configurar
    commands = [
        {
            "command": "start",
            "description": "Iniciar el bot y ver ayuda"
        },
        {
            "command": "feedback",
            "description": "Dar feedback sobre la última respuesta"
        },
        {
            "command": "estadisticas",
            "description": "Ver estadísticas de uso del bot"
        },
        {
            "command": "ayuda",
            "description": "Mostrar ayuda y comandos disponibles"
        }
    ]
    
    # Datos para enviar
    data = {
        "commands": commands
    }
    
    try:
        print("🤖 Configurando comandos del bot...")
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("✅ Comandos configurados exitosamente!")
                print("📱 Ahora cuando escribas '/' en Telegram deberías ver:")
                for cmd in commands:
                    print(f"   • /{cmd['command']} - {cmd['description']}")
            else:
                print(f"❌ Error: {result.get('description', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error configurando comandos: {e}")

def get_bot_info():
    load_dotenv()
    
    TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN no encontrado en .env")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                bot_info = result.get("result", {})
                print("🤖 Información del bot:")
                print(f"   • Nombre: {bot_info.get('first_name', 'N/A')}")
                print(f"   • Username: @{bot_info.get('username', 'N/A')}")
                print(f"   • ID: {bot_info.get('id', 'N/A')}")
            else:
                print(f"❌ Error: {result.get('description', 'Error desconocido')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error obteniendo información del bot: {e}")

if __name__ == "__main__":
    print("🔧 Configurando bot de Telegram...")
    print()
    
    # Obtener información del bot
    get_bot_info()
    print()
    
    # Configurar comandos
    setup_bot_commands()
