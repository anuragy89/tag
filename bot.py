"""
bot.py – Tag Master Bot entry point.

ARCHITECTURE (event-loop safe):
  • Client() is created INSIDE main() — after asyncio.run() has started
    the event loop. Pyrogram, Motor, and all asyncio tasks bind to the
    SAME loop. No "Future attached to different loop" ever.
  • Uses await app.start() / stop() with explicit signal handling.
  • Does NOT use pyrogram.idle() — that function is not consistently
    exported across Kurigram versions and would cause ImportError.
  • Does NOT use app.run() — Kurigram's run() accepts no arguments.
  • asyncio.run(main()) is the correct entry point because Client()
    is created inside main(), not at module level.
"""

import asyncio
import logging
import signal
import sys

from pyrogram import Client, filters, enums
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

    # ── 1. Connect to MongoDB first ───────────────────────────────────────────
    # Motor's AsyncIOMotorClient binds to the already-running loop — correct.
    await init_db()

    # ── 2. Create Pyrogram client INSIDE the running loop ────────────────────
    # Critical: Client() captures the running event loop at instantiation time.
    # Creating it here guarantees it binds to the same loop as Motor and all tasks.
    app = Client(
        "tagbot_session",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        sleep_threshold=Config.FLOOD_SLEEP,
        parse_mode=enums.ParseMode.MARKDOWN,
    )

    # ── 3. Import all handlers ────────────────────────────────────────────────
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
    G = filters.group

    # /start — works everywhere (private DM and groups)
    app.add_handler(MessageHandler(
        cmd_start, filters.command("start")
    ))
    # /help — works anywhere
    app.add_handler(MessageHandler(cmd_help, filters.command("help")))

    # Inline keyboard button callbacks
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Bot added to a group → send welcome
    app.add_handler(MessageHandler(
        on_new_chat_member, filters.new_chat_members & G
    ))

    # Tagging commands — admin-only enforced inside each handler
    app.add_handler(MessageHandler(cmd_hitag,  filters.command("hitag")  & G))
    app.add_handler(MessageHandler(cmd_entag,  filters.command("entag")  & G))
    app.add_handler(MessageHandler(cmd_gmtag,  filters.command("gmtag")  & G))
    app.add_handler(MessageHandler(cmd_gntag,  filters.command("gntag")  & G))
    app.add_handler(MessageHandler(cmd_tagall, filters.command("tagall") & G))
    app.add_handler(MessageHandler(cmd_jtag,   filters.command("jtag")   & G))

    # /admin or @admin — any member can call this
    app.add_handler(MessageHandler(
        cmd_admin_tag,
        (filters.command("admin") | filters.regex(r"^@admin(\s|$)")) & G,
    ))

    # /all or @all — admin-only enforced inside handler
    app.add_handler(MessageHandler(
        cmd_all_tag,
        (filters.command("all") | filters.regex(r"^@all(\s|$)")) & G,
    ))

    # Tagging control — admin-only enforced inside each handler
    app.add_handler(MessageHandler(cmd_stop,   filters.command("stop")   & G))
    app.add_handler(MessageHandler(cmd_pause,  filters.command("pause")  & G))
    app.add_handler(MessageHandler(cmd_resume, filters.command("resume") & G))

    # Owner commands — work everywhere
    app.add_handler(MessageHandler(cmd_broadcast, filters.command("broadcast")))
    app.add_handler(MessageHandler(cmd_stats,     filters.command("stats")))

    # Passive tracker — records every user/group silently to MongoDB
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

    # ── 5. Start the Pyrogram client ──────────────────────────────────────────
    await app.start()

    me = await app.get_me()
    log.info("✅ Logged in as @%s  (ID: %s)", me.username, me.id)
    log.info("🏷️  Tag Master Bot is LIVE — waiting for messages.")

    # ── 6. Block until SIGTERM / SIGINT (Ctrl+C or Heroku dyno stop) ─────────
    # We use asyncio signal handlers + an Event instead of pyrogram.idle()
    # because pyrogram.idle() is not consistently exported across Kurigram
    # builds and would cause ImportError. This approach is 100% reliable.
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _signal_handler():
        log.info("🛑 Shutdown signal received.")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except (NotImplementedError, RuntimeError):
            # Windows doesn't support add_signal_handler for all signals
            signal.signal(sig, lambda s, f: stop_event.set())

    await stop_event.wait()   # blocks here until signal arrives

    # ── 7. Graceful shutdown ──────────────────────────────────────────────────
    log.info("⏳ Stopping bot…")
    await app.stop()
    await close_db()
    log.info("👋 Bot stopped cleanly.")


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
#  asyncio.run() is correct here because Client() is created INSIDE main(),
#  not at module level — so there is no loop mismatch.
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(main())
