import os
import asyncio
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message

# ================== CONFIG ==================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))  # Private group ID (for cache)

DOWNLOAD_PATH = "downloads/"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# ================== BOT ==================
app = Client(
    "VideoDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================== START ==================
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "👋 Hello Bro!\n\n"
        "Send me any video link.\n"
        "I will download & send video directly 😎"
    )

# ================== DOWNLOAD FUNCTION ==================
async def download_video(url, msg):
    try:
        await msg.edit("⏳ Downloading...")

        ydl_opts = {
            "format": "best",
            "outtmpl": f"{DOWNLOAD_PATH}%(title)s.%(ext)s",
            "noplaylist": True,
            "writethumbnail": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            thumb = None

            # Thumbnail check
            thumb_path = file_path.rsplit(".", 1)[0] + ".jpg"
            if os.path.exists(thumb_path):
                thumb = thumb_path

        await msg.edit("📤 Uploading...")

        sent = await app.send_video(
            chat_id=LOG_CHANNEL,
            video=file_path,
            thumb=thumb,
            caption=f"Cached Video\n\n{url}"
        )

        await app.send_video(
            chat_id=msg.chat.id,
            video=sent.video.file_id,
            caption="✅ Here is your video!"
        )

        await msg.delete()

        # Auto delete local file
        os.remove(file_path)
        if thumb and os.path.exists(thumb):
            os.remove(thumb)

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")

# ================== LINK HANDLER ==================
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(_, message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        return

    msg = await message.reply_text("🔍 Checking...")

    # Check cache
    async for m in app.get_chat_history(LOG_CHANNEL):
        if m.caption and url in m.caption:
            await msg.edit("⚡ Found in Cache! Sending...")
            await message.reply_video(
                m.video.file_id,
                caption="⚡ From Cache!"
            )
            await msg.delete()
            return

    await download_video(url, msg)

# ================== RUN ==================
app.run()
