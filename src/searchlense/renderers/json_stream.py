"""Renderer that emits JSON lines. Useful for piping to a WebSocket later.

Writes one JSON object per line to a file-like object (default: stdout).
"""

from __future__ import annotations

import json
import sys
from typing import IO

from ..events import Event
from .base import BaseRenderer


class JsonStreamRenderer(BaseRenderer):
    def __init__(self, stream: IO[str] | None = None) -> None:
        self.stream = stream or sys.stdout

    async def render(self, event: Event) -> None:
        self.stream.write(json.dumps(event.to_dict()) + "\n")
        self.stream.flush()

    async def close(self) -> None:
        return None
