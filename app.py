import logging
from pyrogram import Client

# config
from config import API_ID, API_HASH, BOT_TOKEN

# handlers (ALL FEATURES)
from handlers.start import start_handler
from handlers.tag import tag_handler
from handlers.broadcast import broadcast_handler
from handlers.stats import stats_handler
from handlers.stop_resume import stop_resume_handler
from handlers.collect import collect_handler

# ---------------- LOGGING ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":"%(message)s"}'
)

logger = logging.getLogger(__name__)
logger.info("Bot starting...")

# ---------------- BOT INIT ---------------- #
app = Client(
    name="tagbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=8
)

# ---------------- REGISTER HANDLERS ---------------- #
start_handler(app)          # /start
tag_handler(app)            # /tagall /entag /hitag /jtag /admin /all
broadcast_handler(app)      # /broadcast
stats_handler(app)          # /stats
stop_resume_handler(app)    # /stop /resume
collect_handler(app)        # collect users & groups

# ---------------- RUN ---------------- #
if __name__ == "__main__":
    app.run()
