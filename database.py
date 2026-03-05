"""
database.py  ──  MongoDB (motor async driver) for TagMaster Bot
Collections:
  • users         – every user who /start'd the bot
  • groups        – every group the bot was added to
  • group_members – members with Telegram status + last_fetch timestamp
  • tag_states    – per-group running/paused/stopped state

v3 additions:
  • save_member_with_status()  — stores status_rank + status_label
  • get_sorted_members()       — returns only rank 1-3, sorted by rank
  • last_fetch field           — tracks when member data was last refreshed
"""

import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME", "tagmaster")

_client = None
_db     = None


def get_db():
    return _db


async def init_db():
    global _client, _db
    _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=10_000)
    _db = _client[DB_NAME]

    await _db.users.create_index("user_id", unique=True)
    await _db.groups.create_index("chat_id", unique=True)
    await _db.group_members.create_index(
        [("chat_id", 1), ("user_id", 1)], unique=True
    )
    await _db.group_members.create_index(
        [("chat_id", 1), ("status_rank", 1)]
    )
    await _db.tag_states.create_index(
        [("chat_id", 1), ("task_key", 1)], unique=True
    )
    logger.info("MongoDB connected — database: %s", DB_NAME)


# Users

async def save_user(user_id: int, first_name: str, username: str = None):
    await _db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "first_name": first_name,
            "username":   username,
            "last_seen":  datetime.now(timezone.utc),
        }},
        upsert=True,
    )


async def get_all_users() -> list:
    return [doc["user_id"] async for doc in _db.users.find({}, {"user_id": 1, "_id": 0})]


async def count_users() -> int:
    return await _db.users.count_documents({})


# Groups

async def save_group(chat_id: int, title: str):
    await _db.groups.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


async def get_all_groups() -> list:
    return [doc["chat_id"] async for doc in _db.groups.find({}, {"chat_id": 1, "_id": 0})]


async def count_groups() -> int:
    return await _db.groups.count_documents({})


# Group members - basic save (message tracking)

async def save_member(chat_id: int, user_id: int, first_name: str):
    """Lightweight save triggered on every message. Does not overwrite status."""
    await _db.group_members.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$set":         {"first_name": first_name,
                             "last_active": datetime.now(timezone.utc)},
            "$setOnInsert": {
                "status_rank":  99,
                "status_label": "Unknown",
                "last_fetch":   None,
            },
        },
        upsert=True,
    )


# Group members - full save (from Pyrogram fetcher)

async def save_member_with_status(
    chat_id: int,
    user_id: int,
    first_name: str,
    username: str = None,
    status_rank: int = 99,
    status_label: str = "Unknown",
):
    """Full save from Pyrogram — overwrites status fields."""
    await _db.group_members.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {
            "first_name":   first_name,
            "username":     username,
            "status_rank":  status_rank,
            "status_label": status_label,
            "last_fetch":   datetime.now(timezone.utc),
        }},
        upsert=True,
    )


async def get_sorted_members(chat_id: int) -> list:
    """
    Returns members sorted by status_rank ASC (online first).
    Only rank 1 (online), 2 (recently), 3 (last week).
    Excludes rank 99 (last month / long ago / unknown).
    """
    cursor = _db.group_members.find(
        {"chat_id": chat_id, "status_rank": {"$in": [1, 2, 3]}},
        {"user_id": 1, "first_name": 1, "status_rank": 1, "status_label": 1, "_id": 0},
    ).sort("status_rank", 1)

    return [
        {
            "user_id":      d["user_id"],
            "first_name":   d["first_name"],
            "status_rank":  d.get("status_rank", 99),
            "status_label": d.get("status_label", "Unknown"),
        }
        async for d in cursor
    ]


async def get_group_members(chat_id: int) -> list:
    """Fallback: returns ALL tracked members sorted by rank."""
    cursor = _db.group_members.find(
        {"chat_id": chat_id},
        {"user_id": 1, "first_name": 1, "status_rank": 1, "_id": 0},
    ).sort("status_rank", 1)
    return [{"user_id": d["user_id"], "first_name": d["first_name"]} async for d in cursor]


async def count_group_members(chat_id: int) -> int:
    return await _db.group_members.count_documents({"chat_id": chat_id})


async def count_active_members(chat_id: int) -> int:
    return await _db.group_members.count_documents(
        {"chat_id": chat_id, "status_rank": {"$in": [1, 2, 3]}}
    )


# Tag states

async def set_tag_state(chat_id: int, task_key: str, state: str):
    await _db.tag_states.update_one(
        {"chat_id": chat_id, "task_key": task_key},
        {"$set": {"state": state}},
        upsert=True,
    )


async def get_tag_state(chat_id: int, task_key: str) -> str:
    doc = await _db.tag_states.find_one(
        {"chat_id": chat_id, "task_key": task_key},
        {"state": 1, "_id": 0},
    )
    return doc["state"] if doc else "idle"


# Stats

async def get_stats() -> dict:
    return {
        "users":  await count_users(),
        "groups": await count_groups(),
    }}
