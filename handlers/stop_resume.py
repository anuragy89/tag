from pyrogram import filters
from utils.state import stop_tag, start_tag


def stop_resume_handler(app):

    @app.on_message(filters.command("stop") & filters.group)
    async def stop_cmd(client, message):
        stop_tag(message.chat.id)
        await client.send_message(
            message.chat.id,
            "🛑 **Tagging stopped**",
        )

    @app.on_message(filters.command("resume") & filters.group)
    async def resume_cmd(client, message):
        start_tag(message.chat.id)
        await client.send_message(
            message.chat.id,
            "▶️ **Tagging resumed**",
        )
