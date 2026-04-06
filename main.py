import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types

from config import BOT_TOKEN
from storage.db import init_db
from storage.words import load_words

init_db()
bad_words = load_words()

print("🔥 BAD WORDS LOADED:", len(bad_words))


def is_bad(text: str, words: set):
    text = text.lower()
    return any(w in text for w in words)


async def handle_message(message: types.Message):
    global bad_words

    if not message.text:
        return

    if is_bad(message.text, bad_words):

        username = message.from_user.username
        mention = f"@{username}" if username else message.from_user.full_name

        try:
            await message.delete()
        except:
            pass

        await message.answer(
            f"🚫 {mention} человека к которому он обращается, без мата!\n⏳ Мут на 60 секунд"
        )


async def main():
    print("🔥 BOT STARTED")

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout
    )

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(handle_message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    print("🚀 STARTING SCRIPT")
    asyncio.run(main())
