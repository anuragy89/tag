"""
handlers/vc_notify.py – VC join notifier (polling-based, Kurigram-safe).

WHY POLLING:
  Telegram does NOT deliver UpdateGroupCallParticipants to bot accounts.
  The only reliable method is polling GetGroupParticipants every N seconds.

STARTUP SCAN:
  On bot start, we scan ALL known groups from the database and immediately
  start polling any group that already has an active VC. This handles the
  case where the VC was already running before the bot started/restarted.

FLOW:
  • startup_vc_scan()  — called from bot.py after app.start(); scans all
                         groups in DB for active VCs, starts polling each.
  • on_vc_started()    — service msg handler; starts polling when VC begins.
  • on_vc_ended()      — service msg handler; stops polling when VC ends.
  • _poll_vc()         — background task: every 5 s fetches participants,
                         diffs against snapshot, notifies new joiners.
  • on_raw_update()    — raw UpdateGroupCall fallback for edge cases.
"""

import asyncio
import logging
from typing import Dict, Set

from pyrogram import Client, filters, raw
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from pyrogram.types import Message

from config import Config
from utils.botapi import te, _call

log = logging.getLogger(__name__)

_poll_tasks: Dict[int, asyncio.Task] = {}
_known_participants: Dict[int, Set[int]] = {}

POLL_INTERVAL = 5  # seconds between participant checks


# ══════════════════════════════════════════════════════════════════════════════
#  Notification sender + auto-delete
# ══════════════════════════════════════════════════════════════════════════════

async def _delete_after(chat_id: int, message_id: int, delay: int = 60) -> None:
    await asyncio.sleep(delay)
    try:
        await _call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except Exception:
        pass


async def _notify_vc_join(chat_id: int, user_id: int, first_name: str) -> None:
    mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'
    text = (
        f"{te('mic', '🎙️')} ◈ <b>𝗡𝗲𝘄 𝗩𝗖 𝗝𝗼𝗶𝗻</b>\n\n"
        f"👤 {mention}\n"
        f"🆔 <code>{user_id}</code>\n\n"
        f"{te('heart', '🤍')} <b>Welcome to the VC</b>"
    )
    keyboard = {"inline_keyboard": [[{
        "text":  "➕ Add Me to Your Group",
        "url":   f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
        "style": "primary",
    }]]}
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


# ══════════════════════════════════════════════════════════════════════════════
#  Get current VC participants via raw MTProto
# ══════════════════════════════════════════════════════════════════════════════

async def _get_participants(client: Client, chat_id: int):
    """
    Returns list of (user_id, first_name) currently in the VC.
    Returns None if no active VC exists.
    Returns []   if VC exists but has no human participants yet.
    """
    try:
        peer = await client.resolve_peer(chat_id)

        # Get the active call pointer from the full chat
        if isinstance(peer, raw.types.InputPeerChannel):
            full = await client.invoke(
                raw.functions.channels.GetFullChannel(channel=peer)
            )
            call_ptr = getattr(full.full_chat, "call", None)
        else:
            full = await client.invoke(
                raw.functions.messages.GetFullChat(chat_id=abs(chat_id))
            )
            call_ptr = getattr(full.full_chat, "call", None)

        if call_ptr is None:
            return None  # No active VC

        result = await client.invoke(
            raw.functions.phone.GetGroupParticipants(
                call=call_ptr,
                ids=[],
                sources=[],
                offset="",
                limit=500,
            )
        )

        user_map = {u.id: u for u in result.users}
        participants = []
        for p in result.participants:
            if isinstance(p.peer, raw.types.PeerUser):
                uid = p.peer.user_id
                u = user_map.get(uid)
                if u and not getattr(u, "bot", False):
                    participants.append((uid, getattr(u, "first_name", None) or "User"))

        return participants

    except Exception as e:
        log.debug("_get_participants(%s): %s", chat_id, e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  Polling task
# ══════════════════════════════════════════════════════════════════════════════

async def _poll_vc(client: Client, chat_id: int) -> None:
    log.info("VC polling started → chat %s", chat_id)
    consecutive_none = 0

    # Seed: people already in VC when we started (don't spam notifications for them)
    initial = await _get_participants(client, chat_id)
    if initial is None:
        log.info("No active VC found for chat %s on poll start — aborting", chat_id)
        _poll_tasks.pop(chat_id, None)
        return
    _known_participants[chat_id] = {uid for uid, _ in initial}
    log.info("Seeded %d existing participants in chat %s", len(initial), chat_id)

    while True:
        await asyncio.sleep(POLL_INTERVAL)
        current = await _get_participants(client, chat_id)

        if current is None:
            consecutive_none += 1
            if consecutive_none >= 3:
                log.info("VC ended (no call) for chat %s — stopping poll", chat_id)
                break
            continue

        consecutive_none = 0
        known = _known_participants.get(chat_id, set())
        current_ids = {uid for uid, _ in current}

        for uid, name in current:
            if uid not in known:
                log.info("🎙 New VC joiner: %s (%s) in chat %s", name, uid, chat_id)
                asyncio.create_task(_notify_vc_join(chat_id, uid, name))

        _known_participants[chat_id] = current_ids

    _known_participants.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("VC polling stopped → chat %s", chat_id)


def _start_poll(client: Client, chat_id: int) -> None:
    if chat_id in _poll_tasks and not _poll_tasks[chat_id].done():
        return  # Already polling
    task = asyncio.create_task(_poll_vc(client, chat_id))
    _poll_tasks[chat_id] = task
    log.info("Poll task created for chat %s", chat_id)


def _stop_poll(chat_id: int) -> None:
    task = _poll_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    _known_participants.pop(chat_id, None)


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP SCAN — most important fix
#  Called from bot.py after app.start() so VCs already active get picked up
# ══════════════════════════════════════════════════════════════════════════════

async def startup_vc_scan(client: Client) -> None:
    """
    Scan all groups in the database for active VCs and start polling them.
    Must be called AFTER await app.start() in bot.py main().

    Add to bot.py:
        from handlers.vc_notify import startup_vc_scan, register_vc_handlers
        register_vc_handlers(app)
        ...
        await app.start()
        ...
        asyncio.create_task(startup_vc_scan(app))   # ← add this line
    """
    from database import get_all_chat_ids
    log.info("🔍 VC startup scan: checking all groups for active voice chats…")

    try:
        chat_ids = await get_all_chat_ids()
    except Exception as e:
        log.error("Could not fetch chat_ids for VC scan: %s", e)
        return

    found = 0
    for chat_id in chat_ids:
        try:
            participants = await _get_participants(client, chat_id)
            if participants is not None:  # None = no VC; [] = VC active but empty
                log.info("Active VC found in chat %s (%d participants) → starting poll",
                         chat_id, len(participants))
                _start_poll(client, chat_id)
                found += 1
            await asyncio.sleep(0.3)  # gentle rate limiting
        except Exception as e:
            log.debug("VC scan error for chat %s: %s", chat_id, e)

    log.info("✅ VC startup scan complete — polling started for %d group(s)", found)


# ══════════════════════════════════════════════════════════════════════════════
#  Service message handlers
# ══════════════════════════════════════════════════════════════════════════════

async def on_vc_started(client: Client, message: Message) -> None:
    log.info("video_chat_started in chat %s", message.chat.id)
    _start_poll(client, message.chat.id)


async def on_vc_ended(client: Client, message: Message) -> None:
    log.info("video_chat_ended in chat %s", message.chat.id)
    _stop_poll(message.chat.id)


async def on_vc_invited(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    _start_poll(client, chat_id)   # ensure polling is running

    known = _known_participants.get(chat_id, set())
    for user in (message.new_chat_members or []):
        if user and not user.is_bot and user.id not in known:
            name = user.first_name or "User"
            asyncio.create_task(_notify_vc_join(chat_id, user.id, name))
            known.add(user.id)
    _known_participants[chat_id] = known


# ══════════════════════════════════════════════════════════════════════════════
#  Raw update fallback
# ══════════════════════════════════════════════════════════════════════════════

async def on_raw_update(client: Client, update, users: dict, chats: dict) -> None:
    if not isinstance(update, raw.types.UpdateGroupCall):
        return

    raw_cid = update.chat_id
    chat_id = -raw_cid if raw_cid > 0 else raw_cid

    if isinstance(update.call, raw.types.GroupCallDiscarded):
        _stop_poll(chat_id)
    elif isinstance(update.call, raw.types.GroupCall):
        _start_poll(client, chat_id)


# ══════════════════════════════════════════════════════════════════════════════
#  Registration
# ══════════════════════════════════════════════════════════════════════════════

def register_vc_handlers(app: Client) -> None:
    G = filters.group
    app.add_handler(MessageHandler(on_vc_started,  filters.video_chat_started  & G))
    app.add_handler(MessageHandler(on_vc_ended,    filters.video_chat_ended    & G))
    app.add_handler(MessageHandler(on_vc_invited,  filters.video_chat_members_invited & G))
    app.add_handler(RawUpdateHandler(on_raw_update))
    log.info("✅ VC join notifier registered")
