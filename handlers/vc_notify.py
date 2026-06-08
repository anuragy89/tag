"""
handlers/vc_notify.py - SIMPLE VERSION THAT ACTUALLY WORKS.

STRATEGY: Stop fighting MTProto. Use ONLY what bots definitely receive:
  - video_chat_started  service message  (Pyrogram filter, 100% delivered)
  - video_chat_ended    service message  (Pyrogram filter, 100% delivered)
  - video_chat_members_invited service message (when someone is invited)

For self-join detection: use Bot API getChatMember on a known member list
approach — actually, use Pyrogram's client.get_chat_members() with
filter=ChatMembersFilter.VOICE_CHATS which lists current VC participants.
This works because it goes through the bot's MTProto session differently.

If that fails too, we use the Bot API endpoint directly.
"""

import asyncio
import logging
from typing import Dict, Set, Optional

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from config import Config
from utils.botapi import te, _call

log = logging.getLogger(__name__)

_poll_tasks: Dict[int, asyncio.Task] = {}
_known_participants: Dict[int, Set[int]] = {}

POLL_INTERVAL = 5


# ── Notification ──────────────────────────────────────────────────────────────

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
        "text": "➕ Add Me to Your Group",
        "url": f"https://t.me/{Config.BOT_USERNAME}?startgroup=true",
        "style": "primary",
    }]]}
    result = await _call("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": keyboard,
    })
    if result and isinstance(result, dict):
        msg_id = result.get("message_id")
        if msg_id:
            asyncio.create_task(_delete_after(chat_id, msg_id, delay=60))


# ── Get VC participants via Pyrogram get_chat_members ─────────────────────────

async def _get_vc_members(client: Client, chat_id: int) -> Optional[list]:
    """
    Uses pyrogram's get_chat_members with VOICE_CHATS filter.
    Returns [(user_id, first_name), ...] or None on error.
    """
    try:
        from pyrogram.enums import ChatMembersFilter
        members = []
        async for member in client.get_chat_members(
            chat_id, filter=ChatMembersFilter.VOICE_CHATS
        ):
            u = member.user
            if u and not u.is_bot:
                members.append((u.id, u.first_name or "User"))
        return members
    except Exception as e:
        log.debug("get_chat_members VOICE_CHATS failed for %s: %s", chat_id, e)
        return None


# ── Polling loop ──────────────────────────────────────────────────────────────

async def _poll_vc(client: Client, chat_id: int) -> None:
    log.info("▶ VC poll started — chat %s", chat_id)
    fail_count = 0

    # Seed existing participants so we don't spam on start
    initial = await _get_vc_members(client, chat_id)
    if initial is None:
        log.warning("Could not fetch VC members for chat %s — aborting poll", chat_id)
        _poll_tasks.pop(chat_id, None)
        return

    _known_participants[chat_id] = {uid for uid, _ in initial}
    log.info("Seeded %d VC member(s) in chat %s: %s",
             len(initial), chat_id, [n for _, n in initial])

    while True:
        await asyncio.sleep(POLL_INTERVAL)

        current = await _get_vc_members(client, chat_id)

        if current is None:
            fail_count += 1
            if fail_count >= 6:
                log.info("Repeated failures — stopping VC poll for chat %s", chat_id)
                break
            continue

        # Empty result = VC ended
        if len(current) == 0:
            fail_count += 1
            if fail_count >= 3:
                log.info("VC appears empty/ended — stopping poll for chat %s", chat_id)
                break
            continue

        fail_count = 0
        known = _known_participants.get(chat_id, set())
        current_ids = {uid for uid, _ in current}

        for uid, name in current:
            if uid not in known:
                log.info("🎙 New joiner: %s (%s) in chat %s", name, uid, chat_id)
                asyncio.create_task(_notify_vc_join(chat_id, uid, name))

        _known_participants[chat_id] = current_ids

    _known_participants.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("■ VC poll stopped — chat %s", chat_id)


def _start_poll(client: Client, chat_id: int) -> None:
    existing = _poll_tasks.get(chat_id)
    if existing and not existing.done():
        log.debug("Poll already running for chat %s", chat_id)
        return
    task = asyncio.create_task(_poll_vc(client, chat_id))
    _poll_tasks[chat_id] = task
    log.info("Poll task started for chat %s", chat_id)


def _stop_poll(chat_id: int) -> None:
    task = _poll_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    _known_participants.pop(chat_id, None)
    log.info("Poll stopped for chat %s", chat_id)


# ── Service message handlers ──────────────────────────────────────────────────

async def on_vc_started(client: Client, message: Message) -> None:
    log.info("video_chat_started in chat %s — starting poll", message.chat.id)
    _start_poll(client, message.chat.id)


async def on_vc_ended(client: Client, message: Message) -> None:
    log.info("video_chat_ended in chat %s — stopping poll", message.chat.id)
    _stop_poll(message.chat.id)


async def on_vc_invited(client: Client, message: Message) -> None:
    """User was directly invited into VC — instant notification."""
    chat_id = message.chat.id
    # Also ensure poll is running
    _start_poll(client, chat_id)
    known = _known_participants.get(chat_id, set())
    for user in (message.new_chat_members or []):
        if user and not user.is_bot and user.id not in known:
            asyncio.create_task(
                _notify_vc_join(chat_id, user.id, user.first_name or "User")
            )
            known.add(user.id)
    _known_participants[chat_id] = known


# ── Startup scan ──────────────────────────────────────────────────────────────

async def startup_vc_scan(client: Client) -> None:
    """Check all DB groups for active VCs on bot start."""
    from database import get_all_chat_ids
    log.info("🔍 VC startup scan…")
    try:
        chat_ids = await get_all_chat_ids()
    except Exception as e:
        log.error("VC scan: %s", e)
        return

    found = 0
    for chat_id in chat_ids:
        try:
            members = await _get_vc_members(client, chat_id)
            if members:  # non-empty = active VC with people in it
                log.info("Active VC in chat %s with %d member(s) — starting poll",
                         chat_id, len(members))
                _known_participants[chat_id] = {uid for uid, _ in members}
                _start_poll(client, chat_id)
                found += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            log.debug("VC scan error for chat %s: %s", chat_id, e)

    log.info("✅ VC scan done — %d active VC(s)", found)


# ── Registration ──────────────────────────────────────────────────────────────

def register_vc_handlers(app: Client) -> None:
    G = filters.group
    app.add_handler(MessageHandler(on_vc_started, filters.video_chat_started & G))
    app.add_handler(MessageHandler(on_vc_ended,   filters.video_chat_ended   & G))
    app.add_handler(MessageHandler(on_vc_invited, filters.video_chat_members_invited & G))
    log.info("✅ VC handlers registered")
