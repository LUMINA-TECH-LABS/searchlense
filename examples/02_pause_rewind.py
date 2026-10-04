"""Example: programmatically pause, rewind, and resume a live session.

This shows the DVR behavior without needing keyboard input. It schedules
controller actions to happen while the session is running.
"""

import asyncio

from searchlense import ConsoleRenderer, DemoProvider, Session


async def main() -> None:
    provider = DemoProvider(delay=0.4)
    renderer = ConsoleRenderer()
    session = Session(provider=provider, renderer=renderer, speed=1.0)

    async def director() -> None:
        await asyncio.sleep(1.2)
        print("\n--- PAUSE ---\n")
        session.pause_nowait()

        await asyncio.sleep(1.5)

        print("\n--- REWIND 3 ---\n")
        session.controller.rewind(3)

        print("\n--- RESUME ---\n")
        session.resume_nowait()

    await asyncio.gather(session.run("history of the printing press"), director())


if __name__ == "__main__":
    asyncio.run(main())
