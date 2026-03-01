import asyncio
from pyrogram import filters
from utils.helpers import is_admin, chunk, wait
from utils.state import allowed
from utils.messages import EN, HI, HINGLISH, FLIRTY, pick
from utils.ratelimit import check_rate
from utils.errors import safe_execute

def mention(u):
    return f"[{u.first_name}](tg://user?id={u.id})"

async def tag_one_by_one(app, msg, users, pool):
    chat_id = msg.chat.id
    last = None

    for u in users:
        if not allowed(chat_id):
            break

        text = pick(pool, last).format(m=mention(u))
        last = text

        sent = await safe_execute(msg.reply, text)
        await wait(chat_id)
        if sent:
            await safe_execute(sent.delete)

def register(app):

    @app.on_message(filters.command("tagall") & filters.group)
    async def tagall(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return

        if not check_rate(m.chat.id, m.from_user.id):
            await safe_execute(m.reply, "⏳ Slow down a bit 😄")
            return

        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, HINGLISH)

    @app.on_message(filters.command("entag") & filters.group)
    async def entag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return

        if not check_rate(m.chat.id, m.from_user.id):
            await safe_execute(m.reply, "⏳ Please wait before using again")
            return

        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, EN)

    @app.on_message(filters.command("hitag") & filters.group)
    async def hitag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return

        if not check_rate(m.chat.id, m.from_user.id):
            await safe_execute(m.reply, "⏳ थोड़ा रुकिए 😄")
            return

        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, HI)

    @app.on_message(filters.command("jtag") & filters.group)
    async def jtag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return

        if not check_rate(m.chat.id, m.from_user.id):
            await safe_execute(m.reply, "😏 Thoda patience rakho")
            return

        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, FLIRTY)
