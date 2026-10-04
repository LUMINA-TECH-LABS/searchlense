"""Public interfaces that providers and renderers implement.

A SearchProvider produces raw results for a query. searchlense wraps them into
events. A Renderer consumes events and displays them.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class SearchProvider(Protocol):
    """Anything that can produce search results can be a provider.

    Implement `search` as an async generator yielding raw dicts. searchlense
    converts each dict into a normalized Event. Recognized keys:

        {"kind": "source", "url": ..., "title": ..., "snippet": ..., "score": ...}
        {"kind": "image",  "url": ..., "thumbnail": ..., "alt": ..., "source_url": ...}
        {"kind": "video",  "url": ..., "title": ..., "thumbnail": ..., "duration": ...}
        {"kind": "snippet","source_url": ..., "text": ...}
        {"kind": "note",   "text": ...}
        {"kind": "result", "summary": ..., "sources": [...]}

    Unknown kinds become NOTE events.
    """

    async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
        ...


@runtime_checkable
class Renderer(Protocol):
    """Consumes events and renders them."""

    async def render(self, event: Any) -> None:
        ...

    async def close(self) -> None:
        ...
