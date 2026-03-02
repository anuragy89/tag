from pyrogram import filters
from config import OWNER_ID
from state import stop, resume


def stop_resume_handler(app):

    @app.on_message(filters.command("stop"))
    async def stop_cmd(client, message):
        if message.from_user.id != OWNER_ID:
            return

        stop()
        await message.reply_text("⛔ Bot stopped.")


    @app.on_message(filters.command("resume"))
    async def resume_cmd(client, message):
        if message.from_user.id != OWNER_ID:
            return

        resume()
        await message.reply_text("▶️ Bot resumed.")
