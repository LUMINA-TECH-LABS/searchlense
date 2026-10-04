"""Base class for renderers. Optional, convenient."""

from __future__ import annotations

from typing import Any

from ..interfaces import Renderer


class BaseRenderer(Renderer):
    async def render(self, event: Any) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        return None
