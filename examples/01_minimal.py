"""Minimal example: run a demo session and watch events print."""

import asyncio

from searchlense import ConsoleRenderer, DemoProvider, Session


async def main() -> None:
    provider = DemoProvider(delay=0.35)
    renderer = ConsoleRenderer()
    session = Session(provider=provider, renderer=renderer, speed=1.0)
    ledger = await session.run("quantum computing for beginners")
    print(f"\nledger contains {len(ledger)} events")


if __name__ == "__main__":
    asyncio.run(main())
