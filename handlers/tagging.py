import asyncio
from pyrogram import filters
from utils.helpers import is_admin, chunk, wait
from utils.state import allowed
from utils.messages import EN, HI, HINGLISH, FLIRTY, pick

last_msg = {}

def mention(u):
    return f"[{u.first_name}](tg://user?id={u.id})"

async def tag_one_by_one(app, msg, users, pool):
    cid = msg.chat.id
    last = None
    for u in users:
        if not allowed(cid):
            break
        text = pick(pool, last).format(m=mention(u))
        last = text
        sent = await msg.reply(text)
        await wait(cid)
        await sent.delete()

def register(app):

    @app.on_message(filters.command(["admin","admins"]) & filters.group)
    async def admins(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        admins = [x.user async for x in app.get_chat_members(m.chat.id, filter="administrators")]
        text = m.text.split(maxsplit=1)[1] if len(m.command) > 1 else "Admins please check"
        await tag_one_by_one(app, m, admins, [text + " {m}"])

    @app.on_message(filters.command(["all"]) & filters.group)
    async def all_tag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        for batch in chunk(users):
            if not allowed(m.chat.id):
                break
            mentions = " ".join(mention(u) for u in batch)
            sent = await m.reply(mentions)
            await wait(m.chat.id)
            await sent.delete()

    @app.on_message(filters.command("tagall") & filters.group)
    async def tagall(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, HINGLISH)

    @app.on_message(filters.command("entag") & filters.group)
    async def entag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, EN)

    @app.on_message(filters.command("hitag") & filters.group)
    async def hitag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, HI)

    @app.on_message(filters.command("jtag") & filters.group)
    async def jtag(_, m):
        if not await is_admin(app, m.chat.id, m.from_user.id):
            return
        users = [x.user async for x in app.get_chat_members(m.chat.id)]
        await tag_one_by_one(app, m, users, FLIRTY)
