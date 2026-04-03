import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("TOKEN")

BADWORDS_FILE = "badwords.txt"

def load_words():
    if not os.path.exists(BADWORDS_FILE):
        return set()
    with open(BADWORDS_FILE, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())

def save_words(words):
    with open(BADWORDS_FILE, "w", encoding="utf-8") as f:
        for w in words:
            f.write(w + "\n")

bad_words = load_words()

# админ (твой user_id)
ADMIN_ID = None  # позже можно закрепить

async def handle_message(update, context):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    for word in bad_words:
        if word in text:

            chat_id = update.effective_chat.id
            user_id = update.effective_user.id

            # 1. удалить сообщение пользователя
            await update.message.delete()

            # 2. отправить сообщение в чат (ВАЖНО: СНАЧАЛА отправляем)
            warning = await context.bot.send_message(
                chat_id=chat_id,
                text="🚫 Давайте без мата!\nВам 1 минута молчания в чате."
            )

            # 3. мут на 1 минуту
            await context.bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions={
                    "can_send_messages": False,
                    "can_send_media_messages": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False
                }
            )

            # 4. удалить предупреждение через 30 секунд
            import asyncio
            await asyncio.sleep(30)
            await warning.delete()

            return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add_word))
app.add_handler(CommandHandler("remove", remove_word))
app.add_handler(CommandHandler("list", list_words))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()
