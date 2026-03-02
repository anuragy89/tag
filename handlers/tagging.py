import asyncio
import random
from pyrogram import filters
from utils.state import start_tag, stop_tag, is_running


HINGLISH_MSGS = [
    "Kya haal hai 😄",
    "Bhai zinda ho? 😂",
    "Aaj bade silent ho 👀",
    "Hello ji 👋",
    "Oye kidhar ho 😜"
]

ENGLISH_MSGS = [
    "Hey there 👋",
    "How are you 😄",
    "Long time no see 👀",
    "What's up 🔥",
    "Hope you're doing great 😊"
]

HINDI_MSGS = [
    "क्या हाल है 😄",
    "कहाँ गायब हो 😂",
    "आज बहुत शांत हो 👀",
    "नमस्ते 👋",
    "सब ठीक? 😊"
]


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def tagging_handler(app):

    # /all – tag all users in chunks (7)
    @app.on_message(filters.command(["all", "tagall"]) & filters.group)
    async def tag_all(client, message):
        chat_id = message.chat.id
        start_tag(chat_id)

        members = []
        async for m in client.get_chat_members(chat_id):
            if m.user and not m.user.is_bot:
                members.append(m.user)

        for chunk in chunk_list(members, 7):
            if not is_running(chat_id):
                break

            text = " ".join(f"[{u.first_name}](tg://user?id={u.id})" for u in chunk)
            text += "\n\n" + random.choice(HINGLISH_MSGS)

            await client.send_message(chat_id, text)
            await asyncio.sleep(2)

    # /entag – English one by one
    @app.on_message(filters.command("entag") & filters.group)
    async def en_tag(client, message):
        chat_id = message.chat.id
        start_tag(chat_id)

        async for m in client.get_chat_members(chat_id):
            if not is_running(chat_id):
                break
            if not m.user or m.user.is_bot:
                continue

            msg = f"[{m.user.first_name}](tg://user?id={m.user.id}) — {random.choice(ENGLISH_MSGS)}"
            await client.send_message(chat_id, msg)
            await asyncio.sleep(2)

    # /hitag – Hindi
    @app.on_message(filters.command("hitag") & filters.group)
    async def hi_tag(client, message):
        chat_id = message.chat.id
        start_tag(chat_id)

        async for m in client.get_chat_members(chat_id):
            if not is_running(chat_id):
                break
            if not m.user or m.user.is_bot:
                continue

            msg = f"[{m.user.first_name}](tg://user?id={m.user.id}) — {random.choice(HINDI_MSGS)}"
            await client.send_message(chat_id, msg)
            await asyncio.sleep(2)

    # /jtag – Hinglish flirty/funny
    @app.on_message(filters.command("jtag") & filters.group)
    async def j_tag(client, message):
        chat_id = message.chat.id
        start_tag(chat_id)

        async for m in client.get_chat_members(chat_id):
            if not is_running(chat_id):
                break
            if not m.user or m.user.is_bot:
                continue

            msg = f"[{m.user.first_name}](tg://user?id={m.user.id}) — {random.choice(HINGLISH_MSGS)} 😜"
            await client.send_message(chat_id, msg)
            await asyncio.sleep(2)
