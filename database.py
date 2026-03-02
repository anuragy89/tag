from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["tagbot"]

users_col = db.users
groups_col = db.groups


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


async def get_stats():
    users = await users_col.count_documents({})
    groups = await groups_col.count_documents({})
    return users, groups
