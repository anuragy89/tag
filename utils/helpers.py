import asyncio
from config import TAG_DELAY, BATCH_SIZE
from utils.state import allowed

async def is_admin(app, chat_id, user_id):
    m = await app.get_chat_member(chat_id, user_id)
    return m.status in ("administrator", "creator")

def chunk(users):
    for i in range(0, len(users), BATCH_SIZE):
        yield users[i:i+BATCH_SIZE]

async def wait(chat_id):
    if not allowed(chat_id):
        raise Exception("STOPPED")
    await asyncio.sleep(TAG_DELAY)
