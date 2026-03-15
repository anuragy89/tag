"""
handlers/start.py – /start, /help, callbacks, group join.

All messages use HTML parse mode + te() for animated premium emoji.
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
from utils.botapi import send_styled, edit_styled, _btn, te

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  Keyboards  (colored + premium emoji icons via Bot API 9.4)
# ══════════════════════════════════════════════════════════════════════════════

def _styled_main_kb() -> list:
    return [
        [_btn("➕ Add to Your Group", "add",
              url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
              style="danger")],
        [_btn("📋 Help ", "help",
              callback_data="cb_help", style="primary"),
         _btn("📢 Updates", "updates",
              url=Config.UPDATES_CHANNEL, style="primary")],
        [_btn("💬 Support", "support",
              url=Config.SUPPORT_GROUP, style="success")],
    ]

def _styled_back_kb() -> list:
    return [[_btn("🔙 Back", "back",
                  callback_data="cb_back", style="primary")]]

def _styled_group_kb() -> list:
    return [
        [_btn("➕ Add to Your Group", "add",
              url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
              style="danger")],
        [_btn("📋 Help ", "help",
              callback_data="cb_help", style="primary"),
         _btn("📢 Updates", "updates",
              url=Config.UPDATES_CHANNEL, style="primary")],
        [_btn("💬 Support", "support",
              url=Config.SUPPORT_GROUP, style="success")],
    ]

# ── Plain fallback keyboards (if HTTP call fails) ─────────────────────────────

def _fallback_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Your Group",
                              url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📋 Help ", callback_data="cb_help"),
         InlineKeyboardButton("📢 Updates", url=Config.UPDATES_CHANNEL)],
        [InlineKeyboardButton("💬 Support", url=Config.SUPPORT_GROUP)],
    ])

def _fallback_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back", callback_data="cb_back")
    ]])


# ══════════════════════════════════════════════════════════════════════════════
#  Message templates  (HTML + te() for premium emoji)
# ══════════════════════════════════════════════════════════════════════════════

def start_text(name: str) -> str:
    return (
        f"{te('wave','👋')} Hey <b>{name}</b>! Welcome!\n\n"
        f"I'm the most powerful <b>Tagging Bot</b> on Telegram "
        f"{te('rocket','🚀')}\n\n"
        f"{te('star','🌟')} <b>8 Tagging Styles</b>\n"
        f"   ├ Hindi • English • Hinglish\n"
        f"   ├ Good Morning &amp; Good Night tags\n"
        f"   ├ Joke tags &amp; General tags\n"
        f"   ├ Tag all members OR only admins\n"
        f"   └ Custom message support!\n\n"
        f"{te('lightning','⚡')} <b>Smart Controls</b>\n"
        f"   ├ /stop • /pause • /resume\n"
        f"   └ Only admins can control tagging\n\n"
        f"{te('shield','🛡️')} <b>Spam Protection</b>\n"
        f"   └ Built-in flood-wait guard\n\n"
        f"{te('chart','📊')} <b>Owner Tools</b>\n"
       
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Pick an option below to get started! {te('sparkle','✨')}"
    )


def help_text() -> str:
    return (
        f"{te('chart','📋')} <b>ALL COMMANDS</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{te('tag','🏷️')} <b>Tagging Commands</b> <i>(Admins only)</i>\n\n"
        f"<code>/hitag</code>  — Tag all members in <b>Hindi</b> 🇮🇳\n"
        f"<code>/entag</code>  — Tag all members in <b>English</b> 🇬🇧\n"
        f"<code>/gmtag</code>  — <b>Good Morning</b> tag (Hinglish) 🌅\n"
        f"<code>/gntag</code>  — <b>Good Night</b> tag (Hinglish) 🌙\n"
        f"<code>/tagall</code> — General tag, all members {te('fire','🔥')}\n"
        f"<code>/jtag</code>   — <b>Joke</b> tag, all members 😂\n\n"
        f"{te('target','🎯')} <b>Mention Commands</b>\n\n"
        f"<code>/admin</code> or <code>@admin</code> — Tag <b>only admins</b> (6 per msg)\n"
        f"<code>/all</code>   or <code>@all</code>   — Tag <b>all members</b> (6 per msg)\n"
        f"   <i>Supports custom messages: /admin plz join vc</i>\n\n"
        f"{te('pause','⏸️')} <b>Control Commands</b> <i>(Admins only)</i>\n\n"
        f"<code>/stop</code>   — {te('cross','❌')} Stop ongoing tagging\n"
        f"<code>/pause</code>  — ⏸️ Pause tagging temporarily\n"
        f"<code>/resume</code> — ▶️ Resume paused tagging\n\n"
        f"{te('crown','👑')} <b>Owner Commands</b>\n\n"
        f"<code>/broadcast &lt;msg&gt;</code> — Broadcast to all users &amp; groups\n"
        f"<code>/stats</code> — View bot usage statistics\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{te('bulb','💡')} <b>Tips:</b>\n"
        f"• All tagging cmds auto-stop when complete\n"
        f"• Use /stop anytime to cancel tagging\n"
        f"• Add me as admin for best performance!"
    )


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
    text = start_text(name)
    # Always use Bot API HTTP so HTML + tg-emoji renders correctly.
    # Kurigram's send_message uses the client's default parse mode (Markdown)
    # which does NOT render <tg-emoji> tags — must use HTTP for this.
    result = await send_styled(message.chat.id, text, _styled_main_kb())
    if not result:
        # Fallback: plain Pyrogram send with HTML parse mode forced
        from pyrogram import enums
        await message.reply_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_fallback_main_kb(),
        )


async def cmd_help(client: Client, message: Message) -> None:
    text = help_text()
    result = await send_styled(message.chat.id, text, _styled_back_kb())
    if not result:
        from pyrogram import enums
        await message.reply_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=_fallback_back_kb(),
        )


async def callback_handler(client: Client, query: CallbackQuery) -> None:
    data    = query.data
    chat_id = query.message.chat.id
    msg_id  = query.message.id
    from pyrogram import enums

    if data == "cb_help":
        text = help_text()
        result = await edit_styled(chat_id, msg_id, text, _styled_back_kb())
        if not result:
            await query.message.edit_text(
                text, parse_mode=enums.ParseMode.HTML,
                reply_markup=_fallback_back_kb(),
            )

    elif data == "cb_back":
        name = query.from_user.first_name if query.from_user else "Friend"
        text = start_text(name)
        result = await edit_styled(chat_id, msg_id, text, _styled_main_kb())
        if not result:
            await query.message.edit_text(
                text, parse_mode=enums.ParseMode.HTML,
                reply_markup=_fallback_main_kb(),
            )

    await query.answer()


async def on_new_chat_member(client: Client, message: Message) -> None:
    bot_id = client.me.id if client.me else None
    if bot_id is None:
        try:
            bot_id = (await client.get_me()).id
        except Exception:
            return

    if not any(m.id == bot_id for m in (message.new_chat_members or [])):
        return

    chat = message.chat
    try:
        await upsert_group(chat.id, chat.title, getattr(chat, "username", None))
    except Exception as e:
        log.warning("upsert_group failed for %s: %s", chat.id, e)

    text = GROUP_JOIN_MSG(chat.title or "this group")
    result = await send_styled(chat.id, text, _styled_group_kb())
    if not result:
        from pyrogram import enums
        try:
            await client.send_message(
                chat.id, text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add to Your Group",
                                         url=f"https://t.me/{Config.BOT_USERNAME}?startgroup=true")],
                    [InlineKeyboardButton("📋 Help ", callback_data="cb_help"),
                     InlineKeyboardButton("📢 Updates", url=Config.UPDATES_CHANNEL)],
                    [InlineKeyboardButton("💬 Support", url=Config.SUPPORT_GROUP)],
                ])
            )
        except Exception as e:
            log.warning("Could not send group join msg to %s: %s", chat.id, e)
    else:
        log.info("Sent styled group join msg to %s (%s)", chat.title, chat.id)
