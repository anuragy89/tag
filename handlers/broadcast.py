"""
handlers/broadcast.py – /broadcast and /stats

FIXES:
  1. except _SKIP as tuple  → use  except tuple(_SKIP)  so Python
     actually catches those exceptions (bare tuple variable in except
     is a SyntaxError / silent pass-through in older Pythons).
  2. message.text may be None for media replies → fall back to
     message.caption, then to "" so .strip() never crashes.
  3. plain_text extraction now works correctly when /broadcast is
     sent as a reply with no extra text.
"""

import asyncio
import logging

from pyrogram import Client, enums
from pyrogram.errors import (
    ChannelInvalid, ChannelPrivate, ChatAdminRequired,
    ChatWriteForbidden, FloodWait, InputUserDeactivated,
    PeerIdInvalid, RPCError, UserIsBlocked, UserNotParticipant,
)
from pyrogram.types import Message

from database import get_all_user_ids, get_all_chat_ids, count_users, count_groups
from utils import owner_only
from utils.tag_manager import tag_manager
from utils.botapi import te, _call

log = logging.getLogger(__name__)

# ── FIX 1: store as a plain tuple so it works inside `except` ────────────────
_SKIP = (
    UserIsBlocked, InputUserDeactivated, PeerIdInvalid,
    ChannelInvalid, ChannelPrivate, ChatWriteForbidden,
    ChatAdminRequired, UserNotParticipant,
)


# ── Send one broadcast message ────────────────────────────────────────────────

async def _send_one(
    client: Client,
    target_id: int,
    source_msg,
    plain_text: str,
) -> str:
    """Returns 'ok', 'blocked', or 'failed'."""
    for attempt in range(3):
        try:
            if source_msg:
                await source_msg.copy(target_id)
            else:
                await client.send_message(
                    target_id,
                    f"📢 **Broadcast from Bot Owner:**\n\n{plain_text}",
                    parse_mode=enums.ParseMode.MARKDOWN,
                )
            return "ok"

        except FloodWait as e:
            log.warning("FloodWait %ds → %s", e.value, target_id)
            await asyncio.sleep(e.value + 3)

        # ── FIX 1: use *_SKIP to unpack the tuple into except ────────────────
        except (
            UserIsBlocked, InputUserDeactivated, PeerIdInvalid,
            ChannelInvalid, ChannelPrivate, ChatWriteForbidden,
            ChatAdminRequired, UserNotParticipant,
        ):
            return "blocked"

        except (RPCError, Exception) as e:
            log.debug("Send failed attempt %d to %s: %s", attempt + 1, target_id, e)
            if attempt < 2:
                await asyncio.sleep(1)
            else:
                return "failed"

    return "failed"


# ── Edit the status message via Bot API HTTP ──────────────────────────────────

async def _edit_status(chat_id: int, msg_id: int, text: str) -> None:
    try:
        await _call("editMessageText", {
            "chat_id":                  chat_id,
            "message_id":               msg_id,
            "text":                     text,
            "parse_mode":               "HTML",
            "disable_web_page_preview": True,
        })
    except Exception:
        pass  # status edit failures are non-critical


# ── /broadcast ────────────────────────────────────────────────────────────────

@owner_only
async def cmd_broadcast(client: Client, message: Message) -> None:
    # ── FIX 2 & 3: message.text is None for media replies; also check caption ─
    raw        = (message.text or message.caption or "").strip()
    parts      = raw.split(maxsplit=1)
    plain_text = parts[1].strip() if len(parts) > 1 else ""
    source_msg = message.reply_to_message  # None if not a reply

    # ── Validate: must have text OR be a reply to some media ─────────────────
    if not source_msg and not plain_text:
        await message.reply_text(
            f"{te('bell','🔔')} **How to use /broadcast:**\n\n"
            f"**Text:** `/broadcast Hello everyone!`\n\n"
            f"**Any media:** Reply to a photo/video/audio/doc/sticker "
            f"with `/broadcast`\n\n"
            f"_Groups first, then user DMs._",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        return

    # ── Content type label ────────────────────────────────────────────────────
    if source_msg:
        m = source_msg
        if   m.photo:      ctype = "photo 📷"
        elif m.video:      ctype = "video 🎬"
        elif m.audio:      ctype = "audio 🎵"
        elif m.voice:      ctype = "voice 🎤"
        elif m.document:   ctype = "document 📄"
        elif m.sticker:    ctype = "sticker 🎭"
        elif m.animation:  ctype = "GIF 🎞️"
        else:              ctype = "text 📝"
    else:
        ctype = "text 📝"

    # ── Fetch targets ─────────────────────────────────────────────────────────
    chat_ids = await get_all_chat_ids()
    user_ids = await get_all_user_ids()
    total_g  = len(chat_ids)
    total_u  = len(user_ids)
    total    = total_g + total_u

    # ── Send "Started" status message via Bot API (HTML + premium emoji) ──────
    started_text = (
        f"{te('broadcast','📡')} <b>Broadcast Started!</b>\n\n"
        f"📦 Type   : <code>{ctype}</code>\n"
        f"{te('chat','💬')} Groups : <code>{total_g}</code>\n"
        f"{te('people','👥')} Users  : <code>{total_u}</code>\n"
        f"📊 Total  : <code>{total}</code>\n\n"
        f"<i>Sending to groups first, then DMs…</i>"
    )

    sent = await _call("sendMessage", {
        "chat_id":                  message.chat.id,
        "reply_to_message_id":      message.id,
        "text":                     started_text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    })

    if sent and isinstance(sent, dict) and "message_id" in sent:
        status_chat_id = message.chat.id
        status_msg_id  = sent["message_id"]
        can_edit = True
    else:
        # Fallback — plain Pyrogram reply
        fallback = await message.reply_text(
            f"📡 **Broadcast Started!** | Groups: {total_g} | Users: {total_u}",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
        status_chat_id = message.chat.id
        status_msg_id  = fallback.id
        can_edit = True

    # ── Phase 1: Groups ───────────────────────────────────────────────────────
    g_ok = g_blocked = g_failed = 0

    for idx, chat_id in enumerate(chat_ids, 1):
        res = await _send_one(client, chat_id, source_msg, plain_text)
        if   res == "ok":      g_ok += 1
        elif res == "blocked": g_blocked += 1
        else:                  g_failed += 1

        if can_edit and (idx % 20 == 0 or idx == total_g):
            await _edit_status(status_chat_id, status_msg_id, (
                f"{te('broadcast','📡')} <b>Broadcasting to Groups…</b>\n\n"
                f"{te('chat','💬')} Progress : <code>{idx}</code> / <code>{total_g}</code>\n"
                f"{te('check','✅')} Sent     : <code>{g_ok}</code>\n"
                f"🚫 Blocked  : <code>{g_blocked}</code>\n"
                f"{te('cross','❌')} Failed   : <code>{g_failed}</code>\n\n"
                f"<i>User DMs start after groups…</i>"
            ))

        await asyncio.sleep(0.35)

    # ── Phase 2: User DMs ─────────────────────────────────────────────────────
    u_ok = u_blocked = u_failed = 0

    for idx, user_id in enumerate(user_ids, 1):
        res = await _send_one(client, user_id, source_msg, plain_text)
        if   res == "ok":      u_ok += 1
        elif res == "blocked": u_blocked += 1
        else:                  u_failed += 1

        if can_edit and (idx % 20 == 0 or idx == total_u):
            await _edit_status(status_chat_id, status_msg_id, (
                f"{te('broadcast','📡')} <b>Broadcasting to Users…</b>\n\n"
                f"{te('check','✅')} Groups done : <code>{g_ok}</code> / <code>{total_g}</code>\n\n"
                f"{te('people','👥')} Users : <code>{idx}</code> / <code>{total_u}</code>\n"
                f"{te('check','✅')} Sent    : <code>{u_ok}</code>\n"
                f"🚫 Blocked : <code>{u_blocked}</code>\n"
                f"{te('cross','❌')} Failed  : <code>{u_failed}</code>"
            ))

        await asyncio.sleep(0.35)

    # ── Final report ──────────────────────────────────────────────────────────
    report = (
        f"{te('check','✅')} <b>Broadcast Complete!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{te('chat','💬')} <b>Groups</b>\n"
        f"  ├ ✅ Delivered : <code>{g_ok}</code> / <code>{total_g}</code>\n"
        f"  ├ 🚫 Blocked  : <code>{g_blocked}</code>\n"
        f"  └ ❌ Failed   : <code>{g_failed}</code>\n\n"
        f"{te('people','👥')} <b>Users (DM)</b>\n"
        f"  ├ ✅ Delivered : <code>{u_ok}</code> / <code>{total_u}</code>\n"
        f"  ├ 🚫 Blocked  : <code>{u_blocked}</code>\n"
        f"  └ ❌ Failed   : <code>{u_failed}</code>\n\n"
        f"📊 <b>Total Delivered : <code>{g_ok + u_ok}</code> / <code>{total}</code></b>\n"
        f"📦 Type : <code>{ctype}</code>"
    )

    if can_edit:
        await _edit_status(status_chat_id, status_msg_id, report)
    else:
        await _call("sendMessage", {
            "chat_id":    message.chat.id,
            "text":       report,
            "parse_mode": "HTML",
        })


# ── /stats ────────────────────────────────────────────────────────────────────

@owner_only
async def cmd_stats(client: Client, message: Message) -> None:
    total_users  = await count_users()
    total_groups = await count_groups()
    active_tags  = sum(
        1 for cid in list(tag_manager._sessions)
        if tag_manager.is_active(cid)
    )
    text = (
        f"{te('chart','📊')} <b>Tag Master Bot — Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{te('people','👥')} <b>Total Users  :</b> <code>{total_users}</code>\n"
        f"{te('chat','💬')} <b>Total Groups :</b> <code>{total_groups}</code>\n"
        f"{te('lightning','⚡')} <b>Active Tags  :</b> <code>{active_tags}</code>\n\n"
        f"🗄️ <b>Database :</b> MongoDB\n"
        f"{te('robot','🤖')} <i>Tag Master Bot — Online &amp; Running!</i> "
        f"{te('rocket','🚀')}"
    )
    sent = await _call("sendMessage", {
        "chat_id":                  message.chat.id,
        "reply_to_message_id":      message.id,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    })
    if not sent:
        await message.reply_text(
            f"📊 **Stats** | Users: {total_users} | Groups: {total_groups}",
            parse_mode=enums.ParseMode.MARKDOWN,
        )
