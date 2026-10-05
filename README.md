# searchlense

A DVR for agentic search.

`searchlense` does **not** search the web. It gives you a timeline, playback
controls, and a cinematic workspace for a search that is already happening —
whether that search is driven by an LLM agent, a scraper, an API, or your own
code.

You bring the provider. `searchlense` gives you:

- A normalized event stream (query, source, image, video, snippet, note, result)
- An append-only ledger — the source of truth for a session
- A playback controller: play, pause, rewind, forward, seek-by-time, jump-to-live
- A cooperative checkpoint so an agent can actually pause mid-search
- Renderers: console (Rich), callback (for phone UIs), JSON stream, stdio bridge
- A stdio bridge so any language (Java, Kotlin, Node, Go, Rust, C#, ...) can drive it

## Two integration modes

`searchlense` supports two ways to wire it into an agent. Pick one.

**Mode A — View-only pause (zero effort).**
The agent keeps searching. The user pauses only what they see. Rewind, inspect
images and sources, then jump back to the live edge. No cooperation required.

**Mode B — Cooperative checkpoint (one line).**
The agent calls `await session.checkpoint()` inside its loop. When the user
(or the agent) requests a pause, the checkpoint suspends the agent at the next
loop boundary. On resume, the agent continues from the exact same point. This
is the cinematic, interactive mode.

Both modes ship in v0.1. See `SPEC.md` and `examples/`.

## Control is symmetric

The same methods work whether the **user's UI** calls them or the **agent's
code** calls them. There is no user-only or agent-only surface:

- `session.pause()` / `session.resume()`
- `session.controller.rewind(n)` / `.forward(n)` / `.seek_to_time(t)` / `.jump_to_live()`
- `session.controller.set_speed(x)`
- `await session.checkpoint()` — used by the agent

If a user prefers to let the agent act on their behalf ("rewind two steps",
"show me the third image"), the agent can call the same methods. The library
treats both callers identically.

## Install

Python agents:

```bash
pip install https://github.com/LUMINA-TECH-LABS/searchlense/releases/download/v0.1.0/searchlense-0.1.0-py3-none-any.whl
Or from source:

```bash
pip install git+https://github.com/LUMINA-TECH-LABS/searchlense.git@v0.1.0
```

Quickstart (Python)

```python
import asyncio
from searchlense import Session, ConsoleRenderer, DemoProvider

async def main():
    provider = DemoProvider()
    renderer = ConsoleRenderer()
    session = Session(provider=provider, renderer=renderer)
    await session.run("quantum computing for beginners")

asyncio.run(main())
```

Non-Python agents (Java, Kotlin, Node, Go, Rust, C#, ...)

Any language that can spawn a subprocess can drive searchlense. The pattern
is the same everywhere:

1. On first run, silently create a Python venv and install the wheel from this
   repository's latest GitHub Release. The user sees nothing.
2. Spawn python -m searchlense.bridge from that venv.
3. Send JSON commands on stdin, read JSON events on stdout.
   A TSV mode (--format=tsv) is available for languages that don't want a
   JSON parser dependency.

This mirrors the llama.cpp distribution model: one prebuilt artifact on GitHub
Releases, consumed natively by many languages through a thin bridge.

See SPEC.md for the full protocol. See examples/ for working Java and
Kotlin bootstrap code with no external libraries.

Dependency footprint

Core is pure Python stdlib plus rich (used by the console renderer).

No search APIs. No scrapers. No network code in the library itself.
