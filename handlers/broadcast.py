from pyrogram import filters
from pyrogram.errors import FloodWait
import asyncio

from config import OWNER_ID
from database import get_users, get_groups


def broadcast_handler(app):

    @app.on_message(filters.private & filters.command("broadcast"))
    async def broadcast_cmd(client, message):

        # owner check
        if message.from_user.id != OWNER_ID:
            return await message.reply_text("❌ Only bot owner can use broadcast.")

        if not message.reply_to_message:
            return await message.reply_text(
                "⚠️ Reply to a message to broadcast it."
            )

        sent = 0
        failed = 0

        text = message.reply_to_message

        # -------- USERS --------
        users = await get_users()
        for uid in users:
            try:
                await client.copy_message(
                    chat_id=uid,
                    from_chat_id=text.chat.id,
                    message_id=text.id
                )
                sent += 1
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1

        # -------- GROUPS --------
        groups = await get_groups()
        for gid in groups:
            try:
                await client.copy_message(
                    chat_id=gid,
                    from_chat_id=text.chat.id,
                    message_id=text.id
                )
                sent += 1
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception:
                failed += 1

        await message.reply_text(
            f"✅ Broadcast finished\n\n"
            f"📤 Sent: {sent}\n"
            f"❌ Failed: {failed}"
        )
