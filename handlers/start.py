from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def register(app):

    @app.on_message(filters.command("start") & filters.private)
    async def start(_, m):
        text = (
            "👋 **Hey Welcome!**\n\n"
            "🤖 I’m a *Smart Tagging Bot*\n"
            "✨ Human-like tags\n"
            "🔥 Hindi | English | Hinglish\n\n"
            "➕ Add me to your group & enjoy 😄"
        )

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me", url="https://t.me/YourBotUsername?startgroup=true")],
            [InlineKeyboardButton("📢 Updates", url="https://t.me/YourChannel")]
        ])

        await m.reply(text, reply_markup=buttons)
