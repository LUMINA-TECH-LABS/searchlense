"""Terminal renderer using Rich.

Prints each event as it plays, with color and icons. This is the
first renderer — fast to iterate, good enough to demo, and it proves
the whole pipeline works.

Requires the optional `rich` dependency (`pip install searchlense[console]`).
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..events import Event, EventType
from .base import BaseRenderer


_ICONS = {
    EventType.SESSION_START: "*",
    EventType.QUERY_FORMED: "?",
    EventType.SOURCE_FOUND: "S",
    EventType.SNIPPET_EXTRACTED: "-",
    EventType.IMAGE_FOUND: "I",
    EventType.VIDEO_FOUND: "V",
    EventType.NOTE: ".",
    EventType.ERROR: "!",
    EventType.RESULT_READY: "=",
    EventType.SESSION_END: "#",
}

_COLORS = {
    EventType.SESSION_START: "bold cyan",
    EventType.QUERY_FORMED: "bold cyan",
    EventType.SOURCE_FOUND: "green",
    EventType.SNIPPET_EXTRACTED: "dim green",
    EventType.IMAGE_FOUND: "magenta",
    EventType.VIDEO_FOUND: "magenta",
    EventType.NOTE: "dim",
    EventType.ERROR: "bold red",
    EventType.RESULT_READY: "bold yellow",
    EventType.SESSION_END: "bold cyan",
}


class ConsoleRenderer(BaseRenderer):
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def _format(self, event: Event) -> Text:
        icon = _ICONS.get(event.type, "?")
        color = _COLORS.get(event.type, "white")
        t = Text()
        t.append(f"{icon} ", style=color)
        t.append(f"[{event.sequence:>3}] ", style="dim")
        t.append(f"{event.type.value:<16} ", style=color)
        t.append(self._detail(event), style="white")
        return t

    def _detail(self, event: Event) -> str:
        p = event.payload
        if event.type == EventType.SESSION_START:
            return f"query={p.get('query')!r}"
        if event.type == EventType.QUERY_FORMED:
            return f"{p.get('query')!r} via {p.get('engine')}"
        if event.type == EventType.SOURCE_FOUND:
            return f"{p.get('title') or p.get('url')}  ({p.get('url')})"
        if event.type == EventType.SNIPPET_EXTRACTED:
            text = (p.get("text") or "")[:80]
            return f"{text}..."
        if event.type == EventType.IMAGE_FOUND:
            return f"{p.get('alt') or p.get('url')}"
        if event.type == EventType.VIDEO_FOUND:
            return f"{p.get('title') or p.get('url')}"
        if event.type == EventType.NOTE:
            return p.get("text", "")
        if event.type == EventType.ERROR:
            return f"{p.get('message')} ({p.get('where')})"
        if event.type == EventType.RESULT_READY:
            return p.get("summary", "")
        if event.type == EventType.SESSION_END:
            return f"reason={p.get('reason')}"
        return str(p)

    async def render(self, event: Event) -> None:
        self.console.print(self._format(event))

    async def close(self) -> None:
        self.console.print(Panel.fit("session complete", style="bold cyan"))
