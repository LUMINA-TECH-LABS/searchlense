import asyncio

import pytest

from searchlense.adapters.demo import DemoProvider
from searchlense.events import EventType
from searchlense.renderers.callback import CallbackRenderer
from searchlense.session import Session


@pytest.mark.asyncio
async def test_session_runs_and_collects_events():
    events = []

    def on_event(e):
        events.append(e)

    session = Session(
        provider=DemoProvider(delay=0.01),
        renderer=CallbackRenderer(on_event),
    )
    ledger = await session.run("test query")

    assert len(ledger) > 0
    types = [e.type for e in events]
    assert EventType.SESSION_START in types
    assert EventType.QUERY_FORMED in types
    assert EventType.SOURCE_FOUND in types
    assert EventType.RESULT_READY in types
    assert EventType.SESSION_END in types


@pytest.mark.asyncio
async def test_session_pause_resume_flags():
    events = []
    session = Session(
        provider=DemoProvider(delay=0.01),
        renderer=CallbackRenderer(lambda e: events.append(e)),
    )
    assert session.is_pause_requested() is False
    await session.pause()
    assert session.is_pause_requested() is True
    await session.resume()
    assert session.is_pause_requested() is False


@pytest.mark.asyncio
async def test_checkpoint_returns_immediately_when_not_paused():
    session = Session(
        provider=DemoProvider(delay=0.01),
        renderer=CallbackRenderer(lambda e: None),
    )
    await asyncio.wait_for(session.checkpoint(), timeout=0.2)


def test_session_requires_provider_and_renderer():
    from searchlense.errors import SessionError

    with pytest.raises(SessionError):
        Session(provider=None, renderer=CallbackRenderer(lambda e: None))
    with pytest.raises(SessionError):
        Session(provider=DemoProvider(), renderer=None)
