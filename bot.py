import os
import json
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo

# ================= CONFIG =================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_PATH = "downloads/"
CACHE_FILE = "cache.json"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ================= CACHE =================
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

# ================= BOT =================
app = Client(
    "VideoDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= START =================
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "👋 Send any video or post link.\n"
        "Supports Instagram, YouTube, Pinterest & more 🚀"
    )

# ================= DOWNLOAD =================
async def download_media(url, msg, user_id):
    try:
        await msg.edit("⏳ Downloading...")

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": f"{DOWNLOAD_PATH}%(id)s_%(title)s.%(ext)s",
            "noplaylist": False,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        files = []

        # If playlist / carousel
        if "entries" in info:
            for entry in info["entries"]:
                if entry:
                    filename = ydl.prepare_filename(entry)
                    if os.path.exists(filename):
                        files.append(filename)
        else:
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                files.append(filename)

        if not files:
            await msg.edit("❌ No downloadable media found.")
            return

        await msg.edit("📤 Uploading...")

        media_group = []

        for file_path in files:
            ext = file_path.split(".")[-1].lower()

            if ext in ["mp4", "mkv", "webm"]:
                media_group.append(
                    InputMediaVideo(media=file_path)
                )
            else:
                media_group.append(
                    InputMediaPhoto(media=file_path)
                )

        # If multiple files send as album
        if len(media_group) > 1:
            await app.send_media_group(
                chat_id=user_id,
                media=media_group
            )
        else:
            single = media_group[0]
            if isinstance(single, InputMediaVideo):
                await app.send_video(user_id, single.media)
            else:
                await app.send_photo(user_id, single.media)

        # Cleanup files
        for f in files:
            if os.path.exists(f):
                os.remove(f)

        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")

# ================= HANDLE LINK =================
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(_, message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        return

    msg = await message.reply_text("🔍 Checking...")

    await download_media(url, msg, message.chat.id)

# ================= RUN =================
app.run()
