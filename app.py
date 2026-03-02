import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

from handlers.start import start_handler
from handlers.tag import tag_handler
from handlers.broadcast import broadcast_handler

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":"%(message)s"}'
)

logger = logging.getLogger(__name__)
logger.info("Bot starting...")

app = Client(
    "tagbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# register handlers
start_handler(app)
tag_handler(app)
broadcast_handler(app)

app.run()
