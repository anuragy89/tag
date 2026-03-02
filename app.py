# app.py

import sys
import os
import logging

# 🔥 ADD PROJECT ROOT TO PYTHONPATH (FIXES utils import)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN

# handlers (absolute imports now WORK)
from handlers.start import start_handler
from handlers.tagging import tagging_handler
from handlers.stop_resume import stop_resume_handler
from handlers.broadcast import broadcast_handler
from handlers.stats import stats_handler
from handlers.collect import collect_handler


logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Bot starting...")

    app = Client(
        "mention-bot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True
    )

    start_handler(app)
    tagging_handler(app)
    stop_resume_handler(app)
    broadcast_handler(app)
    stats_handler(app)
    collect_handler(app)

    logger.info("All handlers loaded")

    app.run()


if __name__ == "__main__":
    main()
