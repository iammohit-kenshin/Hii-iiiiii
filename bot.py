import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from database import get_cached, save_cache
import yt_dlp

app = Client(
    "video_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# Upload Progress
async def progress(current, total, message, start_time):
    now = time.time()
    diff = now - start_time
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0

    bar = "█" * int(percentage / 5)

    try:
        await message.edit_text(
            f"📤 Uploading...\n"
            f"[{bar}]\n"
            f"{percentage:.2f}%\n"
            f"Speed: {speed/1024/1024:.2f} MB/s"
        )
    except:
        pass


@app.on_message(filters.command("start"))
async def start(client, message):
    if len(message.command) > 1:
        url = message.command[1]
        await handle_download(client, message, url)
    else:
        await message.reply_text(
            "🔥 Legal Video Downloader Bot Ready!\n\n"
            "Send me a public video link."
        )


@app.on_message(filters.text & ~filters.command(["start"]))
async def normal_handler(client, message):
    url = message.text.strip()
    await handle_download(client, message, url)


async def handle_download(client, message: Message, url: str):

    status = await message.reply_text("🔍 Checking cache...")

    # Check Cache
    cached = get_cached(url)
    if cached:
        await status.edit("⚡ Sending from cache...")
        await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=STORAGE_GROUP_ID,
            message_id=int(cached)
        )
        return

    await status.edit("⬇ Extracting & Downloading...")

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": f"{DOWNLOAD_PATH}%(title)s.%(ext)s",
        "noplaylist": True,
        "writethumbnail": True,
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            base = os.path.splitext(filename)[0]
            thumbnail = None
            for ext in ["jpg", "png", "webp"]:
                if os.path.exists(base + "." + ext):
                    thumbnail = base + "." + ext
                    break

    except Exception as e:
        await status.edit(f"❌ Error:\n{str(e)}")
        return

    await status.edit("📤 Uploading to Telegram...")

    start_time = time.time()

    sent = await client.send_video(
        chat_id=message.chat.id,
        video=filename,
        thumb=thumbnail,
        progress=progress,
        progress_args=(status, start_time)
    )

    # Save in Storage Group
    storage_msg = await client.copy_message(
        chat_id=STORAGE_GROUP_ID,
        from_chat_id=message.chat.id,
        message_id=sent.id
    )

    save_cache(url, storage_msg.id)

    # Auto Delete
    try:
        os.remove(filename)
        if thumbnail and os.path.exists(thumbnail):
            os.remove(thumbnail)
    except:
        pass

    await status.edit("✅ Done & Cached Successfully!")


app.run()
