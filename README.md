# 🤖 Bot de Telegram con OpenAI Assistant

Un bot de Telegram que utiliza OpenAI Assistants para responder mensajes de manera inteligente.

## 🚀 Configuración Rápida

### 1. Instalar dependencias
```bash
# Crear entorno virtual con Python 3.11
python3.11 -m venv venv311

# Activar entorno virtual
source venv311/bin/activate

# Instalar dependencias
pip install openai python-telegram-bot==13.15 python-dotenv
```

### 2. Configurar variables de entorno
Crear archivo `.env` con tus credenciales:
```env
OPENAI_API_KEY=tu_openai_api_key_aqui
TELEGRAM_TOKEN=tu_telegram_token_aqui
ASSISTANT_ID=tu_assistant_id_aqui
```

### 3. Ejecutar el bot
```bash
# Opción 1: Usar el script automático
./run_bot.sh

# Opción 2: Ejecutar manualmente
source venv311/bin/activate
python3 bot_v13.py
```

## 📱 Cómo usar

1. **Busca tu bot en Telegram** usando el token que configuraste
2. **Envía un mensaje** al bot
3. **El bot responderá** usando tu OpenAI Assistant

## 🔧 Archivos importantes

- `bot_v13.py` - Bot principal (compatible con python-telegram-bot 13.15)
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
- Asegurarse de que el bot esté ejecutándose (`ps aux | grep bot_v13`)

## 🔒 Seguridad

- ✅ Variables de entorno protegidas en `.env`
- ✅ `.env` incluido en `.gitignore`
- ✅ Credenciales no se suben al repositorio

## 📝 Notas

- El bot mantiene conversaciones separadas por chat_id
- Usa threads de OpenAI para mantener contexto
- Compatible con Python 3.11 y python-telegram-bot 13.15
