from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import add_user
from config import BOT_USERNAME, UPDATE_CHANNEL


def start_handler(app):

    @app.on_message(filters.private & filters.command("start"))
    async def start_cmd(_, message):
        await add_user(message.from_user.id)

        text = (
            "👋 **Welcome!**\n\n"
            "🤖 Smart Tagging Bot\n"
            "🔥 Tag members & admins easily\n\n"
            "👇 Use buttons below"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates Channel", url=UPDATE_CHANNEL)]
        ])

        await message.reply_text(text, reply_markup=keyboard)
