import asyncio

import pytest

from searchlense.control import ControlSignal


@pytest.mark.asyncio
async def test_initial_state_is_not_paused():
    s = ControlSignal()
    assert s.is_pause_requested() is False
    # checkpoint returns immediately when not paused
    await asyncio.wait_for(s.checkpoint(), timeout=0.2)


@pytest.mark.asyncio
async def test_pause_then_resume_releases_checkpoint():
    s = ControlSignal()
    await s.request_pause()
    assert s.is_pause_requested() is True

    task = asyncio.create_task(s.checkpoint())
    await asyncio.sleep(0.05)
    assert not task.done()

    await s.request_resume()
    await asyncio.wait_for(task, timeout=0.5)
    assert s.is_pause_requested() is False


@pytest.mark.asyncio
async def test_nowait_variants():
    s = ControlSignal()
    s.request_pause_nowait()
    assert s.is_pause_requested() is True

    task = asyncio.create_task(s.checkpoint())
    await asyncio.sleep(0.05)
    assert not task.done()

    s.request_resume_nowait()
    await asyncio.wait_for(task, timeout=0.5)
    assert s.is_pause_requested() is False


@pytest.mark.asyncio
async def test_multiple_waiters_all_release():
    s = ControlSignal()
    await s.request_pause()
    tasks = [asyncio.create_task(s.checkpoint()) for _ in range(3)]
    await asyncio.sleep(0.05)
    assert all(not t.done() for t in tasks)

    await s.request_resume()
    await asyncio.wait_for(asyncio.gather(*tasks), timeout=1.0)


@pytest.mark.asyncio
async def test_wait_for_resume_returns_when_paused():
    """wait_for_resume blocks while paused, returns after resume."""
    s = ControlSignal()
    await s.request_pause()

    task = asyncio.create_task(s.wait_for_resume())
    await asyncio.sleep(0.05)
    assert not task.done()
    assert s.is_pause_requested() is True

    await s.request_resume()
    await asyncio.wait_for(task, timeout=0.5)
    assert s.is_pause_requested() is False
