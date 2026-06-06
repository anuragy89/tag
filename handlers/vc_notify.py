"""
handlers/vc_notify.py – VC join notifier (polling-based, Kurigram-safe).

WHY POLLING:
  Pyrogram/Kurigram bots do NOT receive UpdateGroupCallParticipants via
  webhook — that update is only delivered to user accounts. Bots also miss
  the "user joined on their own" service message entirely.

  The only 100 % reliable method for a BOT account is:
    1. Detect when a Voice/Video Chat becomes active in a group
       (via the `video_chat_started` service message OR by noticing
       the group's `call` field is set).
    2. Poll `GetGroupCallParticipants` every N seconds.
    3. Compare against the last known participant set.
    4. When a new user_id appears → fire the notification.

FLOW:
  • on_vc_started()  — service msg handler for video_chat_started
                       registers a polling task for that chat.
  • _poll_vc()       — background task: every 5 s calls
                       GetGroupCall to get current participants,
                       diffs against previous snapshot, notifies joins.
  • on_vc_ended()    — service msg handler for video_chat_ended
                       cancels the polling task.
  • on_vc_invited()  — catches the rare "user was invited" service msg
                       as a fast-path (no polling lag).

NOTIFICATION FORMAT:
    🎙️ ◈ 𝗡𝗲𝘄 𝗩𝗖 𝗝𝗼𝗶𝗻

    👤 {mention}
    🆔 {uid}

    🤍 Welcome to the VC

    [ ➕ Add Me to Your Group ]   ← blue button

  Auto-deletes after 60 seconds.
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

# chat_id → asyncio.Task
_poll_tasks: Dict[int, asyncio.Task] = {}

# chat_id → set of user_ids currently known to be in VC
_known_participants: Dict[int, Set[int]] = {}

POLL_INTERVAL = 5   # seconds between participant checks


# ══════════════════════════════════════════════════════════════════════════════
#  Notification sender
# ══════════════════════════════════════════════════════════════════════════════

async def _delete_after(chat_id: int, message_id: int, delay: int = 60) -> None:
    await asyncio.sleep(delay)
    try:
        await _call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except Exception:
        pass


async def _notify_vc_join(chat_id: int, user_id: int, first_name: str) -> None:
    """Send the VC join card and schedule auto-delete in 60 s."""
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
    else:
        log.warning("Failed to send VC notify to chat %s", chat_id)


# ══════════════════════════════════════════════════════════════════════════════
#  Polling logic
# ══════════════════════════════════════════════════════════════════════════════

async def _get_call_participants(client: Client, chat_id: int):
    """
    Returns list of (user_id, first_name) currently in the VC.
    Uses raw GetGroupCall + GetGroupCallParticipants.
    Returns [] on any error (VC ended, no call active, etc.).
    """
    try:
        # Resolve the peer
        peer = await client.resolve_peer(chat_id)

        # Get the full chat to find the active call
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
            return []   # No active VC

        # Fetch participants
        result = await client.invoke(
            raw.functions.phone.GetGroupParticipants(
                call=call_ptr,
                ids=[],
                sources=[],
                offset="",
                limit=500,
            )
        )

        participants = []
        user_map = {u.id: u for u in result.users}

        for p in result.participants:
            peer_p = p.peer
            if isinstance(peer_p, raw.types.PeerUser):
                uid = peer_p.user_id
                user = user_map.get(uid)
                if user and not getattr(user, "bot", False):
                    name = getattr(user, "first_name", None) or "User"
                    participants.append((uid, name))

        return participants

    except Exception as e:
        log.debug("_get_call_participants error for chat %s: %s", chat_id, e)
        return []


async def _poll_vc(client: Client, chat_id: int) -> None:
    """
    Background task: polls VC participants every POLL_INTERVAL seconds.
    Fires _notify_vc_join for every new joiner detected.
    """
    log.info("VC polling started for chat %s", chat_id)

    # Seed initial participants (people already in call when bot noticed)
    initial = await _get_call_participants(client, chat_id)
    _known_participants[chat_id] = {uid for uid, _ in initial}
    log.debug("Initial VC participants in %s: %s", chat_id, _known_participants[chat_id])

    consecutive_empty = 0

    while True:
        await asyncio.sleep(POLL_INTERVAL)

        current = await _get_call_participants(client, chat_id)

        if not current:
            consecutive_empty += 1
            # If we get 3 empty polls in a row, assume VC ended
            if consecutive_empty >= 3:
                log.info("VC appears ended for chat %s, stopping poll", chat_id)
                break
            continue

        consecutive_empty = 0
        current_ids = {uid for uid, _ in current}
        known = _known_participants.get(chat_id, set())

        # New joiners = in current but not in last snapshot
        new_joiners = [(uid, name) for uid, name in current if uid not in known]

        for uid, name in new_joiners:
            log.info("VC new joiner detected: %s (%s) in chat %s", name, uid, chat_id)
            asyncio.create_task(_notify_vc_join(chat_id, uid, name))

        _known_participants[chat_id] = current_ids

    # Cleanup
    _known_participants.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("VC polling stopped for chat %s", chat_id)


def _start_poll(client: Client, chat_id: int) -> None:
    """Start a polling task for chat_id, cancelling any existing one."""
    if chat_id in _poll_tasks:
        _poll_tasks[chat_id].cancel()
    task = asyncio.create_task(_poll_vc(client, chat_id))
    _poll_tasks[chat_id] = task


def _stop_poll(chat_id: int) -> None:
    """Cancel and remove the polling task for chat_id."""
    task = _poll_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    _known_participants.pop(chat_id, None)


# ══════════════════════════════════════════════════════════════════════════════
#  Pyrogram message handlers
# ══════════════════════════════════════════════════════════════════════════════

async def on_vc_started(client: Client, message: Message) -> None:
    """VC started service message → begin polling."""
    chat_id = message.chat.id
    log.info("VC started in chat %s — starting participant polling", chat_id)
    _start_poll(client, chat_id)


async def on_vc_ended(client: Client, message: Message) -> None:
    """VC ended service message → stop polling."""
    chat_id = message.chat.id
    log.info("VC ended in chat %s — stopping participant polling", chat_id)
    _stop_poll(chat_id)


async def on_vc_invited(client: Client, message: Message) -> None:
    """
    Fast-path: user was *invited* into VC (service msg).
    Also ensures polling is running for this chat.
    """
    chat_id = message.chat.id
    users = message.new_chat_members or []

    # Make sure polling is running
    if chat_id not in _poll_tasks:
        _start_poll(client, chat_id)

    for user in users:
        if not user or user.is_bot:
            continue
        name = user.first_name or "User"
        known = _known_participants.get(chat_id, set())
        if user.id not in known:
            log.info("VC invited fast-path: %s (%s) in chat %s", name, user.id, chat_id)
            asyncio.create_task(_notify_vc_join(chat_id, user.id, name))
            known.add(user.id)
            _known_participants[chat_id] = known


# ══════════════════════════════════════════════════════════════════════════════
#  Raw update handler — catches group call updates Pyrogram doesn't expose
# ══════════════════════════════════════════════════════════════════════════════

async def on_raw_update(client: Client, update, users: dict, chats: dict) -> None:
    """
    Watches for UpdateGroupCall (VC started/ended on a channel/supergroup).
    Supplements the service-message handlers for edge cases.
    """
    if isinstance(update, raw.types.UpdateGroupCall):
        call = update.call
        chat_id_raw = update.chat_id

        # Supergroup chat_id is negative
        chat_id = -chat_id_raw if chat_id_raw > 0 else chat_id_raw

        if isinstance(call, raw.types.GroupCall) and not getattr(call, "schedule_date", None):
            # Call became active
            if not getattr(call, "participants_count", 1) == 0:
                if chat_id not in _poll_tasks:
                    log.info("UpdateGroupCall: VC active in chat %s → start polling", chat_id)
                    _start_poll(client, chat_id)

        elif isinstance(call, raw.types.GroupCallDiscarded):
            log.info("UpdateGroupCall: VC discarded in chat %s → stop polling", chat_id)
            _stop_poll(chat_id)


# ══════════════════════════════════════════════════════════════════════════════
#  Registration
# ══════════════════════════════════════════════════════════════════════════════

def register_vc_handlers(app: Client) -> None:
    """
    Register all VC handlers. Call inside main() in bot.py after other handlers.

        from handlers.vc_notify import register_vc_handlers
        register_vc_handlers(app)
    """
    G = filters.group

    app.add_handler(MessageHandler(on_vc_started,  filters.video_chat_started  & G))
    app.add_handler(MessageHandler(on_vc_ended,    filters.video_chat_ended    & G))
    app.add_handler(MessageHandler(on_vc_invited,  filters.video_chat_members_invited & G))
    app.add_handler(RawUpdateHandler(on_raw_update))

    log.info("✅ VC join notifier registered (polling + raw update fallback)")
