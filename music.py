import asyncio
import os
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL

router = Router()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_audio(query: str) -> str:
    url = f"ytsearch1:{query}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info["entries"][0])
        return filename.rsplit(".", 1)[0] + ".mp3"


@router.message(Command("music"))
async def music_handler(message: types.Message):
    query = message.text.replace("/music", "").strip()

    if not query:
        await message.answer("Напиши: /music название трека")
        return

    await message.answer("🎧 Ищу музыку...")

    try:
        file_path = await asyncio.to_thread(download_audio, query)

        await message.answer_audio(
            FSInputFile(file_path),
            title=query
        )

        os.remove(file_path)

    except Exception as e:
        await message.answer(f"Ошибка: {e}")
