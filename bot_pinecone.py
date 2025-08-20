#!/usr/bin/env python3
"""
Bot de Telegram con Pinecone: RAG + Airtable + Ejemplos de respuestas exitosas
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
from pinecone_client import get_pinecone_manager

# Load environment variables
load_dotenv()

# Global variables
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ASSISTANT_ID = os.environ["ASSISTANT_ID"]

client = OpenAI()
threads = {}  # chat_id -> thread_id
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

        # Obtener clientes
        airtable_client = get_airtable_client()
        pinecone_manager = get_pinecone_manager()
        
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

        # Preparar el contexto
        context_parts = []
        
        # Contexto de Airtable
        if airtable_data and (airtable_data['items'] or airtable_data['houses']):
            airtable_context = airtable_client.format_response(airtable_data, text)
            if airtable_context != "No encontré información específica sobre eso en mi base de datos.":
                context_parts.append(airtable_context)
                print(f"📋 Contexto de Airtable: {len(airtable_context)} caracteres")
        
        # Contexto de ejemplos exitosos de Pinecone
        pinecone_context = pinecone_manager.get_examples_for_context(text, top_k=2)
        if pinecone_context:
            context_parts.append(pinecone_context)
            print(f"📚 Contexto de Pinecone: {len(pinecone_context)} caracteres")
        
        # Determinar qué fuente usar
        if context_parts:
            # Usar contexto combinado
            reply = "\n\n".join(context_parts)
            used_rag = False
            used_airtable = bool(airtable_data and (airtable_data['items'] or airtable_data['houses']))
            used_pinecone = bool(pinecone_context)
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
            used_pinecone = False
        
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
        
        print(f"✅ Respuesta enviada a {chat_id} en {response_time:.2f}s (RAG: {used_rag}, Airtable: {used_airtable}, Pinecone: {used_pinecone})")
        
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
        update.message.reply_text("Lo siento, hubo un error procesando tu mensaje. Inténtalo de nuevo.")

def handle_feedback_input(update, context):
    """Manejar input de feedback del usuario con respuesta esperada"""
    chat_id = str(update.effective_chat.id)
    text = update.message.text
    
    # Obtener la última conversación
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("No encuentro una conversación reciente para dar feedback.")
        user_states[chat_id] = 'normal'
        return
    
    # Procesar el feedback
    feedback_type = 'example_response'
    
    # Guardar feedback en SQLite
    db.add_feedback(
        user_id=chat_id,
        original_query=last_conv['query'],
        original_response=last_conv['response'],
        feedback_type=feedback_type,
        feedback_text=text,
        conversation_id=last_conv['id']
    )
    
    # Guardar como ejemplo exitoso en Pinecone
    pinecone_manager = get_pinecone_manager()
    success = pinecone_manager.add_example(
        query=last_conv['query'],
        response=text,  # La respuesta que el usuario esperaba
        user_feedback="Respuesta esperada proporcionada por el usuario"
    )
    
    if success:
        update.message.reply_text("✅ ¡Gracias! Tu respuesta esperada se ha guardado como ejemplo exitoso. Esto ayudará a mejorar mis respuestas futuras.")
    else:
        update.message.reply_text("📝 Gracias por tu feedback. Lo tendré en cuenta para mejorar.")
    
    # Resetear estado
    user_states[chat_id] = 'normal'

def feedback_command(update, context):
    """Comando /feedback - Solicitar respuesta esperada"""
    chat_id = str(update.effective_chat.id)
    
    # Verificar si hay una conversación reciente
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("No encuentro una conversación reciente para dar feedback.")
        return
    
    # Mostrar la última conversación y solicitar respuesta esperada
    feedback_text = f"""
📝 **Última conversación:**

**Tu pregunta:** {last_conv['query']}

**Mi respuesta:** {last_conv['response']}

---
**¿Cuál era la respuesta que esperabas?**

Por favor, escribe la respuesta que hubieras querido recibir. Esto me ayudará a aprender y mejorar mis respuestas futuras.

**Ejemplo:**
Si preguntaste "¿Qué hay en la cocina?" y mi respuesta no fue la esperada, escribe algo como:
"La cocina tiene nevera Samsung, horno eléctrico, microondas y cafetera. Todos están en perfecto estado."
"""
    
    update.message.reply_text(feedback_text)
    user_states[chat_id] = 'waiting_feedback'

def stats_command(update, context):
    """Comando /estadisticas"""
    chat_id = str(update.effective_chat.id)
    
    # Estadísticas de SQLite
    sqlite_stats = db.get_feedback_stats()
    
    # Estadísticas de Pinecone
    pinecone_manager = get_pinecone_manager()
    pinecone_stats = pinecone_manager.get_index_stats()
    
    stats_text = f"""
📊 **Estadísticas del Bot:**

**💾 Base de datos local:**
• Total de conversaciones: {sqlite_stats['total_conversations']}
• Conversaciones con feedback: {sqlite_stats['conversations_with_feedback']}
• Tasa de feedback: {sqlite_stats['feedback_rate']:.1f}%

**🧠 Memoria de ejemplos (Pinecone):**
• Total de ejemplos: {pinecone_stats.get('total_vector_count', 0)}
• Dimensión: {pinecone_stats.get('dimension', 'N/A')}

**Tipos de feedback:**
"""
    
    for feedback_type, count in sqlite_stats['feedback_types'].items():
        emoji = "📝" if feedback_type == "example_response" else "👍" if feedback_type == "positive" else "👎" if feedback_type == "negative" else "📝"
        stats_text += f"• {emoji} {feedback_type}: {count}\n"
    
    update.message.reply_text(stats_text)

def help_command(update, context):
    """Comando /ayuda"""
    help_text = """
🤖 **Comandos disponibles:**

• `/feedback` - Proporcionar la respuesta que esperabas
• `/estadisticas` - Ver estadísticas de uso y ejemplos
• `/ayuda` - Mostrar esta ayuda

**Tipos de consultas que puedo responder:**
• 📦 **Electrodomésticos** - nevera, horno, microondas, etc.
• 🏠 **Habitaciones** - cocina, baño, dormitorio, etc.
• 🏊 **Amenidades** - piscina, jacuzzi, wifi, etc.
• 📍 **Ubicación** - piso, nivel, planta, etc.

**Para mejorar mis respuestas:**
1. Envía `/feedback`
2. Revisa mi última respuesta
3. Escribe la respuesta que esperabas
4. ¡Aprenderé de tu ejemplo!

**Fuentes de información:**
• 🧠 **RAG (OpenAI)** - Para consultas generales
• 📊 **Airtable** - Para datos específicos de propiedades
• 📚 **Pinecone** - Ejemplos de respuestas exitosas

¡Tu feedback me ayuda a mejorar continuamente! 🚀
"""
    update.message.reply_text(help_text)

def main():
    print("🤖 Iniciando bot con Pinecone (RAG + Airtable + Ejemplos)...")
    print(f"📱 Token: {TELEGRAM_TOKEN[:10]}...")
    print(f"🧠 Assistant: {ASSISTANT_ID}")
    
    # Probar conexiones
    print("📊 Probando conexión con Airtable...")
    airtable_client = get_airtable_client()
    if airtable_client.test_connection():
        print("✅ Conexión con Airtable exitosa")
    else:
        print("❌ Error conectando con Airtable")
        return
    
    print("🧠 Probando conexión con Pinecone...")
    pinecone_manager = get_pinecone_manager()
    stats = pinecone_manager.get_index_stats()
    print(f"✅ Conexión con Pinecone exitosa ({stats.get('total_vector_count', 0)} ejemplos)")
    
    try:
        up = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = up.dispatcher
        
        # Handlers
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(CommandHandler("feedback", feedback_command))
        dp.add_handler(CommandHandler("estadisticas", stats_command))
        dp.add_handler(CommandHandler("ayuda", help_command))
        dp.add_handler(CommandHandler("start", help_command))
        
        print("✅ Bot con Pinecone iniciado correctamente")
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
