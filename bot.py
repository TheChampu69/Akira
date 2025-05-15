import logging
import asyncio
import signal
from aiohttp import web
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

# Create web app for health checks
web_app = web.Application()

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

# Health check endpoint
async def health_check(request):
    return web.Response(text="OK", status=200)

web_app.router.add_get("/health", health_check)

async def run_web_server():
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logger.info("Health check server started on port 8000")

async def run_bot():
    await app.start()
    logger.info("Bot started successfully")
    await app.idle()

async def shutdown(signal, loop):
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == "__main__":
    logger.info("Bot is starting...")
    try:
        loop = asyncio.get_event_loop()
        
        # Register signal handlers
        signals = (signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, 
                lambda s=s: asyncio.create_task(shutdown(s, loop))
            )
            
        # Start both bot and health check server
        loop.create_task(run_web_server())
        loop.create_task(run_bot())
        
        loop.run_forever()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        loop.close()
        logger.info("Successfully shutdown the bot.")
