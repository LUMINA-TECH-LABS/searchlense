"""Cooperative control signal.

The control signal is how a user (or the agent itself) asks an agent to pause
mid-search and resume later. It is deliberately cooperative: the library
cannot force an LLM to stop, but it gives the agent a single call —
`await signal.checkpoint()` — that any well-behaved agent is expected to make
inside its loop.

The same signal is exposed to the user's UI, the agent's code, and (through
the stdio bridge) any external program. There is no privileged caller.
"""

from __future__ import annotations

import asyncio


class ControlSignal:
    """A cooperative pause/resume signal.

    Semantics:
      - `request_pause()` sets the pause flag. Any caller currently inside
        `checkpoint()` will suspend. Any caller that enters `checkpoint()`
        afterwards will suspend too, until `request_resume()` is called.
      - `request_resume()` clears the flag and wakes all waiters.
      - `checkpoint()` is safe to call from any number of coroutines.
    """

    def __init__(self) -> None:
        self._pause_requested = False
        self._resume_event = asyncio.Event()
        self._resume_event.set()  # not paused by default
        self._lock = asyncio.Lock()

    def is_pause_requested(self) -> bool:
        return self._pause_requested

    async def request_pause(self) -> None:
        async with self._lock:
            self._pause_requested = True
            self._resume_event.clear()

    async def request_resume(self) -> None:
        async with self._lock:
            self._pause_requested = False
            self._resume_event.set()

    def request_pause_nowait(self) -> None:
        """Non-async variant, for callers that cannot await."""
        self._pause_requested = True
        self._resume_event.clear()

    def request_resume_nowait(self) -> None:
        self._pause_requested = False
        self._resume_event.set()

    async def checkpoint(self) -> None:
        """Suspend here if a pause has been requested.

        Agents are expected to call this inside their loop. If the agent never
        calls it, pause requests become view-only at the controller layer
        (Mode A) and the agent itself is unaffected.
        """
        if not self._pause_requested:
            return
        await self._resume_event.wait()

    async def wait_for_resume(self) -> None:
        """Block until resume is requested. Does not set the pause flag."""
        await self._resume_event.wait()
