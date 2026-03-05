"""
database.py  ──  MongoDB (motor async driver) for TagMaster Bot
Collections:
  • users         – every user who /start'd the bot
  • groups        – every group the bot was added to
  • group_members – members seen chatting in a group
  • tag_states    – per-group running/paused/stopped state
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME", "tagmaster")

_client: AsyncIOMotorClient = None
_db = None


def get_db():
    """Return the motor database handle (call after init_db())."""
    return _db


async def init_db():
    """Connect to MongoDB and create indexes."""
    global _client, _db
    _client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=10_000)
    _db = _client[DB_NAME]

    # Indexes
    await _db.users.create_index("user_id",  unique=True)
    await _db.groups.create_index("chat_id", unique=True)
    await _db.group_members.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
    await _db.tag_states.create_index([("chat_id", 1), ("task_key", 1)], unique=True)

    logger.info("✅ MongoDB connected — database: %s", DB_NAME)


# ── Users ─────────────────────────────────────────────────────────────────────

async def save_user(user_id: int, first_name: str, username: str = None):
    await _db.users.update_one(
        {"user_id": user_id},
        {"$set": {"first_name": first_name, "username": username}},
        upsert=True,
    )


async def get_all_users() -> list[int]:
    cursor = _db.users.find({}, {"user_id": 1, "_id": 0})
    return [doc["user_id"] async for doc in cursor]


async def count_users() -> int:
    return await _db.users.count_documents({})


# ── Groups ────────────────────────────────────────────────────────────────────

async def save_group(chat_id: int, title: str):
    await _db.groups.update_one(
        {"chat_id": chat_id},
        {"$set": {"title": title}},
        upsert=True,
    )


async def get_all_groups() -> list[int]:
    cursor = _db.groups.find({}, {"chat_id": 1, "_id": 0})
    return [doc["chat_id"] async for doc in cursor]


async def count_groups() -> int:
    return await _db.groups.count_documents({})


# ── Group members ─────────────────────────────────────────────────────────────

async def save_member(chat_id: int, user_id: int, first_name: str):
    await _db.group_members.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"first_name": first_name}},
        upsert=True,
    )


async def get_group_members(chat_id: int) -> list[dict]:
    cursor = _db.group_members.find(
        {"chat_id": chat_id},
        {"user_id": 1, "first_name": 1, "_id": 0},
    )
    return [{"user_id": d["user_id"], "first_name": d["first_name"]} async for d in cursor]


async def count_group_members(chat_id: int) -> int:
    return await _db.group_members.count_documents({"chat_id": chat_id})


# ── Tag states ────────────────────────────────────────────────────────────────

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


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_stats() -> dict:
    users  = await count_users()
    groups = await count_groups()
    return {"users": users, "groups": groups}
