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

## What it looks like

`searchlense` doesn't search. It turns a search — yours, or your agent's —
into a timeline you can play, pause, rewind, and inspect. Here is a real
search against Wikipedia's public API, streamed through searchlense:

```
* [  0] session_start    query='quantum computing for beginners'
? [  1] query_formed     'quantum computing for beginners' via WikipediaProvider
. [  2] note             searching Wikipedia (en) for: 'quantum computing for beginners'
S [  3] source_found     IBM Quantum Platform  (https://en.wikipedia.org/wiki/IBM_Quantum_Platform)
S [  4] source_found     Quantum error correction  (https://en.wikipedia.org/wiki/Quantum_error_correction)
S [  5] source_found     Shor code  (https://en.wikipedia.org/wiki/Shor_code)
I [  6] image_found      Shor code
S [  7] source_found     Five-qubit error correcting code  (https://en.wikipedia.org/wiki/Five-qubit_error_correcting_code)
S [  8] source_found     Loop quantum gravity  (https://en.wikipedia.org/wiki/Loop_quantum_gravity)
I [  9] image_found      Loop quantum gravity
S [ 10] source_found     Microsoft Azure  (https://en.wikipedia.org/wiki/Microsoft_Azure)
I [ 11] image_found      Microsoft Azure
S [ 12] source_found     Suhail Zubairy  (https://en.wikipedia.org/wiki/Suhail_Zubairy)
S [ 13] source_found     Chuck Easttom  (https://en.wikipedia.org/wiki/Chuck_Easttom)
= [ 14] result_ready     Found 8 Wikipedia articles for 'quantum computing for beginners'.
# [ 15] session_end      reason=provider_done
```

Every source, image, and result is a single event on the timeline. The user
can pause mid-stream, rewind to look at any image, inspect a source, then
resume from the live edge:

```
* [  0] session_start    query='history of the printing press'
? [  1] query_formed     'history of the printing press' via DemoProvider
. [  2] note             planning search for: 'history of the printing press'

--- USER: PAUSE ---

S [  3] source_found     Overview of history of the printing press

--- USER: REWIND 3 ---

--- USER: RESUME ---

? [  1] query_formed     'history of the printing press' via DemoProvider
. [  2] note             planning search for: 'history of the printing press'
S [  3] source_found     Overview of history of the printing press
S [  4] source_found     Deep dive: history of the printing press
I [  5] image_found      Diagram of history of the printing press
V [  6] video_found      Explained: history of the printing press
- [  7] snippet_extracted Key sentence about history of the printing press...
= [  8] result_ready     Here is what I found about history of the printing press.
# [  9] session_end      reason=provider_done
```

The pause froze the view at event #3. The rewind moved the cursor back to
event #1. The resume played forward from there. The agent never stopped —
only the *view* did. That is the DVR.

A complete reference provider — real search, real data, no API key, no
scraping — is in `examples/09_real_provider.py`.

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
```

Or from source:

```bash
pip install git+https://github.com/LUMINA-TECH-LABS/searchlense.git@v0.1.0
```

## Quickstart (Python)

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

## Pause, rewind, resume

```python
import asyncio
from searchlense import Session, ConsoleRenderer, DemoProvider

async def main():
    session = Session(
        provider=DemoProvider(delay=0.4),
        renderer=ConsoleRenderer(),
    )

    async def director():
        await asyncio.sleep(1.2)
        print("\n--- USER: PAUSE ---\n")
        session.pause_nowait()

        await asyncio.sleep(1.5)
        print("\n--- USER: REWIND 3 ---\n")
        session.controller.rewind(3)

        print("\n--- USER: RESUME ---\n")
        session.resume_nowait()

    await asyncio.gather(
        session.run("history of the printing press"),
        director(),
    )

asyncio.run(main())
```

## Real search example

`examples/09_real_provider.py` wraps Wikipedia's public API and streams real
search results through searchlense. Zero dependencies beyond the standard
library, no API key, no scraping. Use it as a template for your own provider.

```python
from searchlense import Session, ConsoleRenderer
from examples.real_provider import WikipediaProvider  # illustrative import

session = Session(
    provider=WikipediaProvider(limit=8),
    renderer=ConsoleRenderer(),
)
await session.run("quantum computing for beginners")
```

## Non-Python agents (Java, Kotlin, Node, Go, Rust, C#, ...)

Any language that can spawn a subprocess can drive `searchlense`. The pattern
is the same everywhere:

1. On first run, silently create a Python venv and install the wheel from this
   repository's latest GitHub Release. The user sees nothing.
2. Spawn `python -m searchlense.bridge` from that venv.
3. Send JSON commands on stdin, read JSON events on stdout.
   A TSV mode (`--format=tsv`) is available for languages that don't want a
   JSON parser dependency.

This mirrors the llama.cpp distribution model: one prebuilt artifact on GitHub
Releases, consumed natively by many languages through a thin bridge.

See `SPEC.md` for the full protocol. See `examples/` for working Java and
Kotlin bootstrap code with no external libraries.

## Dependency footprint

Core is pure Python stdlib plus `rich` (used by the console renderer).

No search APIs. No scrapers. No network code in the library itself. Search
sources are always supplied by you, in your code, as a provider.

## Status

v0.1.0 — early. Ships with a demo provider and a Wikipedia reference provider.
The bridge, ledger, controller, and all three Python renderers are functional.

Roadmap:
- v0.2: more reference providers (DuckDuckGo via a proxy, Brave Search API, LangChain adapter)
- v0.3: JS/Go/Rust ports following `SPEC.md`
- v0.4: Web UI renderer

## License

MIT. Contributions are welcome under the same terms.
