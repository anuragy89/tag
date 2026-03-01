from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import add_user
from config import UPDATE_CHANNEL, BOT_USERNAME

def start_handler(app):

    @app.on_message(filters.private & filters.command("start"))
    async def start_cmd(client, message):
        user = message.from_user
        await add_user(user.id)

        text = (
            "👋 **Hey Welcome!**\n\n"
            "🤖 I am a **Smart Tagging Bot**\n"
            "🔥 I can tag members & admins in cool styles\n\n"
            "👇 Use buttons below to get started"
        )

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates Channel", url=UPDATE_CHANNEL)]
        ])

        await message.reply_text(text, reply_markup=buttons)
