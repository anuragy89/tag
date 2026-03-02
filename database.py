import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["tagbot"]

users_col = db.users
groups_col = db.groups


# ---------- ADD / UPDATE ----------

async def add_user(user_id: int):
    await users_col.update_one(
        {"_id": user_id},
        {"$set": {"_id": user_id}},
        upsert=True
    )


async def add_group(group_id: int):
    await groups_col.update_one(
        {"_id": group_id},
        {"$set": {"_id": group_id}},
        upsert=True
    )


# ---------- REQUIRED FOR BROADCAST ----------

async def get_users():
    users = []
    async for u in users_col.find({}):
        users.append(u["_id"])
    return users


async def get_groups():
    groups = []
    async for g in groups_col.find({}):
        groups.append(g["_id"])
    return groups


# ---------- STATS ----------

async def get_stats():
    users = await users_col.count_documents({})
    groups = await groups_col.count_documents({})
    return users, groups
