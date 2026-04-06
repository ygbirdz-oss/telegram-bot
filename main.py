import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ChatPermissions

from config import BOT_TOKEN

from storage.db import init_db
from storage.words import load_words

# -----------------------------
# INIT DB + LOAD WORDS
# -----------------------------
init_db()
bad_words = load_words()

print("🔥 BAD WORDS LOADED:", len(bad_words))


# -----------------------------
# CHECK BAD WORDS
# -----------------------------
def is_bad(text: str, words: set) -> bool:
    text = text.lower()
    return any(word in text for word in words)


# -----------------------------
# MODERATION FORMAT (ТВОЙ СТАНДАРТ)
# -----------------------------
MUTE_TEXT = "🚫 @{username} человека к которому он обращается, без мата!\n⏳ Мут на 60 секунд"


# -----------------------------
# HANDLER
# -----------------------------
async def handle_message(message: types.Message):
    global bad_words

    if not message.text:
        return

    if is_bad(message.text, bad_words):

        username = message.from_user.username
        if not username:
            username = message.from_user.full_name

        # удаляем сообщение нарушителя
        try:
            await message.delete()
        except:
            pass

        # ответ по твоему формату
        await message.answer(
            MUTE_TEXT.format(username=username)
        )


# -----------------------------
# START BOT
# -----------------------------
async def main():
    print("🔥 MAIN STARTED")

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # регистрируем обработчик
    dp.message.register(handle_message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    print("🚀 SCRIPT STARTED")
    asyncio.run(main())
