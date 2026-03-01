from pyrogram import Client
from config import *
from handlers import start, collect, broadcast, tagging, stop_resume, stats
from utils.logger import setup_logger

logger = setup_logger()
logger.info("Bot starting...")

app = Client(
    "tagbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

start.register(app)
collect.register(app)
broadcast.register(app)
tagging.register(app)
stop_resume.register(app)
stats.register(app)

logger.info("Handlers loaded. Bot is running.")
app.run()
