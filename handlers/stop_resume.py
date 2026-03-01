from pyrogram import filters
from utils.state import stop, resume
from utils.helpers import is_admin

def register(app):

    @app.on_message(filters.command("stop") & filters.group)
    async def stop_cmd(_, m):
        if await is_admin(app, m.chat.id, m.from_user.id):
            stop(m.chat.id)
            await m.reply("⛔ Tagging stopped")

    @app.on_message(filters.command("resume") & filters.group)
    async def resume_cmd(_, m):
        if await is_admin(app, m.chat.id, m.from_user.id):
            resume(m.chat.id)
            await m.reply("▶️ Tagging resumed")
