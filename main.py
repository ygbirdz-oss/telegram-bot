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

async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Напиши слово: /add слово")

    word = context.args[0].lower()
    bad_words.add(word)
    save_words(bad_words)

    await update.message.reply_text(f"Добавил слово: {word}")

async def remove_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Напиши слово: /remove слово")

    word = context.args[0].lower()
    bad_words.discard(word)
    save_words(bad_words)

    await update.message.reply_text(f"Удалил слово: {word}")

async def list_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bad_words:
        return await update.message.reply_text("Список пуст")

    await update.message.reply_text("\n".join(sorted(bad_words)))

async def mute_user(context, chat_id, user_id):
    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions={"can_send_messages": False},
        until_date=None
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    for word in bad_words:
        if word in text:
            await update.message.delete()

            await context.bot.restrict_chat_member(
                update.effective_chat.id,
                update.effective_user.id,
                permissions={
                    "can_send_messages": False,
                    "can_send_media_messages": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False
                },
                until_date=None
            )

            msg = await update.message.reply_text(
                "⚠️ Давайте без мата!"
            )

            # удалить сообщение через 30 сек
            import asyncio
            await asyncio.sleep(30)
            await msg.delete()

            return

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("add", add_word))
app.add_handler(CommandHandler("remove", remove_word))
app.add_handler(CommandHandler("list", list_words))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
