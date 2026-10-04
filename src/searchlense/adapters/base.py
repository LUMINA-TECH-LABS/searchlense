"""Base class for provider adapters. Optional but convenient."""

from __future__ import annotations

from typing import Any, AsyncIterator

from ..interfaces import SearchProvider


class BaseProvider(SearchProvider):
    """Subclass this to get a clean place to implement `search`."""

    name: str = "base"

    async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
        raise NotImplementedError
        yield {}  # pragma: no cover - keeps this an async generator
