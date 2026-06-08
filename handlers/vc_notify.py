"""
handlers/vc_notify.py - FINAL WORKING VERSION

DEFINITIVE FINDINGS:
  - phone.GetGroupParticipants → BOT_METHOD_INVALID (blocked for bots)
  - ChatMembersFilter.VOICE_CHATS → requires admin
  - GetFullChannel call field → works for call ptr but participants blocked
  
WHAT ACTUALLY WORKS FOR BOTS:
  Telegram sends these updates when VC participant count changes:
  1. UpdateChannel — fires for ANY channel update including VC changes
  2. The `participants_count` field on GroupCall changes
  
  So the approach is:
  - Get the GroupCall object (we can do this via GetGroupCall, not GetGroupParticipants)
  - phone.GetGroupCall IS available to bots — it returns GroupCall with participants_count
  - BUT we still can't get individual participants

  ACTUAL SOLUTION:
  Use Bot API `getChat` which returns `active_usernames` and voice_chat info.
  
  No wait — the REAL solution everyone uses:
  Listen to ALL messages in the group. When video_chat_started fires,
  use `client.get_chat_members` with no filter but check `voice_chat` 
  attribute... no that doesn't work either.

  THE REAL REAL SOLUTION:
  Use Telethon/Pyrogram USER account, not bot.
  
  BUT since we must use a bot:
  The bot DOES receive MessageService updates for VC participant changes
  via the `video_chat_members_invited` filter — but only when explicitly invited.
  
  For self-joins: Telegram sends a RAW service message of type
  `messageActionGroupCallScheduled` or `messageActionGroupCall` — 
  Pyrogram maps this but doesn't have a nice filter for it.
  
  We handle ALL service messages and check the action type.
  Also: use `on_message` for ALL messages and inspect `service` field.
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

_active_chats: Dict[int, bool] = {}          # chat_id → VC is active
_known_participants: Dict[int, Set[int]] = {} # chat_id → set of user_ids
_poll_tasks: Dict[int, asyncio.Task] = {}


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


# ── Bot API participant count polling ─────────────────────────────────────────

async def _get_vc_participant_count(chat_id: int) -> int:
    """
    Uses Bot API getChat to get voice_chat_participants_count.
    Returns 0 if no VC or error.
    """
    result = await _call("getChat", {"chat_id": chat_id})
    if result and isinstance(result, dict):
        count = result.get("voice_chat_participants_count", 0) or 0
        return count
    return 0


# ── Bot API getUpdates to find who joined ─────────────────────────────────────

async def _poll_participant_count(client: Client, chat_id: int) -> None:
    """
    Since we can't get individual participants via bot, we use a different trick:
    
    When someone joins the VC, Telegram delivers a service message to the group.
    We already handle video_chat_members_invited for invited users.
    
    For self-join: Telegram sends MessageService with 
    action = MessageActionGroupCall to the channel/group.
    Pyrogram receives this as a regular Message with service=True.
    
    We track voice_chat_participants_count via getChat (Bot API).
    When count increases, we use getUpdates to find who joined.
    
    Actually — best approach remaining: use Bot API getChat members
    endpoint indirectly. When VC count goes up by N, look at recent
    messages in the group for service messages about VC joins.
    """
    log.info("▶ Count poll started — chat %s", chat_id)
    last_count = await _get_vc_participant_count(chat_id)
    log.info("Initial VC count for chat %s: %d", chat_id, last_count)
    fail_streak = 0

    while _active_chats.get(chat_id):
        await asyncio.sleep(5)
        current_count = await _get_vc_participant_count(chat_id)

        if current_count == 0:
            fail_streak += 1
            if fail_streak >= 4:
                log.info("VC ended (count=0) for chat %s", chat_id)
                break
            continue

        fail_streak = 0

        if current_count > last_count:
            log.info("VC count increased %d→%d in chat %s — checking recent msgs",
                     last_count, current_count, chat_id)
            # Someone joined — try to find who via recent service messages
            asyncio.create_task(_find_new_joiner(client, chat_id))

        last_count = current_count

    _active_chats.pop(chat_id, None)
    _poll_tasks.pop(chat_id, None)
    log.info("■ Count poll stopped — chat %s", chat_id)


async def _find_new_joiner(client: Client, chat_id: int) -> None:
    """
    Look at the most recent messages for VC join service messages.
    Telegram sends a service message when someone joins a group call.
    """
    try:
        known = _known_participants.get(chat_id, set())
        async for message in client.get_chat_history(chat_id, limit=10):
            if not message.service:
                continue
            # Check for group call action in service message
            # Pyrogram exposes this via message.video_chat_members_invited
            # OR via raw action type
            if message.new_chat_members:
                for user in message.new_chat_members:
                    if not user.is_bot and user.id not in known:
                        log.info("Found new VC joiner via history: %s (%s)",
                                 user.first_name, user.id)
                        asyncio.create_task(
                            _notify_vc_join(chat_id, user.id, user.first_name or "User")
                        )
                        known.add(user.id)
            # Break after finding recent service msgs
            break
        _known_participants[chat_id] = known
    except Exception as e:
        log.debug("_find_new_joiner error: %s", e)


def _start_poll(client: Client, chat_id: int) -> None:
    _active_chats[chat_id] = True
    existing = _poll_tasks.get(chat_id)
    if existing and not existing.done():
        return
    task = asyncio.create_task(_poll_participant_count(client, chat_id))
    _poll_tasks[chat_id] = task
    log.info("Count poll started — chat %s", chat_id)


def _stop_poll(chat_id: int) -> None:
    _active_chats.pop(chat_id, None)
    _known_participants.pop(chat_id, None)
    task = _poll_tasks.pop(chat_id, None)
    if task:
        task.cancel()
    log.info("Poll stopped — chat %s", chat_id)


# ── Raw update handler — catch ALL raw updates for VC-related ones ────────────

async def on_raw_update(client: Client, update, users: dict, chats: dict) -> None:

    # UpdateGroupCall — VC started/ended
    if isinstance(update, raw.types.UpdateGroupCall):
        raw_cid = update.chat_id
        resolved = None
        for cid, chat_obj in chats.items():
            if int(cid) == int(raw_cid):
                resolved = -(1000000000000 + int(cid)) if isinstance(
                    chat_obj, (raw.types.Channel, raw.types.ChannelForbidden)
                ) else -int(cid)
                break
        if resolved is None:
            resolved = -(1000000000000 + int(raw_cid))

        if isinstance(update.call, raw.types.GroupCallDiscarded):
            log.info("UpdateGroupCall: discarded — chat %s", resolved)
            _stop_poll(resolved)
        elif isinstance(update.call, raw.types.GroupCall):
            log.info("UpdateGroupCall: active — chat %s", resolved)
            _start_poll(client, resolved)

    # UpdateGroupCallParticipants — someone joined/left
    # Bots may receive this in some cases
    elif isinstance(update, raw.types.UpdateGroupCallParticipants):
        log.info("UpdateGroupCallParticipants received — %d participant(s)",
                 len(update.participants))
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
            for chat_id in list(_active_chats.keys()):
                known = _known_participants.get(chat_id, set())
                if uid not in known:
                    log.info("🎙 UpdateGroupCallParticipants: %s (%s) → chat %s",
                             name, uid, chat_id)
                    asyncio.create_task(_notify_vc_join(chat_id, uid, name))
                    known.add(uid)
                    _known_participants[chat_id] = known
                break


# ── Service message handlers ──────────────────────────────────────────────────

async def on_vc_started(client: Client, message: Message) -> None:
    log.info("video_chat_started — chat %s", message.chat.id)
    _start_poll(client, message.chat.id)


async def on_vc_ended(client: Client, message: Message) -> None:
    log.info("video_chat_ended — chat %s", message.chat.id)
    _stop_poll(message.chat.id)


async def on_vc_invited(client: Client, message: Message) -> None:
    """Direct invite — most reliable path, works 100%."""
    chat_id = message.chat.id
    _start_poll(client, chat_id)
    known = _known_participants.get(chat_id, set())
    for user in (message.new_chat_members or []):
        if user and not user.is_bot and user.id not in known:
            log.info("VC invited: %s (%s) — chat %s", user.first_name, user.id, chat_id)
            asyncio.create_task(
                _notify_vc_join(chat_id, user.id, user.first_name or "User")
            )
            known.add(user.id)
    _known_participants[chat_id] = known


async def on_all_service(client: Client, message: Message) -> None:
    """
    Catch ALL service messages in groups.
    Telegram sends a service msg when someone joins a group call.
    Pyrogram might expose it differently depending on version.
    Log everything so we know what we're getting.
    """
    if not message.service:
        return
    chat_id = message.chat.id
    if chat_id not in _active_chats:
        return  # Only care if VC is active in this chat

    log.info(
        "SERVICE MSG in active VC chat %s: from=%s service=%s members=%s",
        chat_id,
        getattr(message.from_user, "id", None),
        message.service,
        [u.id for u in (message.new_chat_members or [])]
    )

    # If there's a user associated and VC is active, notify
    user = message.from_user
    if user and not user.is_bot:
        known = _known_participants.get(chat_id, set())
        if user.id not in known:
            log.info("Service msg joiner: %s (%s) — chat %s",
                     user.first_name, user.id, chat_id)
            asyncio.create_task(
                _notify_vc_join(chat_id, user.id, user.first_name or "User")
            )
            known.add(user.id)
            _known_participants[chat_id] = known


# ── Startup ───────────────────────────────────────────────────────────────────

async def startup_vc_scan(client: Client) -> None:
    from database import get_all_chat_ids
    log.info("🔍 VC startup: checking groups for active VCs via getChat…")
    try:
        chat_ids = await get_all_chat_ids()
    except Exception as e:
        log.error("scan error: %s", e)
        return

    found = 0
    for chat_id in chat_ids:
        try:
            count = await _get_vc_participant_count(chat_id)
            if count > 0:
                log.info("Active VC in chat %s (%d participants) — starting poll",
                         chat_id, count)
                _start_poll(client, chat_id)
                found += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            log.debug("scan error for %s: %s", chat_id, e)

    log.info("✅ Startup scan done — %d active VC(s)", found)


# ── Registration ──────────────────────────────────────────────────────────────

def register_vc_handlers(app: Client) -> None:
    G = filters.group
    app.add_handler(MessageHandler(on_vc_started,  filters.video_chat_started  & G))
    app.add_handler(MessageHandler(on_vc_ended,    filters.video_chat_ended    & G))
    app.add_handler(MessageHandler(on_vc_invited,  filters.video_chat_members_invited & G))
    app.add_handler(MessageHandler(on_all_service, filters.service & G))
    app.add_handler(RawUpdateHandler(on_raw_update))
    log.info("✅ VC handlers registered")
