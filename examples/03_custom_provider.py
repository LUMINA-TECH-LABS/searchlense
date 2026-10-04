"""Example: write your own provider and plug it in.

A provider is anything with an async `search(query)` generator that yields
dicts. searchlense wraps them into events automatically. In a real agent,
your provider would call your search API, your scraper, your LangChain tool,
or your own code.
"""

import asyncio
from typing import Any, AsyncIterator

from searchlense import BaseProvider, ConsoleRenderer, Session


class MyProvider(BaseProvider):
    name = "my-provider"

    async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
        yield {"kind": "note", "text": f"custom provider received: {query!r}"}
        await asyncio.sleep(0.3)
        yield {
            "kind": "source",
            "url": "https://my-source.example/page",
            "title": "My custom source",
            "snippet": "Whatever your API returns, mapped to this shape.",
            "score": 0.77,
        }
        await asyncio.sleep(0.3)
        yield {
            "kind": "result",
            "summary": "Custom provider finished.",
            "sources": ["https://my-source.example/page"],
        }


async def main() -> None:
    session = Session(provider=MyProvider(), renderer=ConsoleRenderer())
    await session.run("whatever your user searched for")


if __name__ == "__main__":
    asyncio.run(main())
