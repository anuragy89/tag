"""
handlers/vc_notify.py – Voice Chat join notifier with auto-delete.

Sends this exact message when someone joins a VC:

    🎙️ ◈ 𝗡𝗲𝘄 𝗩𝗖 𝗝𝗼𝗶𝗻

    👤 {mention}
    🆔 {uid}

    🤍 Welcome to the VC

    [ ➕ Add Me to Your Group ]   ← blue button

Message auto-deletes after 60 seconds.

Two detection paths:
  Path A – voice_chat_members_invited service message (invited / link join)
  Path B – raw UpdateGroupCallParticipants MTProto update (self-join)
"""

import asyncio
import logging

from pyrogram import Client, filters, raw
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from pyrogram.types import Message

from config import Config
from utils.botapi import te, _call

log = logging.getLogger(__name__)


# ── Auto-delete helper ────────────────────────────────────────────────────────

async def _delete_after(chat_id: int, message_id: int, delay: int = 60) -> None:
    """Wait *delay* seconds then delete the notification via Bot API."""
    await asyncio.sleep(delay)
    try:
        await _call("deleteMessage", {
            "chat_id":    chat_id,
            "message_id": message_id,
        })
        log.debug("Auto-deleted VC notify msg %s in chat %s", message_id, chat_id)
    except Exception as e:
        log.warning("Could not auto-delete VC notify msg %s: %s", message_id, e)


# ── Send notification + schedule deletion ────────────────────────────────────

async def _notify_vc_join(chat_id: int, user_id: int, first_name: str) -> None:
    """
    Sends the VC join notification with exact requested format +
    a blue 'Add Me' inline button. Auto-deletes after 60 seconds.
    """
    # Clickable mention link for the user
    mention_link = f'<a href="tg://user?id={user_id}">{first_name}</a>'

    text = (
        f"{te('mic', '🎙️')} ◈ <b>𝗡𝗲𝘄 𝗩𝗖 𝗝𝗼𝗶𝗻</b>\n\n"
        f"👤 {mention_link}\n"
        f"🆔 <code>{user_id}</code>\n\n"
        f"{te('heart', '🤍')} <b>Welcome to the VC</b>"
    )

    # Blue button (style=primary → blue in Bot API 9.4)
    keyboard = {
        "inline_keyboard": [[{
            "text":  "➕ Add Me to Your Group",
            "url":   f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
            "style": "primary",
        }]]
    }

    result = await _call("sendMessage", {
        "chat_id":                  chat_id,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
        "reply_markup":             keyboard,
    })

    if result and isinstance(result, dict):
        msg_id = result.get("message_id")
        if msg_id:
            asyncio.create_task(_delete_after(chat_id, msg_id, delay=60))
    else:
        log.warning("Failed to send VC notify to chat %s", chat_id)


# ══════════════════════════════════════════════════════════════════════════════
#  PATH A – Service message: voice_chat_members_invited
#  Fires when Telegram sends the "User joined voice chat" service message.
# ══════════════════════════════════════════════════════════════════════════════

async def on_vc_members_invited(client: Client, message: Message) -> None:
    users   = message.new_chat_members or []
    chat_id = message.chat.id

    for user in users:
        if not user or user.is_bot:
            continue
        name = user.first_name or "User"
        log.info("VC join (invited): %s (%s) in chat %s", name, user.id, chat_id)
        asyncio.create_task(_notify_vc_join(chat_id, user.id, name))


# ══════════════════════════════════════════════════════════════════════════════
#  PATH B – Raw update: UpdateGroupCallParticipants
#  Fires for SELF-JOIN (user tapped "Join VC" themselves).
# ══════════════════════════════════════════════════════════════════════════════

async def on_raw_vc_update(
    client: Client,
    update,
    users: dict,
    chats: dict,
) -> None:
    if not isinstance(update, raw.types.UpdateGroupCallParticipants):
        return

    for participant in update.participants:
        if not getattr(participant, "just_joined", False):
            continue

        peer = participant.peer
        user_id = None

        if isinstance(peer, raw.types.PeerUser):
            user_id = peer.user_id
        elif isinstance(peer, raw.types.PeerChannel):
            continue  # anonymous admin / channel — skip

        if user_id is None:
            continue

        user_obj   = users.get(user_id)
        first_name = getattr(user_obj, "first_name", None) or "User" if user_obj else "User"
        is_bot     = getattr(user_obj, "bot", False) if user_obj else False

        if is_bot:
            continue

        # Resolve chat_id from the chats dict (first entry — group calls are per-chat)
        chat_id = None
        for cid in chats:
            raw_id = int(str(cid).lstrip("-"))
            chat_id = -raw_id  # supergroups are negative
            break

        if chat_id is None:
            log.warning("Could not resolve chat_id for VC join by user %s", user_id)
            return

        log.info("VC join (self): %s (%s) in chat %s", first_name, user_id, chat_id)
        asyncio.create_task(_notify_vc_join(chat_id, user_id, first_name))


# ══════════════════════════════════════════════════════════════════════════════
#  Registration helper — call this from bot.py
# ══════════════════════════════════════════════════════════════════════════════

def register_vc_handlers(app: Client) -> None:
    """
    Register both VC join handlers on the Pyrogram Client.

    Usage in bot.py  (inside main(), after all other handlers):
        from handlers.vc_notify import register_vc_handlers
        register_vc_handlers(app)
    """
    app.add_handler(
        MessageHandler(
            on_vc_members_invited,
            filters.video_chat_members_invited & filters.group,
        )
    )
    app.add_handler(RawUpdateHandler(on_raw_vc_update))
    log.info("✅ VC join notifier registered (Path A + Path B)")
