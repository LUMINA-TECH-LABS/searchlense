"""Normalized event schema.

Every result a provider yields is wrapped into one of these events before it
enters the ledger. This is the single vocabulary the whole framework speaks.
The same shape is used on the wire in the stdio bridge.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class EventType(str, Enum):
    SESSION_START = "session_start"
    QUERY_FORMED = "query_formed"
    SOURCE_FOUND = "source_found"
    SNIPPET_EXTRACTED = "snippet_extracted"
    IMAGE_FOUND = "image_found"
    VIDEO_FOUND = "video_found"
    NOTE = "note"
    ERROR = "error"
    RESULT_READY = "result_ready"
    SESSION_END = "session_end"


@dataclass
class Event:
    """A single timestamped moment in a search session."""

    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)
    sequence: int = -1  # assigned by the ledger on append

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Event":
        data = dict(d)
        data["type"] = EventType(data["type"])
        return cls(**data)

    def __repr__(self) -> str:
        return f"<Event #{self.sequence} {self.type.value} t={self.timestamp:.3f}>"


# --- Convenience constructors -------------------------------------------------


def session_start(query: str | None = None) -> Event:
    return Event(type=EventType.SESSION_START, payload={"query": query})


def query_formed(query: str, engine: str | None = None) -> Event:
    return Event(type=EventType.QUERY_FORMED, payload={"query": query, "engine": engine})


def source_found(
    url: str,
    title: str = "",
    snippet: str = "",
    score: float | None = None,
) -> Event:
    return Event(
        type=EventType.SOURCE_FOUND,
        payload={"url": url, "title": title, "snippet": snippet, "score": score},
    )


def snippet_extracted(source_url: str, text: str) -> Event:
    return Event(
        type=EventType.SNIPPET_EXTRACTED,
        payload={"source_url": source_url, "text": text},
    )


def image_found(
    url: str,
    thumbnail: str = "",
    alt: str = "",
    source_url: str = "",
) -> Event:
    return Event(
        type=EventType.IMAGE_FOUND,
        payload={"url": url, "thumbnail": thumbnail, "alt": alt, "source_url": source_url},
    )


def video_found(
    url: str,
    title: str = "",
    thumbnail: str = "",
    duration: float | None = None,
) -> Event:
    return Event(
        type=EventType.VIDEO_FOUND,
        payload={"url": url, "title": title, "thumbnail": thumbnail, "duration": duration},
    )


def note(text: str) -> Event:
    return Event(type=EventType.NOTE, payload={"text": text})


def error(message: str, where: str | None = None) -> Event:
    return Event(type=EventType.ERROR, payload={"message": message, "where": where})


def result_ready(summary: str, sources: list[str] | None = None) -> Event:
    return Event(
        type=EventType.RESULT_READY,
        payload={"summary": summary, "sources": sources or []},
    )


def session_end(reason: str = "complete") -> Event:
    return Event(type=EventType.SESSION_END, payload={"reason": reason})
