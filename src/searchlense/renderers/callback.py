"""Callback renderer — call a Python function for each event.

This is the renderer phones and custom UIs use. Instead of printing to a
terminal, it hands every event to a function you provide. That function can
push into a UI list, a websocket, a database, a queue, anything.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from ..events import Event
from .base import BaseRenderer

SyncCallback = Callable[[Event], None]
AsyncCallback = Callable[[Event], Awaitable[None]]


class CallbackRenderer(BaseRenderer):
    def __init__(self, on_event: SyncCallback | AsyncCallback) -> None:
        if not callable(on_event):
            raise TypeError("on_event must be callable")
        self.on_event = on_event

    async def render(self, event: Event) -> None:
        result: Any = self.on_event(event)
        if hasattr(result, "__await__"):
            await result

    async def close(self) -> None:
        return None
