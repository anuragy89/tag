import logging
import asyncio
from pyrogram.errors import FloodWait

logger = logging.getLogger()

async def safe_execute(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)

    except FloodWait as e:
        logger.warning(f"FloodWait triggered → sleeping {e.value}s")
        await asyncio.sleep(e.value)

    except Exception:
        logger.error("Unhandled exception occurred", exc_info=True)
