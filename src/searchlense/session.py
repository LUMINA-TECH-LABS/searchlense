"""Session — top-level orchestrator.

A Session ties a provider, ledger, controller, control signal, and renderer
together. You create one, call `run(query)`, and it:

    1. Starts the provider in the background (writes to ledger).
    2. Starts the controller (reads from ledger, feeds the renderer).
    3. Returns when the provider is done and the controller has drained.

The Session is also the surface an agent talks to for cooperative control.
`await session.checkpoint()` is the one line an agent places inside its loop
to honor pause requests (Mode B). Without that call, pause is view-only
(Mode A) and nothing breaks.
"""

from __future__ import annotations

import asyncio
from typing import Any

from .control import ControlSignal
from .controller import Controller, PlaybackState
from .errors import SessionError
from .events import (
    Event,
    EventType,
    error as ev_error,
    image_found,
    note,
    query_formed,
    result_ready,
    session_end,
    session_start,
    snippet_extracted,
    source_found,
    video_found,
)
from .interfaces import Renderer, SearchProvider
from .ledger import Ledger


def _dict_to_event(d: dict[str, Any]) -> Event:
    kind = d.get("kind", "note")
    if kind == "source":
        return source_found(
            url=d.get("url", ""),
            title=d.get("title", ""),
            snippet=d.get("snippet", ""),
            score=d.get("score"),
        )
    if kind == "image":
        return image_found(
            url=d.get("url", ""),
            thumbnail=d.get("thumbnail", ""),
            alt=d.get("alt", ""),
            source_url=d.get("source_url", ""),
        )
    if kind == "video":
        return video_found(
            url=d.get("url", ""),
            title=d.get("title", ""),
            thumbnail=d.get("thumbnail", ""),
            duration=d.get("duration"),
        )
    if kind == "snippet":
        return snippet_extracted(
            source_url=d.get("source_url", ""), text=d.get("text", "")
        )
    if kind == "result":
        return result_ready(
            summary=d.get("summary", ""), sources=d.get("sources", [])
        )
    if kind == "note":
        return note(d.get("text", ""))
    return note(f"unrecognized provider result: {d!r}")


class Session:
    """Orchestrates provider -> ledger -> controller -> renderer."""

    def __init__(
        self,
        provider: SearchProvider,
        renderer: Renderer,
        *,
        speed: float = 1.0,
    ) -> None:
        if provider is None:
            raise SessionError("provider is required")
        if renderer is None:
            raise SessionError("renderer is required")
        self.provider = provider
        self.renderer = renderer
        self.ledger = Ledger()
        self.controller = Controller(self.ledger, speed=speed)
        self.control = ControlSignal()

    # --- cooperative control surface (symmetric: user or agent may call) ----

    async def pause(self) -> None:
        """Pause the view and request that the agent suspend at its next checkpoint."""
        self.controller.pause()
        await self.control.request_pause()

    async def resume(self) -> None:
        """Resume the view and let the agent continue past its checkpoint."""
        await self.control.request_resume()
        self.controller.play()

    def pause_nowait(self) -> None:
        self.controller.pause()
        self.control.request_pause_nowait()

    def resume_nowait(self) -> None:
        self.control.request_resume_nowait()
        self.controller.play()

    async def checkpoint(self) -> None:
        """Agent-side call. Place inside your loop.

        If no pause is requested, returns immediately. If one is, suspends
        until resume is requested.
        """
        await self.control.checkpoint()

    def is_pause_requested(self) -> bool:
        return self.control.is_pause_requested()

    # --- internal runners ----------------------------------------------------

    async def _run_provider(self, query: str) -> None:
        self.ledger.append(session_start(query))
        self.ledger.append(
            query_formed(query, engine=type(self.provider).__name__)
        )
        try:
            async for raw in self.provider.search(query):
                try:
                    event = _dict_to_event(raw)
                except Exception as exc:  # noqa: BLE001
                    event = ev_error(f"failed to convert provider result: {exc}")
                self.ledger.append(event)
        except Exception as exc:  # noqa: BLE001
            self.ledger.append(ev_error(str(exc), where="provider"))
        finally:
            self.ledger.append(session_end("provider_done"))

    async def _run_renderer(self) -> None:
        async for event in self.controller.events():
            await self.renderer.render(event)
            if (
                event.type == EventType.SESSION_END
                and self.controller.at_live_edge()
            ):
                self.controller.stop()
                return

    async def run(self, query: str) -> Ledger:
        """Run a full session end-to-end. Returns the ledger."""
        self.controller.jump_to_live()
        self.controller.play()

        provider_task = asyncio.create_task(self._run_provider(query))
        renderer_task = asyncio.create_task(self._run_renderer())

        await provider_task
        await renderer_task

        await self.renderer.close()
        return self.ledger
