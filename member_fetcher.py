"""
member_fetcher.py  ──  Pyrogram MTProto member fetcher for TagMaster Bot

WHY Pyrogram instead of PTB for this:
  • Telegram Bot API (PTB) has NO method to list group members
  • PTB also cannot read UserStatus (online/offline/last seen)
  • Pyrogram uses MTProto which CAN do both — even with just a bot token
  • We run Pyrogram in bot mode (no user session needed)

What this module does:
  • Fetches ALL members of a group via get_chat_members()
  • Reads each member's UserStatus from Telegram
  • Stores them in MongoDB with a status_rank
  • Returns members sorted: Online → Recently → LastWeek only
  • Members last seen > 7 days are excluded from tagging

Status rank mapping:
  1 = Online right now          (tag first — guaranteed active)
  2 = Recently online           (was online in last few days)
  3 = Last seen within a week   (somewhat active)
  4 = Last seen within a month  (excluded by default)
  5 = Long time ago / empty     (excluded)
"""

import os
import logging
import asyncio
from datetime import datetime, timezone

from pyrogram import Client
from pyrogram.enums import UserStatus
from pyrogram.errors import (
    FloodWait,
    ChatAdminRequired,
    ChannelPrivate,
    PeerIdInvalid,
    RPCError,
)

import database as db

logger = logging.getLogger(__name__)

# ── Pyrogram client (bot mode — no user session needed) ──────────────────────
API_ID   = int(os.environ.get("API_ID",   "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Singleton Pyrogram client
_pyro_client: Client = None


def get_pyro_client() -> Client:
    """Return (or lazily create) the Pyrogram bot client."""
    global _pyro_client
    if _pyro_client is None:
        if not API_ID or not API_HASH:
            raise RuntimeError(
                "❌ API_ID and API_HASH are required for member fetching. "
                "Get them from https://my.telegram.org"
            )
        _pyro_client = Client(
            name="tagmaster_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True,          # No session file on disk
        )
    return _pyro_client


async def start_pyro():
    """Start the Pyrogram client. Called once at bot startup."""
    client = get_pyro_client()
    if not client.is_connected:
        await client.start()
        me = await client.get_me()
        logger.info("✅ Pyrogram client started — @%s", me.username)


async def stop_pyro():
    """Stop the Pyrogram client. Called on bot shutdown."""
    global _pyro_client
    if _pyro_client and _pyro_client.is_connected:
        await _pyro_client.stop()
        logger.info("Pyrogram client stopped.")


# ── Status helpers ────────────────────────────────────────────────────────────

def _status_rank(status: UserStatus) -> int:
    """
    Convert Pyrogram UserStatus to a sort rank.
    Lower = more active = tagged first.
    Returns 99 for excluded statuses.
    """
    rank_map = {
        UserStatus.ONLINE:       1,   # Currently online ✅
        UserStatus.RECENTLY:     2,   # Online in last 2–3 days ✅
        UserStatus.LAST_WEEK:    3,   # Online within 7 days ✅
        UserStatus.LAST_MONTH:   99,  # Too old — excluded
        UserStatus.LONG_AGO:     99,  # Very old — excluded
        UserStatus.EMPTY:        99,  # Hidden / unknown — excluded
    }
    return rank_map.get(status, 99)


def _status_label(status: UserStatus) -> str:
    labels = {
        UserStatus.ONLINE:    "🟢 Online",
        UserStatus.RECENTLY:  "🟡 Recently",
        UserStatus.LAST_WEEK: "🔵 Last week",
        UserStatus.LAST_MONTH:"⚪ Last month",
        UserStatus.LONG_AGO:  "⚫ Long ago",
        UserStatus.EMPTY:     "❓ Unknown",
    }
    return labels.get(status, "❓ Unknown")


# ── Core fetch function ───────────────────────────────────────────────────────

async def fetch_members(chat_id: int) -> dict:
    """
    Fetch ALL non-bot members of a group via Pyrogram MTProto.
    Stores them in MongoDB with status_rank.
    Returns a breakdown dict with counts per status tier.

    This is the ONLY reliable way to get the full member list
    — Telegram Bot API has no equivalent method.
    """
    client = get_pyro_client()

    if not client.is_connected:
        logger.warning("Pyrogram not connected — attempting reconnect")
        await client.start()

    stats = {"online": 0, "recently": 0, "last_week": 0, "excluded": 0, "total": 0}

    try:
        async for member in client.get_chat_members(chat_id):
            user = member.user
            if user.is_bot or user.is_deleted:
                continue

            status = user.status or UserStatus.EMPTY
            rank   = _status_rank(status)

            stats["total"] += 1

            # Save to MongoDB with status info
            await db.save_member_with_status(
                chat_id    = chat_id,
                user_id    = user.id,
                first_name = user.first_name or "User",
                username   = user.username,
                status_rank= rank,
                status_label=_status_label(status),
            )

            # Tally stats
            if rank == 1:   stats["online"]    += 1
            elif rank == 2: stats["recently"]  += 1
            elif rank == 3: stats["last_week"] += 1
            else:           stats["excluded"]  += 1

            # Tiny sleep to avoid hammering MTProto
            await asyncio.sleep(0.01)

    except FloodWait as e:
        logger.warning("FloodWait %ss while fetching members for %s", e.value, chat_id)
        await asyncio.sleep(e.value + 2)
    except ChatAdminRequired:
        logger.warning("Bot needs admin rights to fetch members in %s", chat_id)
    except (ChannelPrivate, PeerIdInvalid) as e:
        logger.warning("Cannot access chat %s: %s", chat_id, e)
    except RPCError as e:
        logger.error("RPCError fetching members for %s: %s", chat_id, e)
    except Exception as e:
        logger.exception("Unexpected error fetching members for %s: %s", chat_id, e)

    logger.info(
        "Fetched %d members for chat %s | online=%d recently=%d last_week=%d excluded=%d",
        stats["total"], chat_id,
        stats["online"], stats["recently"], stats["last_week"], stats["excluded"],
    )
    return stats


async def get_sorted_members(chat_id: int) -> tuple[list, dict]:
    """
    High-level function used by tag commands.

    1. Fetches fresh member list from Telegram via Pyrogram
    2. Sorts: Online (1) → Recently (2) → Last Week (3)
    3. Excludes Last Month / Long Ago / Unknown
    4. Returns (sorted_member_list, stats_dict)

    Falls back to MongoDB cache if Pyrogram fetch fails.
    """
    # Step 1: Fetch fresh data
    stats = await fetch_members(chat_id)

    # Step 2: Get sorted from MongoDB (status_rank ASC, excludes rank=99)
    members = await db.get_sorted_members(chat_id)

    # Step 3: Fallback — if Pyrogram got nothing, use full cached list
    if not members:
        logger.warning("Pyrogram returned no members — falling back to cached list for %s", chat_id)
        members = await db.get_group_members(chat_id)
        stats["fallback"] = True

    return members, stats
