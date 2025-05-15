import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import os
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Validate configuration
Config.validate_config()

# Initialize the bot
app = Client(
    "streamup_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.private & (filters.video | filters.document))
async def upload_file(client: Client, message: Message):
    msg = await message.reply_text("Downloading file...")
    path = None

    try:
        logger.info(f"Processing file from user {message.from_user.id}")
        media = message.video or message.document
        file_name = media.file_name or f"{media.file_id}.mp4"
        path = await client.download_media(message, file_name)

        await msg.edit("Uploading to StreamUP...")

        with open(path, "rb") as f:
            files = {"videoFile": (file_name, f, "video/mp4")}
            headers = {
                "Origin": "https://streamup.cc",
                "Referer": "https://streamup.cc/",
                "User-Agent": "Mozilla/5.0"
            }
            response = requests.post(
                "https://e1.beymtv.com/upload.php?id=1254",
                files=files,
                headers=headers
            )

        if response.ok:
            # Now fetch the latest uploaded video link
            api_url = f"https://api.streamup.cc/v1/data?api_key={Config.STREAMUP_API_KEY}&page=1"
            api_response = requests.get(api_url)
            data = api_response.json()

            if "videos" in data and len(data["videos"]) > 0:
                latest_video = data["videos"][0]
                filecode = latest_video.get("Filecode")
                streamup_link = f"https://streamup.ws/{filecode}"
                await msg.edit(f"Upload successful!\n{streamup_link}")
            else:
                await msg.edit("Upload successful, but no link found in API data.")

        else:
            await msg.edit(f"Upload failed: {response.text}")

    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message)
        await msg.edit(error_message)

    finally:
        if 'path' in locals() and os.path.exists(path):
            os.remove(path)

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply_text("Send a video or document. I’ll upload it to StreamUP and send back the link.")

if __name__ == "__main__":
    logger.info("Bot is starting...")
    try:
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
