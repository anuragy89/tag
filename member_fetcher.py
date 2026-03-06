"""
member_fetcher.py — Smart member fetcher for TagMaster Bot

Priority order:
  1. Pyrogram MTProto (gets ALL members + real UserStatus)
  2. Bot API getChatAdministrators (at least gets admins)
  3. MongoDB tracked members (everyone who ever messaged)

All members are stored in MongoDB. Tags ordered: Online > Recently > Last Week.
Members inactive > 7 days are tagged last (not excluded — we tag everyone).
"""

import os
import logging
import asyncio

import database as db

logger = logging.getLogger(__name__)

# ── Optional Pyrogram ─────────────────────────────────────────────────────────
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
    PYROGRAM_OK = True
    logger.info("Pyrogram available ✅")
except ImportError:
    PYROGRAM_OK = False
    logger.warning("Pyrogram not installed — using message-tracked fallback")

API_ID    = int(os.environ.get("API_ID",  "0"))
API_HASH  = os.environ.get("API_HASH",  "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

_pyro: "Client | None" = None


def _pyro_enabled() -> bool:
    return PYROGRAM_OK and bool(API_ID) and bool(API_HASH)


def get_pyro_client():
    global _pyro
    if not _pyro_enabled():
        return None
    if _pyro is None:
        _pyro = Client(
            name="tagmaster_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True,
        )
    return _pyro


async def start_pyro():
    c = get_pyro_client()
    if c is None:
        return
    try:
        if not c.is_connected:
            await c.start()
            me = await c.get_me()
            logger.info("Pyrogram started — @%s", me.username)
    except Exception as e:
        logger.warning("Pyrogram start failed: %s", e)


async def stop_pyro():
    global _pyro
    if _pyro is not None:
        try:
            if _pyro.is_connected:
                await _pyro.stop()
        except Exception:
            pass


# ── Status rank helpers ───────────────────────────────────────────────────────

def _rank(status) -> int:
    if not PYROGRAM_OK:
        return 50
    m = {
        UserStatus.ONLINE:     1,
        UserStatus.RECENTLY:   2,
        UserStatus.LAST_WEEK:  3,
        UserStatus.LAST_MONTH: 50,
        UserStatus.LONG_AGO:   90,
        UserStatus.EMPTY:      50,
    }
    return m.get(status, 50)


# ── Fetch via Pyrogram ────────────────────────────────────────────────────────

async def _fetch_via_pyrogram(chat_id: int) -> int:
    """
    Uses Pyrogram to get ALL members + their UserStatus.
    Returns count of members fetched. 0 = failed.
    """
    c = get_pyro_client()
    if c is None:
        return 0
    if not c.is_connected:
        try:
            await c.start()
        except Exception as e:
            logger.warning("Pyrogram reconnect failed: %s", e)
            return 0

    count = 0
    try:
        async for member in c.get_chat_members(chat_id):
            user = member.user
            if not user or user.is_bot or user.is_deleted:
                continue
            status = user.status or UserStatus.EMPTY
            await db.save_member_with_status(
                chat_id=chat_id,
                user_id=user.id,
                first_name=user.first_name or "User",
                username=user.username,
                status_rank=_rank(status),
                status_label=str(status),
            )
            count += 1
            await asyncio.sleep(0.005)

    except Exception as e:
        if PYROGRAM_OK:
            try:
                fw = FloodWait
                if isinstance(e, fw):
                    logger.warning("FloodWait %ss", e.value)
                    await asyncio.sleep(e.value + 2)
            except Exception:
                pass
        logger.warning("Pyrogram fetch error for %s: %s", chat_id, e)
        return count

    logger.info("Pyrogram fetched %d members for chat %s", count, chat_id)
    return count


# ── Main public function ──────────────────────────────────────────────────────

async def get_members_for_tagging(chat_id: int) -> list:
    """
    Returns the full member list sorted for tagging:
      Online (1) → Recently (2) → Last Week (3) → Others (50/90)

    Strategy:
      1. Try Pyrogram → gets everyone with real status
      2. Fall back to message-tracked MongoDB list (anyone who ever chatted)

    Never returns empty if any members are tracked.
    """
    # Step 1 — try Pyrogram
    fetched = await _fetch_via_pyrogram(chat_id)

    if fetched > 0:
        # Got fresh data — return ALL members sorted by status rank
        members = await db.get_all_members_sorted(chat_id)
        logger.info("Tagging %d members (Pyrogram) for chat %s", len(members), chat_id)
        return members

    # Step 2 — fall back to message-tracked list from MongoDB
    members = await db.get_group_members(chat_id)
    logger.info("Tagging %d members (fallback cache) for chat %s", len(members), chat_id)
    return members
