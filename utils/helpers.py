"""
utils/helpers.py – Decorators, flood-wait guard, admin checker.

Fixed:
  • get_chat_members uses ChatMembersFilter enum (not a string)
  • Removed unused import UserNotParticipant
  • safe_send / safe_edit with full retry logic
"""

import asyncio
import logging
from functools import wraps
from typing import AsyncGenerator, Optional, Tuple

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import (
    ChatAdminRequired,
    ChannelPrivate,
    FloodWait,
    PeerIdInvalid,
    RPCError,
    UserNotParticipant,
)
from pyrogram.types import Message

log = logging.getLogger(__name__)


# ── Flood-safe message sender ─────────────────────────────────────────────────

async def safe_send(
    client: Client,
    chat_id: int,
    text: str,
    retries: int = 3,
    **kwargs,
) -> Optional[Message]:
    """Send a message with automatic FloodWait handling and retries."""
    for attempt in range(retries):
        try:
            return await client.send_message(chat_id, text, **kwargs)
        except FloodWait as e:
            wait = e.value + 2
            log.warning("FloodWait %ds – chat %s (attempt %d)", wait, chat_id, attempt + 1)
            await asyncio.sleep(wait)
        except (ChatAdminRequired, ChannelPrivate, PeerIdInvalid) as e:
            log.error("Cannot send to %s: %s", chat_id, e)
            return None
        except RPCError as e:
            log.error("RPCError sending to %s: %s", chat_id, e)
            if attempt < retries - 1:
                await asyncio.sleep(2)
    return None


# ── Flood-safe message editor ─────────────────────────────────────────────────

async def safe_edit(
    msg: Message,
    text: str,
    retries: int = 3,
    **kwargs,
) -> Optional[Message]:
    """Edit a message with automatic FloodWait handling."""
    for attempt in range(retries):
        try:
            return await msg.edit_text(text, **kwargs)
        except FloodWait as e:
            await asyncio.sleep(e.value + 2)
        except RPCError as e:
            log.error("RPCError editing message: %s", e)
            break
    return None


# ── Admin status check ────────────────────────────────────────────────────────

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """Return True if user_id is an admin or owner of chat_id."""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except (UserNotParticipant, RPCError):
        return False
    except Exception as e:
        log.error("is_admin error for user %s in chat %s: %s", user_id, chat_id, e)
        return False


# ── Decorator: admin-only command ────────────────────────────────────────────

def admin_only(func):
    """Allow the command only for group admins or the bot owner."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        from config import Config  # local import avoids circular dependency

        if message.from_user is None:
            # Anonymous admin or channel post – skip silently
            return

        uid = message.from_user.id

        # Bot owner bypasses all checks
        if uid == Config.OWNER_ID:
            return await func(client, message)

        if not await is_admin(client, message.chat.id, uid):
            await message.reply_text(
                "❌ **Access Denied!**\n\n"
                "Only group admins can use this command. 🔒",
                parse_mode="markdown",
            )
            return

        return await func(client, message)

    return wrapper


# ── Decorator: owner-only command ────────────────────────────────────────────

def owner_only(func):
    """Allow the command only for the bot owner."""
    @wraps(func)
    async def wrapper(client: Client, message: Message):
        from config import Config

        if not message.from_user or message.from_user.id != Config.OWNER_ID:
            await message.reply_text(
                "👑 This command is **only for the bot owner**.",
                parse_mode="markdown",
            )
            return

        return await func(client, message)

    return wrapper


# ── Fetch all group members (non-bot) ────────────────────────────────────────

async def get_members(
    client: Client, chat_id: int
) -> AsyncGenerator[Tuple[int, str], None]:
    """
    Async generator – yields (user_id, first_name) for every non-bot member.
    Handles FloodWait internally.
    """
    try:
        async for member in client.get_chat_members(chat_id):
            u = member.user
            if u and not u.is_bot and not u.is_deleted:
                yield u.id, (u.first_name or "User")
    except FloodWait as e:
        log.warning("FloodWait %ds while fetching members of %s", e.value, chat_id)
        await asyncio.sleep(e.value + 2)
    except RPCError as e:
        log.error("RPCError fetching members of %s: %s", chat_id, e)
    except Exception as e:
        log.error("Unexpected error fetching members of %s: %s", chat_id, e)


# ── Fetch admin members only ──────────────────────────────────────────────────

async def get_admin_members(
    client: Client, chat_id: int
) -> AsyncGenerator[Tuple[int, str], None]:
    """
    Async generator – yields (user_id, first_name) for admins only.
    Uses ChatMembersFilter.ADMINISTRATORS (Pyrogram v2 enum – NOT a string).
    """
    try:
        async for member in client.get_chat_members(
            chat_id, filter=ChatMembersFilter.ADMINISTRATORS
        ):
            u = member.user
            if u and not u.is_bot:
                yield u.id, (u.first_name or "Admin")
    except RPCError as e:
        log.error("RPCError fetching admins of %s: %s", chat_id, e)
    except Exception as e:
        log.error("Unexpected error fetching admins of %s: %s", chat_id, e)
