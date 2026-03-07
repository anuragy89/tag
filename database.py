"""
database.py – Async MongoDB layer using Motor.

Collections:
  • users  → tracks every user who starts the bot or messages in a group
  • groups → tracks every group the bot is added to

Motor is the official async MongoDB driver for Python (asyncio-compatible).
Install: pip install motor dnspython
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

import motor.motor_asyncio
from pymongo import UpdateOne

from config import Config

log = logging.getLogger(__name__)

# ── Module-level client & collection references ───────────────────────────────
_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

users_col:  Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None
groups_col: Optional[motor.motor_asyncio.AsyncIOMotorCollection] = None


# ── Initialise ────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """Connect to MongoDB and ensure indexes exist."""
    global _client, _db, users_col, groups_col

    _client = motor.motor_asyncio.AsyncIOMotorClient(
        Config.MONGO_URI,
        serverSelectionTimeoutMS=10_000,   # fail fast if URI is wrong
    )
    _db = _client[Config.MONGO_DB_NAME]

    users_col  = _db["users"]
    groups_col = _db["groups"]

    # Unique indexes (safe to call repeatedly – MongoDB is idempotent here)
    await users_col.create_index("user_id",  unique=True, background=True)
    await groups_col.create_index("chat_id", unique=True, background=True)

    # Verify connection is alive
    await _client.admin.command("ping")
    log.info("✅ MongoDB connected  –  db: %s", Config.MONGO_DB_NAME)


async def close_db() -> None:
    """Close the MongoDB connection gracefully."""
    if _client is not None:
        _client.close()
        log.info("🔒 MongoDB connection closed.")


# ══════════════════════════════════════════════════════════════════════════════
#  Users
# ══════════════════════════════════════════════════════════════════════════════

async def upsert_user(
    user_id: int,
    username: Optional[str] = None,
    full_name: Optional[str] = None,
) -> None:
    """Insert or update a user document."""
    await users_col.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "username":  username,
                "full_name": full_name,
                "updated_at": datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "user_id":   user_id,
                "joined_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


async def get_all_user_ids() -> List[int]:
    """Return a list of all tracked user IDs."""
    cursor = users_col.find({}, {"user_id": 1, "_id": 0})
    return [doc["user_id"] async for doc in cursor]


async def count_users() -> int:
    """Return total number of tracked users."""
    return await users_col.count_documents({})


# ══════════════════════════════════════════════════════════════════════════════
#  Groups
# ══════════════════════════════════════════════════════════════════════════════

async def upsert_group(
    chat_id: int,
    title: Optional[str] = None,
    username: Optional[str] = None,
    member_count: int = 0,
) -> None:
    """Insert or update a group document."""
    await groups_col.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "title":        title,
                "username":     username,
                "member_count": member_count,
                "updated_at":   datetime.now(timezone.utc),
            },
            "$setOnInsert": {
                "chat_id":   chat_id,
                "joined_at": datetime.now(timezone.utc),
            },
        },
        upsert=True,
    )


async def remove_group(chat_id: int) -> None:
    """Remove a group from the database (bot was kicked)."""
    await groups_col.delete_one({"chat_id": chat_id})


async def get_all_chat_ids() -> List[int]:
    """Return a list of all tracked group chat IDs."""
    cursor = groups_col.find({}, {"chat_id": 1, "_id": 0})
    return [doc["chat_id"] async for doc in cursor]


async def count_groups() -> int:
    """Return total number of tracked groups."""
    return await groups_col.count_documents({})
