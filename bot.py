"""
bot.py – Tag Master Bot entry point.

KEY FIX: Uses app.run(main()) — Pyrogram's own event loop manager.
         This prevents the RuntimeError "Future attached to a different loop"
         that occurs when Client() is instantiated at module level and then
         a separate loop manager is used to start it.

Required environment variables:
  API_ID, API_HASH, BOT_TOKEN, OWNER_ID, MONGO_URI

Optional:
  UPDATES_CHANNEL, SUPPORT_GROUP, BOT_USERNAME,
  TAG_DELAY, BATCH_DELAY, FLOOD_SLEEP, USERS_PER_MSG, MONGO_DB_NAME
"""

import asyncio
import logging
import sys

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message

from config import Config
from database import init_db, close_db, upsert_user, upsert_group

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("TagBot")


# ── Validate required env vars before doing anything else ────────────────────
def _validate_config() -> None:
    missing = []
    if not Config.API_ID:       missing.append("API_ID")
    if not Config.API_HASH:     missing.append("API_HASH")
    if not Config.BOT_TOKEN:    missing.append("BOT_TOKEN")
    if not Config.OWNER_ID:     missing.append("OWNER_ID")
    if not Config.MONGO_URI:    missing.append("MONGO_URI")
    if missing:
        log.critical("❌ Missing required environment variables: %s", ", ".join(missing))
        sys.exit(1)

_validate_config()


# ── Create Pyrogram Client at module level (handlers registered here too) ────
# NOTE: The client must NOT be started here. app.run() below handles startup
#       inside the correct event loop context.
app = Client(
    "tagbot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    sleep_threshold=Config.FLOOD_SLEEP,
)


# ── Import all command handlers ───────────────────────────────────────────────
from handlers.start    import cmd_start, cmd_help, callback_handler, on_new_chat_member
from handlers.tagging  import (
    cmd_hitag, cmd_entag, cmd_gmtag, cmd_gntag,
    cmd_tagall, cmd_jtag, cmd_admin_tag, cmd_all_tag,
)
from handlers.control   import cmd_stop, cmd_pause, cmd_resume
from handlers.broadcast import cmd_broadcast, cmd_stats


# ══════════════════════════════════════════════════════════════════════════════
#  Register all handlers
# ══════════════════════════════════════════════════════════════════════════════

_GRP = filters.group

# /start – private DM only
app.add_handler(MessageHandler(cmd_start, filters.command("start") & filters.private))

# /help – anywhere
app.add_handler(MessageHandler(cmd_help, filters.command("help")))

# Inline keyboard button callbacks
app.add_handler(CallbackQueryHandler(callback_handler))

# Bot added to a group → send welcome message
app.add_handler(MessageHandler(on_new_chat_member, filters.new_chat_members & _GRP))

# ── Tagging commands (admin-only check inside each handler) ──────────────────
app.add_handler(MessageHandler(cmd_hitag,  filters.command("hitag")  & _GRP))
app.add_handler(MessageHandler(cmd_entag,  filters.command("entag")  & _GRP))
app.add_handler(MessageHandler(cmd_gmtag,  filters.command("gmtag")  & _GRP))
app.add_handler(MessageHandler(cmd_gntag,  filters.command("gntag")  & _GRP))
app.add_handler(MessageHandler(cmd_tagall, filters.command("tagall") & _GRP))
app.add_handler(MessageHandler(cmd_jtag,   filters.command("jtag")   & _GRP))

# /admin or @admin – tag only admins (any member can use)
app.add_handler(MessageHandler(
    cmd_admin_tag,
    (filters.command("admin") | filters.regex(r"^@admin(\s|$)")) & _GRP,
))

# /all or @all – tag everyone (admins only, checked inside handler)
app.add_handler(MessageHandler(
    cmd_all_tag,
    (filters.command("all") | filters.regex(r"^@all(\s|$)")) & _GRP,
))

# ── Tagging control (admin-only check inside each handler) ───────────────────
app.add_handler(MessageHandler(cmd_stop,   filters.command("stop")   & _GRP))
app.add_handler(MessageHandler(cmd_pause,  filters.command("pause")  & _GRP))
app.add_handler(MessageHandler(cmd_resume, filters.command("resume") & _GRP))

# ── Owner-only commands (DM and groups) ──────────────────────────────────────
app.add_handler(MessageHandler(cmd_broadcast, filters.command("broadcast")))
app.add_handler(MessageHandler(cmd_stats,     filters.command("stats")))


# ── Passive tracker – records every user/group silently to MongoDB ────────────
@app.on_message(filters.group & ~filters.bot)
async def _passive_tracker(client: Client, message: Message) -> None:
    if message.from_user:
        await upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
    if message.chat:
        await upsert_group(
            message.chat.id,
            message.chat.title,
            getattr(message.chat, "username", None),
        )


# ══════════════════════════════════════════════════════════════════════════════
#  Main coroutine
#  Called by app.run() – the event loop already exists at this point,
#  so Motor and Pyrogram both bind to the SAME loop.
# ══════════════════════════════════════════════════════════════════════════════

async def main() -> None:
    # Connect to MongoDB (runs inside the loop app.run() created)
    await init_db()

    me = await app.get_me()
    log.info("✅ Logged in as @%s  (ID: %s)", me.username, me.id)
    log.info("🏷️  Tag Master Bot is running. Send Ctrl+C or SIGTERM to stop.")

    # Keep running until Ctrl+C / SIGTERM
    await asyncio.Event().wait()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
#
#  app.run(coroutine) is the correct Pyrogram pattern:
#    1. Creates a fresh event loop
#    2. Starts (connects + authenticates) the Pyrogram client
#    3. Runs the coroutine inside that SAME loop
#    4. On exit: stops the client, closes the loop
#
#  Using a separate event loop manager caused "Future attached to a
#  different loop" – app.run() prevents that entirely.
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        app.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        # Close MongoDB connection after the event loop ends
        import asyncio as _asyncio
        try:
            loop = _asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(close_db())
            else:
                loop.run_until_complete(close_db())
        except Exception:
            pass
        log.info("👋 Bot stopped cleanly.")
