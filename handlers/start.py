"""
handlers/start.py – /start, /help, callbacks, group join.

Button colors use Bot API 9.4 style field (danger=red, primary=blue, success=green)
sent via direct HTTP (utils/botapi.py) because Kurigram's MTProto layer doesn't
expose these fields in its high-level types yet.

icon_custom_emoji_id on buttons works only if the bot owner has Telegram Premium.
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
from utils.botapi import send_styled, edit_styled, _btn

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  Keyboard definitions
#  Two versions of every keyboard:
#   • _styled_*  → list-of-rows dicts   → sent via botapi.py  (colored buttons)
#   • _fallback_*→ InlineKeyboardMarkup → used if styled send fails
# ══════════════════════════════════════════════════════════════════════════════

def _styled_main_kb() -> list:
    """Main /start keyboard with colored + premium emoji buttons."""
    return [
        [
            _btn("➕ Add to Your Group", "add",
                 url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
                 style="danger"),
        ],
        [
            _btn("📋 Help & Commands", "help",
                 callback_data="cb_help", style="primary"),
            _btn("📢 Updates", "updates",
                 url=Config.UPDATES_CHANNEL, style="primary"),
        ],
        [
            _btn("💬 Support", "support",
                 url=Config.SUPPORT_GROUP, style="success"),
        ],
    ]


def _styled_back_kb() -> list:
    return [[_btn("🔙 Back", "back", callback_data="cb_back", style="primary")]]


def _styled_group_kb() -> list:
    """Welcome keyboard shown when bot is added to a group."""
    return [
        [
            _btn("➕ Add to Your Group", "add",
                 url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
                 style="danger"),
        ],
        [
            _btn("📋 Help & Commands", "help",
                 callback_data="cb_help", style="primary"),
            _btn("📢 Updates", "updates",
                 url=Config.UPDATES_CHANNEL, style="primary"),
        ],
        [
            _btn("💬 Support", "support",
                 url=Config.SUPPORT_GROUP, style="success"),
        ],
    ]


# ── Plain InlineKeyboardMarkup fallbacks (used if aiohttp call fails) ─────────

def _fallback_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Your Group",
                              url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📋 Help & Commands", callback_data="cb_help"),
         InlineKeyboardButton("📢 Updates",         url=Config.UPDATES_CHANNEL)],
        [InlineKeyboardButton("💬 Support",          url=Config.SUPPORT_GROUP)],
    ])


def _fallback_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="cb_back")]])


# ══════════════════════════════════════════════════════════════════════════════
#  Message templates
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
#  Handlers
# ══════════════════════════════════════════════════════════════════════════════

async def cmd_start(client: Client, message: Message) -> None:
    if message.from_user:
        await upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    name = message.from_user.first_name if message.from_user else "Friend"
    text = START_TEXT.format(name=name)

    # Try styled (colored) buttons first; fall back to plain if aiohttp fails
    result = await send_styled(message.chat.id, text, _styled_main_kb())
    if not result:
        await message.reply_text(text, reply_markup=_fallback_main_kb())


async def cmd_help(client: Client, message: Message) -> None:
    result = await send_styled(message.chat.id, HELP_TEXT, _styled_back_kb())
    if not result:
        await message.reply_text(HELP_TEXT, reply_markup=_fallback_back_kb())


async def callback_handler(client: Client, query: CallbackQuery) -> None:
    data    = query.data
    chat_id = query.message.chat.id
    msg_id  = query.message.id

    if data == "cb_help":
        result = await edit_styled(chat_id, msg_id, HELP_TEXT, _styled_back_kb())
        if not result:
            await query.message.edit_text(HELP_TEXT, reply_markup=_fallback_back_kb())

    elif data == "cb_back":
        name = query.from_user.first_name if query.from_user else "Friend"
        text = START_TEXT.format(name=name)
        result = await edit_styled(chat_id, msg_id, text, _styled_main_kb())
        if not result:
            await query.message.edit_text(text, reply_markup=_fallback_main_kb())

    await query.answer()


# ── Handler: bot added to a group ────────────────────────────────────────────

async def on_new_chat_member(client: Client, message: Message) -> None:
    # Use cached client.me — avoids a network round-trip on every join event
    bot_id = client.me.id if client.me else None
    if bot_id is None:
        try:
            bot_id = (await client.get_me()).id
        except Exception:
            return

    # Only fire when it's THIS BOT being added, not regular members
    if not any(m.id == bot_id for m in (message.new_chat_members or [])):
        return

    chat = message.chat
    try:
        await upsert_group(chat.id, chat.title, getattr(chat, "username", None))
    except Exception as e:
        log.warning("upsert_group failed for %s: %s", chat.id, e)

    text = GROUP_JOIN_MSG.format(chat_title=chat.title or "this group")

    # Try colored buttons first via Bot API HTTP
    result = await send_styled(chat.id, text, _styled_group_kb())
    if not result:
        # Fallback to Kurigram's regular send
        try:
            await client.send_message(
                chat.id,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(" Add to Your Group",
                                         url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
                    [InlineKeyboardButton(" Help ", callback_data="cb_help"),
                     InlineKeyboardButton(" Updates", url=Config.UPDATES_CHANNEL)],
                    [InlineKeyboardButton(" Support", url=Config.SUPPORT_GROUP)],
                ])
            )
        except Exception as e:
            log.warning("Could not send group join msg to %s: %s", chat.id, e)
    else:
        log.info("Sent styled group join msg to %s (%s)", chat.title, chat.id)
