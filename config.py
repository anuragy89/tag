"""
config.py – All bot configuration loaded from environment variables.
"""

import os


class Config:
    # ── Core Telegram Credentials ─────────────────────────────────────────────
    API_ID    = int(os.environ.get("API_ID", 0))
    API_HASH  = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # ── Owner ─────────────────────────────────────────────────────────────────
    OWNER_ID  = int(os.environ.get("OWNER_ID", 0))

    # ── MongoDB ───────────────────────────────────────────────────────────────
    MONGO_URI     = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "tagbot")

    # ── Tagging Speed / Flood Protection ──────────────────────────────────────
    TAG_DELAY     = float(os.environ.get("TAG_DELAY",   1.5))
    BATCH_DELAY   = float(os.environ.get("BATCH_DELAY", 3.0))
    FLOOD_SLEEP   = int(os.environ.get("FLOOD_SLEEP",   60))
    USERS_PER_MSG = int(os.environ.get("USERS_PER_MSG", 6))

    # ── Bot Links ─────────────────────────────────────────────────────────────
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL", "https://t.me/yourchannel")
    SUPPORT_GROUP   = os.environ.get("SUPPORT_GROUP",   "https://t.me/yoursupport")
    BOT_USERNAME    = os.environ.get("BOT_USERNAME",    "YourTagBot")

    # ══════════════════════════════════════════════════════════════════════════
    #  PREMIUM EMOJI IDs
    #  ─────────────────
    #  Run:  heroku run python fetch_emoji_ids.py
    #  Paste the printed document IDs below.  Leave "" to use plain emoji.
    #
    #  HOW IT WORKS:
    #   • Telegram renders  <tg-emoji emoji-id="ID">fallback</tg-emoji>
    #     in HTML parse mode as an animated sticker inline in the text.
    #   • Every user sees it — Premium is only needed on the BOT OWNER account
    #     to SEND them (which your bot does on your behalf).
    #
    #  Keys are used in te() calls throughout handlers and messages.py.
    # ══════════════════════════════════════════════════════════════════════════
    PREMIUM_EMOJI = {

        # ── Inline button icons ───────────────────────────────────────────────
        "add":       "5339085583803244634",   # ➕  Add to Your Group  (red button)
        "help":      "5971885530957222021",   # 📋  Help & Commands    (blue button)
        "updates":   "6021418126061605425",   # 📢  Updates            (blue button)
        "support":   "5972302069770488984",   # 💬  Support            (green button)
        "back":      "5971831809506282660",   # 🔙  Back               (blue button)

        # ── START / HELP / GROUP JOIN messages ───────────────────────────────
        "tag":       "5888620056551625531",   # 🏷️  main bot identity emoji
        "rocket":    "5188481279963715781",   # 🚀  launch / live / go
        "star":      "6316383393185533398",   # 🌟  features / highlights
        "lightning": "6316383393185533398",   # ⚡  controls / speed
        "shield":    "5251203410396458957",   # 🛡️  spam protection
        "chart":     "5231200819986047254",   # 📊  owner tools / stats
        "wave":      "5407076281898512830",   # v  hello / welcome
        "robot":     "5397824497141170866",   # 🤖  bot identity in group join
        "fire":      "5424972470023104089",   # 🔥  hype
        "crown":     "5825744960858623833",   # 👑  owner / admin / premium
        "diamond":   "5215377245639549895",   # 💎  premium / special
        "sparkle":   "5451636889717062286",   # ✨  extra flair
        "target":    "6321322884748806084,    # 🎯  mention commands
        "pause":     "5359543311897998264,    # ⏸️  control commands
        "bulb":      "5323743114513373152",   # 💡  tips section
        "check":     "5852871561983299073",   # ✅  success / delivered
        "cross":     "5796291784539639311",   # ❌  stop / failed
        "warning":   "5818962528893407510",   # ⚠️  admin alert
        "bell":      "5413764331957398331",   # 🔔  attention / notification
        "trophy":    "5188344996356448758",   # 🏆  achievement
        "heart":     "5470080737711502911",   # 💖  warm / love
        "zap":       "5373066076558996568",   # ⚡  energy (alias fire)
        "tada":      "5193018401810822951",   # 🎉  celebration
        "stats":     "5298614648138919107",   # 📈  stats / numbers
        "broadcast": "5256134032852278918",   # 📡  broadcast
        "people":    "5891207662678317861",   # 👥  users
        "chat":      "5190547876492615432",   # 💬  groups / chat
        "done":      "5927066550791048673",   # 🏁  tagging complete
        "stop":      "5366040905927113475",   # 🛑  stopped
        "play":      "5972265777296838427",   # ▶️  resumed
        "mic":       "5294339927318739359",   # 🎙️  VC / voice
    }
