"""
member_fetcher.py — Pyrogram MTProto member fetcher for TagMaster Bot

Uses Pyrogram (MTProto) to fetch full group member lists and read
UserStatus — something the Bot API cannot do.

If pyrogram is unavailable at runtime, all functions gracefully fall
back to the message-tracked member list stored in MongoDB.

Status rank:
  1 = Online now        (tagged first)
  2 = Recently online
  3 = Last seen this week
  99 = Older / unknown  (excluded from tagging)
"""

import os
import logging
import asyncio
from datetime import datetime, timezone

import database as db

logger = logging.getLogger(__name__)

# ── Optional Pyrogram import ──────────────────────────────────────────────────
try:
    from pyrogram import Client
    from pyrogram.enums import UserStatus
    from pyrogram.errors import (
        FloodWait,
        ChatAdminRequired,
        ChannelPrivate,
        PeerIdInvalid,
        RPCError,
    )
    PYROGRAM_AVAILABLE = True
    logger.info("Pyrogram available — smart member fetching enabled")
except ImportError:
    PYROGRAM_AVAILABLE = False
    logger.warning(
        "Pyrogram not installed — member fetching will use message-tracked "
        "fallback only. Install pyrogram + tgcrypto to enable smart fetching."
    )

# ── Config ────────────────────────────────────────────────────────────────────
API_ID    = int(os.environ.get("API_ID", "0"))
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

_pyro_client = None


def get_pyro_client():
    global _pyro_client
    if not PYROGRAM_AVAILABLE:
        return None
    if _pyro_client is None:
        if not API_ID or not API_HASH:
            logger.warning("API_ID/API_HASH not set — Pyrogram disabled")
            return None
        _pyro_client = Client(
            name="tagmaster_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True,
        )
    return _pyro_client


async def start_pyro():
    client = get_pyro_client()
    if client is None:
        return
    try:
        if not client.is_connected:
            await client.start()
            me = await client.get_me()
            logger.info("Pyrogram started — @%s", me.username)
    except Exception as e:
        logger.warning("Pyrogram start failed: %s", e)


async def stop_pyro():
    global _pyro_client
    if _pyro_client is not None:
        try:
            if _pyro_client.is_connected:
                await _pyro_client.stop()
        except Exception:
            pass


# ── Status helpers ────────────────────────────────────────────────────────────

def _status_rank(status) -> int:
    if not PYROGRAM_AVAILABLE:
        return 99
    rank_map = {
        UserStatus.ONLINE:      1,
        UserStatus.RECENTLY:    2,
        UserStatus.LAST_WEEK:   3,
        UserStatus.LAST_MONTH:  99,
        UserStatus.LONG_AGO:    99,
        UserStatus.EMPTY:       99,
    }
    return rank_map.get(status, 99)


def _status_label(status) -> str:
    if not PYROGRAM_AVAILABLE:
        return "Unknown"
    labels = {
        UserStatus.ONLINE:      "Online",
        UserStatus.RECENTLY:    "Recently",
        UserStatus.LAST_WEEK:   "Last week",
        UserStatus.LAST_MONTH:  "Last month",
        UserStatus.LONG_AGO:    "Long ago",
        UserStatus.EMPTY:       "Unknown",
    }
    return labels.get(status, "Unknown")


# ── Core fetch ────────────────────────────────────────────────────────────────

async def fetch_members(chat_id: int) -> dict:
    """
    Fetch all members via Pyrogram and store in MongoDB with status.
    Returns stats dict. Falls back gracefully if Pyrogram unavailable.
    """
    stats = {"online": 0, "recently": 0, "last_week": 0, "excluded": 0, "total": 0, "fallback": False}

    client = get_pyro_client()
    if client is None:
        stats["fallback"] = True
        return stats

    if not client.is_connected:
        try:
            await client.start()
        except Exception as e:
            logger.warning("Pyrogram reconnect failed: %s", e)
            stats["fallback"] = True
            return stats

    try:
        async for member in client.get_chat_members(chat_id):
            user = member.user
            if user.is_bot or user.is_deleted:
                continue

            status = user.status or UserStatus.EMPTY
            rank   = _status_rank(status)
            label  = _status_label(status)
            stats["total"] += 1

            await db.save_member_with_status(
                chat_id=chat_id,
                user_id=user.id,
                first_name=user.first_name or "User",
                username=user.username,
                status_rank=rank,
                status_label=label,
            )

            if rank == 1:
                stats["online"] += 1
            elif rank == 2:
                stats["recently"] += 1
            elif rank == 3:
                stats["last_week"] += 1
            else:
                stats["excluded"] += 1

            await asyncio.sleep(0.01)

    except FloodWait as e:
        logger.warning("FloodWait %ss fetching members for %s", e.value, chat_id)
        await asyncio.sleep(e.value + 2)
    except (ChatAdminRequired, ChannelPrivate, PeerIdInvalid) as e:
        logger.warning("Cannot fetch members for %s: %s", chat_id, e)
        stats["fallback"] = True
    except RPCError as e:
        logger.error("RPCError for %s: %s", chat_id, e)
        stats["fallback"] = True
    except Exception as e:
        logger.exception("Unexpected error fetching members for %s: %s", chat_id, e)
        stats["fallback"] = True

    return stats


async def get_sorted_members(chat_id: int) -> tuple:
    """
    Returns (member_list, stats_dict).
    Uses Pyrogram if available, falls back to cached MongoDB list.
    """
    stats = await fetch_members(chat_id)

    # Get sorted active members from MongoDB
    members = await db.get_sorted_members(chat_id)

    # If Pyrogram got nothing (fallback), use all tracked members
    if not members:
        members = await db.get_group_members(chat_id)
        stats["fallback"] = True

    return members, stats
