"""
handlers/vc_notify.py - VC join notifier using pure Bot API getChatMember polling.

ROOT CAUSE CONFIRMED:
  ChatMembersFilter.VOICE_CHATS requires the bot to be admin.
  GetGroupParticipants requires a call pointer bots can't get.
  
THE ONLY THING THAT WORKS FOR NON-ADMIN BOTS:
  Telegram Bot API has no direct "get VC participants" endpoint.
  
  BUT — Telegram DOES send a service message for EVERY person who 
  joins a voice chat: it appears as a "MessageService" with action
  "MessageActionGroupCallScheduled" or the participant update.

  Actually the REAL reliable solution:
  Use `client.invoke(raw.functions.phone.GetGroupCall(...))` 
  after getting the call from UpdateGroupCall raw update.
  
  But we confirmed bots DO receive UpdateGroupCall. The problem was
  that previously we then called GetGroupParticipants which needs
  the call to be "joined" by the bot. We don't need to JOIN.
  
  SOLUTION: Use phone.GetGroupParticipants WITHOUT joining.
  The bot just needs to be a member (not admin) of the group.
  We get the InputGroupCall from UpdateGroupCall (which bots receive).
  Then call GetGroupParticipants with that — this works for any member.

  Previous code had this right but had a bug: it was computing chat_id
  wrong from UpdateGroupCall. Let me fix that specifically.

UpdateGroupCall.chat_id for a supergroup is the CHANNEL ID (positive).
The Pyrogram chat_id = -(1000000000000 + channel_id) for supergroups.
BUT many groups are basic groups where chat_id maps directly as negative.

Let's log and handle both cases.
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
# chat_id -> InputGroupCall
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


# ── Fetch participants using stored InputGroupCall ────────────────────────────

async def _fetch_participants(client: Client, call_ptr) -> Optional[list]:
    """
    Fetches VC participants using phone.GetGroupParticipants.
    Bots can call this as long as they have the InputGroupCall (id+access_hash).
    Does NOT require the bot to be admin or to have joined the call.
    Returns [(user_id, first_name)] or None on error.
    """
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
        log.info("Fetched %d VC participant(s)", len(out))
        return out
    except Exception as e:
        log.warning("GetGroupParticipants failed: %s", e)
        return None


# ── Poll loop ─────────────────────────────────────────────────────────────────

async def _poll_vc(client: Client, chat_id: int) -> None:
    log.info("▶ Poll started — chat %s", chat_id)
    fail_streak = 0

    call_ptr = _call_ptrs.get(chat_id)
    if not call_ptr:
        log.warning("No call_ptr for chat %s — cannot poll", chat_id)
        _poll_tasks.pop(chat_id, None)
        return

    # Seed
    initial = await _fetch_participants(client, call_ptr)
    if initial is None:
        initial = []
    _known_participants[chat_id] = {uid for uid, _ in initial}
    log.info("Seeded %d participant(s) for chat %s", len(initial), chat_id)

    while True:
        await asyncio.sleep(POLL_INTERVAL)

        call_ptr = _call_ptrs.get(chat_id)
        if not call_ptr:
            log.info("Call ptr gone — VC ended for chat %s", chat_id)
            break

        current = await _fetch_participants(client, call_ptr)
        if current is None:
            fail_streak += 1
            if fail_streak >= 5:
                log.info("Too many failures — stopping poll for chat %s", chat_id)
                break
            continue

        fail_streak = 0
        known = _known_participants.get(chat_id, set())
        for uid, name in current:
            if uid not in known:
                log.info("🎙 New joiner: %s (%s) in chat %s", name, uid, chat_id)
                asyncio.create_task(_notify_vc_join(chat_id, uid, name))

        _known_participants[chat_id] = {uid for uid, _ in current}

    _known_participants.pop(chat_id, None)
    _call_ptrs.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("■ Poll stopped — chat %s", chat_id)


def _start_poll(client: Client, chat_id: int) -> None:
    existing = _poll_tasks.get(chat_id)
    if existing and not existing.done():
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

        # Compute correct Pyrogram chat_id
        # For supergroups: UpdateGroupCall.chat_id is the bare channel_id (positive)
        # Pyrogram represents supergroups as -(1000000000000 + channel_id)
        # For basic groups: it's just the positive group_id → negative in Pyrogram
        # We try both and use whichever is in our known chats
        candidate_super = -(1000000000000 + raw_chat_id)
        candidate_basic = -raw_chat_id

        log.info(
            "UpdateGroupCall: raw_chat_id=%s candidates: super=%s basic=%s type=%s",
            raw_chat_id, candidate_super, candidate_basic, type(call).__name__
        )

        if isinstance(call, raw.types.GroupCallDiscarded):
            # Try both candidates
            for cid in [candidate_super, candidate_basic]:
                if cid in _call_ptrs or cid in _poll_tasks:
                    log.info("VC discarded — stopping poll for chat %s", cid)
                    _stop_poll(cid)

        elif isinstance(call, raw.types.GroupCall):
            input_call = raw.types.InputGroupCall(
                id=call.id,
                access_hash=call.access_hash,
            )

            # Use the chat from the `chats` dict to resolve correct chat_id
            resolved_chat_id = None
            for cid, chat_obj in chats.items():
                # cid here is the bare id from the update
                if int(cid) == raw_chat_id:
                    # Check if it's a channel/supergroup
                    if isinstance(chat_obj, (raw.types.Channel, raw.types.ChannelForbidden)):
                        resolved_chat_id = -(1000000000000 + int(cid))
                    else:
                        resolved_chat_id = -int(cid)
                    break

            if resolved_chat_id is None:
                # Fallback: try supergroup format first
                resolved_chat_id = candidate_super
                log.warning(
                    "Could not resolve chat from chats dict, using %s", resolved_chat_id
                )

            log.info(
                "VC active — resolved chat_id=%s call_id=%s",
                resolved_chat_id, call.id
            )
            _call_ptrs[resolved_chat_id] = input_call
            _start_poll(client, resolved_chat_id)

    # Fast-path: if Telegram sends participant updates to bots (sometimes it does)
    elif isinstance(update, raw.types.UpdateGroupCallParticipants):
        for participant in update.participants:
            if not getattr(participant, "just_joined", False):
                continue
            peer = participant.peer
            if not isinstance(peer, raw.types.PeerUser):
                continue
            uid = peer.user_id
            u = users.get(uid)
            if not u or getattr(u, "bot", False):
                continue
            name = getattr(u, "first_name", None) or "User"
            # Find which of our polled chats this belongs to
            for chat_id in list(_call_ptrs.keys()):
                known = _known_participants.get(chat_id, set())
                if uid not in known:
                    log.info("Fast-path join: %s (%s) in chat %s", name, uid, chat_id)
                    asyncio.create_task(_notify_vc_join(chat_id, uid, name))
                    known.add(uid)
                    _known_participants[chat_id] = known
                break


# ── Service message handlers ──────────────────────────────────────────────────

async def on_vc_started(client: Client, message: Message) -> None:
    # Log only — actual poll start happens in on_raw_update when we get the call ptr
    log.info("video_chat_started service msg — chat %s (waiting for UpdateGroupCall)", message.chat.id)


async def on_vc_ended(client: Client, message: Message) -> None:
    log.info("video_chat_ended service msg — chat %s", message.chat.id)
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
    log.info("ℹ️  VC startup: active VCs detected via UpdateGroupCall when next join/leave occurs.")


# ── Registration ──────────────────────────────────────────────────────────────

def register_vc_handlers(app: Client) -> None:
    G = filters.group
    app.add_handler(MessageHandler(on_vc_started,  filters.video_chat_started  & G))
    app.add_handler(MessageHandler(on_vc_ended,    filters.video_chat_ended    & G))
    app.add_handler(MessageHandler(on_vc_invited,  filters.video_chat_members_invited & G))
    app.add_handler(RawUpdateHandler(on_raw_update))
    log.info("✅ VC handlers registered")
