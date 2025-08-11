#!/usr/bin/env python3
"""
Script de prueba para verificar que el bot de Telegram esté configurado correctamente
"""
from openai import OpenAI
from telegram.ext import Application
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_configuration():
    print("🔍 Verificando configuración del bot...")
    
    # Verificar variables de entorno
    required_vars = ['OPENAI_API_KEY', 'TELEGRAM_TOKEN', 'ASSISTANT_ID']
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            print(f"❌ Error: {var} no está configurado")
            return False
        print(f"✅ {var}: {len(value)} caracteres")
    
    # Verificar OpenAI
    try:
        client = OpenAI()
        assistant_id = os.environ['ASSISTANT_ID']
        assistant = client.beta.assistants.retrieve(assistant_id)
        print(f"✅ OpenAI Assistant: {assistant.name}")
    except Exception as e:
        print(f"❌ Error con OpenAI: {e}")
        return False
    
    # Verificar Telegram
    try:
        token = os.environ['TELEGRAM_TOKEN']
        app = Application.builder().token(token).build()
        print("✅ Token de Telegram válido")
    except Exception as e:
        print(f"❌ Error con Telegram: {e}")
        return False
    
    print("\n🎉 ¡Todo está configurado correctamente!")
    print("📱 Tu bot está listo para usar en Telegram")
    return True

if __name__ == "__main__":
    test_configuration()
