"""
config.py – All bot configuration loaded from environment variables.
Set these via Heroku Config Vars or a local .env file.
"""

import os


class Config:
    # ── Core Telegram Credentials ──────────────────────────────────────────────
    API_ID          = int(os.environ.get("API_ID", 0))
    API_HASH        = os.environ.get("API_HASH", "")
    BOT_TOKEN       = os.environ.get("BOT_TOKEN", "")

    # ── Owner ──────────────────────────────────────────────────────────────────
    OWNER_ID        = int(os.environ.get("OWNER_ID", 0))

    # ── MongoDB ────────────────────────────────────────────────────────────────
    # On Heroku: heroku config:set MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net"
    # Free cluster: https://cloud.mongodb.com
    MONGO_URI       = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME   = os.environ.get("MONGO_DB_NAME", "tagbot")

    # ── Tagging Speed / Flood Protection ──────────────────────────────────────
    TAG_DELAY       = float(os.environ.get("TAG_DELAY", 1.5))    # sec between single-tag msgs
    BATCH_DELAY     = float(os.environ.get("BATCH_DELAY", 3.0))  # sec between batch msgs
    FLOOD_SLEEP     = int(os.environ.get("FLOOD_SLEEP", 60))     # pyrogram sleep_threshold
    USERS_PER_MSG   = int(os.environ.get("USERS_PER_MSG", 6))    # mentions per /all and /admin msg

    # ── Bot Links (used in inline buttons) ────────────────────────────────────
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "https://t.me/yourchannel")
    SUPPORT_GROUP   = os.environ.get("SUPPORT_GROUP",   "https://t.me/yoursupport")
    BOT_USERNAME    = os.environ.get("BOT_USERNAME",    "YourTagBot")

    # ── Premium Emoji IDs for inline keyboard button icons ────────────────────
    # These are Telegram document IDs for animated premium emoji.
    # Run  python fetch_emoji_ids.py  once to find real IDs, then paste below.
    # Works because your bot owner account has Telegram Premium.
    # Set to "" to show that button without an emoji icon (no crash).
    PREMIUM_EMOJI = {
        "add":     "",   # ➕  Add to Your Group  button  (style: danger/red)
        "help":    "",   # 📋  Help & Commands    button  (style: primary/blue)
        "updates": "",   # 📢  Updates            button  (style: primary/blue)
        "support": "",   # 💬  Support            button  (style: success/green)
        "back":    "",   # 🔙  Back               button  (style: primary/blue)
    }
