"""
handlers/tagging.py – All 8 tagging command handlers.

Architecture:
  • Tagging runs as a background asyncio.Task (fire-and-forget).
    The handler returns immediately after starting the task so Pyrogram
    can keep processing other updates during long tagging sessions.
  • Between each message the loop checks session.status (pause / stop).
  • FloodWait is caught and slept through transparently (up to 4 retries).
  • 6 mentions per message for /admin and /all (configurable via USERS_PER_MSG).
"""

import asyncio
import logging
import random

from pyrogram import Client, enums
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from config import Config
from database import upsert_group
from utils import (
    admin_only,
    get_members,
    get_admin_members,
    safe_send,
    build_mention,
    get_msg,
    ADMIN_TAG_PREFIX,
    ADMIN_TAG_SUFFIX,
    ALL_TAG_PREFIX,
    ALL_TAG_SUFFIX,
    tag_manager)
from utils.botapi import te

log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  Core tagging loop  (runs as a background Task)
# ══════════════════════════════════════════════════════════════════════════════

async def _run_tag_loop(
    client: Client,
    chat_id: int,
    members: list,
    tag_type: str,
    session,
    progress_msg: Message,
    custom_text: str = "") -> None:
    total  = len(members)
    tagged = 0
    random.shuffle(members)

    for uid, name in members:
        # honour pause / stop
        await session.wait_if_paused()
        if session.is_stopped:
            break

        mention = build_mention(uid, name)
        text    = get_msg(tag_type, mention, custom_text)

        # send with FloodWait retry
        for _ in range(4):
            try:
                await client.send_message(chat_id, text)
                tagged += 1
                break
            except FloodWait as e:
                wait = e.value + 3
                log.warning("FloodWait %ds in chat %s", wait, chat_id)
                await asyncio.sleep(wait)
            except RPCError as e:
                log.error("RPCError tagging uid %s: %s", uid, e)
                break

        await asyncio.sleep(Config.TAG_DELAY)

        # progress edit every 10 successful tags
        if tagged > 0 and tagged % 10 == 0:
            try:
                await progress_msg.edit_text(
                    
                    f"{te('tag','🏷️')} **Tagging in progress…**\n\n"
                    f"✅ Tagged : `{tagged}` / `{total}`\n"
                    f"{te('lightning','⚡')} Use /stop or /pause to control."
                ,
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass

    # completion message
    if session.is_stopped:
        finish = (
            f"{te('stop','🛑')} **Tagging stopped!**\n"
            f"Tagged `{tagged}` out of `{total}` members."
        )
    else:
        finish = (
            f"{te('check','✅')} **Tagging complete!**\n\n"
            f"👥 Total tagged : `{tagged}` / `{total}`\n"
            f"{te('tada','🎉')} All done! Great success!"
        )

    try:
        await progress_msg.edit_text(finish,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception:
        await safe_send(client, chat_id, finish, parse_mode=enums.ParseMode.HTML)

    tag_manager.stop(chat_id)


# ══════════════════════════════════════════════════════════════════════════════
#  Generic tagger factory
# ══════════════════════════════════════════════════════════════════════════════

async def _generic_tagger(
    client: Client,
    message: Message,
    tag_type: str,
    type_label: str) -> None:
    chat = message.chat
    await upsert_group(chat.id, chat.title, getattr(chat, "username", None))

    if tag_manager.is_active(chat.id):
        await message.reply_text(
            
            f"{te('warning','⚠️')} **A tagging session is already running!**\n\n"
            "Use /stop first, then start a new one."
        ,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    progress_msg = await message.reply_text(
        
        f"⏳ <b>{type_label} starting…</b> Please wait."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    members = await get_members(client, chat.id)

    if not members:
        await progress_msg.edit_text(
            
            f"{te('cross','❌')} No taggable members found.\n"
            "_Make sure I have permission to view group members._"
        ,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    await progress_msg.edit_text(
        
        f"{te('rocket','🚀')} <b>{type_label} is LIVE!</b>\n\n"
        f"Use /pause · /resume · /stop to control."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    session = tag_manager.start(chat.id)
    task = asyncio.create_task(
        _run_tag_loop(client, chat.id, members, tag_type, session, progress_msg)
    )
    session.task = task
    # Handler returns here — task runs in the background


# ══════════════════════════════════════════════════════════════════════════════
#  1. /hitag  – Hindi only
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_hitag(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "hitag", "🇮🇳 Hindi Tag")


# ══════════════════════════════════════════════════════════════════════════════
#  2. /entag  – English only
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_entag(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "entag", "🇬🇧 English Tag")


# ══════════════════════════════════════════════════════════════════════════════
#  3. /gmtag  – Good Morning Hinglish
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_gmtag(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "gmtag", "🌅 Good Morning Tag")


# ══════════════════════════════════════════════════════════════════════════════
#  4. /gntag  – Good Night Hinglish
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_gntag(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "gntag", "🌙 Good Night Tag")


# ══════════════════════════════════════════════════════════════════════════════
#  5. /tagall  – General Hinglish mix
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_tagall(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "tagall", "🔥 Tag All")


# ══════════════════════════════════════════════════════════════════════════════
#  6. /jtag  – Joke tag Hinglish
# ══════════════════════════════════════════════════════════════════════════════
@admin_only
async def cmd_jtag(client: Client, message: Message) -> None:
    await _generic_tagger(client, message, "jtag", "😂 Joke Tag")


# ══════════════════════════════════════════════════════════════════════════════
#  7. /admin or @admin  – Tag only admins, 6 per message  (anyone can use)
# ══════════════════════════════════════════════════════════════════════════════

async def cmd_admin_tag(client: Client, message: Message) -> None:
    chat = message.chat
    raw  = message.text or message.caption or ""

    # Strip command/prefix and capture optional custom text
    parts  = raw.strip().split(maxsplit=1)
    custom = parts[1].strip() if len(parts) > 1 else ""

    progress_msg = await message.reply_text(
        "📢 **Fetching admin list…** Please wait."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    admins: list = []
    async for uid, name in get_admin_members(client, chat.id):
        admins.append((uid, name))

    if not admins:
        await progress_msg.edit_text(f"{te('cross','❌')} No admins found in this group.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    chunks = [
        admins[i : i + Config.USERS_PER_MSG]
        for i in range(0, len(admins), Config.USERS_PER_MSG)
    ]

    for idx, chunk in enumerate(chunks):
        mentions = "\n".join(
            f"👤 {build_mention(uid, name)}" for uid, name in chunk
        )
        header = f"💬 **{custom}**\n\n" if custom else ""
        text   = ADMIN_TAG_PREFIX + header + mentions + ADMIN_TAG_SUFFIX

        for _ in range(4):
            try:
                await client.send_message(chat.id, text)
                break
            except FloodWait as e:
                await asyncio.sleep(e.value + 2)
            except RPCError as e:
                log.error("RPCError in cmd_admin_tag: %s", e)
                break

        await asyncio.sleep(Config.BATCH_DELAY)

    try:
        await progress_msg.delete()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  8. /all or @all  – Tag everyone, 6 per message  (admins only)
# ══════════════════════════════════════════════════════════════════════════════

@admin_only
async def cmd_all_tag(client: Client, message: Message) -> None:
    chat = message.chat
    raw  = message.text or message.caption or ""

    parts  = raw.strip().split(maxsplit=1)
    custom = parts[1].strip() if len(parts) > 1 else ""

    if tag_manager.is_active(chat.id):
        await message.reply_text(
            "⚠️ **Another tagging session is active.**\n\nUse /stop first."
        ,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    progress_msg = await message.reply_text(
        "⏳ **Collecting members…** Please wait."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    members = await get_members(client, chat.id)

    if not members:
        await progress_msg.edit_text(f"{te('cross','❌')} No members found.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    await progress_msg.edit_text(
        
        f"{te('rocket','🚀')} <b>All-Tag is LIVE!</b>\n\n"
        f"Use /pause · /resume · /stop to control."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    session = tag_manager.start(chat.id)

    async def _all_tag_task() -> None:
        chunks = [
            members[i : i + Config.USERS_PER_MSG]
            for i in range(0, len(members), Config.USERS_PER_MSG)
        ]
        batches_sent = 0

        for idx, chunk in enumerate(chunks):
            await session.wait_if_paused()
            if session.is_stopped:
                break

            mentions = "\n".join(
                f"👤 {build_mention(uid, name)}" for uid, name in chunk
            )
            header = f"💬 **{custom}**\n\n" if custom else ""
            text   = ALL_TAG_PREFIX + header + mentions + ALL_TAG_SUFFIX

            for _ in range(4):
                try:
                    await client.send_message(chat.id, text)
                    batches_sent += 1
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value + 2)
                except RPCError as e:
                    log.error("RPCError in cmd_all_tag: %s", e)
                    break

            await asyncio.sleep(Config.BATCH_DELAY)

        total_tagged = batches_sent * Config.USERS_PER_MSG
        finish = (
            f"{te('stop','🛑')} **All-tag stopped!** Sent `{batches_sent}` batches (~{total_tagged} users)."
            if session.is_stopped
            else
            f"✅ **All-tag complete!**\n\n"
            f"{te('bell','📣')} Reached ~`{total_tagged}` members in `{batches_sent}` messages. {te('tada','🎉')}"
        )

        try:
            await progress_msg.edit_text(finish,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            await safe_send(client, chat.id, finish, parse_mode=enums.ParseMode.HTML)

        tag_manager.stop(chat.id)

    task = asyncio.create_task(_all_tag_task())
    session.task = task


# ══════════════════════════════════════════════════════════════════════════════
#  9. /vctag  – VC invite, one mention per message, online-first ordering
# ══════════════════════════════════════════════════════════════════════════════

@admin_only
async def cmd_vctag(client: Client, message: Message) -> None:
    chat = message.chat
    await upsert_group(chat.id, chat.title, getattr(chat, "username", None))

    if tag_manager.is_active(chat.id):
        await message.reply_text(
            
            f"{te('warning','⚠️')} **A tagging session is already running!**\n\n"
            "Use /stop first, then start /vctag."
        ,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    progress_msg = await message.reply_text(
        
        f"{te('mic','🎙️')} <b>VC Tag starting…</b> Please wait."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    # get_members already returns list sorted online → recently → last_week
    members = await get_members(client, chat.id)

    if not members:
        await progress_msg.edit_text(
            
            f"{te('cross','❌')} No taggable members found."
        ,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    await progress_msg.edit_text(
        
        f"{te('mic','🎙️')} <b>VC Tag is LIVE!</b> 🔴\n\n"
        f"Use /pause · /resume · /stop to control."
    ,
        parse_mode=enums.ParseMode.HTML,
    )

    session = tag_manager.start(chat.id)

    async def _vctag_task() -> None:
        tagged = 0
        for uid, name in members:
            await session.wait_if_paused()
            if session.is_stopped:
                break

            mention = build_mention(uid, name)
            # Each message = unique VC invite text + mention (one per msg)
            vc_msg = get_msg("vctag", mention)

            # Wrap vc_msg with HTML — prepend premium mic emoji, send as HTML
            html_vc_msg = f"{te('mic','🎙️')} {vc_msg}"

            for _ in range(4):
                try:
                    await client.send_message(
                        chat.id, html_vc_msg,
                        parse_mode=enums.ParseMode.HTML,
                    )
                    tagged += 1
                    break
                except FloodWait as e:
                    await asyncio.sleep(e.value + 2)
                except RPCError as e:
                    log.error("RPCError vctag uid %s: %s", uid, e)
                    break

            # Update progress every 10 tags
            if tagged > 0 and tagged % 10 == 0:
                try:
                    await progress_msg.edit_text(
                        
                        f"{te('mic','🎙️')} <b>VC Tag in progress…</b> 🔴\n"
                        f"Use /stop or /pause to control."
                    ,
                        parse_mode=enums.ParseMode.HTML,
                    )
                except Exception:
                    pass

            await asyncio.sleep(Config.TAG_DELAY)

        if session.is_stopped:
            finish = (
                f"{te('stop','🛑')} **VC Tag stopped!**\n"
                f"Invited `{tagged}` out of `{len(members)}` members."
            )
        else:
            finish = (
                f"{te('mic','🎙️')} **VC Tag complete!** 🎉\n\n"
                f"✅ Invited : `{tagged}` / `{len(members)}`\n"
                f"{te('fire','🔥')} VC should be lit now! Enjoy!"
            )

        try:
            await progress_msg.edit_text(finish,
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            await safe_send(client, chat.id, finish, parse_mode=enums.ParseMode.HTML)

        tag_manager.stop(chat.id)

    task = asyncio.create_task(_vctag_task())
    session.task = task
