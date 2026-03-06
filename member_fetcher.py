"""
member_fetcher.py — 3-tier member fetcher

Tier 1: Pyrogram MTProto   — ALL members + real UserStatus
Tier 2: MongoDB cache      — everyone who ever messaged
Tier 3: []                 — bot.py falls back to Bot API admins

Sorted: Online(1) → Recently(2) → LastWeek(3) → Others(50+)
"""

import os
import logging
import asyncio

import database as db

logger = logging.getLogger(__name__)

try:
    from pyrogram import Client
    from pyrogram.enums import UserStatus
    from pyrogram.errors import FloodWait
    PYROGRAM_OK = True
except ImportError:
    PYROGRAM_OK = False
    logger.warning("Pyrogram not installed — using DB cache fallback")

API_ID    = int(os.environ.get("API_ID",   "0"))
API_HASH  = os.environ.get("API_HASH",  "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

_pyro = None


def _pyro_enabled():
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


def _rank(status):
    if not PYROGRAM_OK:
        return 50
    return {
        UserStatus.ONLINE:     1,
        UserStatus.RECENTLY:   2,
        UserStatus.LAST_WEEK:  3,
        UserStatus.LAST_MONTH: 50,
        UserStatus.LONG_AGO:   90,
        UserStatus.EMPTY:      50,
    }.get(status, 50)


async def _fetch_pyrogram(chat_id):
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
        if PYROGRAM_OK and isinstance(e, FloodWait):
            await asyncio.sleep(e.value + 2)
        logger.warning("Pyrogram fetch error %s: %s", chat_id, e)
    if count:
        logger.info("Pyrogram fetched %d members for %s", count, chat_id)
    return count


async def get_members_for_tagging(chat_id):
    """
    Returns sorted member list. Never raises.
    Tries Pyrogram → DB cache → returns [] (bot.py handles empty with admin fallback).
    """
    fetched = await _fetch_pyrogram(chat_id)
    if fetched > 0:
        members = await db.get_all_members_sorted(chat_id)
        if members:
            return members

    members = await db.get_group_members(chat_id)
    if members:
        logger.info("DB cache: %d members for %s", len(members), chat_id)
        return members

    return []
