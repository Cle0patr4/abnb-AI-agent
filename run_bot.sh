#!/bin/bash

echo "🤖 Iniciando bot de Telegram..."
echo "📱 Usando Python 3.11 y python-telegram-bot 13.15"

# Activar el entorno virtual con Python 3.11
source venv311/bin/activate

# Verificar que las variables de entorno estén configuradas
echo "🔍 Verificando configuración..."
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
required = ['OPENAI_API_KEY', 'TELEGRAM_TOKEN', 'ASSISTANT_ID']
for var in required:
    if not os.environ.get(var):
        print(f'❌ Error: {var} no está configurado')
        exit(1)
    print(f'✅ {var}: {len(os.environ.get(var))} caracteres')
print('🎉 Configuración correcta')
"

if [ $? -ne 0 ]; then
    echo "❌ Error en la configuración. Verifica tu archivo .env"
    exit 1
fi

echo ""
echo "🚀 Iniciando bot..."
echo "📱 Busca tu bot en Telegram y envíale un mensaje"
echo "🛑 Presiona Ctrl+C para detener el bot"
echo ""

# Ejecutar el bot
python3 bot_v13.py
