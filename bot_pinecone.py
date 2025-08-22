#!/usr/bin/env python3
"""
Telegram Bot with Pinecone: RAG + Airtable + Successful response examples
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
        
        print(f"📨 Message received from {chat_id}: {text[:50]}...")

        # Verificar si el usuario está en modo feedback
        print(f"🔍 User state for {chat_id}: {user_states.get(chat_id, 'normal')}")
        if chat_id in user_states and user_states[chat_id] == 'waiting_feedback':
            print(f"📝 Processing feedback input for {chat_id}")
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
        
        print(f"🔍 Query analysis: {query_analysis['query_type']} (use Airtable: {should_use_airtable})")

        # Get Airtable data if necessary
        airtable_data = None
        if should_use_airtable:
            print("📊 Querying Airtable...")
            airtable_data = airtable_client.get_property_info(text)
            print(f"📊 Airtable data: {len(airtable_data['items'])} items, {len(airtable_data['houses'])} houses")

        # Prepare context
        context_parts = []
        
        # Airtable context
        if airtable_data and (airtable_data['items'] or airtable_data['houses']):
            airtable_context = airtable_client.format_response(airtable_data, text)
            if airtable_context != "I didn't find specific information about that in my database.":
                context_parts.append(airtable_context)
                print(f"📋 Airtable context: {len(airtable_context)} characters")
        
        # Pinecone successful examples context
        pinecone_context = pinecone_manager.get_examples_for_context(text, top_k=2)
        if pinecone_context:
            context_parts.append(pinecone_context)
            print(f"📚 Pinecone context: {len(pinecone_context)} characters")
        
        # Always use OpenAI Assistant, but with context if available
        print("🧠 Using OpenAI Assistant...")
        
        # 1) thread per chat
        if chat_id not in threads:
            t = client.beta.threads.create()
            threads[chat_id] = t.id
        thread_id = threads[chat_id]

        # 2) Prepare message with context if available
        message_content = text
        if context_parts:
            context_text = "\n\n".join(context_parts)
            message_content = f"Context for reference:\n{context_text}\n\nGuest question: {text}"
            print(f"📝 Message with context: {len(message_content)} characters")

        # 3) user message
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=message_content)

        # 4) Assistant run
        run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=ASSISTANT_ID)

        # 5) basic polling
        while True:
            r = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if r.status in ["completed","failed","requires_action"]: break
            time.sleep(0.7)

        # 6) last response
        msgs = client.beta.threads.messages.list(thread_id=thread_id, order="desc")
        reply = msgs.data[0].content[0].text.value
        used_rag = True
        used_airtable = bool(airtable_data and (airtable_data['items'] or airtable_data['houses']))
        used_pinecone = bool(pinecone_context)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Send response
        update.message.reply_text(reply)
        
        # Log conversation
        conversation_id = db.log_conversation(
            user_id=chat_id,
            query=text,
            response=reply,
            response_time=response_time,
            used_rag=used_rag,
            used_airtable=used_airtable
        )
        
        # Save conversation ID for feedback
        if chat_id not in user_states or not isinstance(user_states[chat_id], dict):
            user_states[chat_id] = {}
        user_states[chat_id]['last_conversation_id'] = conversation_id
        
        print(f"✅ Response sent to {chat_id} in {response_time:.2f}s (RAG: {used_rag}, Airtable: {used_airtable}, Pinecone: {used_pinecone})")
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        print(f"🔍 Full error traceback:")
        traceback.print_exc()
        update.message.reply_text("Sorry, there was an error processing your message. Please try again.")

def handle_feedback_input(update, context):
    """Handle user feedback input with expected response"""
    chat_id = str(update.effective_chat.id)
    text = update.message.text
    
    # Get last conversation
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("I can't find a recent conversation to give feedback on.")
        user_states[chat_id] = 'normal'
        return
    
    # Process feedback
    feedback_type = 'example_response'
    
    # Save feedback in SQLite
    db.add_feedback(
        user_id=chat_id,
        original_query=last_conv['query'],
        original_response=last_conv['response'],
        feedback_type=feedback_type,
        feedback_text=text,
        conversation_id=last_conv['id']
    )
    
    # Save as successful example in Pinecone
    pinecone_manager = get_pinecone_manager()
    success = pinecone_manager.add_example(
        query=last_conv['query'],
        response=text,  # The response the user expected
        user_feedback="Expected response provided by user"
    )
    
    if success:
        update.message.reply_text("✅ Thank you! Your expected response has been saved as a successful example. This will help improve my future responses.")
    else:
        update.message.reply_text("📝 Thank you for your feedback. I'll take it into account to improve.")
    
    # Reset state
    user_states[chat_id] = 'normal'
    print(f"✅ Reset user state for {chat_id} to 'normal'")

def feedback_command(update, context):
    """Command /feedback - Request expected response"""
    chat_id = str(update.effective_chat.id)
    
    # Check if there's a recent conversation
    last_conv = db.get_last_conversation(chat_id)
    if not last_conv:
        update.message.reply_text("I can't find a recent conversation to give feedback on.")
        return
    
    # Show last conversation and request expected response
    feedback_text = f"""
🤖 **Feedback Request**

**Guest Question:** {last_conv['query']}

**Bot Response:** {last_conv['response']}

---
**💡 How should I have responded?**
"""
    
    update.message.reply_text(feedback_text)
    user_states[chat_id] = 'waiting_feedback'
    print(f"⏳ Set user state for {chat_id} to 'waiting_feedback'")

def stats_command(update, context):
    """Command /stats"""
    chat_id = str(update.effective_chat.id)
    
    # SQLite statistics
    sqlite_stats = db.get_feedback_stats()
    
    # Pinecone statistics
    pinecone_manager = get_pinecone_manager()
    pinecone_stats = pinecone_manager.get_index_stats()
    
    stats_text = f"""
📊 **Bot Statistics:**

**💾 Local database:**
• Total conversations: {sqlite_stats['total_conversations']}
• Conversations with feedback: {sqlite_stats['conversations_with_feedback']}
• Feedback rate: {sqlite_stats['feedback_rate']:.1f}%

**🧠 Example memory (Pinecone):**
• Total examples: {pinecone_stats.get('total_vector_count', 0)}
• Dimension: {pinecone_stats.get('dimension', 'N/A')}

**Feedback types:**
"""
    
    for feedback_type, count in sqlite_stats['feedback_types'].items():
        emoji = "📝" if feedback_type == "example_response" else "👍" if feedback_type == "positive" else "👎" if feedback_type == "negative" else "📝"
        stats_text += f"• {emoji} {feedback_type}: {count}\n"
    
    update.message.reply_text(stats_text)

def help_command(update, context):
    """Command /help"""
    help_text = """
🤖 **Available commands:**

• `/feedback` - Provide the response you expected
• `/stats` - View usage statistics and examples
• `/help` - Show this help

**Types of queries I can answer:**
• 📦 **Appliances** - refrigerator, oven, microwave, etc.
• 🏠 **Rooms** - kitchen, bathroom, bedroom, etc.
• 🏊 **Amenities** - pool, jacuzzi, wifi, etc.
• 📍 **Location** - floor, level, story, etc.

**To improve my responses:**
1. Send `/feedback`
2. Review my last response
3. Write the response you expected
4. I'll learn from your example!

**Information sources:**
• 🧠 **RAG (OpenAI)** - For general queries
• 📊 **Airtable** - For specific property data
• 📚 **Pinecone** - Examples of successful responses

Your feedback helps me improve continuously! 🚀
"""
    update.message.reply_text(help_text)

def main():
    print("🤖 Starting bot with Pinecone (RAG + Airtable + Examples)...")
    print(f"📱 Token: {TELEGRAM_TOKEN[:10]}...")
    print(f"🧠 Assistant: {ASSISTANT_ID}")
    
    # Test connections
    print("📊 Testing Airtable connection...")
    airtable_client = get_airtable_client()
    if airtable_client.test_connection():
        print("✅ Airtable connection successful")
    else:
        print("❌ Error connecting to Airtable")
        return
    
    print("🧠 Testing Pinecone connection...")
    pinecone_manager = get_pinecone_manager()
    stats = pinecone_manager.get_index_stats()
    print(f"✅ Pinecone connection successful ({stats.get('total_vector_count', 0)} examples)")
    
    try:
        up = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = up.dispatcher
        
        # Handlers
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_msg))
        dp.add_handler(CommandHandler("feedback", feedback_command))
        dp.add_handler(CommandHandler("stats", stats_command))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("start", help_command))
        
        print("✅ Bot with Pinecone started successfully")
        print("📱 Available commands: /feedback, /stats, /help")
        print("🛑 Press Ctrl+C to stop the bot")
        
        up.start_polling()
        up.idle()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    print("\n🛑 Stopping bot...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
