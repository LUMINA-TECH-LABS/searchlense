"""A fake provider for testing searchlense without touching the internet.

It emits a realistic sequence of events with small delays so you can watch
the playback, pause, and rewind behavior.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

from .base import BaseProvider


class DemoProvider(BaseProvider):
    """Emits a scripted sequence of results with delays."""

    name = "demo"

    def __init__(self, delay: float = 0.35) -> None:
        self.delay = delay

    async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
        await asyncio.sleep(self.delay)
        yield {"kind": "note", "text": f"planning search for: {query!r}"}

        await asyncio.sleep(self.delay)
        yield {
            "kind": "source",
            "url": "https://example.org/a",
            "title": f"Overview of {query}",
            "snippet": f"A high-level introduction to {query}.",
            "score": 0.93,
        }

        await asyncio.sleep(self.delay)
        yield {
            "kind": "source",
            "url": "https://example.org/b",
            "title": f"Deep dive: {query}",
            "snippet": f"Technical details and examples about {query}.",
            "score": 0.88,
        }

        await asyncio.sleep(self.delay)
        yield {
            "kind": "image",
            "url": "https://example.org/img/1.png",
            "thumbnail": "https://example.org/img/1_thumb.png",
            "alt": f"Diagram of {query}",
            "source_url": "https://example.org/a",
        }

        await asyncio.sleep(self.delay)
        yield {
            "kind": "video",
            "url": "https://example.org/video/1",
            "title": f"Explained: {query}",
            "thumbnail": "https://example.org/video/1_thumb.png",
            "duration": 412.0,
        }

        await asyncio.sleep(self.delay)
        yield {
            "kind": "snippet",
            "source_url": "https://example.org/a",
            "text": f"Key sentence about {query} extracted from the page.",
        }

        await asyncio.sleep(self.delay)
        yield {
            "kind": "result",
            "summary": f"Here is what I found about {query}.",
            "sources": ["https://example.org/a", "https://example.org/b"],
        }
