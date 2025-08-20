#!/usr/bin/env python3
"""
Bot de Telegram híbrido: RAG + Airtable
"""
from openai import OpenAI
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
import os
from dotenv import load_dotenv
import signal
import sys
import time
from database import db
from airtable_client import get_airtable_client

# Load environment variables
load_dotenv()

# Global variables
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ASSISTANT_ID = os.environ["ASSISTANT_ID"]

client = OpenAI()
threads = {}  # chat_id -> thread_id (en memoria; luego usa Redis/DB)
user_states = {}  # chat_id -> estado actual del usuario

def handle_msg(update, context):
    try:
        chat_id = str(update.effective_chat.id)
        text = update.message.text
        
        print(f"📨 Mensaje recibido de {chat_id}: {text[:50]}...")

        # Verificar si el usuario está en modo feedback
        if chat_id in user_states and user_states[chat_id] == 'waiting_feedback':
            handle_feedback_input(update, context)
            return

        # Medir tiempo de respuesta
        start_time = time.time()

        # Obtener cliente de Airtable
        airtable_client = get_airtable_client()
        
        # Analizar la consulta para determinar si usar Airtable
        query_analysis = airtable_client.analyze_query(text)
        should_use_airtable = query_analysis['should_use_airtable']
        
        print(f"🔍 Análisis de consulta: {query_analysis['query_type']} (usar Airtable: {should_use_airtable})")

        # Obtener datos de Airtable si es necesario
        airtable_data = None
        if should_use_airtable:
            print("📊 Consultando Airtable...")
            airtable_data = airtable_client.get_property_info(text)
            print(f"📊 Datos de Airtable: {len(airtable_data['items'])} items, {len(airtable_data['houses'])} houses")

        # Preparar el contexto para OpenAI
        context = ""
        if airtable_data and (airtable_data['items'] or airtable_data['houses']):
            context = airtable_client.format_response(airtable_data, text)
            print(f"📋 Contexto de Airtable: {len(context)} caracteres")
        
        # Si tenemos datos de Airtable, usarlos directamente
        if context and context != "No encontré información específica sobre eso en mi base de datos.":
            reply = context
            used_rag = False
            used_airtable = True
        else:
            # Usar OpenAI Assistant (RAG)
            print("🧠 Usando OpenAI Assistant...")
            
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
            while True:
                r = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                if r.status in ["completed","failed","requires_action"]: break
                time.sleep(0.7)

            # 5) última respuesta
            msgs = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
            reply = msgs.data[0].content[0].text.value
            used_rag = True
            used_airtable = False
        
        # Calcular tiempo de respuesta
        response_time = time.time() - start_time
        
        # Enviar respuesta
        update.message.reply_text(reply)
        
        # Log de la conversación
        conversation_id = db.log_conversation(
            user_id=chat_id,
            query=text,
            response=reply,
            response_time=response_time,
            used_rag=used_rag,
            used_airtable=used_airtable
        )
        
        # Guardar el ID de la conversación para feedback
        if chat_id not in user_states:
            user_states[chat_id] = {}
        user_states[chat_id]['last_conversation_id'] = conversation_id
        
        print(f"✅ Respuesta enviada a {chat_id} en {response_time:.2f}s (RAG: {used_rag}, Airtable: {used_airtable})")
        
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
        update.message.reply_text("Lo siento, hubo un error procesando tu mensaje. Inténtalo de nuevo.")

def handle_feedback_input(update, context):
    """Manejar input de feedback del usuario"""
    chat_id = str(update.effective_chat.id)
    text = update.message.text
    
    # Obtener la última conversación
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("No encuentro una conversación reciente para dar feedback.")
        user_states[chat_id] = 'normal'
        return
    
    # Procesar el feedback
    feedback_type = 'comment'
    if text.lower() in ['👍', '👍🏻', '👍🏼', '👍🏽', '👍🏾', '👍🏿', 'bueno', 'bien', 'excelente']:
        feedback_type = 'positive'
    elif text.lower() in ['👎', '👎🏻', '👎🏼', '👎🏽', '👎🏾', '👎🏿', 'malo', 'mal', 'pésimo']:
        feedback_type = 'negative'
    
    # Guardar feedback
    db.add_feedback(
        user_id=chat_id,
        original_query=last_conv['query'],
        original_response=last_conv['response'],
        feedback_type=feedback_type,
        feedback_text=text if feedback_type == 'comment' else None,
        conversation_id=last_conv['id']
    )
    
    # Confirmar feedback
    if feedback_type == 'positive':
        update.message.reply_text("👍 ¡Gracias por tu feedback positivo! Me ayuda a mejorar.")
    elif feedback_type == 'negative':
        update.message.reply_text("👎 Gracias por tu feedback. Trabajaré en mejorar mis respuestas.")
    else:
        update.message.reply_text("📝 Gracias por tu comentario. Lo tendré en cuenta para mejorar.")
    
    # Resetear estado
    user_states[chat_id] = 'normal'

def feedback_command(update, context):
    """Comando /feedback"""
    chat_id = str(update.effective_chat.id)
    
    # Verificar si hay una conversación reciente
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("No encuentro una conversación reciente para dar feedback.")
        return
    
    # Mostrar la última conversación y solicitar feedback
    feedback_text = f"""
📝 **Última conversación:**

**Tu pregunta:** {last_conv['query']}

**Mi respuesta:** {last_conv['response']}

---
¿Qué te pareció mi respuesta?

Puedes:
• 👍 Dar feedback positivo
• 👎 Dar feedback negativo  
• 📝 Escribir un comentario específico
"""
    
    update.message.reply_text(feedback_text)
    user_states[chat_id] = 'waiting_feedback'

def stats_command(update, context):
    """Comando /estadisticas"""
    chat_id = str(update.effective_chat.id)
    
    stats = db.get_feedback_stats()
    
    stats_text = f"""
📊 **Estadísticas del Bot:**

• Total de conversaciones: {stats['total_conversations']}
• Conversaciones con feedback: {stats['conversations_with_feedback']}
• Tasa de feedback: {stats['feedback_rate']:.1f}%

**Tipos de feedback:**
"""
    
    for feedback_type, count in stats['feedback_types'].items():
        emoji = "👍" if feedback_type == "positive" else "👎" if feedback_type == "negative" else "📝"
        stats_text += f"• {emoji} {feedback_type}: {count}\n"
    
    update.message.reply_text(stats_text)

def help_command(update, context):
    """Comando /ayuda"""
    help_text = """
🤖 **Comandos disponibles:**

• `/feedback` - Dar feedback sobre mi última respuesta
• `/estadisticas` - Ver estadísticas de uso
• `/ayuda` - Mostrar esta ayuda

**Tipos de consultas que puedo responder:**
• 📦 **Electrodomésticos** - nevera, horno, microondas, etc.
• 🏠 **Habitaciones** - cocina, baño, dormitorio, etc.
• 🏊 **Amenidades** - piscina, jacuzzi, wifi, etc.
• 📍 **Ubicación** - piso, nivel, planta, etc.

**Para dar feedback:**
1. Envía `/feedback`
2. Revisa mi última respuesta
3. Envía 👍, 👎, o un comentario

¡Tu feedback me ayuda a mejorar! 🚀
"""
    update.message.reply_text(help_text)

def main():
    print("🤖 Iniciando bot híbrido (RAG + Airtable)...")
    print(f"📱 Token: {TELEGRAM_TOKEN[:10]}...")
    print(f"🧠 Assistant: {ASSISTANT_ID}")
    
    # Probar conexión con Airtable
    print("📊 Probando conexión con Airtable...")
    airtable_client = get_airtable_client()
    if airtable_client.test_connection():
        print("✅ Conexión con Airtable exitosa")
    else:
        print("❌ Error conectando con Airtable")
        return
    
    try:
        up = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = up.dispatcher
        
        # Handlers
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(CommandHandler("feedback", feedback_command))
        dp.add_handler(CommandHandler("estadisticas", stats_command))
        dp.add_handler(CommandHandler("ayuda", help_command))
        dp.add_handler(CommandHandler("start", help_command))
        
        print("✅ Bot híbrido iniciado correctamente")
        print("📱 Comandos disponibles: /feedback, /estadisticas, /ayuda")
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
