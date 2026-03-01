from pyrogram import Client
from config import *
from handlers import tagging, stop_resume, start, broadcast, collect, stats

app = Client(
    "tagbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

start.register(app)
broadcast.register(app)
collect.register(app)
tagging.register(app)
stop_resume.register(app)
stats.register(app)

app.run()
