import os
import asyncio
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import defaultdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")

ADMIN_ID = 388777732  # ✅ твой ID

BADWORDS_FILE = "badwords.txt"

# =========================
# RENDER KEEP-ALIVE PORT
# =========================

def run_web():
    port = int(os.environ.get("PORT", 10000))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

# =========================
# DATA
# =========================

bad_words = set()
warnings = defaultdict(int)
context_state = {}

# =========================
# LOAD / SAVE WORDS
# =========================

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

# =========================
# NORMALIZE TEXT
# =========================

def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-zа-яё0-9]", "", text)
    return text

# =========================
# PANEL
# =========================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Добавить слово", callback_data="add")],
        [InlineKeyboardButton("➖ Удалить слово", callback_data="remove")],
        [InlineKeyboardButton("📃 Список слов", callback_data="list")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]

    await update.message.reply_text(
        "🎛 Панель управления",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTONS
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    uid = query.from_user.id

    if query.data == "add":
        context_state[uid] = "add"
        await query.message.reply_text("✏️ Отправь слово для ДОБАВЛЕНИЯ")

    elif query.data == "remove":
        context_state[uid] = "remove"
        await query.message.reply_text("✏️ Отправь слово для УДАЛЕНИЯ")

    elif query.data == "list":
        await query.message.reply_text("\n".join(sorted(bad_words)) or "Список пуст")

    elif query.data == "stats":
        await query.message.reply_text(f"📊 Нарушителей: {len(warnings)}")

# =========================
# MAIN LOGIC
# =========================

async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    text_raw = update.message.text

    # =========================
    # ADMIN WORD INPUT
    # =========================

    if user_id == ADMIN_ID and user_id in context_state:

        mode = context_state[user_id]
        word = text_raw.lower().strip()

        if mode == "add":
            bad_words.add(word)
            save_words(bad_words)
            await update.message.reply_text(f"➕ Добавлено: {word}")

        elif mode == "remove":
            bad_words.discard(word)
            save_words(bad_words)
            await update.message.reply_text(f"➖ Удалено: {word}")

        del context_state[user_id]
        return

    # =========================
    # ANTI-MAT
    # =========================

    text = normalize(text_raw)

    for word in bad_words:
        if word in text:

            warnings[user_id] += 1

            try:
                await update.message.delete()
            except:
                pass

            await context.bot.send_message(
                chat_id=chat_id,
                text="🚫 Без мата!\n⏳ Мут на 60 секунд"
            )

            # mute 60 sec
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

            # auto unmute
            await asyncio.sleep(60)

            await context.bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions={
                    "can_send_messages": True,
                    "can_send_media_messages": True,
                    "can_send_polls": True,
                    "can_send_other_messages": True,
                    "can_add_web_page_previews": True
                }
            )

            return

# =========================
# APP START
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("panel", panel))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))

app.run_polling()
