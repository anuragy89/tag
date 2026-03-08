"""
bot.py – Tag Master Bot entry point.

ARCHITECTURE (event-loop safe):
  • Client() is created INSIDE main() — after asyncio.run() has started
    the event loop. This guarantees Pyrogram, Motor, and all asyncio tasks
    all bind to the SAME loop. No "Future attached to different loop" ever.
  • We use await app.start() / pyrogram.idle() / await app.stop() instead
    of app.run() (which accepts no args in Kurigram) or async with app
    (which had the same loop-capture issue when Client was at module level).
"""

import asyncio
import logging
import sys

from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message

from config import Config
from database import init_db, close_db, upsert_user, upsert_group

# ── Logging setup (runs before the loop so logging is always available) ───────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("TagBot")


# ── Validate env vars immediately ─────────────────────────────────────────────
def _validate_config() -> None:
    missing = []
    if not Config.API_ID:    missing.append("API_ID")
    if not Config.API_HASH:  missing.append("API_HASH")
    if not Config.BOT_TOKEN: missing.append("BOT_TOKEN")
    if not Config.OWNER_ID:  missing.append("OWNER_ID")
    if not Config.MONGO_URI: missing.append("MONGO_URI")
    if missing:
        log.critical("❌ Missing required env vars: %s", ", ".join(missing))
        sys.exit(1)

_validate_config()


# ══════════════════════════════════════════════════════════════════════════════
#  main() — everything runs inside a single asyncio.run() loop
# ══════════════════════════════════════════════════════════════════════════════

async def main() -> None:

    # ── 1. Connect to MongoDB ─────────────────────────────────────────────────
    # Motor's AsyncIOMotorClient binds to the running loop here — correct.
    await init_db()

    # ── 2. Create Pyrogram client INSIDE the running loop ────────────────────
    # This is the critical fix: Client() captures asyncio.get_event_loop()
    # at instantiation. By creating it here, it captures the loop that
    # asyncio.run() started — the same one Motor and all tasks will use.
    app = Client(
        "tagbot_session",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        sleep_threshold=Config.FLOOD_SLEEP,
    )

    # ── 3. Import handlers (inside main so they can reference app) ────────────
    from handlers.start import (
        cmd_start, cmd_help, callback_handler, on_new_chat_member,
    )
    from handlers.tagging import (
        cmd_hitag, cmd_entag, cmd_gmtag, cmd_gntag,
        cmd_tagall, cmd_jtag, cmd_admin_tag, cmd_all_tag,
    )
    from handlers.control import cmd_stop, cmd_pause, cmd_resume
    from handlers.broadcast import cmd_broadcast, cmd_stats

    # ── 4. Register all handlers ──────────────────────────────────────────────
    G = filters.group  # shorthand

    # /start — private DM only
    app.add_handler(MessageHandler(
        cmd_start, filters.command("start") & filters.private
    ))

    # /help — anywhere
    app.add_handler(MessageHandler(cmd_help, filters.command("help")))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Bot added to group
    app.add_handler(MessageHandler(
        on_new_chat_member, filters.new_chat_members & G
    ))

    # Tagging commands (admin-only enforced inside each handler)
    app.add_handler(MessageHandler(cmd_hitag,  filters.command("hitag")  & G))
    app.add_handler(MessageHandler(cmd_entag,  filters.command("entag")  & G))
    app.add_handler(MessageHandler(cmd_gmtag,  filters.command("gmtag")  & G))
    app.add_handler(MessageHandler(cmd_gntag,  filters.command("gntag")  & G))
    app.add_handler(MessageHandler(cmd_tagall, filters.command("tagall") & G))
    app.add_handler(MessageHandler(cmd_jtag,   filters.command("jtag")   & G))

    # /admin or @admin (any member can call)
    app.add_handler(MessageHandler(
        cmd_admin_tag,
        (filters.command("admin") | filters.regex(r"^@admin(\s|$)")) & G,
    ))

    # /all or @all (admins only — enforced inside handler)
    app.add_handler(MessageHandler(
        cmd_all_tag,
        (filters.command("all") | filters.regex(r"^@all(\s|$)")) & G,
    ))

    # Control commands
    app.add_handler(MessageHandler(cmd_stop,   filters.command("stop")   & G))
    app.add_handler(MessageHandler(cmd_pause,  filters.command("pause")  & G))
    app.add_handler(MessageHandler(cmd_resume, filters.command("resume") & G))

    # Owner commands (work everywhere)
    app.add_handler(MessageHandler(cmd_broadcast, filters.command("broadcast")))
    app.add_handler(MessageHandler(cmd_stats,     filters.command("stats")))

    # Passive tracker — silently records users/groups to MongoDB
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

    # ── 5. Start the bot ──────────────────────────────────────────────────────
    await app.start()

    me = await app.get_me()
    log.info("✅ Logged in as @%s  (ID: %s)", me.username, me.id)
    log.info("🏷️  Tag Master Bot is LIVE — waiting for messages.")

    # ── 6. Block until SIGTERM / Ctrl+C ──────────────────────────────────────
    # pyrogram.idle() is the official way to keep a Pyrogram bot alive.
    # It handles SIGINT and SIGTERM cleanly on both Linux and Windows.
    await idle()

    # ── 7. Graceful shutdown ──────────────────────────────────────────────────
    log.info("🛑 Shutdown signal received — stopping bot…")
    await app.stop()
    await close_db()
    log.info("👋 Bot stopped cleanly.")


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point — standard asyncio.run() is correct here because
#  Client() is now created INSIDE main(), not at module level.
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(main())
