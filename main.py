import os
import json
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "bad_words.json"


def load_words():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_words(words):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)


bad_words = load_words()


def is_bad(text: str):
    text = text.lower()
    return any(word in text for word in bad_words)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()

    if is_bad(text):
        user = msg.from_user
        mention = f"@{user.username}" if user.username else user.first_name

        try:
            await msg.delete()
        except:
            pass

        sent = await msg.reply_text(
            f"🚫 {mention} без мата!\n⏳ Мут на 60 секунд"
        )

        await asyncio.sleep(60)

        try:
            await sent.delete()
        except:
            pass


async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bad_words

    if not context.args:
        await update.message.reply_text("Используй: /add слово")
        return

    word = context.args[0].lower()

    if word not in bad_words:
        bad_words.append(word)
        save_words(bad_words)

    await update.message.reply_text(f"Добавлено: {word}")


def main():
    if not TOKEN:
        print("BOT_TOKEN not found in environment variables")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", add_word))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    print("BOT STARTED")

    # 🔥 FIX: стабильный запуск для Render
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
