"""searchlense — a DVR for agentic search."""

from ._version import __version__
from .control import ControlSignal
from .controller import Controller, PlaybackState
from .events import (
    Event,
    EventType,
    error,
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
from .session import Session

from .adapters import BaseProvider, DemoProvider
from .renderers import (
    BaseRenderer,
    CallbackRenderer,
    ConsoleRenderer,
    JsonStreamRenderer,
)

__all__ = [
    "__version__",
    "Session",
    "Ledger",
    "Controller",
    "PlaybackState",
    "ControlSignal",
    "Event",
    "EventType",
    "SearchProvider",
    "Renderer",
    "BaseProvider",
    "DemoProvider",
    "BaseRenderer",
    "CallbackRenderer",
    "ConsoleRenderer",
    "JsonStreamRenderer",
    "session_start",
    "query_formed",
    "source_found",
    "snippet_extracted",
    "image_found",
    "video_found",
    "note",
    "error",
    "result_ready",
    "session_end",
]
