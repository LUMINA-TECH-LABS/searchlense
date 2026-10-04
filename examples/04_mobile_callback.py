"""Example: use the callback renderer instead of a console.

Phones and custom UIs cannot print to a terminal. Instead, hand each event
to a function. That function can push into a list your UI reads, a queue,
a websocket, a database — anywhere.
"""

import asyncio
from typing import Any

from searchlense import CallbackRenderer, DemoProvider, Event, Session


collected: list[dict[str, Any]] = []


def on_event(event: Event) -> None:
    # On a phone UI, this would append to an observable list the view renders.
    collected.append(event.to_dict())


async def main() -> None:
    session = Session(
        provider=DemoProvider(delay=0.25),
        renderer=CallbackRenderer(on_event),
    )
    await session.run("how solar panels work")
    print(f"collected {len(collected)} events")
    for item in collected[:5]:
        print(item["type"], item["sequence"])


if __name__ == "__main__":
    asyncio.run(main())
