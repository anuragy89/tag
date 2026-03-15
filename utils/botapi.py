"""
utils/botapi.py – Thin async wrapper around the Telegram Bot API HTTP endpoint.

WHY THIS EXISTS:
  Kurigram (our MTProto library) lags behind the HTTP Bot API.
  Bot API 9.4 added two fields to InlineKeyboardButton that Kurigram's
  high-level types don't expose yet:

    • style              → "danger" (red) | "primary" (blue) | "success" (green)
    • icon_custom_emoji_id → custom emoji shown before button text
                           (requires bot owner to have Telegram Premium)

  This module calls api.telegram.org directly using aiohttp so we can use
  these new fields without waiting for Kurigram to update.

USAGE:
  from utils.botapi import send_styled, edit_styled

  await send_styled(
      token  = Config.BOT_TOKEN,
      chat_id= chat.id,
      text   = "Hello!",
      keyboard=[
          [{"text": "🔴 Add to Group", "url": "...",           "style": "danger"}],
          [{"text": "Help",            "callback_data": "...", "style": "primary"},
           {"text": "Updates",         "url": "...",           "style": "primary"}],
          [{"text": "Support",         "url": "...",           "style": "success"}],
      ],
  )
"""

import logging
from typing import Any, List, Optional

import aiohttp

from config import Config

log = logging.getLogger(__name__)

_BASE = f"https://api.telegram.org/bot{Config.BOT_TOKEN}"


def _btn(text: str, emoji_key: str = "", **kwargs) -> dict:
    """
    Build one InlineKeyboardButton dict.
    Automatically adds icon_custom_emoji_id when a non-empty ID is configured
    in Config.PREMIUM_EMOJI for the given emoji_key.

    Usage:
        _btn("➕ Add to Group", "add", url="...", style="danger")
        _btn("📋 Help",        "help", callback_data="cb_help", style="primary")
    """
    button = {"text": text, **kwargs}
    if emoji_key:
        doc_id = Config.PREMIUM_EMOJI.get(emoji_key, "")
        if doc_id:
            button["icon_custom_emoji_id"] = doc_id
    return button


async def _call(method: str, payload: dict) -> Optional[dict]:
    """POST one Bot API method and return the result dict, or None on error."""
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
        log.error("aiohttp error calling %s: %s", method, e)
        return None
    except Exception as e:
        log.error("Unexpected error calling %s: %s", method, e)
        return None


def _build_markup(keyboard: List[List[dict]]) -> dict:
    """Wrap a list-of-rows into a Bot API reply_markup dict."""
    return {"inline_keyboard": keyboard}


async def send_styled(
    chat_id: int,
    text: str,
    keyboard: List[List[dict]],
    parse_mode: str = "Markdown",
    disable_web_page_preview: bool = True,
) -> Optional[dict]:
    """
    Send a message with colored/icon inline buttons via Bot API HTTP.

    Each button dict supports all standard Bot API InlineKeyboardButton fields
    plus the Bot API 9.4 additions:
      - style: "danger" | "primary" | "success"
      - icon_custom_emoji_id: str  (requires bot owner Telegram Premium)
    """
    return await _call("sendMessage", {
        "chat_id":                  chat_id,
        "text":                     text,
        "parse_mode":               parse_mode,
        "reply_markup":             _build_markup(keyboard),
        "disable_web_page_preview": disable_web_page_preview,
    })


async def edit_styled(
    chat_id: int,
    message_id: int,
    text: str,
    keyboard: List[List[dict]],
    parse_mode: str = "Markdown",
) -> Optional[dict]:
    """Edit a message's text + styled keyboard via Bot API HTTP."""
    return await _call("editMessageText", {
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       text,
        "parse_mode": parse_mode,
        "reply_markup": _build_markup(keyboard),
    })
