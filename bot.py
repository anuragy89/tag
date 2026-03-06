"""
bot.py — TagMaster Bot v4
Changes in v4:
  - Tags ONE user per message with their name inside the text (human feel)
  - No status/count messages before or during tagging — silent start
  - Member fetch: Pyrogram first, then full MongoDB fallback (tags EVERYONE)
  - /all and /admin keep 6-per-message bulk format (notification style)
  - Only sends "tagging stopped/complete" at the very end
"""

import os
import asyncio
import random
import logging
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMemberAdministrator,
    ChatMemberOwner,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError, RetryAfter
from telegram.constants import ParseMode

import database as db
import member_fetcher as mf

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")
BOT_OWNER       = int(os.environ.get("OWNER_ID", "0"))
UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "https://t.me/yourchannel")
SUPPORT_GROUP   = os.environ.get("SUPPORT_GROUP",   "https://t.me/yourgroup")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set!")
if not BOT_OWNER:
    raise RuntimeError("OWNER_ID not set!")

# ─────────────────────────────────────────────────────────────────────────────
# Message pools  — every msg MUST contain {name} so the user feels called out
# ─────────────────────────────────────────────────────────────────────────────

HINDI_MSGS = [
    "Aye {name} bhai! 👀 Tujhe yaad kiya maine, aa ja yaar! 🔥",
    "Oye {name} ji! 😄 Kahan chhup gaye ho? Sab yaad kar rahe hain tumhe 💕",
    "Dekho dekho! {name} ko bulaaya gaya hai 🎉 Aa ja bhai scene hai!",
    "{name} bhaiya/didi! 🙏 Bahut yaad aayi aapki, please aa jao 🥺",
    "Arre {name}! 😜 Itne sannate mein tujhe hi awaaz laga raha hoon!",
    "Hey {name}! 😍 Tum bina group soona lagta hai yaar, aa jao please!",
    "{name} ji 🌹 Aap jaisa koi nahi... bas aa jao na ek baar!",
    "Oye {name}! 😂 Group mein teri bahut zaroorat hai, baith ja!",
    "Arre yaar {name}! 💫 Tujhe tag kiya hai, ab aa ja warna mood kharaab hoga 😤",
    "Heyy {name}! 😘 Miss kar raha hun tujhe, aa ja jaldi!",
    "{name} bhai/didi 🤩 Scene hai aaj, miss mat karna!",
    "Oye hoye {name}! 🎊 Aaj kuch maza hoga, aa ja!",
    "{name}! 😎 Boss ne bulaya. Aa ja pehle.",
    "Hey {name} 🌟 Tum group ki jaan ho... toh aa bhi jao!",
    "{name} dost! 💌 Ek message toh maar, group ro raha hai tere bina!",
    "Oye {name}! 🤭 Pata hai tu hi sabse zyada miss hota/hoti hai group mein?",
    "{name}! 🫶 Teri smile miss karti hai group, aa ja na yaar!",
    "{name} bhai/didi! 🔔 Tujhe ping kiya hai, sun le zara!",
]

ENGLISH_MSGS = [
    "Hey {name}! 👋 You're being summoned, don't ignore this! 😄",
    "Psst... {name}! 👀 The group misses you, come on over! 💕",
    "Attention {name}! 📢 Your presence is officially requested 😂",
    "{name}! 🌟 You're the missing piece today, join in!",
    "Yo {name}! 😎 Don't be a ghost, say something!",
    "Hey {name}! 😍 You make this group 10x better, show up!",
    "{name} babe! 😘 We can't start the party without you! 🎉",
    "ALERT: {name} is needed ASAP! 🚨 Please report to the chat 😂",
    "Hello gorgeous {name}! 💫 The group is calling your name!",
    "{name}! 🔥 Stop lurking and start talking, we see you!",
    "Paging {name}! 📞 You've got messages waiting!",
    "Hey {name}! 🤩 Something fun is happening and you're missing it!",
    "{name} sweetheart! 🥰 Just checking you're alive in there!",
    "Oi {name}! 😜 Tag! You're it. Now respond!",
    "{name}! ⭐ The squad needs you, no excuses!",
    "Hey {name}! 🫂 A hug from the group — now come say hi!",
    "Calling {name}! 📡 We know you're there, stop hiding! 😏",
    "{name}! 💥 Boom, tagged. Your move now! 😂",
]

GM_MSGS = [
    "Good Morning {name}! ☀️ Uth ja yaar, din shuru ho gaya! 😄",
    "Goood Morniinggg {name}! 🌅 Chai pi li? Ya abhi bhi so raha/rahi hai? 😂",
    "Subah subah {name} ko yaad kiya! 🌸 Have a fantastic day yaar!",
    "GM {name}! 🌻 Aaj ka din tere liye ekdum mast rahega! ✨",
    "Oye {name}! ☕ Uth ja, chai mentally ready hai 😂 Good Morning!",
    "Rise and shine {name}! 🌈 Aaj kuch toh karo na yaar!",
    "Hey {name}! 🐓 Murga bhi uth gaya, tu nahi uthega kya? GM! 😜",
    "GM {name} ji! 🙏 Bhagwan kare aaj tera din bahut pyaara rahe! 💐",
    "Subah bhi tujhe hi socha {name}! 🥰 Good Morning sweetheart!",
    "Good Morning {name}! 🌞 Agenda for today: masti karo, mostly masti! 😄",
    "{name}! 🦋 Naya din, nayi energy! GM bhai/didi!",
    "Aye {name}! ⭐ Din shuru karo with full josh! Good Morning!",
    "Wakey wakey {name}! 🌄 Duniya uth gayi, tu bhi aa ja!",
    "Good Morning {name}! 🌺 Hope your day is as amazing as you are 😊",
]

GN_MSGS = [
    "Good Night {name}! 🌙 So ja, bahut thak gaya/gayi hoga/hogi aaj! 💤",
    "Raat ko bhi {name} yaad aaya/aayi! 🌟 Sweet dreams yaar!",
    "GN {name}! 😴 Kal milenge, tab tak meethe sapne aa jayen! 💕",
    "Hey {name}! 🌛 So ja ab, phone rakh! GN sweetheart!",
    "Good Night {name}! 🌌 Kal phir scene hoga, aaj rest karo!",
    "Oye {name}! 🛌 Raat ho gayi, so ja! Sweet dreams! 🌙",
    "{name} ji! ⭐ Aaj ki raat peaceful ho tumhare liye! Good Night! 🤍",
    "GN {name}! 🥱 Neend aa rahi hai? Toh so ja! Miss you already! 💫",
    "Good Night {name}! 🌠 Sapno mein milenge! 😄",
    "Sone se pehle {name} ko tag karna tha! 🌙 GN yaar, take care!",
    "{name}! 🫶 Raat ki neend acchi ho, kal fresh aana! GN 💤",
    "Shubh Ratri {name}! 🌛 Chand bhi so raha hai, tu bhi so ja! 😂",
]

TAGALL_MSGS = [
    "Aye {name}! 👀 Kahan ho? Group mein teri zaroorat hai! 😄",
    "{name}! 🔥 Active ho jao yaar, kuch toh bolo!",
    "Hey {name}! 😜 Tujhe tag kiya — iska matlab hai aana padega!",
    "{name} ji! 🎭 Drama shuru hone wala hai, aa ja!",
    "Oye {name}! 🤡 Tu hi toh life of the party hai, aa ja!",
    "Psst {name}! 👻 Ghost mat ban, bol kuch na!",
    "{name}! 💥 Boom! Tag ho gaya. Ab jawab de! 😂",
    "Hello {name}! 🌟 Ek baar online aao na yaar please 🥺",
    "{name}! 😎 Scene hai, miss mat karna!",
    "Heyy {name}! 🎊 Party in the group, tu bhi aa!",
    "{name} bhai/didi! 💫 Tum bina group adhura lagta hai!",
    "Taggg {name}! 😘 Bas ek hello? Please?",
    "{name}! 🎯 Targeted! Ab toh baat karo 😂",
    "Yo {name}! 🫵 Haaan tujhe hi bol raha/rahi hun, aa ja na!",
    "{name} yaar! 🤗 Kaafi time ho gaya, group miss kar raha hai tujhe!",
]

JTAG_MSGS = [
    "{name} bhai/didi! 😂 Ye joke tere liye:\nQ: Homework kyun late tha?\nA: Kyunki baap ne time pe diya nahi! 😭",
    "{name}! 🤣 Aaj ka joke:\nStudent: Sir main fail kyun hua?\nTeacher: Kyunki tum paas nahi aaye! 😂",
    "{name}! 😜 Joke of the day:\nBanta: Meri biwi bahut seedhi hai\nSanta: Toh jhagda kaise?\nBanta: Main tircha hun! 🤣",
    "{name}! 🤡 Chhota joke:\nDarzi: '3 din lagenge'\nMain: 'Theek hai, 3 saal baad aata hun' 😂",
    "{name}! 😂 Gym wala:\nMaine 6 pack ke liye gym join kiya\nAb 1 pack bhi nahi hai 🍕",
    "{name}! 🎭 Relatable:\nMaa: Beta padhai kar\nBeta: Kal karunga\nMaa: 3 saal se kal kal! 😭😂",
    "{name}! 🤣 Sach baat:\nWake up 6 AM: Impossible ❌\nWake up 6 AM free food ke liye: Done ✅",
    "{name} yaar! 😜 WiFi joke:\nNeighbour ka WiFi connected tha\nNeighbour: 'Bhai password change kar diya' 💀😂",
    "{name}! 😂 Exam joke:\nPaper dekha toh aankh bhar aayi\nTeacher: Kyon ro rahe ho?\nYe sawaal toh mujhe bhi aata tha! 🤣",
    "{name}! 🤡 Love joke:\nUsne kaha 'I love you'\nMaine kaha 'Proof do'\nUsne math ki copy dikhayi 😭😂",
]

ALL_TASK_KEYS = ["hitag", "entag", "gmtag", "gntag", "tagall", "jtag", "all_tag"]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = update.effective_user.id
    if uid == BOT_OWNER:
        return True
    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return isinstance(m, (ChatMemberAdministrator, ChatMemberOwner))
    except TelegramError:
        return False


def chunk_list(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def safe_send(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, **kwargs):
    for attempt in range(6):
        try:
            return await context.bot.send_message(chat_id, text, **kwargs)
        except RetryAfter as e:
            wait = getattr(e, "retry_after", 5)
            logger.warning("RetryAfter %ss (attempt %d)", wait, attempt + 1)
            await asyncio.sleep(float(wait) + 1.5)
        except TelegramError as e:
            logger.error("TelegramError to %s: %s", chat_id, e)
            break
    return None


def _mention(user: dict) -> str:
    uid   = user["user_id"]
    name  = user.get("first_name", "User")
    return f'<a href="tg://user?id={uid}">{name}</a>'


# ─────────────────────────────────────────────────────────────────────────────
# Core tagging engine  — ONE user per message, name injected into text
# ─────────────────────────────────────────────────────────────────────────────

async def _tagging_loop(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    members: list,
    msg_pool: list,
    task_key: str,
    delay: float = 4.0,
):
    """
    Tags each member individually:
      <mention>
      random funny/flirty msg with their name
    No status messages — just tags, one by one, like a human.
    """
    await db.set_tag_state(chat_id, task_key, "running")

    for user in members:
        # Check state before every single message
        state = await db.get_tag_state(chat_id, task_key)

        if state == "stopped":
            await safe_send(context, chat_id, "⛔ Tagging stopped.", parse_mode=ParseMode.HTML)
            return

        while state == "paused":
            await asyncio.sleep(2)
            state = await db.get_tag_state(chat_id, task_key)
            if state == "stopped":
                await safe_send(context, chat_id, "⛔ Tagging stopped.", parse_mode=ParseMode.HTML)
                return

        name = user.get("first_name", "User")
        mention = _mention(user)
        # Inject the real first name into the message
        msg = random.choice(msg_pool).replace("{name}", name)
        text = f"{mention}\n{msg}"

        await safe_send(context, chat_id, text, parse_mode=ParseMode.HTML)
        await asyncio.sleep(delay)

    await db.set_tag_state(chat_id, task_key, "idle")
    await safe_send(
        context, chat_id,
        "✅ Done! Everyone's been tagged 🎉",
        parse_mode=ParseMode.HTML,
    )


def _launch(context, chat_id, members, pool, key, delay=4.0):
    async def _w():
        try:
            await _tagging_loop(context, chat_id, members, pool, key, delay)
        except Exception as e:
            logger.exception("Tag task %s crashed: %s", key, e)
            await db.set_tag_state(chat_id, key, "idle")
    asyncio.create_task(_w())


# ─────────────────────────────────────────────────────────────────────────────
# Generic tag command  — silent start, fetch members then go
# ─────────────────────────────────────────────────────────────────────────────

async def _generic_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    msg_pool: list,
    task_key: str,
):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Use in groups only!")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!", parse_mode=ParseMode.HTML)
    if await db.get_tag_state(chat.id, task_key) == "running":
        return await update.message.reply_text("⚠️ Already running! /stop first.")

    # Fetch members silently (no message to user)
    members = await mf.get_members_for_tagging(chat.id)

    if not members:
        return await update.message.reply_text(
            "⚠️ No members found yet!\n"
            "Ask members to send a message in the group so I can track them,\n"
            "or make me admin so I can fetch the full member list.",
        )

    # Silent start — no "starting…" message
    _launch(context, chat.id, members, msg_pool, task_key)


# ─────────────────────────────────────────────────────────────────────────────
# Tag commands
# ─────────────────────────────────────────────────────────────────────────────

async def hitag_cmd(update, context):
    await _generic_tag(update, context, HINDI_MSGS,   "hitag")

async def entag_cmd(update, context):
    await _generic_tag(update, context, ENGLISH_MSGS, "entag")

async def gmtag_cmd(update, context):
    await _generic_tag(update, context, GM_MSGS,      "gmtag")

async def gntag_cmd(update, context):
    await _generic_tag(update, context, GN_MSGS,      "gntag")

async def tagall_cmd(update, context):
    pool = TAGALL_MSGS + HINDI_MSGS + ENGLISH_MSGS
    await _generic_tag(update, context, pool,         "tagall")

async def jtag_cmd(update, context):
    await _generic_tag(update, context, JTAG_MSGS,    "jtag")


# ─────────────────────────────────────────────────────────────────────────────
# /admin  — bulk tag admins 6 per message (with custom msg above)
# ─────────────────────────────────────────────────────────────────────────────

async def _admin_tag(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_msg: str):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Groups only!")
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
    except TelegramError as e:
        return await update.message.reply_text(f"❌ Can't fetch admins: {e}")

    admin_list = [
        {"user_id": a.user.id, "first_name": a.user.first_name or "Admin"}
        for a in admins if not a.user.is_bot
    ]
    if not admin_list:
        return await update.message.reply_text("⚠️ No admins found!")

    header = f"📢 <b>{custom_msg}</b>\n\n" if custom_msg else "👮 <b>Attention Admins!</b>\n\n"
    for chunk in chunk_list(admin_list, 6):
        tags = " ".join(_mention(u) for u in chunk)
        await safe_send(context, chat.id, f"{header}{tags}", parse_mode=ParseMode.HTML)
        await asyncio.sleep(2)


async def admin_tag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _admin_tag(update, context, " ".join(context.args) if context.args else "")


# ─────────────────────────────────────────────────────────────────────────────
# /all  — bulk tag all members 6 per message (with custom msg above)
# ─────────────────────────────────────────────────────────────────────────────

async def _all_tag(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_msg: str):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Groups only!")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")
    if await db.get_tag_state(chat.id, "all_tag") == "running":
        return await update.message.reply_text("⚠️ Already running! /stop first.")

    members = await mf.get_members_for_tagging(chat.id)
    if not members:
        return await update.message.reply_text("⚠️ No members found yet!")

    header = f"📢 <b>{custom_msg}</b>\n\n" if custom_msg else None

    async def _run():
        await db.set_tag_state(chat.id, "all_tag", "running")
        try:
            for chunk in chunk_list(members, 6):
                state = await db.get_tag_state(chat.id, "all_tag")
                if state == "stopped":
                    await safe_send(context, chat.id, "⛔ Stopped.", parse_mode=ParseMode.HTML)
                    return
                while state == "paused":
                    await asyncio.sleep(2)
                    state = await db.get_tag_state(chat.id, "all_tag")
                    if state == "stopped":
                        await safe_send(context, chat.id, "⛔ Stopped.", parse_mode=ParseMode.HTML)
                        return
                tags = " ".join(_mention(u) for u in chunk)
                text = f"{header}{tags}" if header else tags
                await safe_send(context, chat.id, text, parse_mode=ParseMode.HTML)
                await asyncio.sleep(3)
            await db.set_tag_state(chat.id, "all_tag", "idle")
            await safe_send(context, chat.id, "✅ Done! All tagged 🎉", parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.exception("all_tag crashed: %s", e)
            await db.set_tag_state(chat.id, "all_tag", "idle")

    asyncio.create_task(_run())


async def all_tag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _all_tag(update, context, " ".join(context.args) if context.args else "")


# ─────────────────────────────────────────────────────────────────────────────
# @admin / @all text triggers
# ─────────────────────────────────────────────────────────────────────────────

async def text_trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    t = update.message.text.strip()
    if t.lower().startswith("@admin"):
        await _admin_tag(update, context, t[6:].strip())
    elif t.lower().startswith("@all"):
        await _all_tag(update, context, t[4:].strip())


# ─────────────────────────────────────────────────────────────────────────────
# Controls
# ─────────────────────────────────────────────────────────────────────────────

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")
    for k in ALL_TASK_KEYS:
        await db.set_tag_state(chat.id, k, "stopped")
    await update.message.reply_text("⛔ Tagging stopped!", parse_mode=ParseMode.HTML)


async def pause_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")
    paused = False
    for k in ALL_TASK_KEYS:
        if await db.get_tag_state(chat.id, k) == "running":
            await db.set_tag_state(chat.id, k, "paused")
            paused = True
    msg = "⏸️ Paused! /resume to continue." if paused else "ℹ️ Nothing running."
    await update.message.reply_text(msg)


async def resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")
    resumed = False
    for k in ALL_TASK_KEYS:
        if await db.get_tag_state(chat.id, k) == "paused":
            await db.set_tag_state(chat.id, k, "running")
            resumed = True
    msg = "▶️ Resumed!" if resumed else "ℹ️ Nothing paused."
    await update.message.reply_text(msg)


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.save_user(user.id, user.first_name or "User", user.username)
    text = (
        f"<b>👋 Hey {user.first_name}! Welcome to TagMaster Bot! 🤖✨</b>\n\n"
        "I'm your <b>ultimate group tagging assistant</b> — human-like, funny & smart!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>What I Can Do:</b>\n\n"
        "🏷️ <b>8 Tagging Modes</b> — Hindi, English, GM, GN, Jokes & more!\n"
        "😄 <b>One-by-One Tags</b> — Each user gets their own personalized msg!\n"
        "🟢 <b>Smart Order</b> — Online first, then recent, then last week!\n"
        "🛡️ <b>Flood Protected</b> — Smart delays, never gets banned!\n"
        "⏸️ <b>Full Control</b> — Pause, Resume, Stop anytime!\n"
        "📢 <b>Broadcast</b> — Message all users & groups at once!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <b>Get started below!</b>"
    )
    kb = [
        [InlineKeyboardButton("➕ Add to Your Group",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
         InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL)],
    ]
    await update.message.reply_text(text, parse_mode=ParseMode.HTML,
                                    reply_markup=InlineKeyboardMarkup(kb))


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────

HELP_TEXT = (
    "<b>📖 TagMaster Bot — Commands</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>🏷️ Tag Commands</b> <i>(Admins only)</i>\n\n"
    "/hitag  — Hindi funny+flirty tags 🇮🇳\n"
    "/entag  — English funny+flirty tags 🇬🇧\n"
    "/gmtag  — Good Morning tags 🌅\n"
    "/gntag  — Good Night tags 🌙\n"
    "/tagall — Hinglish mix tags 🔥\n"
    "/jtag   — Joke tags 😂\n\n"
    "<i>💡 Each member gets their own message with their name!</i>\n\n"
    "<b>👑 Bulk Tag</b>\n\n"
    "/admin &lt;msg&gt; — Tag all admins 👮 <i>(anyone can use)</i>\n"
    "/all &lt;msg&gt;   — Tag all members 📢 <i>(admins only)</i>\n"
    "@admin / @all  — Same as above (plain text)\n\n"
    "<b>⏸️ Controls</b> <i>(Admins only)</i>\n\n"
    "/stop   — Stop tagging 🛑\n"
    "/pause  — Pause tagging ⏸️\n"
    "/resume — Resume tagging ▶️\n\n"
    "<b>📊 Info</b>\n\n"
    "/stats  — Bot usage stats 📈\n"
    "/help   — This menu ❓\n\n"
    "<b>👑 Owner Only</b>\n\n"
    "/broadcast &lt;msg&gt; — Broadcast to all\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    "<b>🟢 Tag Order:</b> Online → Recently → Last Week → Others\n"
    "<i>Make bot admin for full member list access!</i>"
)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = [[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]
    await q.edit_message_text(HELP_TEXT, parse_mode=ParseMode.HTML,
                              reply_markup=InlineKeyboardMarkup(kb))


async def back_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user = q.from_user
    text = (
        f"<b>👋 Hey {user.first_name}! Welcome to TagMaster Bot! 🤖✨</b>\n\n"
        "I'm your <b>ultimate group tagging assistant</b> — human-like, funny & smart!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>What I Can Do:</b>\n\n"
        "🏷️ <b>8 Tagging Modes</b> — Hindi, English, GM, GN, Jokes & more!\n"
        "😄 <b>One-by-One Tags</b> — Each user gets their own personalized msg!\n"
        "🟢 <b>Smart Order</b> — Online first, then recent, then last week!\n"
        "🛡️ <b>Flood Protected</b> — Smart delays, never gets banned!\n"
        "⏸️ <b>Full Control</b> — Pause, Resume, Stop anytime!\n"
        "📢 <b>Broadcast</b> — Message all users & groups at once!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <b>Get started below!</b>"
    )
    kb = [
        [InlineKeyboardButton("➕ Add to Your Group",
                              url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
         InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL)],
    ]
    await q.edit_message_text(text, parse_mode=ParseMode.HTML,
                              reply_markup=InlineKeyboardMarkup(kb))


# ─────────────────────────────────────────────────────────────────────────────
# Bot added to group
# ─────────────────────────────────────────────────────────────────────────────

async def new_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            await db.save_group(chat.id, chat.title or "Group")
            await safe_send(
                context, chat.id,
                "🎉 <b>Thanks for adding me!</b>\n\n"
                "I'm <b>TagMaster Bot</b> 🤖 — your smart group tagger!\n\n"
                "📌 /help — see all commands\n\n"
                "💡 <b>Make me admin</b> so I can fetch all members & tag everyone!\n\n"
                "Ready to tag? Try /hitag 🔥",
                parse_mode=ParseMode.HTML,
            )


# ─────────────────────────────────────────────────────────────────────────────
# /stats
# ─────────────────────────────────────────────────────────────────────────────

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = await db.get_stats()
    await update.message.reply_text(
        "📊 <b>TagMaster — Live Stats</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Users   : <b>{s['users']:,}</b>\n"
        f"🏘️ Groups  : <b>{s['groups']:,}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 <i>{datetime.now().strftime('%d %b %Y %H:%M UTC')}</i>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────────────────────────────────────
# /broadcast
# ─────────────────────────────────────────────────────────────────────────────

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER:
        return await update.message.reply_text("❌ Owner only!")
    if not context.args:
        return await update.message.reply_text(
            "Usage: /broadcast &lt;message&gt;", parse_mode=ParseMode.HTML
        )

    bcast = " ".join(context.args)
    formatted = (
        "📢 <b>Message from Bot Owner</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{bcast}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>— TagMaster Bot</i>"
    )

    all_users  = await db.get_all_users()
    all_groups = await db.get_all_groups()

    status = await update.message.reply_text(
        f"📤 Broadcasting to {len(all_users)} users + {len(all_groups)} groups...",
        parse_mode=ParseMode.HTML,
    )

    su = fu = bu = sg = fg = 0

    for uid in all_users:
        try:
            await context.bot.send_message(uid, formatted, parse_mode=ParseMode.HTML)
            su += 1
        except TelegramError as e:
            if any(x in str(e).lower() for x in ("blocked", "deactivated", "not found")):
                bu += 1
            else:
                fu += 1
        await asyncio.sleep(0.05)
        if (su + fu + bu) % 50 == 0:
            try:
                await status.edit_text(
                    f"📤 Users: ✔️{su} 🚫{bu} ❌{fu} — Groups pending...",
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError:
                pass

    for gid in all_groups:
        try:
            await context.bot.send_message(gid, formatted, parse_mode=ParseMode.HTML)
            sg += 1
        except TelegramError:
            fg += 1
        await asyncio.sleep(0.1)

    await status.edit_text(
        "✅ <b>Broadcast Done!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Users  — ✔️ {su} | 🚫 {bu} blocked | ❌ {fu} failed\n"
        f"🏘️ Groups — ✔️ {sg} | ❌ {fg} failed\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Total sent: <b>{su + sg}</b>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Activity tracker — save every user who messages in a group
# ─────────────────────────────────────────────────────────────────────────────

async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_chat:
        return
    user = update.effective_user
    chat = update.effective_chat
    await db.save_user(user.id, user.first_name or "User", user.username)
    if chat.type in ("group", "supergroup"):
        await db.save_group(chat.id, chat.title or "Group")
        await db.save_member(chat.id, user.id, user.first_name or "User")


# ─────────────────────────────────────────────────────────────────────────────
# App lifecycle
# ─────────────────────────────────────────────────────────────────────────────

async def post_init(app: Application):
    await db.init_db()
    try:
        await mf.start_pyro()
    except Exception as e:
        logger.warning("Pyrogram startup skipped: %s", e)
    logger.info("Bot online | Owner: %s", BOT_OWNER)


async def post_shutdown(app: Application):
    await mf.stop_pyro()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start",     start_cmd))
    app.add_handler(CommandHandler("help",      help_cmd))
    app.add_handler(CommandHandler("hitag",     hitag_cmd))
    app.add_handler(CommandHandler("entag",     entag_cmd))
    app.add_handler(CommandHandler("gmtag",     gmtag_cmd))
    app.add_handler(CommandHandler("gntag",     gntag_cmd))
    app.add_handler(CommandHandler("tagall",    tagall_cmd))
    app.add_handler(CommandHandler("jtag",      jtag_cmd))
    app.add_handler(CommandHandler("admin",     admin_tag_cmd))
    app.add_handler(CommandHandler("all",       all_tag_cmd))
    app.add_handler(CommandHandler("stop",      stop_cmd))
    app.add_handler(CommandHandler("pause",     pause_cmd))
    app.add_handler(CommandHandler("resume",    resume_cmd))
    app.add_handler(CommandHandler("stats",     stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))

    app.add_handler(CallbackQueryHandler(help_callback,       pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(back_start_callback, pattern="^back_start$"))

    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        text_trigger_handler,
    ))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_chat_member_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, track_activity))

    logger.info("TagMaster Bot started...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
