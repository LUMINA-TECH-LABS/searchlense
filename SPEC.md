# searchlense protocol specification

Version: 0.1

This document defines the **cross-language contract** for searchlense. Any
language can drive searchlense by implementing a small bridge that speaks this
protocol. The Python package is the reference implementation; other languages
follow this spec.

---

## 1. Concepts

- **Provider** — the thing that actually searches. Supplied by the user. Never
  part of searchlense.
- **Event** — a single timestamped result. The universal unit.
- **Ledger** — an append-only, ordered list of events. The source of truth.
- **Controller** — a cursor over the ledger with playback state.
- **Checkpoint** — a cooperative suspension point. Agents call it inside
  their loop to honor pause requests.
- **Bridge** — a subprocess that speaks JSON (or TSV) on stdin/stdout.

---

## 2. Event schema

An event is a JSON object:

```json
{
  "type": "source_found",
  "payload": { "url": "https://example.org", "title": "...", "snippet": "...", "score": 0.93 },
  "event_id": "8f2c9b...",
  "timestamp": 1730000000.123,
  "sequence": 7
}
```

Fields:

| field       | type   | meaning                                                    |
|-------------|--------|------------------------------------------------------------|
| `type`      | string | one of the event types below                               |
| `payload`   | object | event-specific data                                        |
| `event_id`  | string | unique hex id                                              |
| `timestamp` | float  | seconds since epoch (provider's clock)                     |
| `sequence`  | int    | assigned by the ledger; `-1` until appended                |

Event types and their required payload keys:

| `type`             | payload keys                                                     |
|--------------------|------------------------------------------------------------------|
| `session_start`    | `query` (string or null)                                         |
| `query_formed`     | `query` (string), `engine` (string or null)                      |
| `source_found`     | `url`, `title`, `snippet`, `score` (float or null)               |
| `snippet_extracted`| `source_url`, `text`                                             |
| `image_found`      | `url`, `thumbnail`, `alt`, `source_url`                          |
| `video_found`      | `url`, `title`, `thumbnail`, `duration` (float or null)          |
| `note`             | `text`                                                           |
| `error`            | `message`, `where` (string or null)                              |
| `result_ready`     | `summary`, `sources` (list of strings)                           |
| `session_end`      | `reason` (string)                                                |

Unknown `type` values must be preserved by consumers but may be ignored.

---

## 3. Provider contract (Python)

A provider is any object with:

```python
async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
    ...
```

Each yielded dict is converted to an event by matching the `kind` key:

| `kind`    | maps to             |
|-----------|---------------------|
| `source`  | `source_found`      |
| `image`   | `image_found`       |
| `video`   | `video_found`       |
| `snippet` | `snippet_extracted` |
| `result`  | `result_ready`      |
| `note`    | `note`              |
| _other_   | `note`              |

Example:

```python
async def search(self, query):
    yield {"kind": "note", "text": "planning"}
    yield {"kind": "source", "url": "...", "title": "...", "snippet": "...", "score": 0.9}
```

---

## 4. Stdio bridge protocol

The bridge is launched as:

```
python -m searchlense.bridge
python -m searchlense.bridge --format=tsv
```

### 4.1 Commands (stdin)

One JSON object per line. Required key: `cmd`.

| `cmd`        | extra fields             | effect                                            |
|--------------|--------------------------|---------------------------------------------------|
| `run`        | `query`, `provider`      | start a session; `provider` defaults to `"demo"`  |
| `pause`      | —                        | pause the view and request agent checkpoint       |
| `resume`     | —                        | resume the view and let the agent continue        |
| `rewind`     | `steps` (int, default 1) | move cursor back                                  |
| `forward`    | `steps` (int, default 1) | move cursor forward                               |
| `seek_time`  | `t` (float)              | move cursor to last event at or before time `t`   |
| `jump_live`  | —                        | move cursor to the newest event                   |
| `set_speed`  | `speed` (float > 0)      | playback speed multiplier                         |
| `checkpoint` | —                        | block until not paused, then ack                  |
| `ping`       | —                        | health check                                      |
| `quit`       | —                        | terminate the bridge                              |

### 4.2 Events (stdout)

One JSON object per line, exactly the event schema in §2.

### 4.3 Acknowledgments (stdout)

For every command, the bridge replies with:

```json
{"ack": "<cmd>", "ok": true}
```

or, on failure:

```json
{"ack": "<cmd>", "ok": false, "error": "..."}
```

Errors with no associated command are emitted as:

```json
{"error": "..."}
```

The `run` ack echoes the query and provider:

```json
{"ack": "run", "ok": true, "query": "...", "provider": "demo"}
```

The `ping` ack includes the version:

```json
{"ack": "ping", "ok": true, "version": "0.1.0"}
```

### 4.4 Ordering

Acks and events may interleave. Consumers must read stdout as a single stream
and dispatch by presence of `ack`, `error`, or `type`.

### 4.5 Stderr

Reserved for logs. The bridge never writes JSON to stderr.

---

## 5. TSV mode

When launched with `--format=tsv`, events are written as:

```
<sequence>\t<type>\t<timestamp>\t<k1>=<v1>\t<k2>=<v2>...
```

- Values are URL-encoded (RFC 3986 unreserved + `%`).
- `null` payload values are omitted.
- Acks and errors are still emitted as JSON lines.
- This mode exists for languages without a JSON parser in their standard
  library (for example, plain Java without Maven dependencies).

---

## 6. Cooperative checkpoint (Mode B)

The bridge exposes a single blocking call:

```
{"cmd": "checkpoint"}
```

The bridge holds the reply until the session is not paused. Callers should
invoke this inside their agent loop. If a caller never invokes it, pause
becomes **view-only** (Mode A) and nothing breaks.

There is no way for the bridge to force a pause on an agent that does not
check in. This is a property of cooperative scheduling; it is documented
explicitly so implementers are not surprised.

---

## 7. Bootstrapping from a GitHub Release

A language that wants zero-install consumption should:

1. Query the GitHub API for the latest release of `<owner>/searchlense`.
2. Find the wheel asset (`*.whl`).
3. Create a Python virtual environment in a stable cache directory
   (recommended: `~/.searchlense/venv`).
4. `pip install <wheel-url>` into that venv.
5. Spawn `<venv>/bin/python -m searchlense.bridge`.
6. Cache the venv; do not reinstall on every launch.

Requirements at runtime:

- Python 3.10+ on `PATH` (`python` or `python3`).
- Network access on first run only.

Failure modes to handle in the caller:

- Python not found → clear error to the user.
- Network unavailable on first run → clear error to the user.
- Venv creation or pip install failed → surface pip's stderr.

---

## 8. Versioning

The bridge's protocol version is the same as the package version
(`searchlense.__version__`). Breaking changes to this spec increment the
major version (0.x → 1.0 is the first stable cut). Additive changes do not
increment.

Clients should:

- Send `{"cmd": "ping"}` on startup and read `version`.
- Refuse to proceed if the version's major component differs from what they
  were built against.

---

## 9. What this spec is not

- It is not a search API. searchlense does not search.
- It is not a hosted service. There is no server.
- It does not define ranking, filtering, or content extraction. Those live in
  the provider, which is the caller's responsibility.

searchlense is the timeline. Everything else is yours.
