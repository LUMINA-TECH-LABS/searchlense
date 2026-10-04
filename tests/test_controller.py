import asyncio

import pytest

from searchlense.controller import Controller, PlaybackState
from searchlense.errors import ControllerError
from searchlense.events import note
from searchlense.ledger import Ledger


def _fill(l: Ledger, n: int = 5) -> None:
    for i in range(n):
        l.append(note(str(i)))


def test_initial_state():
    l = Ledger()
    c = Controller(l)
    assert c.state == PlaybackState.PAUSED
    assert c.cursor == -1
    assert c.speed == 1.0


def test_invalid_speed():
    l = Ledger()
    with pytest.raises(ControllerError):
        Controller(l, speed=0)
    with pytest.raises(ControllerError):
        Controller(l, speed=-1)


def test_play_pause_stop():
    l = Ledger()
    c = Controller(l)
    c.play()
    assert c.state == PlaybackState.PLAYING
    c.pause()
    assert c.state == PlaybackState.PAUSED
    c.stop()
    assert c.state == PlaybackState.ENDED


def test_rewind_and_forward_clamp():
    l = Ledger()
    _fill(l, 5)
    c = Controller(l)
    c._cursor = 3
    c.rewind(2)
    assert c.cursor == 1
    c.rewind(100)
    assert c.cursor == -1
    c.forward(2)
    assert c.cursor == 1
    c.forward(100)
    assert c.cursor == 4  # last index


def test_rewind_negative_steps_raises():
    l = Ledger()
    _fill(l)
    c = Controller(l)
    with pytest.raises(ControllerError):
        c.rewind(-1)
    with pytest.raises(ControllerError):
        c.forward(-1)


def test_seek_and_jump_live():
    l = Ledger()
    _fill(l, 5)
    for i, e in enumerate(l):
        e.timestamp = 100.0 + i * 10
    c = Controller(l)
    c.seek_to_time(125.0)
    assert c.cursor == 2
    c.jump_to_live()
    assert c.cursor == 4
    assert c.at_live_edge() is True


@pytest.mark.asyncio
async def test_events_yields_in_order_when_playing():
    l = Ledger()
    _fill(l, 3)
    c = Controller(l, speed=1000.0)  # don't sleep long
    c.jump_to_live()
    c._cursor = -1
    c.play()

    collected = []
    async def consume():
        async for e in c.events(idle_poll=0.01):
            collected.append(e.sequence)
            if len(collected) == 3:
                c.stop()
                return

    await asyncio.wait_for(consume(), timeout=2.0)
    assert collected == [0, 1, 2]


@pytest.mark.asyncio
async def test_pause_holds_cursor():
    l = Ledger()
    _fill(l, 3)
    c = Controller(l, speed=1000.0)
    c._cursor = -1
    c.play()

    collected = []

    async def consume():
        async for e in c.events(idle_poll=0.01):
            collected.append(e.sequence)
            if len(collected) == 1:
                c.pause()
            if c.state == PlaybackState.ENDED:
                return

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.2)
    assert collected == [0]

    c.play()
    await asyncio.sleep(0.2)
    c.stop()
    await asyncio.wait_for(task, timeout=1.0)
    assert collected[:3] == [0, 1, 2]
