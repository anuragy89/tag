"""
handlers/vc_notify.py - VC join notifier.

CONFIRMED FROM LOGS:
  - UpdateGroupCall DOES arrive (worked once in image 2 logs)
  - video_chat_started service msg arrives reliably
  - The problem: after bot restart, UpdateGroupCall stops coming
    because the MTProto session isn't subscribed to group call updates

FIX:
  1. On video_chat_started, actively INVOKE GetFullChannel ourselves
     using the message's chat peer — this subscribes the session to
     that channel's updates including group call updates
  2. Also try to get the call ptr directly from GetFullChannel right
     after the VC starts (small delay for Telegram to register it)
  3. Keep UpdateGroupCall as primary, GetFullChannel as fallback
"""

import asyncio
import logging
from typing import Dict, Set, Optional

from pyrogram import Client, filters, raw
from pyrogram.handlers import MessageHandler, RawUpdateHandler
from pyrogram.types import Message

from config import Config
from utils.botapi import te, _call

log = logging.getLogger(__name__)

_poll_tasks: Dict[int, asyncio.Task] = {}
_known_participants: Dict[int, Set[int]] = {}
_call_ptrs: Dict[int, object] = {}

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


# ── Get call pointer from full channel (fallback) ─────────────────────────────

async def _get_call_ptr_from_full(client: Client, chat_id: int) -> Optional[object]:
    """
    Tries to get InputGroupCall via GetFullChannel.
    Also has the side effect of subscribing this MTProto session
    to updates for this channel (important for UpdateGroupCall delivery).
    """
    try:
        peer = await client.resolve_peer(chat_id)
        if isinstance(peer, raw.types.InputPeerChannel):
            full = await client.invoke(
                raw.functions.channels.GetFullChannel(channel=peer)
            )
        else:
            full = await client.invoke(
                raw.functions.messages.GetFullChat(chat_id=abs(chat_id))
            )
        call = getattr(full.full_chat, "call", None)
        if call is not None:
            log.info("Got call ptr from GetFullChannel for chat %s: id=%s", chat_id, call.id)
            return raw.types.InputGroupCall(id=call.id, access_hash=call.access_hash)
        else:
            log.info("GetFullChannel: no active call in chat %s", chat_id)
            return None
    except Exception as e:
        log.warning("GetFullChannel failed for chat %s: %s", chat_id, e)
        return None


# ── Fetch participants ────────────────────────────────────────────────────────

async def _fetch_participants(client: Client, call_ptr) -> Optional[list]:
    try:
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
        out = []
        for p in result.participants:
            if isinstance(p.peer, raw.types.PeerUser):
                uid = p.peer.user_id
                u = user_map.get(uid)
                if u and not getattr(u, "bot", False):
                    out.append((uid, getattr(u, "first_name", None) or "User"))
        return out
    except Exception as e:
        log.warning("GetGroupParticipants error: %s", e)
        return None


# ── Poll loop ─────────────────────────────────────────────────────────────────

async def _poll_vc(client: Client, chat_id: int) -> None:
    log.info("▶ Poll started — chat %s", chat_id)
    fail_streak = 0

    call_ptr = _call_ptrs.get(chat_id)
    if not call_ptr:
        log.warning("No call_ptr for chat %s — aborting", chat_id)
        _poll_tasks.pop(chat_id, None)
        return

    initial = await _fetch_participants(client, call_ptr)
    if initial is None:
        initial = []
    _known_participants[chat_id] = {uid for uid, _ in initial}
    log.info("Seeded %d participant(s) — chat %s: %s",
             len(initial), chat_id, [(n, u) for u, n in initial])

    while True:
        await asyncio.sleep(POLL_INTERVAL)

        call_ptr = _call_ptrs.get(chat_id)
        if not call_ptr:
            log.info("Call ptr removed — VC ended for chat %s", chat_id)
            break

        current = await _fetch_participants(client, call_ptr)
        if current is None:
            fail_streak += 1
            if fail_streak >= 5:
                log.info("5 consecutive failures — stopping poll for chat %s", chat_id)
                break
            continue

        fail_streak = 0
        known = _known_participants.get(chat_id, set())

        for uid, name in current:
            if uid not in known:
                log.info("🎙 NEW JOINER: %s (%s) in chat %s", name, uid, chat_id)
                asyncio.create_task(_notify_vc_join(chat_id, uid, name))

        _known_participants[chat_id] = {uid for uid, _ in current}

    _known_participants.pop(chat_id, None)
    _call_ptrs.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("■ Poll stopped — chat %s", chat_id)


def _start_poll(client: Client, chat_id: int) -> None:
    existing = _poll_tasks.get(chat_id)
    if existing and not existing.done():
        log.debug("Poll already running for chat %s", chat_id)
        return
    task = asyncio.create_task(_poll_vc(client, chat_id))
    _poll_tasks[chat_id] = task
    log.info("Poll task created — chat %s", chat_id)


def _stop_poll(chat_id: int) -> None:
    _call_ptrs.pop(chat_id, None)
    _known_participants.pop(chat_id, None)
    task = _poll_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    log.info("Poll stopped — chat %s", chat_id)


# ── Raw update handler ────────────────────────────────────────────────────────

async def on_raw_update(client: Client, update, users: dict, chats: dict) -> None:

    if isinstance(update, raw.types.UpdateGroupCall):
        raw_chat_id = update.chat_id
        call = update.call

        # Resolve chat_id correctly using the chats dict
        resolved_chat_id = None
        for cid, chat_obj in chats.items():
            if int(cid) == int(raw_chat_id):
                if isinstance(chat_obj, (raw.types.Channel, raw.types.ChannelForbidden)):
                    resolved_chat_id = -(1000000000000 + int(cid))
                else:
                    resolved_chat_id = -int(cid)
                break

        if resolved_chat_id is None:
            # Fallback: assume supergroup
            resolved_chat_id = -(1000000000000 + int(raw_chat_id))

        log.info("UpdateGroupCall: chat_id=%s type=%s", resolved_chat_id, type(call).__name__)

        if isinstance(call, raw.types.GroupCallDiscarded):
            _stop_poll(resolved_chat_id)

        elif isinstance(call, raw.types.GroupCall):
            input_call = raw.types.InputGroupCall(
                id=call.id,
                access_hash=call.access_hash,
            )
            _call_ptrs[resolved_chat_id] = input_call
            log.info("Stored call ptr for chat %s — starting poll", resolved_chat_id)
            _start_poll(client, resolved_chat_id)

    elif isinstance(update, raw.types.UpdateGroupCallParticipants):
        for participant in update.participants:
            if not getattr(participant, "just_joined", False):
                continue
            if not isinstance(participant.peer, raw.types.PeerUser):
                continue
            uid = participant.peer.user_id
            u = users.get(uid)
            if not u or getattr(u, "bot", False):
                continue
            name = getattr(u, "first_name", None) or "User"
            for chat_id in list(_call_ptrs.keys()):
                known = _known_participants.get(chat_id, set())
                if uid not in known:
                    log.info("Fast-path: %s (%s) joined chat %s", name, uid, chat_id)
                    asyncio.create_task(_notify_vc_join(chat_id, uid, name))
                    known.add(uid)
                    _known_participants[chat_id] = known
                break


# ── Service message handlers ──────────────────────────────────────────────────

async def on_vc_started(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    log.info("video_chat_started — chat %s", chat_id)

    # Try GetFullChannel immediately (subscribes session + may return call ptr)
    # Run in background so handler returns fast
    async def _try_get_ptr():
        # Wait a bit for Telegram to register the call
        for delay in [2, 5, 10]:
            await asyncio.sleep(delay)
            call_ptr = await _get_call_ptr_from_full(client, chat_id)
            if call_ptr is not None:
                _call_ptrs[chat_id] = call_ptr
                log.info("Got call ptr via GetFullChannel after %ds delay", delay)
                _start_poll(client, chat_id)
                return
            log.info("No call ptr yet after %ds delay for chat %s", delay, chat_id)
        log.warning("Could not get call ptr via GetFullChannel for chat %s — waiting for UpdateGroupCall", chat_id)

    asyncio.create_task(_try_get_ptr())


async def on_vc_ended(client: Client, message: Message) -> None:
    log.info("video_chat_ended — chat %s", message.chat.id)
    _stop_poll(message.chat.id)


async def on_vc_invited(client: Client, message: Message) -> None:
    chat_id = message.chat.id
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
    """
    On startup: try GetFullChannel for all known groups.
    This both subscribes the session AND detects already-active VCs.
    """
    from database import get_all_chat_ids
    log.info("🔍 VC startup scan — checking all groups via GetFullChannel…")
    try:
        chat_ids = await get_all_chat_ids()
    except Exception as e:
        log.error("Could not get chat_ids: %s", e)
        return

    found = 0
    for chat_id in chat_ids:
        try:
            call_ptr = await _get_call_ptr_from_full(client, chat_id)
            if call_ptr is not None:
                _call_ptrs[chat_id] = call_ptr
                _start_poll(client, chat_id)
                found += 1
            await asyncio.sleep(0.4)
        except Exception as e:
            log.debug("Scan error for chat %s: %s", chat_id, e)

    log.info("✅ VC startup scan done — %d active VC(s) found", found)


# ── Registration ──────────────────────────────────────────────────────────────

def register_vc_handlers(app: Client) -> None:
    G = filters.group
    app.add_handler(MessageHandler(on_vc_started,  filters.video_chat_started  & G))
    app.add_handler(MessageHandler(on_vc_ended,    filters.video_chat_ended    & G))
    app.add_handler(MessageHandler(on_vc_invited,  filters.video_chat_members_invited & G))
    app.add_handler(RawUpdateHandler(on_raw_update))
    log.info("✅ VC handlers registered")
