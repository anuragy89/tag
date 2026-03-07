"""
handlers/control.py – /stop, /pause, /resume commands.
Admins control their own group; owner can stop any group.
"""

import logging
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import admin_only, tag_manager

log = logging.getLogger(__name__)


@admin_only
async def cmd_stop(client: Client, message: Message):
    chat_id = message.chat.id
    if tag_manager.stop(chat_id):
        await message.reply_text(
            "🛑 **Tagging stopped!**\n\nAll ongoing tagging has been cancelled. ✅",
            parse_mode="markdown"
        )
    else:
        await message.reply_text(
            "ℹ️ No active tagging session to stop.",
            parse_mode="markdown"
        )


@admin_only
async def cmd_pause(client: Client, message: Message):
    chat_id = message.chat.id
    if tag_manager.pause(chat_id):
        await message.reply_text(
            "⏸️ **Tagging paused!**\n\nUse /resume to continue where we left off.",
            parse_mode="markdown"
        )
    else:
        await message.reply_text(
            "ℹ️ No running tagging session to pause.\n"
            "_Session may already be paused or stopped._",
            parse_mode="markdown"
        )


@admin_only
async def cmd_resume(client: Client, message: Message):
    chat_id = message.chat.id
    if tag_manager.resume(chat_id):
        await message.reply_text(
            "▶️ **Tagging resumed!**\n\nContinuing from where we left off… 🚀",
            parse_mode="markdown"
        )
    else:
        await message.reply_text(
            "ℹ️ Nothing to resume.\n"
            "_Start a tagging command first!_",
            parse_mode="markdown"
        )
