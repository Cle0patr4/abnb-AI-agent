#!/usr/bin/env python3
"""
Bot de Telegram compatible con python-telegram-bot 13.15
"""
from openai import OpenAI
from telegram.ext import Updater, MessageHandler, Filters
import os
from dotenv import load_dotenv
import signal
import sys

# Load environment variables
load_dotenv()

# Global variables
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ASSISTANT_ID = os.environ["ASSISTANT_ID"]

client = OpenAI()
threads = {}  # chat_id -> thread_id (en memoria; luego usa Redis/DB)

def handle_msg(update, context):
    try:
        chat_id = str(update.effective_chat.id)
        text = update.message.text
        
        print(f"📨 Mensaje recibido de {chat_id}: {text[:50]}...")

        # 1) thread por chat
        if chat_id not in threads:
            t = client.beta.threads.create()
            threads[chat_id] = t.id
        thread_id = threads[chat_id]

        # 2) mensaje del usuario
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=text)

        # 3) run del Assistant
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

        # 4) poll básico
        import time
        while True:
            r = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if r.status in ["completed","failed","requires_action"]: break
            time.sleep(0.7)

        # 5) última respuesta
        msgs = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
        reply = msgs.data[0].content[0].text.value
        update.message.reply_text(reply)
        
        print(f"✅ Respuesta enviada a {chat_id}")
        
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
        update.message.reply_text("Lo siento, hubo un error procesando tu mensaje. Inténtalo de nuevo.")

def main():
    print("🤖 Iniciando bot de Telegram...")
    print(f"📱 Token: {TELEGRAM_TOKEN[:10]}...")
    print(f"🧠 Assistant: {ASSISTANT_ID}")
    
    try:
        up = Updater(TELEGRAM_TOKEN, use_context=True)
        up.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        
        print("✅ Bot iniciado correctamente")
        print("📱 Busca tu bot en Telegram y envíale un mensaje")
        print("🛑 Presiona Ctrl+C para detener el bot")
        
        up.start_polling()
        up.idle()
        
    except Exception as e:
        print(f"❌ Error iniciando bot: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    print("\n🛑 Deteniendo bot...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
