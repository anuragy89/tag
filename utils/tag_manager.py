"""
utils/tag_manager.py – Per-group tagging state machine.

States: running | paused | stopped
"""

import asyncio
import logging
from typing import Dict, Optional

log = logging.getLogger(__name__)


class TagSession:
    """Tracks one active tagging job in a group."""

    def __init__(self):
        self.status: str = "running"   # running | paused | stopped
        self._pause_event = asyncio.Event()
        self._pause_event.set()         # not paused initially
        self.task: Optional[asyncio.Task] = None

    def pause(self):
        self.status = "paused"
        self._pause_event.clear()

    def resume(self):
        self.status = "running"
        self._pause_event.set()

    def stop(self):
        self.status = "stopped"
        self._pause_event.set()         # unblock any waiting coroutine
        if self.task and not self.task.done():
            self.task.cancel()

    async def wait_if_paused(self):
        """Await this inside tagging loop to honour pause/resume."""
        await self._pause_event.wait()

    @property
    def is_running(self) -> bool:
        return self.status == "running"

    @property
    def is_stopped(self) -> bool:
        return self.status == "stopped"


class TagManager:
    """Global registry of TagSession objects keyed by chat_id."""

    def __init__(self):
        self._sessions: Dict[int, TagSession] = {}

    def start(self, chat_id: int) -> TagSession:
        """Create (or replace) a session for a chat."""
        if chat_id in self._sessions:
            self._sessions[chat_id].stop()   # cancel any old job
        s = TagSession()
        self._sessions[chat_id] = s
        return s

    def get(self, chat_id: int) -> Optional[TagSession]:
        return self._sessions.get(chat_id)

    def pause(self, chat_id: int) -> bool:
        s = self._sessions.get(chat_id)
        if s and s.is_running:
            s.pause()
            return True
        return False

    def resume(self, chat_id: int) -> bool:
        s = self._sessions.get(chat_id)
        if s and s.status == "paused":
            s.resume()
            return True
        return False

    def stop(self, chat_id: int) -> bool:
        s = self._sessions.get(chat_id)
        if s and not s.is_stopped:
            s.stop()
            self._sessions.pop(chat_id, None)
            return True
        return False

    def is_active(self, chat_id: int) -> bool:
        s = self._sessions.get(chat_id)
        return bool(s and not s.is_stopped)


# Singleton
tag_manager = TagManager()
