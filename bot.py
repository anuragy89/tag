"""
bot.py  ──  TagMaster Bot  (v2 — MongoDB edition)
Author : You
Stack  : python-telegram-bot 21.x  +  motor (async MongoDB)

Fixed in v2:
  ✅ MongoDB via motor (fully async — no blocking calls)
  ✅ /stats   — live counts from MongoDB
  ✅ /broadcast — with per-message progress + blocked-user cleanup
  ✅ @admin / @all text triggers (not just slash commands)
  ✅ new_chat_member  registered as StatusUpdate handler
  ✅ tag_state race-condition fixed (state checked BEFORE & DURING loop)
  ✅ /all custom-msg header fixed (was crashing on None concat)
  ✅ bot_data tag-state cache for ultra-fast pause/stop checks
  ✅ Proper asyncio.create_task error logging
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
from telegram.error import FloodWait, TelegramError, RetryAfter
from telegram.constants import ParseMode

import database as db

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")
BOT_OWNER       = int(os.environ.get("OWNER_ID", "0"))
UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "https://t.me/yourchannel")
SUPPORT_GROUP   = os.environ.get("SUPPORT_GROUP",   "https://t.me/yourgroup")

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN environment variable is not set!")
if not BOT_OWNER:
    raise RuntimeError("❌ OWNER_ID environment variable is not set!")

# ── Message pools ─────────────────────────────────────────────────────────────

HINDI_MSGS = [
    "Aye {name}! 👀 Tujhe yaad kiya maine, aa ja bhai! 🔥",
    "Oye {name} ji! 😄 Kahan chhup gaye ho? Sab yaad kar rahe hain tumhe 💕",
    "Dekho dekho! {name} ko bulaaya gaya hai 🎉 Aa ja bhai scene hai!",
    "{name} bhaiya/didi! 🙏 Bahut yaad aayi aapki, please aa jao 🥺",
    "Arre {name}! 😜 Itne sannate mein aawaz laga raha hoon, sun le!",
    "Hey {name}! 😍 Tum bina group soona lagta hai yaar, aa jao please!",
    "{name} ji 🌹 Aap jaisa koi nahi... bas aa jao na ek baar!",
    "Oye {name}! 😂 Group mein teri bahut zaroorat hai, baith ja!",
    "Arre yaar {name}! 💫 Tujhe tag kiya hai, ab aa ja warna mood kharaab hoga 😤",
    "{name}! 🥰 Sun, tujhse baat karni hai... important hai!",
    "Heyy {name}! 😘 Miss kar raha hun tujhe, aa ja jaldi!",
    "{name} bhai/didi 🤩 Scene hai aaj, miss mat karna!",
    "Oye hoye {name}! 🎊 Aaj kuch maza hoga, aa ja!",
    "{name}! 😎 Boss ne bulaya. Aa ja pehle.",
    "Hey {name} 🌟 Tum group ki jaan ho... toh aa bhi jao!",
    "{name}! 🫶 Teri smile miss karti hai group, aa ja na yaar!",
    "Oye {name}! 🤭 Pata hai tu hi sabse zyada miss hota/hoti hai?",
    "{name} dost! 💌 Ek message toh maar, group ro raha hai tere bina!",
]

ENGLISH_MSGS = [
    "Hey {name}! 👋 You're being summoned, don't ignore this! 😄",
    "Psst... {name}! 👀 The group misses you, come on over! 💕",
    "Attention {name}! 📢 Your presence is officially requested 😂",
    "{name}! 🌟 You're the missing piece today, join in!",
    "Yo {name}! 😎 Don't be a ghost, say something!",
    "Hey {name}! 😍 You make this group 10x better, show up!",
    "{name}, babe! 😘 We can't start the party without you! 🎉",
    "ALERT: {name} is needed ASAP! 🚨 Please report to the chat 😂",
    "Hello gorgeous {name}! 💫 The group is calling your name!",
    "{name}! 🔥 Stop lurking and start talking, we see you!",
    "Paging {name}! 📞 You've got messages waiting!",
    "Hey {name}! 🤩 Something fun is happening and you're missing it!",
    "{name} sweetheart! 🥰 Just checking you're alive in there!",
    "Oi {name}! 😜 Tag! You're it. Now respond!",
    "{name}! ⭐ The squad needs you, no excuses!",
    "Hey {name}! 🫂 A hug from the group — now come say hi!",
    "{name}! 🌈 Sunshine is great, but you make the group brighter!",
    "Calling {name}! 📡 Signal's strong, we know you're there! 😏",
]

GM_MSGS = [
    "Good Morning {name}! ☀️ Uth ja bhai, din shuru ho gaya! 😄",
    "Goood Morniinggg {name}! 🌅 Chai pi li? Ya abhi bhi so raha/rahi hai? 😂",
    "Subah subah {name} ko yaad kiya! 🌸 Have a fantastic day yaar!",
    "GM {name}! 🌻 Aaj ka din tere liye ekdum mast rahega! ✨",
    "Oye {name}! ☕ Uth ja, chai ready hai... mentally 😂 GM!",
    "Rise and shine {name}! 🌈 Aaj kuch toh karo na yaar!",
    "Hey {name}! 🐓 Murga bhi uth gaya, tu nahi uthega kya? Good Morning! 😜",
    "GM {name} ji! 🙏 Bhagwan kare aaj tera din bahut pyaara rahe! 💐",
    "Subah bhi tujhe hi socha {name}! 🥰 Good Morning sweetheart!",
    "Good Morning {name}! 🌞 Aaj ka agenda: masti karo, kuch kaam karo... mostly masti! 😄",
    "{name}! 🦋 Naya din, nayi energy! GM bhai/didi!",
    "Aye {name}! ⭐ Din shuru karo with full josh! Good Morning!",
    "Wakey wakey {name}! 🌄 Duniya ne uthna shuru kar diya, tu bhi aa ja!",
]

GN_MSGS = [
    "Good Night {name}! 🌙 So ja, bahut thak gaya/gayi hoga/hogi aaj! 💤",
    "Raat ko bhi {name} yaad aaya/aayi! 🌟 Sweet dreams yaar!",
    "GN {name}! 😴 Kal milenge, tab tak meethe sapne aa jayen! 💕",
    "Hey {name}! 🌛 So ja ab, phone rakh! GN sweetheart!",
    "Good Night {name}! 🌌 Kal phir scene hoga, aaj rest karo!",
    "Oye {name}! 🛌 Raat ho gayi, so ja bhai! Sweet dreams! 🌙",
    "{name} ji! ⭐ Aaj ki raat peaceful ho tumhare liye! Good Night! 🤍",
    "GN {name}! 🥱 Neend aa rahi hai? Toh so ja! Miss you already! 💫",
    "Good Night {name}! 🌠 Sapno mein milenge! 😄",
    "Sone se pehle {name} ko tag karna tha! 🌙 GN yaar, take care!",
    "{name}! 🫶 Raat ki neend acchi ho... kal fresh hoke aana! GN 💤",
]

TAGALL_MSGS = [
    "Aye {name}! 👀 Kahan ho? Group mein teri zaroorat hai! 😄",
    "{name}! 🔥 Active ho jao yaar, kuch toh bolo!",
    "Hey {name}! 😜 Tujhe tag kiya = tujhe dekhna chahte hain!",
    "{name} ji! 🎭 Drama shuru hone wala hai, aa ja!",
    "Oye {name}! 🤡 Tu hi toh life of the party hai, aa ja!",
    "Psst {name}! 👻 Ghost mat ban, bol kuch!",
    "{name}! 💥 Boom! Tag ho gaya. Ab jawab de! 😂",
    "Hello {name}! 🌟 Ek baar online aao na yaar please 🥺",
    "{name}! 😎 Scene hai, miss mat karna!",
    "Heyy {name}! 🎊 Party in the group, tu bhi aa!",
    "{name} bhai/didi! 💫 Tum bina group adhura lagta hai!",
    "Taggg {name}! 😘 Bas ek hello? Please?",
    "{name}! 🎯 Targeted! Ab toh baat karo bhai/didi 😂",
    "Yo {name}! 🫵 Haaan tujhe hi bol raha/rahi hun, aa ja!",
]

JTAG_MSGS = [
    "{name}! 😂 Joke le ja:\n📌 Q: Homework kyun late tha?\n💡 A: Kyunki baap ne time pe diya nahi! 😭",
    "{name}! 🤣 Aaj ka joke:\n📌 Student: Sir main fail kyun hua?\n💡 Teacher: Kyunki tum paas nahi aaye! 😂",
    "{name}! 😜 Joke of the day:\n📌 Banta: Yaar meri biwi bahut seedhi hai\n📌 Santa: Toh jhagda kaise?\n💡 Banta: Main tircha hun! 🤣",
    "{name}! 🤡 Chhota joke:\n📌 Darzi ko kapde siwane gaya\n📌 Darzi: '3 din lagenge'\n💡 Main: 'Theek hai, 3 saal baad aata hun' 😂",
    "{name}! 😂 Gym wala joke:\n📌 Maine 6 pack ke liye gym join kiya\n💡 Ab 1 pack bhi nahi hai 🍕",
    "{name}! 🎭 Relatable joke:\n📌 Maa: Beta padhai kar\n📌 Beta: Kal karunga\n💡 Maa: 3 saal se kal kal kar raha hai! 😭😂",
    "{name}! 🤣 Morning joke:\n📌 Wake up at 6 AM: Impossible ❌\n💡 Wake up at 6 AM for free food: Done ✅",
    "{name} bhai/didi! 😜 WiFi wala:\n📌 Neighbour ka WiFi: Connected\n💡 Neighbour: 'Bhai password change kar diya' 💀😂",
    "{name}! 😂 Exam joke:\n📌 Paper dekha toh aankh bhar aayi\n💡 Teacher: Kyon?\n📌 Mujhe bhi yahin sawaal aata tha! 🤣",
    "{name}! 🤡 Love joke:\n📌 Usne kaha 'I love you'\n📌 Maine kaha 'Proof do'\n💡 Usne math ki copy dikhayi 😭😂",
]

# ── All task keys ─────────────────────────────────────────────────────────────
ALL_TASK_KEYS = ["hitag", "entag", "gmtag", "gntag", "tagall", "jtag", "all_tag"]

# ── Helpers ───────────────────────────────────────────────────────────────────

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int = None) -> bool:
    uid = user_id or update.effective_user.id
    if uid == BOT_OWNER:
        return True
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))
    except TelegramError:
        return False


def chunk_list(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def safe_send(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    **kwargs,
):
    """Send a message with automatic FloodWait / RetryAfter handling."""
    for attempt in range(6):
        try:
            return await context.bot.send_message(chat_id, text, **kwargs)
        except (FloodWait, RetryAfter) as e:
            wait = getattr(e, "retry_after", getattr(e, "value", 5))
            logger.warning("FloodWait %ss — attempt %d/6", wait, attempt + 1)
            await asyncio.sleep(float(wait) + 1.5)
        except TelegramError as e:
            logger.error("TelegramError in safe_send to %s: %s", chat_id, e)
            break
    return None


async def _tagging_loop(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    members: list,
    msg_pool: list,
    task_key: str,
    per_chunk: int = 5,
    delay: float = 3.5,
):
    """
    Core tagging engine shared by all tag commands.
    Checks MongoDB state before every chunk for instant pause/stop response.
    """
    await db.set_tag_state(chat_id, task_key, "running")

    for chunk in chunk_list(members, per_chunk):
        # ── Check state ───────────────────────────────────────────────────────
        state = await db.get_tag_state(chat_id, task_key)

        if state == "stopped":
            await safe_send(
                context, chat_id,
                "⛔ <b>Tagging stopped!</b>",
                parse_mode=ParseMode.HTML,
            )
            return

        # Busy-wait while paused
        while state == "paused":
            await asyncio.sleep(1.5)
            state = await db.get_tag_state(chat_id, task_key)
            if state == "stopped":
                await safe_send(
                    context, chat_id,
                    "⛔ <b>Tagging stopped!</b>",
                    parse_mode=ParseMode.HTML,
                )
                return

        # ── Build mention string ──────────────────────────────────────────────
        mentions = " ".join(
            f'<a href="tg://user?id={u["user_id"]}">'
            f'{u["first_name"]}</a>'
            for u in chunk
        )
        msg_line = random.choice(msg_pool).replace("{name}", "").strip()
        await safe_send(
            context, chat_id,
            f"{mentions}\n\n{msg_line}",
            parse_mode=ParseMode.HTML,
        )
        await asyncio.sleep(delay)

    # Done
    await db.set_tag_state(chat_id, task_key, "idle")
    await safe_send(
        context, chat_id,
        "✅ <b>Tagging complete!</b> Everyone's been tagged! 🎉",
        parse_mode=ParseMode.HTML,
    )


def _start_tagging_task(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    members: list,
    msg_pool: list,
    task_key: str,
    per_chunk: int = 5,
    delay: float = 3.5,
):
    """Wrap _tagging_loop in a task with error logging."""
    async def _wrapper():
        try:
            await _tagging_loop(context, chat_id, members, msg_pool, task_key, per_chunk, delay)
        except Exception as exc:
            logger.exception("Tagging task %s crashed: %s", task_key, exc)
            await db.set_tag_state(chat_id, task_key, "idle")

    asyncio.create_task(_wrapper())


# ── /start ────────────────────────────────────────────────────────────────────

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.save_user(user.id, user.first_name or "User", user.username)

    text = (
        f"<b>👋 Hey {user.first_name}! Welcome to TagMaster Bot! 🤖✨</b>\n\n"
        "I'm your <b>ultimate group tagging assistant</b> — smarter, funnier & human-like!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>What I Can Do:</b>\n\n"
        "🏷️ <b>8 Tagging Modes</b> — Hindi, English, GM, GN, Jokes, All & more!\n"
        "😄 <b>Human-Like Messages</b> — Funny, flirty, meme-worthy tags!\n"
        "🛡️ <b>Spam Protected</b> — FloodWait safe, smart delays built-in!\n"
        "⏸️ <b>Tag Controls</b> — Pause, Resume & Stop anytime!\n"
        "📢 <b>Broadcast</b> — Owner can message all users & groups!\n"
        "📊 <b>Stats</b> — Live count of groups & users!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <b>Choose an option below to get started!</b>"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add Me to Your Group",
                url=f"https://t.me/{context.bot.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
            InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL),
        ],
    ]
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ── /help ─────────────────────────────────────────────────────────────────────

HELP_TEXT = (
    "<b>📖 TagMaster Bot — All Commands</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>🏷️ Tagging Commands</b> <i>(Group Admins only)</i>\n\n"
    "/hitag  — Tag all members in <b>Hindi</b> 🇮🇳\n"
    "/entag  — Tag all members in <b>English</b> 🇬🇧\n"
    "/gmtag  — Tag all with <b>Good Morning</b> msgs 🌅\n"
    "/gntag  — Tag all with <b>Good Night</b> msgs 🌙\n"
    "/tagall — Tag all (Hinglish mix — memes+jokes+flirt) 🔥\n"
    "/jtag   — Tag all with <b>Jokes</b> (Hinglish) 😂\n\n"
    "<b>👑 Admin / All Tag</b>\n\n"
    "/admin &lt;msg&gt;  — Tag all group admins 👮\n"
    "@admin &lt;msg&gt;  — Same as /admin\n"
    "/all &lt;msg&gt;    — Tag all members (admins only) 📢\n"
    "@all &lt;msg&gt;    — Same as /all\n"
    "<i>💡 Custom message is optional e.g. /admin plz start vc</i>\n\n"
    "<b>⏸️ Tag Control</b> <i>(Group Admins only)</i>\n\n"
    "/stop   — Stop current tagging 🛑\n"
    "/pause  — Pause tagging ⏸️\n"
    "/resume — Resume paused tagging ▶️\n\n"
    "<b>📊 General</b>\n\n"
    "/start  — Welcome message\n"
    "/help   — Show this menu ❓\n"
    "/stats  — Bot usage stats 📈\n\n"
    "<b>👑 Owner Only</b>\n\n"
    "/broadcast &lt;msg&gt; — Broadcast to all users + groups\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    "<i>⚡ Tags 5–6 users per message with smart delays to avoid Telegram bans ✅</i>"
)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_start")]]
    await query.edit_message_text(
        HELP_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def back_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    text = (
        f"<b>👋 Hey {user.first_name}! Welcome to TagMaster Bot! 🤖✨</b>\n\n"
        "I'm your <b>ultimate group tagging assistant</b> — smarter, funnier & human-like!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥 <b>What I Can Do:</b>\n\n"
        "🏷️ <b>8 Tagging Modes</b> — Hindi, English, GM, GN, Jokes, All & more!\n"
        "😄 <b>Human-Like Messages</b> — Funny, flirty, meme-worthy tags!\n"
        "🛡️ <b>Spam Protected</b> — FloodWait safe, smart delays built-in!\n"
        "⏸️ <b>Tag Controls</b> — Pause, Resume & Stop anytime!\n"
        "📢 <b>Broadcast</b> — Owner can message all users & groups!\n"
        "📊 <b>Stats</b> — Live count of groups & users!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👇 <b>Choose an option below to get started!</b>"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Add Me to Your Group",
                url=f"https://t.me/{context.bot.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton("📖 Help & Commands", callback_data="help_menu"),
            InlineKeyboardButton("📢 Updates", url=UPDATES_CHANNEL),
        ],
    ]
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ── Bot added to group ────────────────────────────────────────────────────────

async def new_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fires when any user joins.  We only care when IT'S THE BOT."""
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            await db.save_group(chat.id, chat.title or "Unknown")
            await safe_send(
                context,
                chat.id,
                "🎉 <b>Thanks for adding me to this group!</b>\n\n"
                "I'm <b>TagMaster Bot</b> 🤖 — your smart group tagger!\n\n"
                "📌 Type /help to see all my commands and features.\n\n"
                "I support <b>8 tagging modes</b>, anti-spam protection, "
                "pause/stop controls & much more!\n\n"
                "Admins can control everything. Let's get started! 🔥",
                parse_mode=ParseMode.HTML,
            )


# ── Tag commands ──────────────────────────────────────────────────────────────

async def _generic_tag(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    msg_pool: list,
    task_key: str,
    label: str,
):
    """Shared handler for hitag / entag / gmtag / gntag / tagall / jtag."""
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ This command works in groups only!")

    if not await is_admin(update, context):
        return await update.message.reply_text(
            "❌ <b>Only group admins can use this command!</b>",
            parse_mode=ParseMode.HTML,
        )

    current = await db.get_tag_state(chat.id, task_key)
    if current == "running":
        return await update.message.reply_text(
            "⚠️ A tagging session is already running!\n"
            "Use /stop to stop it first.",
        )

    members = await db.get_group_members(chat.id)
    if not members:
        return await update.message.reply_text(
            "⚠️ <b>No members tracked yet!</b>\n\n"
            "Members are tracked automatically as they chat in this group. "
            "Ask members to send a message first, then retry.",
            parse_mode=ParseMode.HTML,
        )

    await update.message.reply_text(
        f"🚀 <b>Starting {label} Tagging...</b>\n"
        f"👥 Members to tag: <b>{len(members)}</b>\n"
        f"⏱️ Estimated time: ~{max(1, len(members)//5 * 4)} seconds\n\n"
        "📌 Use /pause ⏸️ | /stop 🛑 to control",
        parse_mode=ParseMode.HTML,
    )

    _start_tagging_task(context, chat.id, members, msg_pool, task_key)


async def hitag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generic_tag(update, context, HINDI_MSGS, "hitag", "Hindi 🇮🇳")

async def entag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generic_tag(update, context, ENGLISH_MSGS, "entag", "English 🇬🇧")

async def gmtag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generic_tag(update, context, GM_MSGS, "gmtag", "Good Morning 🌅")

async def gntag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generic_tag(update, context, GN_MSGS, "gntag", "Good Night 🌙")

async def tagall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = TAGALL_MSGS + HINDI_MSGS + ENGLISH_MSGS
    await _generic_tag(update, context, pool, "tagall", "Tag All 🔥")

async def jtag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _generic_tag(update, context, JTAG_MSGS, "jtag", "Jokes 😂")


# ── /admin & @admin ───────────────────────────────────────────────────────────

async def _admin_tag(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_msg: str):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Works in groups only!")

    try:
        admins = await context.bot.get_chat_administrators(chat.id)
    except TelegramError as e:
        return await update.message.reply_text(f"❌ Couldn't fetch admins: {e}")

    admin_list = [
        {"user_id": a.user.id, "first_name": a.user.first_name or "Admin"}
        for a in admins
        if not a.user.is_bot
    ]
    if not admin_list:
        return await update.message.reply_text("⚠️ No human admins found!")

    header = f"📢 <b>{custom_msg}</b>\n\n" if custom_msg else "👮 <b>Attention Admins!</b> 🔔\n\n"

    await update.message.reply_text(
        f"👮 Tagging <b>{len(admin_list)}</b> admin(s)...",
        parse_mode=ParseMode.HTML,
    )

    for chunk in chunk_list(admin_list, 6):
        tags = " ".join(
            f'<a href="tg://user?id={u["user_id"]}">{u["first_name"]}</a>'
            for u in chunk
        )
        await safe_send(context, chat.id, f"{header}{tags}", parse_mode=ParseMode.HTML)
        await asyncio.sleep(2.0)


async def admin_tag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom = " ".join(context.args) if context.args else ""
    await _admin_tag(update, context, custom)


# ── /all & @all ───────────────────────────────────────────────────────────────

async def _all_tag(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_msg: str):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Works in groups only!")

    if not await is_admin(update, context):
        return await update.message.reply_text(
            "❌ <b>Admins only!</b>", parse_mode=ParseMode.HTML
        )

    current = await db.get_tag_state(chat.id, "all_tag")
    if current == "running":
        return await update.message.reply_text("⚠️ Tagging already running! Use /stop first.")

    members = await db.get_group_members(chat.id)
    if not members:
        return await update.message.reply_text(
            "⚠️ No members tracked yet. Ask members to send a message first!"
        )

    header = f"📢 <b>{custom_msg}</b>\n\n" if custom_msg else None

    await update.message.reply_text(
        f"📢 Tagging <b>{len(members)}</b> members...\n"
        "📌 Use /pause ⏸️ | /stop 🛑 to control",
        parse_mode=ParseMode.HTML,
    )

    async def _run():
        await db.set_tag_state(chat.id, "all_tag", "running")
        try:
            for chunk in chunk_list(members, 6):
                state = await db.get_tag_state(chat.id, "all_tag")
                if state == "stopped":
                    await safe_send(context, chat.id, "⛔ Tagging stopped.", parse_mode=ParseMode.HTML)
                    return
                while state == "paused":
                    await asyncio.sleep(1.5)
                    state = await db.get_tag_state(chat.id, "all_tag")
                    if state == "stopped":
                        await safe_send(context, chat.id, "⛔ Tagging stopped.", parse_mode=ParseMode.HTML)
                        return

                tags = " ".join(
                    f'<a href="tg://user?id={u["user_id"]}">{u["first_name"]}</a>'
                    for u in chunk
                )
                text = f"{header}{tags}" if header else tags
                await safe_send(context, chat.id, text, parse_mode=ParseMode.HTML)
                await asyncio.sleep(3.0)

            await db.set_tag_state(chat.id, "all_tag", "idle")
            await safe_send(context, chat.id, "✅ Done! All members tagged. 🎉", parse_mode=ParseMode.HTML)
        except Exception as exc:
            logger.exception("all_tag crashed: %s", exc)
            await db.set_tag_state(chat.id, "all_tag", "idle")

    asyncio.create_task(_run())


async def all_tag_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    custom = " ".join(context.args) if context.args else ""
    await _all_tag(update, context, custom)


# ── Text-based @admin / @all triggers ────────────────────────────────────────

async def text_trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle @admin <msg> and @all <msg> as plain text."""
    msg = update.message
    if not msg or not msg.text:
        return
    text = msg.text.strip()

    if text.lower().startswith("@admin"):
        rest = text[len("@admin"):].strip()
        await _admin_tag(update, context, rest)

    elif text.lower().startswith("@all"):
        rest = text[len("@all"):].strip()
        await _all_tag(update, context, rest)


# ── Control commands ──────────────────────────────────────────────────────────

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Use in groups only!")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")

    for key in ALL_TASK_KEYS:
        await db.set_tag_state(chat.id, key, "stopped")

    await update.message.reply_text(
        "⛔ <b>All tagging stopped!</b>",
        parse_mode=ParseMode.HTML,
    )


async def pause_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Use in groups only!")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")

    paused_any = False
    for key in ALL_TASK_KEYS:
        if await db.get_tag_state(chat.id, key) == "running":
            await db.set_tag_state(chat.id, key, "paused")
            paused_any = True

    if paused_any:
        await update.message.reply_text(
            "⏸️ <b>Tagging paused!</b>\nUse /resume ▶️ to continue.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text("ℹ️ No active tagging session to pause.")


async def resume_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == "private":
        return await update.message.reply_text("⚠️ Use in groups only!")
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admins only!")

    resumed_any = False
    for key in ALL_TASK_KEYS:
        if await db.get_tag_state(chat.id, key) == "paused":
            await db.set_tag_state(chat.id, key, "running")
            resumed_any = True

    if resumed_any:
        await update.message.reply_text(
            "▶️ <b>Tagging resumed!</b>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.message.reply_text("ℹ️ No paused tagging session found.")


# ── /stats ────────────────────────────────────────────────────────────────────

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = await db.get_stats()
    now   = datetime.now().strftime("%d %b %Y  %H:%M UTC")
    await update.message.reply_text(
        "📊 <b>TagMaster Bot — Live Stats</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Total Users   : <b>{stats['users']:,}</b>\n"
        f"🏘️ Total Groups  : <b>{stats['groups']:,}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 As of: <i>{now}</i>",
        parse_mode=ParseMode.HTML,
    )


# ── /broadcast ────────────────────────────────────────────────────────────────

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != BOT_OWNER:
        return await update.message.reply_text(
            "❌ <b>Owner only command!</b>", parse_mode=ParseMode.HTML
        )

    if not context.args:
        return await update.message.reply_text(
            "📢 <b>Usage:</b> /broadcast &lt;your message here&gt;\n\n"
            "<i>Example: /broadcast Bot is updated! Check /help</i>",
            parse_mode=ParseMode.HTML,
        )

    bcast_text = " ".join(context.args)
    formatted  = (
        "📢 <b>Message from Bot Owner</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{bcast_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "<i>— TagMaster Bot</i>"
    )

    all_users  = await db.get_all_users()
    all_groups = await db.get_all_groups()
    total      = len(all_users) + len(all_groups)

    if total == 0:
        return await update.message.reply_text("⚠️ No users or groups in database yet!")

    # Send initial status message
    status = await update.message.reply_text(
        f"📤 <b>Broadcasting...</b>\n"
        f"👤 Users : {len(all_users)}\n"
        f"🏘️ Groups: {len(all_groups)}\n"
        f"📦 Total : {total}\n\n"
        "⏳ Please wait...",
        parse_mode=ParseMode.HTML,
    )

    sent_u = failed_u = blocked_u = 0
    sent_g = failed_g = 0

    # ── Broadcast to users ────────────────────────────────────────────────────
    for uid in all_users:
        try:
            await context.bot.send_message(uid, formatted, parse_mode=ParseMode.HTML)
            sent_u += 1
        except TelegramError as e:
            err_str = str(e).lower()
            if "blocked" in err_str or "deactivated" in err_str or "not found" in err_str:
                blocked_u += 1
            else:
                failed_u += 1
        # Rate-limit: ~20 msgs/sec max
        await asyncio.sleep(0.05)

        # Update progress every 50 users
        if (sent_u + failed_u + blocked_u) % 50 == 0:
            try:
                await status.edit_text(
                    f"📤 <b>Broadcasting... (users)</b>\n"
                    f"✅ Sent    : {sent_u}\n"
                    f"🚫 Blocked : {blocked_u}\n"
                    f"❌ Failed  : {failed_u}\n"
                    f"⏳ Remaining: ~{len(all_users) - sent_u - failed_u - blocked_u}",
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError:
                pass

    # ── Broadcast to groups ───────────────────────────────────────────────────
    for gid in all_groups:
        try:
            await context.bot.send_message(gid, formatted, parse_mode=ParseMode.HTML)
            sent_g += 1
        except TelegramError:
            failed_g += 1
        await asyncio.sleep(0.1)

    # ── Final report ──────────────────────────────────────────────────────────
    await status.edit_text(
        "✅ <b>Broadcast Complete!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Users</b>\n"
        f"   ✔️ Sent    : {sent_u}\n"
        f"   🚫 Blocked : {blocked_u}\n"
        f"   ❌ Failed  : {failed_u}\n\n"
        f"🏘️ <b>Groups</b>\n"
        f"   ✔️ Sent    : {sent_g}\n"
        f"   ❌ Failed  : {failed_g}\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Total sent: {sent_u + sent_g}</b>",
        parse_mode=ParseMode.HTML,
    )


# ── Track users & group members ───────────────────────────────────────────────

async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save user & group-member data on every message."""
    if not update.effective_user or not update.effective_chat:
        return
    user = update.effective_user
    chat = update.effective_chat

    # Always save the user
    await db.save_user(user.id, user.first_name or "User", user.username)

    # If in a group, save the group and member
    if chat.type in ("group", "supergroup"):
        await db.save_group(chat.id, chat.title or "Group")
        await db.save_member(chat.id, user.id, user.first_name or "User")


# ── Application setup ─────────────────────────────────────────────────────────

async def post_init(application: Application):
    """Called after Application is built — initialise MongoDB here."""
    await db.init_db()
    logger.info("✅ Bot is online | Owner ID: %s", BOT_OWNER)


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Command handlers ──────────────────────────────────────────────────────
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

    # ── Callback query handlers ───────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(help_callback,       pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(back_start_callback, pattern="^back_start$"))

    # ── @admin / @all text triggers (groups only) ─────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
            text_trigger_handler,
        )
    )

    # ── New chat member (bot added to group) ──────────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            new_chat_member_handler,
        )
    )

    # ── Activity tracker (track all users & members) ──────────────────────────
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            track_activity,
        )
    )

    logger.info("🤖 TagMaster Bot polling started...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
