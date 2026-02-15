import os
import json
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message

# ============== CONFIG ==============
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

DOWNLOAD_PATH = "downloads/"
CACHE_FILE = "cache.json"

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Load cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)
else:
    cache = {}

# ============== BOT ==============
app = Client(
    "VideoDownloaderBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ============== START ==============
@app.on_message(filters.command("start"))
async def start(_, message: Message):
    await message.reply_text(
        "👋 Send any video link.\nI will download it for you 😎"
    )

# ============== DOWNLOAD ==============
async def download_video(url, msg, user_id):
    try:
        await msg.edit("⏳ Downloading...")

        ydl_opts = {
            "format": "best",
            "outtmpl": f"{DOWNLOAD_PATH}%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await msg.edit("📤 Uploading...")

        sent = await app.send_video(
            chat_id=user_id,
            video=file_path,
            caption="✅ Here is your video!"
        )

        # Save in cache
        cache[url] = sent.video.file_id
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f)

        os.remove(file_path)
        await msg.delete()

    except Exception as e:
        await msg.edit(f"❌ Error:\n{str(e)}")

# ============== HANDLE LINK ==============
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_link(_, message: Message):
    url = message.text.strip()

    if not url.startswith("http"):
        return

    msg = await message.reply_text("🔍 Checking...")

    # Check cache
    if url in cache:
        await msg.edit("⚡ From Cache!")
        await message.reply_video(
            cache[url],
            caption="⚡ Cached Video!"
        )
        await msg.delete()
        return

    await download_video(url, msg, message.chat.id)

# ============== RUN ==============
app.run()
