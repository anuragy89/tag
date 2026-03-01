from pyrogram import filters
from database import count_users, count_groups
from config import OWNER_ID

def register(app):

    @app.on_message(filters.command("stats") & filters.user(OWNER_ID))
    async def stats(_, m):
        user_count = await count_users()
        group_count = await count_groups()

        text = (
            "📊 **Bot Statistics**\n\n"
            f"👤 Users started bot: **{user_count}**\n"
            f"👥 Groups added: **{group_count}**\n\n"
            "🤖 Status: **Running Smoothly** ✅"
        )

        await m.reply(text)
