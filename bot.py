import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command

# =====================================================
# CONFIG
# =====================================================

BOT_TOKEN = "8830066103:AAF_CX6GvkuPHQ8Mq5bCWqLx90TM3pVda7A"

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =====================================================
# BOT
# =====================================================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =====================================================
# DATABASE
# =====================================================

conn = sqlite3.connect(
    "music.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS music (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    artist TEXT DEFAULT '',
    file_id TEXT UNIQUE NOT NULL,
    plays INTEGER DEFAULT 0
)
""")

conn.commit()

# =====================================================
# KEYBOARDS
# =====================================================

def play_keyboard(music_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶ Play",
                    callback_data=f"play:{music_id}"
                )
            ]
        ]
    )

# =====================================================
# START
# =====================================================

@dp.message(Command("start"))
async def start(message: Message):

    text = (
        "🎧 <b>Pepe Music Bot</b>\n\n"
        "Возможности:\n"
        "• хранение музыки\n"
        "• поиск треков\n"
        "• встроенный player\n\n"
        "Команды:\n"
        "/search название"
    )

    await message.answer(text)

# =====================================================
# SAVE MUSIC
# =====================================================

@dp.message(F.audio)
async def save_music(message: Message):

    audio = message.audio

    title = audio.title or "Unknown"
    artist = audio.performer or "Unknown"
    file_id = audio.file_id

    try:

        cursor.execute("""
            INSERT OR IGNORE INTO music (
                title,
                artist,
                file_id
            )
            VALUES (?, ?, ?)
        """, (
            title.strip(),
            artist.strip(),
            file_id
        ))

        conn.commit()

        await message.answer(
            f"✅ Трек сохранён\n\n"
            f"🎵 {title}\n"
            f"👤 {artist}"
        )

        logger.info(f"Added: {title}")

    except Exception as e:

        logger.error(e)

        await message.answer(
            "❌ Ошибка сохранения"
        )

# =====================================================
# SEARCH
# =====================================================

@dp.message(Command("search"))
async def search_music(message: Message):

    query = message.text.replace("/search", "").strip()

    if not query:

        await message.answer(
            "❌ Введи название\n\n"
            "Пример:\n"
            "/search drake"
        )

        return

    q = f"%{query}%"

    cursor.execute("""
        SELECT
            id,
            title,
            artist,
            file_id,
            plays
        FROM music
        WHERE
            title LIKE ?
            OR artist LIKE ?
        ORDER BY plays DESC
        LIMIT 10
    """, (q, q))

    results = cursor.fetchall()

    if not results:

        await message.answer(
            "😔 Ничего не найдено"
        )

        return

    for row in results:

        music_id, title, artist, file_id, plays = row

        text = (
            f"🎵 <b>{title}</b>\n"
            f"👤 {artist}\n"
            f"🔥 Прослушиваний: {plays}"
        )

        await message.answer(
            text,
            reply_markup=play_keyboard(music_id)
        )

# =====================================================
# PLAY
# =====================================================

@dp.callback_query(F.data.startswith("play:"))
async def play_music(callback: CallbackQuery):

    music_id = int(
        callback.data.split(":")[1]
    )

    cursor.execute("""
        SELECT
            title,
            artist,
            file_id
        FROM music
        WHERE id = ?
    """, (music_id,))

    track = cursor.fetchone()

    if not track:

        await callback.answer(
            "❌ Трек не найден"
        )

        return

    title, artist, file_id = track

    cursor.execute("""
        UPDATE music
        SET plays = plays + 1
        WHERE id = ?
    """, (music_id,))

    conn.commit()

    await callback.message.answer_audio(
        audio=file_id,
        title=title,
        performer=artist
    )

    await callback.answer()

# =====================================================
# MAIN
# =====================================================

async def main():

    logger.info("🚀 Pepe Music Bot started")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
