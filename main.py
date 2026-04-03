import os
import asyncio
import re
from collections import defaultdict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("TOKEN")

BADWORDS_FILE = "badwords.txt"
ADMIN_ID = 123456789  # 👈 вставь свой ID

# -----------------------
# ДАННЫЕ
# -----------------------

bad_words = set()
warnings = defaultdict(int)
user_stats = defaultdict(int)

# -----------------------
# ЗАГРУЗКА СЛОВ
# -----------------------

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

# -----------------------
# НОРМАЛИЗАЦИЯ
# -----------------------

def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-zа-яё0-9]", "", text)
    return text

# -----------------------
# ГЛАВНОЕ МЕНЮ
# -----------------------

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Добавить слово", callback_data="add_word")],
        [InlineKeyboardButton("➖ Удалить слово", callback_data="remove_word")],
        [InlineKeyboardButton("📃 Список слов", callback_data="list_words")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🏆 Топ нарушителей", callback_data="top")],
    ]

    await update.message.reply_text(
        "🎛 <b>Панель управления ботом</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# -----------------------
# CALLBACK КНОПКИ
# -----------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    data = query.data

    # ➕ ДОБАВИТЬ
    if data == "add_word":
        await query.message.reply_text("✏️ Напиши слово для добавления:")
        context.user_data["mode"] = "add"

    # ➖ УДАЛИТЬ
    elif data == "remove_word":
        await query.message.reply_text("✏️ Напиши слово для удаления:")
        context.user_data["mode"] = "remove"

    # 📃 СПИСОК
    elif data == "list_words":
        text = "\n".join(sorted(bad_words)) if bad_words else "Список пуст"
        await query.message.reply_text(text)

    # 📊 СТАТИСТИКА
    elif data == "stats":
        text = f"👥 Пользователей с нарушениями: {len(warnings)}"
        await query.message.reply_text(text)

    # 🏆 ТОП
    elif data == "top":
        top = sorted(warnings.items(), key=lambda x: x[1], reverse=True)[:10]

        if not top:
            await query.message.reply_text("Нет нарушений")
            return

        text = "🏆 Топ нарушителей:\n"
        for user_id, count in top:
            text += f"{user_id} — {count}\n"

        await query.message.reply_text(text)

# -----------------------
# ТЕКСТОВЫЙ ВВОД (КНОПКИ)
# -----------------------

async def text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    mode = context.user_data.get("mode")

    if not mode:
        return

    word = update.message.text.lower().strip()

    if mode == "add":
        bad_words.add(word)
        save_words(bad_words)
        await update.message.reply_text(f"➕ Добавлено: {word}")

    elif mode == "remove":
        bad_words.discard(word)
        save_words(bad_words)
        await update.message.reply_text(f"➖ Удалено: {word}")

    context.user_data["mode"] = None

# -----------------------
# АНТИ-МАТ
# -----------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    text = normalize(update.message.text)

    for word in bad_words:
        if word in text:

            warnings[user_id] += 1
            user_stats[user_id] += 1

            await update.message.delete()

            await context.bot.send_message(
                chat_id=chat_id,
                text="🚫 Без мата!\n⏳ Мут 60 секунд."
            )

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

            # 60 минут мут после 3 нарушений
            if warnings[user_id] >= 3:

                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⛔ 3 нарушения → мут 60 минут"
                )

                await asyncio.sleep(3600)

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

                warnings[user_id] = 0
                return

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

# -----------------------
# ЗАПУСК
# -----------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("panel", panel))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
