import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait

from database import add_group

# ---------------- STATE ---------------- #
ACTIVE_TAGS = {}      # chat_id -> True
PAUSED_TAGS = set()   # chat_id
LAST_MSG = {}         # chat_id -> last_message


# ---------------- MESSAGE POOLS ---------------- #

EN_MESSAGES = [
    "Hey {u}, how are you? 😄",
    "Hello {u}! Hope you're doing great ✨",
    "What's up {u}? 👋",
    "{u} you're awesome 🔥",
]

HI_MESSAGES = [
    "नमस्ते {u}! कैसे हो? 😊",
    "{u} क्या हाल है? 😄",
    "{u} आज बहुत बढ़िया लग रहे हो 🔥",
]

HINGLISH_MESSAGES = [
    "Hey {u}, kya scene hai? 😜",
    "{u} bhai kya chal raha hai? 🔥",
    "Oye {u}, mast lag rahe ho 😄",
]

FLIRTY_MESSAGES = [
    "{u} aaj bade cute lag rahe ho 😏",
    "{u} tumhari smile OP hai 😄",
    "{u} heart hacker ho kya? 💘",
]


# ---------------- HELPERS ---------------- #

def is_admin(member):
    return member.status in (
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER
    )


def get_random_msg(chat_id, pool, user_mention):
    msg = random.choice(pool)
    # prevent immediate repeat
    if LAST_MSG.get(chat_id) == msg:
        msg = random.choice(pool)
    LAST_MSG[chat_id] = msg
    return msg.format(u=user_mention)


async def wait_if_paused(chat_id):
    while chat_id in PAUSED_TAGS:
        await asyncio.sleep(1)


# ---------------- HANDLER ---------------- #

def tag_handler(app):

    @app.on_message(filters.group & filters.command(
        ["tagall", "entag", "hitag", "jtag", "admin", "all"]
    ))
    async def tag_cmd(client, message):
        chat_id = message.chat.id

        # admin check
        member = await client.get_chat_member(chat_id, message.from_user.id)
        if not is_admin(member):
            return await message.reply_text("❌ Only admins can use tagging commands.")

        # already running
        if ACTIVE_TAGS.get(chat_id):
            return await message.reply_text("⚠️ Tagging already running. Use /stop.")

        ACTIVE_TAGS[chat_id] = True
        await add_group(chat_id)

        command = message.command[0]

        # get users
        users = []
        admins = []

        async for m in client.get_chat_members(chat_id):
            if m.user.is_bot:
                continue
            users.append(m.user)
            if m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                admins.append(m.user)

        random.shuffle(users)

        try:
            # -------- ADMIN TAG -------- #
            if command in ("admin",):
                for u in admins:
                    await message.reply_text(f"🚨 {u.mention}")
                    await asyncio.sleep(1)

            # -------- ALL (7-7 batch) -------- #
            elif command in ("all",):
                batch = []
                for u in users:
                    batch.append(u.mention)
                    if len(batch) == 7:
                        await message.reply_text(" ".join(batch))
                        batch.clear()
                        await asyncio.sleep(2)
                if batch:
                    await message.reply_text(" ".join(batch))

            # -------- ONE BY ONE TAGS -------- #
            else:
                if command == "entag":
                    pool = EN_MESSAGES
                elif command == "hitag":
                    pool = HI_MESSAGES
                elif command == "jtag":
                    pool = FLIRTY_MESSAGES
                else:  # tagall
                    pool = HINGLISH_MESSAGES

                for u in users:
                    if not ACTIVE_TAGS.get(chat_id):
                        break

                    await wait_if_paused(chat_id)

                    try:
                        text = get_random_msg(chat_id, pool, u.mention)
                        await message.reply_text(text)
                        await asyncio.sleep(2)

                    except FloodWait as e:
                        await asyncio.sleep(e.value)

        finally:
            ACTIVE_TAGS.pop(chat_id, None)
            PAUSED_TAGS.discard(chat_id)


    # ---------------- STOP ---------------- #
    @app.on_message(filters.group & filters.command("stop"))
    async def stop_cmd(_, message):
        chat_id = message.chat.id
        ACTIVE_TAGS.pop(chat_id, None)
        PAUSED_TAGS.discard(chat_id)
        await message.reply_text("⛔ Tagging stopped.")


    # ---------------- RESUME ---------------- #
    @app.on_message(filters.group & filters.command("resume"))
    async def resume_cmd(_, message):
        chat_id = message.chat.id
        if chat_id in ACTIVE_TAGS:
            PAUSED_TAGS.discard(chat_id)
            await message.reply_text("▶️ Tagging resumed.")
        else:
            await message.reply_text("⚠️ No active tagging to resume.")
