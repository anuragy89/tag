from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

client = AsyncIOMotorClient(MONGO_URI)
db = client["tagbot"]

users = db.users
groups = db.groups


async def add_user(user_id: int):
    await users.update_one(
        {"_id": user_id},
        {"$set": {"_id": user_id}},
        upsert=True
    )


async def add_group(group_id: int):
    await groups.update_one(
        {"_id": group_id},
        {"$set": {"_id": group_id}},
        upsert=True
    )


async def get_stats():
    return {
        "users": await users.count_documents({}),
        "groups": await groups.count_documents({})
    }
