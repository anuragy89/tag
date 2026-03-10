"""
handlers/start.py – /start, /help, inline button callbacks, group join handler.
parse_mode is set globally on the Client in bot.py — no per-call arg needed.
"""

import logging

from pyrogram import Client
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from config import Config
from database import upsert_user, upsert_group
from utils import GROUP_JOIN_MSG

log = logging.getLogger(__name__)


# ── Keyboard helpers ──────────────────────────────────────────────────────────

def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ Add Me To Your Group",
                url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
            ),
        ],
        [
            InlineKeyboardButton("📋 Help & Commands", callback_data="cb_help"),
            InlineKeyboardButton("📢 Updates", url=Config.UPDATES_CHANNEL),
        ],
        [
            InlineKeyboardButton("💬 Support", url=Config.SUPPORT_GROUP),
        ],
    ])


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back", callback_data="cb_back"),
    ]])


# ── Message templates ─────────────────────────────────────────────────────────

START_TEXT = """

👋 Hey **{name}**! Welcome!

I'm the most powerful **Tagging Bot** on Telegram 🚀
Here's what I can do for you:

🌟 **8 Tagging Styles**
   ├ Hindi • English • Hinglish
   ├ Good Morning & Good Night tags
   ├ Joke tags & General tags
   ├ Tag all members OR only admins
   └ Custom message support!

⚡ **Smart Controls**
   ├ /stop • /pause • /resume
   └ Only admins can control tagging

🛡️ **Spam Protection**
   └ Built-in flood-wait guard

📊 **Owner Tools**
   └ /broadcast & /stats

━━━━━━━━━━━━━━━━━━━━━━━
Pick an option below to get started! 👇
"""

HELP_TEXT = """
📋 **ALL COMMANDS**
━━━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ **Tagging Commands** _(Admins only)_

`/hitag`  — Tag all members in **Hindi** 🇮🇳
`/entag`  — Tag all members in **English** 🇬🇧
`/gmtag`  — **Good Morning** tag (Hinglish) 🌅
`/gntag`  — **Good Night** tag (Hinglish) 🌙
`/tagall` — General tag, all members (Hinglish) 🔥
`/jtag`   — **Joke** tag, all members (Hinglish) 😂

🎯 **Mention Commands**

`/admin` or `@admin` — Tag **only admins** (6 per msg)
`/all`   or `@all`   — Tag **all members** (6 per msg)
  _Supports custom messages: `/admin plz join vc`_

⏸️ **Control Commands** _(Admins only)_

`/stop`   — ❌ Stop ongoing tagging
`/pause`  — ⏸️ Pause tagging temporarily
`/resume` — ▶️ Resume paused tagging

👑 **Owner Commands**

`/broadcast <msg>` — Broadcast to all users & groups
`/stats` — View bot usage statistics

━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 **Tips:**
• All tagging cmds auto-stop when complete
• Use /stop anytime to cancel tagging
• Add me as admin for best performance!
"""


# ── Handler: /start ───────────────────────────────────────────────────────────

async def cmd_start(client: Client, message: Message) -> None:
    if message.from_user:
        await upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    name = message.from_user.first_name if message.from_user else "Friend"
    await message.reply_text(
        START_TEXT.format(name=name),
        reply_markup=main_keyboard(),
    )


# ── Handler: /help ────────────────────────────────────────────────────────────

async def cmd_help(client: Client, message: Message) -> None:
    await message.reply_text(
        HELP_TEXT,
        reply_markup=back_keyboard(),
    )


# ── Callback: inline keyboard buttons ────────────────────────────────────────

async def callback_handler(client: Client, query: CallbackQuery) -> None:
    data = query.data

    if data == "cb_help":
        await query.message.edit_text(
            HELP_TEXT,
            reply_markup=back_keyboard(),
        )
    elif data == "cb_back":
        name = query.from_user.first_name if query.from_user else "Friend"
        await query.message.edit_text(
            START_TEXT.format(name=name),
            reply_markup=main_keyboard(),
        )

    await query.answer()


# ── Handler: bot added to a group ────────────────────────────────────────────

async def on_new_chat_member(client: Client, message: Message) -> None:
    bot_me = await client.get_me()
    for member in message.new_chat_members:
        if member.id == bot_me.id:
            chat = message.chat
            await upsert_group(
                chat.id,
                chat.title,
                getattr(chat, "username", None),
            )
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "➕ Add to Your Group",
                        url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
                    ),
                ],
                [
                    InlineKeyboardButton("📋 Help & Commands", callback_data="cb_help"),
                    InlineKeyboardButton("📢 Updates", url=Config.UPDATES_CHANNEL),
                ],
            ])
            try:
                await client.send_message(
                    chat.id,
                    GROUP_JOIN_MSG.format(chat_title=chat.title or "this group"),
                    reply_markup=keyboard,
                )
            except Exception as e:
                log.warning("Could not send group join msg to %s: %s", chat.id, e)
            break
