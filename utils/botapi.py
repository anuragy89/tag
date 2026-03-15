"""
utils/botapi.py – Bot API HTTP wrapper + premium emoji helpers.

WHY:
  Kurigram (MTProto) doesn't expose Bot API 9.4 features:
    • InlineKeyboardButton.style  (danger=red, primary=blue, success=green)
    • InlineKeyboardButton.icon_custom_emoji_id
    • <tg-emoji emoji-id="...">  in HTML messages (premium animated emoji)

  We call api.telegram.org directly via aiohttp for all structured messages.

PREMIUM EMOJI IN TEXT:
  HTML parse mode supports:  <tg-emoji emoji-id="DOCUMENT_ID">🔥</tg-emoji>
  Use the te() helper:       te("fire", "🔥")
  → returns full tg-emoji tag if ID is set in config, plain emoji otherwise.
  → every user sees the animated emoji; Premium only needed on the sender.
"""

import html
import logging
from typing import List, Optional

import aiohttp

from config import Config

log = logging.getLogger(__name__)

_BASE = f"https://api.telegram.org/bot{Config.BOT_TOKEN}"


# ══════════════════════════════════════════════════════════════════════════════
#  Premium emoji helper
# ══════════════════════════════════════════════════════════════════════════════

def te(key: str, fallback: str) -> str:
    """
    Return an animated premium emoji tag for use in HTML messages.

    If Config.PREMIUM_EMOJI[key] has a document ID:
        returns  <tg-emoji emoji-id="ID">fallback</tg-emoji>
    Otherwise:
        returns  fallback  (plain emoji, no crash)

    Usage in message strings:
        f"{te('fire', '🔥')} Bot is LIVE!"
        f"{te('crown', '👑')} Owner Commands"
    """
    doc_id = Config.PREMIUM_EMOJI.get(key, "")
    if doc_id:
        return f'<tg-emoji emoji-id="{doc_id}">{fallback}</tg-emoji>'
    return fallback


def h(text: str) -> str:
    """Escape a plain string for safe insertion into HTML message text."""
    return html.escape(str(text))


def b(text: str) -> str:
    """Bold in HTML."""
    return f"<b>{text}</b>"


def i(text: str) -> str:
    """Italic in HTML."""
    return f"<i>{text}</i>"


def code(text: str) -> str:
    """Inline code in HTML."""
    return f"<code>{html.escape(str(text))}</code>"


# ══════════════════════════════════════════════════════════════════════════════
#  Button builder
# ══════════════════════════════════════════════════════════════════════════════

def _btn(text: str, emoji_key: str = "", **kwargs) -> dict:
    """
    Build one InlineKeyboardButton dict.
    • Adds icon_custom_emoji_id when a non-empty ID is configured.
    • When icon IS set: strips the leading emoji from button text so it
      doesn't appear twice (Telegram renders icon + text side by side).
    • When icon NOT set: keeps emoji in text as visual fallback.
    """
    button = {"text": text, **kwargs}
    if emoji_key:
        doc_id = Config.PREMIUM_EMOJI.get(emoji_key, "")
        if doc_id:
            button["icon_custom_emoji_id"] = doc_id
            # Drop leading non-ASCII chars (emoji) until first real letter/digit
            i = 0
            for i, ch in enumerate(text):
                if ch.isascii() and (ch.isalpha() or ch.isdigit()):
                    break
            button["text"] = text[i:].strip()
    return button


# ══════════════════════════════════════════════════════════════════════════════
#  HTTP helpers
# ══════════════════════════════════════════════════════════════════════════════

async def _call(method: str, payload: dict) -> Optional[dict]:
    url = f"{_BASE}/{method}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    log.warning("Bot API %s error: %s", method, data.get("description"))
                    return None
                return data.get("result")
    except aiohttp.ClientError as e:
        log.error("aiohttp ClientError %s: %s", method, e)
        return None
    except Exception as e:
        log.error("Unexpected error %s: %s", method, e)
        return None


def _markup(keyboard: List[List[dict]]) -> dict:
    return {"inline_keyboard": keyboard}


# ── Send / edit with styled keyboard (HTML parse mode) ───────────────────────

async def send_styled(
    chat_id: int,
    text: str,
    keyboard: List[List[dict]],
    parse_mode: str = "HTML",
    disable_web_page_preview: bool = True,
) -> Optional[dict]:
    """Send a message with colored + emoji-icon inline buttons."""
    return await _call("sendMessage", {
        "chat_id":                  chat_id,
        "text":                     text,
        "parse_mode":               parse_mode,
        "reply_markup":             _markup(keyboard),
        "disable_web_page_preview": disable_web_page_preview,
    })


async def edit_styled(
    chat_id: int,
    message_id: int,
    text: str,
    keyboard: List[List[dict]],
    parse_mode: str = "HTML",
) -> Optional[dict]:
    """Edit a message text + keyboard (HTML + colored buttons)."""
    return await _call("editMessageText", {
        "chat_id":      chat_id,
        "message_id":   message_id,
        "text":         text,
        "parse_mode":   parse_mode,
        "reply_markup": _markup(keyboard),
    })


async def send_html(
    chat_id: int,
    text: str,
    disable_web_page_preview: bool = True,
) -> Optional[dict]:
    """
    Send a plain HTML message (no keyboard) with premium emoji support.
    Use this everywhere instead of client.send_message() so tg-emoji renders.
    Falls back gracefully if the HTTP call fails (caller should handle None).
    """
    return await _call("sendMessage", {
        "chat_id":                  chat_id,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": disable_web_page_preview,
    })


async def reply_html(
    chat_id: int,
    reply_to_message_id: int,
    text: str,
    disable_web_page_preview: bool = True,
) -> Optional[dict]:
    """Reply to a specific message with HTML text + premium emoji."""
    return await _call("sendMessage", {
        "chat_id":                  chat_id,
        "reply_to_message_id":      reply_to_message_id,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": disable_web_page_preview,
    })
