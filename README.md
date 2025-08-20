# 🤖 Bot de Telegram Inteligente con IA Híbrida

Un bot de Telegram avanzado que combina **RAG (OpenAI)**, **Airtable** y **Pinecone** para respuestas inteligentes y aprendizaje continuo.

## 🚀 Configuración Rápida

### 1. Instalar dependencias
```bash
# Crear entorno virtual con Python 3.11
python3.11 -m venv venv311

# Activar entorno virtual
source venv311/bin/activate

# Instalar dependencias
pip install openai python-telegram-bot==13.15 python-dotenv pyairtable pinecone
```

### 2. Configurar variables de entorno
Crear archivo `.env` con tus credenciales:
```env
OPENAI_API_KEY=tu_openai_api_key_aqui
TELEGRAM_TOKEN=tu_telegram_token_aqui
ASSISTANT_ID=tu_assistant_id_aqui
AIRTABLE_API_KEY=tu_airtable_api_key_aqui
AIRTABLE_BASE_ID=tu_airtable_base_id_aqui
PINECONE_API_KEY=tu_pinecone_api_key_aqui
PINECONE_ENVIRONMENT=tu_pinecone_environment
PINECONE_INDEX_NAME=tu_pinecone_index_name
```

### 3. Ejecutar el bot
```bash
# Opción 1: Usar el script automático
./run_bot.sh

# Opción 2: Ejecutar manualmente
source venv311/bin/activate
python3 bot_pinecone.py
```

## 📱 Cómo usar

### 🗣️ Conversación Normal
1. **Busca tu bot en Telegram** usando el token que configuraste
2. **Envía un mensaje** al bot
3. **El bot responderá** usando la mejor fuente disponible:
   - 📊 **Airtable** para consultas específicas sobre propiedades
   - 📚 **Pinecone** para ejemplos de respuestas exitosas
   - 🧠 **OpenAI RAG** para consultas generales

### 🎯 Sistema de Feedback Inteligente
1. **Usa `/feedback`** después de recibir una respuesta
2. **Escribe la respuesta que esperabas** (no solo 👍/👎)
3. **El bot aprende** y guardará tu ejemplo para futuras consultas similares

### 📊 Comandos Disponibles
- `/feedback` - Proporcionar respuesta esperada para mejorar el bot
- `/estadisticas` - Ver estadísticas de uso y ejemplos almacenados  
- `/ayuda` - Mostrar comandos disponibles
- `/start` - Iniciar conversación

## 🏗️ Arquitectura

### 🧠 Fuentes de Información
- **🤖 OpenAI RAG** - Para consultas generales y conversación natural
- **📊 Airtable** - Base de datos relacional con información específica de propiedades
- **📚 Pinecone** - Memoria de ejemplos de respuestas exitosas para aprendizaje continuo

### 🔄 Flujo de Respuesta
1. **Análisis** - Determina el tipo de consulta
2. **Búsqueda** - Consulta Airtable y/o Pinecone según sea necesario  
3. **Generación** - Usa la mejor fuente disponible o combina múltiples fuentes
4. **Aprendizaje** - Permite feedback para mejorar respuestas futuras

## 🔧 Archivos importantes

- `bot_pinecone.py` - Bot principal con IA híbrida
- `airtable_client.py` - Cliente para conexión con Airtable
- `pinecone_client.py` - Cliente para memoria de ejemplos exitosos
- `database.py` - Base de datos SQLite para feedback local
- `run_bot.sh` - Script de inicio automático
- `.env` - Variables de entorno (NO se sube a Git)
- `.gitignore` - Protege archivos sensibles

## 🛠️ Solución de problemas

### Error: "No module named 'imghdr'"
- Usar Python 3.11 en lugar de Python 3.13
- El entorno virtual `venv311` ya está configurado correctamente

### Error: "Only timezones from the pytz library are supported"
- Usar python-telegram-bot versión 13.15
- Ya está configurado en el entorno virtual

### El bot no responde
- Verificar que las variables en `.env` sean correctas
- Asegurarse de que el bot esté ejecutándose (`ps aux | grep bot_pinecone`)
- Verificar conexiones: Airtable y Pinecone

### Error de conexión con Pinecone
- Verificar PINECONE_API_KEY y PINECONE_INDEX_NAME
- Asegurarse de que el índice tenga 1536 dimensiones
- Usar región soportada en plan gratuito (us-east-1)

### Error de conexión con Airtable  
- Verificar AIRTABLE_API_KEY y AIRTABLE_BASE_ID
- Comprobar nombres de tablas: "Items per property" y "Houses Organization"

## 🔒 Seguridad

- ✅ Variables de entorno protegidas en `.env`
- ✅ `.env` incluido en `.gitignore`
- ✅ Credenciales no se suben al repositorio

## ✨ Características Principales

### 🤖 IA Híbrida
- **Múltiples fuentes** de información integradas
- **Selección inteligente** de la mejor fuente para cada consulta
- **Combinación** de datos relacionales y vectoriales

### 🧠 Aprendizaje Continuo
- **Feedback inteligente** con respuestas esperadas
- **Memoria de ejemplos exitosos** en Pinecone
- **Mejora automática** con cada interacción

### 📊 Datos Relacionales
- **Integración con Airtable** para información estructurada
- **Búsqueda semántica** en datos de propiedades
- **Respuestas específicas** y precisas

### 🔄 Sistema de Feedback
- **Base de datos local** para tracking de conversaciones
- **Estadísticas** de uso y mejora
- **Comandos intuitivos** para dar feedback

## 📝 Notas Técnicas

- Compatible con **Python 3.11** y **python-telegram-bot 13.15**
- Usa **embeddings de OpenAI** (text-embedding-ada-002, 1536 dimensiones)
- **Base de datos SQLite** local para logs y feedback
- **Threads separados** por chat_id para contexto individual
- **Búsqueda vectorial** optimizada en Pinecone
