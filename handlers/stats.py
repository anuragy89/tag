from pyrogram import filters
from config import OWNER_ID
from database import count_users, count_groups


def stats_handler(app):

    @app.on_message(filters.command("stats"))
    async def stats_cmd(client, message):

        if message.from_user.id != OWNER_ID:
            return await message.reply_text("❌ Only owner can view stats.")

        users = await count_users()
        groups = await count_groups()

        await message.reply_text(
            "📊 **Bot Statistics**\n\n"
            f"👤 Users: `{users}`\n"
            f"👥 Groups: `{groups}`"
        )
