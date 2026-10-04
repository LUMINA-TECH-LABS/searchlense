"""Append-only event ledger.

The ledger is the source of truth for a session. Events are appended, never
mutated. The playback controller reads from the ledger; the provider writes to
it. This separation is what makes pause/rewind possible: the search keeps
producing while the view is paused.
"""

from __future__ import annotations

import threading
from typing import Iterable, Iterator

from .errors import LedgerError
from .events import Event, note as note_event


class Ledger:
    """Thread-safe, append-only list of events with sequence numbers."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._lock = threading.RLock()

    def append(self, event: Event) -> Event:
        with self._lock:
            event.sequence = len(self._events)
            self._events.append(event)
        return event

    def append_raw(self, text: str) -> Event:
        """Convenience: append a plain string as a `note` event.

        Useful for agents that want to record their own progress on the
        timeline without constructing an Event explicitly.
        """
        return self.append(note_event(text))

    def extend(self, events: Iterable[Event]) -> None:
        for e in events:
            self.append(e)

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        with self._lock:
            snapshot = list(self._events)
        return iter(snapshot)

    def get(self, sequence: int) -> Event:
        with self._lock:
            n = len(self._events)
            if sequence < 0 or sequence >= n:
                raise LedgerError(f"sequence {sequence} out of range (0..{n - 1})")
            return self._events[sequence]

    def slice(self, start: int = 0, end: int | None = None) -> list[Event]:
        with self._lock:
            return list(self._events[start:end])

    def latest(self) -> Event | None:
        with self._lock:
            return self._events[-1] if self._events else None

    def at_or_before_time(self, t: float) -> int:
        """Return the sequence index of the last event at or before time t.

        Returns -1 if no such event exists.
        """
        with self._lock:
            idx = -1
            for i, e in enumerate(self._events):
                if e.timestamp <= t:
                    idx = i
                else:
                    break
        return idx

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
