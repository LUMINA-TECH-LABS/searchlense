"""Stdio bridge — drive searchlense from any language.

Any program that can spawn a subprocess can use searchlense through this
bridge. The protocol is one JSON object per line on stdin (commands) and one
JSON object per line on stdout (events). A TSV mode is available for callers
that do not want a JSON parser dependency.

Commands (one JSON object per line on stdin):

    {"cmd": "run", "query": "...", "provider": "demo"}
    {"cmd": "pause"}
    {"cmd": "resume"}
    {"cmd": "rewind", "steps": 2}
    {"cmd": "forward", "steps": 1}
    {"cmd": "seek_time", "t": 1234567890.0}
    {"cmd": "jump_live"}
    {"cmd": "set_speed", "speed": 2.0}
    {"cmd": "checkpoint"}        # blocks until not paused, then replies
    {"cmd": "ping"}
    {"cmd": "quit"}

Events (one JSON object per line on stdout) are exactly the Event.to_dict()
shape from searchlense.events.

TSV mode (`--format=tsv`) emits each event as:

    sequence \t type \t timestamp \t key1=val1 \t key2=val2 ...

Values are URL-encoded so tabs and newlines are safe.

Usage:

    python -m searchlense.bridge
    python -m searchlense.bridge --format=tsv
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.parse
from typing import Any, TextIO

from ._version import __version__
from .adapters.demo import DemoProvider
from .errors import BridgeError
from .events import Event
from .renderers.base import BaseRenderer
from .session import Session


class _BridgeRenderer(BaseRenderer):
    """Writes each event to an output stream in JSON or TSV format."""

    def __init__(self, out: TextIO, fmt: str = "json") -> None:
        self.out = out
        self.fmt = fmt

    def _emit_json(self, event: Event) -> None:
        self.out.write(json.dumps(event.to_dict()) + "\n")
        self.out.flush()

    def _emit_tsv(self, event: Event) -> None:
        parts = [str(event.sequence), event.type.value, f"{event.timestamp:.6f}"]
        for k, v in event.payload.items():
            if v is None:
                continue
            val = urllib.parse.quote(str(v), safe="")
            parts.append(f"{k}={val}")
        self.out.write("\t".join(parts) + "\n")
        self.out.flush()

    async def render(self, event: Event) -> None:
        if self.fmt == "tsv":
            self._emit_tsv(event)
        else:
            self._emit_json(event)

    async def close(self) -> None:
        return None


def _make_provider(name: str):
    if name == "demo":
        return DemoProvider()
    raise BridgeError(f"unknown provider: {name!r} (only 'demo' ships with v0.1)")


async def _run_bridge(fmt: str) -> int:
    stdin = sys.stdin
    stdout = sys.stdout

    loop = asyncio.get_running_loop()

    # Session is created lazily when a "run" command arrives.
    state: dict[str, Any] = {"session": None, "task": None}

    async def read_command() -> dict[str, Any] | None:
        line = await loop.run_in_executor(None, stdin.readline)
        if not line:
            return None
        line = line.strip()
        if not line:
            return {"cmd": "noop"}
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BridgeError(f"invalid JSON command: {exc}") from exc
        if not isinstance(obj, dict) or "cmd" not in obj:
            raise BridgeError(f"command must be an object with a 'cmd' field: {obj!r}")
        return obj

    def write_ack(cmd: str, ok: bool = True, **extra: Any) -> None:
        msg = {"ack": cmd, "ok": ok}
        msg.update(extra)
        stdout.write(json.dumps(msg) + "\n")
        stdout.flush()

    while True:
        try:
            command = await read_command()
        except BridgeError as exc:
            stdout.write(json.dumps({"error": str(exc)}) + "\n")
            stdout.flush()
            continue

        if command is None:
            break

        cmd = command.get("cmd")

        if cmd == "noop":
            continue

        if cmd == "ping":
            write_ack("ping", version=__version__)
            continue

        if cmd == "quit":
            write_ack("quit")
            break

        if cmd == "run":
            if state["session"] is not None:
                write_ack("run", ok=False, error="a session is already running")
                continue
            query = command.get("query", "")
            provider_name = command.get("provider", "demo")
            try:
                provider = _make_provider(provider_name)
            except BridgeError as exc:
                write_ack("run", ok=False, error=str(exc))
                continue
            renderer = _BridgeRenderer(stdout, fmt=fmt)
            session = Session(provider=provider, renderer=renderer)
            state["session"] = session
            state["task"] = asyncio.create_task(session.run(query))
            write_ack("run", query=query, provider=provider_name)
            continue

        # All remaining commands require a session.
        session: Session | None = state["session"]
        if session is None:
            write_ack(cmd, ok=False, error="no session running")
            continue

        if cmd == "pause":
            session.pause_nowait()
            write_ack("pause")
            continue

        if cmd == "resume":
            session.resume_nowait()
            write_ack("resume")
            continue

        if cmd == "rewind":
            session.controller.rewind(int(command.get("steps", 1)))
            write_ack("rewind")
            continue

        if cmd == "forward":
            session.controller.forward(int(command.get("steps", 1)))
            write_ack("forward")
            continue

        if cmd == "seek_time":
            session.controller.seek_to_time(float(command["t"]))
            write_ack("seek_time")
            continue

        if cmd == "jump_live":
            session.controller.jump_to_live()
            write_ack("jump_live")
            continue

        if cmd == "set_speed":
            session.controller.set_speed(float(command["speed"]))
            write_ack("set_speed")
            continue

        if cmd == "checkpoint":
            # Blocks until the session is not paused, then acknowledges.
            await session.checkpoint()
            write_ack("checkpoint")
            continue

        write_ack(cmd, ok=False, error=f"unknown command: {cmd!r}")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="searchlense.bridge")
    parser.add_argument(
        "--format",
        choices=["json", "tsv"],
        default="json",
        help="output format for events (default: json)",
    )
    args = parser.parse_args(argv)
    try:
        return asyncio.run(_run_bridge(fmt=args.format))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
