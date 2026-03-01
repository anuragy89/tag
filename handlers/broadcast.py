from pyrogram import filters
from database import get_users, get_groups
from config import OWNER_ID

def register(app):

    @app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
    async def broadcast(_, m):
        if not m.reply_to_message:
            await m.reply("Reply to a message to broadcast")
            return

        text = m.reply_to_message.text

        sent = 0
        for uid in await get_users():
            try:
                await app.send_message(uid, text)
                sent += 1
            except:
                pass

        for gid in await get_groups():
            try:
                await app.send_message(gid, text)
            except:
                pass

        await m.reply(f"✅ Broadcast sent to {sent} users")
