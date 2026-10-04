"""Playback controller — the DVR for the ledger.

The controller owns a cursor into the ledger and a state
(PLAYING / PAUSED / ENDED). It can play forward in real time, pause, rewind,
seek to a timestamp, or jump to the live edge.

Pausing the controller does NOT stop the provider. The provider keeps
appending. The controller just stops advancing its cursor.
"""

from __future__ import annotations

import asyncio
from enum import Enum
from typing import AsyncIterator

from .errors import ControllerError
from .events import Event
from .ledger import Ledger


class PlaybackState(str, Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    ENDED = "ended"


class Controller:
    """Controls playback over a ledger."""

    def __init__(self, ledger: Ledger, speed: float = 1.0) -> None:
        if speed <= 0:
            raise ControllerError("speed must be > 0")
        self.ledger = ledger
        self.speed = speed
        self.state = PlaybackState.PAUSED
        self._cursor = -1  # last emitted sequence
        self._stop = asyncio.Event()

    @property
    def cursor(self) -> int:
        return self._cursor

    def at_live_edge(self) -> bool:
        return self._cursor >= len(self.ledger) - 1

    # --- controls ------------------------------------------------------------

    def play(self) -> None:
        self._stop.clear()
        self.state = PlaybackState.PLAYING

    def pause(self) -> None:
        self.state = PlaybackState.PAUSED

    def stop(self) -> None:
        self._stop.set()
        self.state = PlaybackState.ENDED

    def rewind(self, steps: int = 1) -> None:
        if steps < 0:
            raise ControllerError("steps must be >= 0")
        self._cursor = max(-1, self._cursor - steps)

    def forward(self, steps: int = 1) -> None:
        if steps < 0:
            raise ControllerError("steps must be >= 0")
        self._cursor = min(len(self.ledger) - 1, self._cursor + steps)

    def seek_to_time(self, t: float) -> None:
        self._cursor = self.ledger.at_or_before_time(t)

    def jump_to_live(self) -> None:
        self._cursor = len(self.ledger) - 1

    def set_speed(self, speed: float) -> None:
        if speed <= 0:
            raise ControllerError("speed must be > 0")
        self.speed = speed

    # --- playback stream -----------------------------------------------------

    async def events(self, idle_poll: float = 0.05) -> AsyncIterator[Event]:
        """Yield events one at a time, respecting state, speed, and seeking."""
        while True:
            if self._stop.is_set():
                return

            if self.state == PlaybackState.PAUSED:
                await asyncio.sleep(idle_poll)
                continue

            next_seq = self._cursor + 1

            if next_seq < len(self.ledger):
                event = self.ledger.get(next_seq)
                self._cursor = next_seq

                prev_seq = next_seq - 1
                if prev_seq >= 0:
                    prev_t = self.ledger.get(prev_seq).timestamp
                    gap = max(0.0, event.timestamp - prev_t) / self.speed
                    if gap > 0:
                        await asyncio.sleep(min(gap, 2.0))

                yield event
                continue

            await asyncio.sleep(idle_poll)
