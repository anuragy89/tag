"""
database.py — MongoDB async (motor) for TagMaster Bot
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
    logger.info("MongoDB connected: %s", DB_NAME)


# ── Users ─────────────────────────────────────────────────────────────────────

async def save_user(user_id: int, first_name: str, username: str = None):
    update_doc = {
        "$set": {
            "first_name": first_name,
            "username": username,
            "last_seen": datetime.now(timezone.utc),
        }
    }
    await _db.users.update_one({"user_id": user_id}, update_doc, upsert=True)


async def get_all_users() -> list:
    cursor = _db.users.find({}, {"user_id": 1, "_id": 0})
    return [doc["user_id"] async for doc in cursor]


async def count_users() -> int:
    return await _db.users.count_documents({})


# ── Groups ────────────────────────────────────────────────────────────────────

async def save_group(chat_id: int, title: str):
    update_doc = {
        "$set": {
            "title": title,
            "updated_at": datetime.now(timezone.utc),
        }
    }
    await _db.groups.update_one({"chat_id": chat_id}, update_doc, upsert=True)


async def get_all_groups() -> list:
    cursor = _db.groups.find({}, {"chat_id": 1, "_id": 0})
    return [doc["chat_id"] async for doc in cursor]


async def count_groups() -> int:
    return await _db.groups.count_documents({})


# ── Group members — lightweight (message tracking) ────────────────────────────

async def save_member(chat_id: int, user_id: int, first_name: str):
    """Called on every message. Does NOT overwrite status set by Pyrogram."""
    query = {"chat_id": chat_id, "user_id": user_id}
    update_doc = {
        "$set": {
            "first_name": first_name,
            "last_active": datetime.now(timezone.utc),
        },
        "$setOnInsert": {
            "status_rank": 99,
            "status_label": "Unknown",
            "last_fetch": None,
        },
    }
    await _db.group_members.update_one(query, update_doc, upsert=True)


# ── Group members — full save (from Pyrogram fetcher) ─────────────────────────

async def save_member_with_status(
    chat_id: int,
    user_id: int,
    first_name: str,
    username: str = None,
    status_rank: int = 99,
    status_label: str = "Unknown",
):
    """Called by Pyrogram member fetcher. Overwrites status fields."""
    query = {"chat_id": chat_id, "user_id": user_id}
    update_doc = {
        "$set": {
            "first_name": first_name,
            "username": username,
            "status_rank": status_rank,
            "status_label": status_label,
            "last_fetch": datetime.now(timezone.utc),
        }
    }
    await _db.group_members.update_one(query, update_doc, upsert=True)


async def get_sorted_members(chat_id: int) -> list:
    """
    Returns members sorted online-first.
    Rank 1 = online, 2 = recently, 3 = last week.
    Rank 99 (inactive) is excluded.
    """
    query  = {"chat_id": chat_id, "status_rank": {"$in": [1, 2, 3]}}
    fields = {"user_id": 1, "first_name": 1, "status_rank": 1, "status_label": 1, "_id": 0}
    cursor = _db.group_members.find(query, fields).sort("status_rank", 1)
    result = []
    async for doc in cursor:
        result.append({
            "user_id": doc["user_id"],
            "first_name": doc["first_name"],
            "status_rank": doc.get("status_rank", 99),
            "status_label": doc.get("status_label", "Unknown"),
        })
    return result


async def get_group_members(chat_id: int) -> list:
    """Fallback: all tracked members, sorted by rank."""
    cursor = _db.group_members.find(
        {"chat_id": chat_id},
        {"user_id": 1, "first_name": 1, "status_rank": 1, "_id": 0},
    ).sort("status_rank", 1)
    result = []
    async for doc in cursor:
        result.append({
            "user_id": doc["user_id"],
            "first_name": doc["first_name"],
        })
    return result


async def count_group_members(chat_id: int) -> int:
    return await _db.group_members.count_documents({"chat_id": chat_id})


async def count_active_members(chat_id: int) -> int:
    return await _db.group_members.count_documents(
        {"chat_id": chat_id, "status_rank": {"$in": [1, 2, 3]}}
    )


# ── Tag states ────────────────────────────────────────────────────────────────

async def set_tag_state(chat_id: int, task_key: str, state: str):
    query      = {"chat_id": chat_id, "task_key": task_key}
    update_doc = {"$set": {"state": state}}
    await _db.tag_states.update_one(query, update_doc, upsert=True)


async def get_tag_state(chat_id: int, task_key: str) -> str:
    query = {"chat_id": chat_id, "task_key": task_key}
    doc   = await _db.tag_states.find_one(query, {"state": 1, "_id": 0})
    return doc["state"] if doc else "idle"


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    users  = await count_users()
    groups = await count_groups()
    return {"users": users, "groups": groups}
