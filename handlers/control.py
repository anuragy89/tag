"""
handlers/control.py – /stop, /pause, /resume with premium emoji HTML replies.
"""

import logging
from pyrogram import Client
from pyrogram.types import Message

from utils import admin_only, tag_manager
from utils.botapi import reply_html, te

log = logging.getLogger(__name__)


@admin_only
async def cmd_stop(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    if tag_manager.stop(chat_id):
        text = (
            f"{te('stop','🛑')} <b>Tagging stopped!</b>\n\n"
            f"All ongoing tagging has been cancelled. {te('check','✅')}"
        )
    else:
        text = "ℹ️ No active tagging session to stop."
    result = await reply_html(chat_id, message.id, text)
    if not result:
        await message.reply_text(text)


@admin_only
async def cmd_pause(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    if tag_manager.pause(chat_id):
        text = (
            f"⏸️ <b>Tagging paused!</b>\n\n"
            f"Use /resume to continue where we left off."
        )
    else:
        text = (
            "ℹ️ No running tagging session to pause.\n"
            "<i>Session may already be paused or stopped.</i>"
        )
    result = await reply_html(chat_id, message.id, text)
    if not result:
        await message.reply_text(text)


@admin_only
async def cmd_resume(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    if tag_manager.resume(chat_id):
        text = (
            f"{te('play','▶️')} <b>Tagging resumed!</b>\n\n"
            f"Continuing from where we left off… {te('rocket','🚀')}"
        )
    else:
        text = (
            "ℹ️ Nothing to resume.\n"
            "<i>Start a tagging command first!</i>"
        )
    result = await reply_html(chat_id, message.id, text)
    if not result:
        await message.reply_text(text)
