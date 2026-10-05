"""Reference provider: a real web search using only the Python standard library.

This is an EXAMPLE. It lives in `examples/`, not in `src/searchlense/`.

    searchlense does not search.
    searchlense is the timeline for a search that is already happening.

This file shows one way to wrap a real search source and feed it to
searchlense as a provider. Copy it, change the `search` method to call
whatever tool or API you already use, and delete the rest.

How it works:
- Fetches DuckDuckGo's public HTML search results page.
- Parses result titles, URLs, and snippets with a tiny regex-based parser.
- Yields dicts that searchlense's Session automatically converts into events.

No API key. No extra dependency. No install beyond the searchlense wheel itself.

Run:

    python examples/09_real_provider.py "your query here"
"""

from __future__ import annotations

import asyncio
import re
import sys
import urllib.parse
import urllib.request
from html import unescape
from typing import Any, AsyncIterator

from searchlense import BaseProvider, ConsoleRenderer, Session


USER_AGENT = (
    "Mozilla/5.0 (compatible; searchlense-example/0.1; "
    "+https://github.com/LUMINA-TECH-LABS/searchlense)"
)

DDG_HTML = "https://html.duckduckgo.com/html/?q={q}"


class DuckDuckGoProvider(BaseProvider):
    """A tiny, honest example provider. Not production-grade.

    It fetches one page of results, parses them, and yields source events.
    For real work you'd want pagination, retries, and a proper HTML parser.
    That's not the point of this example.
    """

    name = "duckduckgo"

    def __init__(self, limit: int = 8) -> None:
        self.limit = limit

    async def search(self, query: str) -> AsyncIterator[dict[str, Any]]:
        yield {"kind": "note", "text": f"querying DuckDuckGo for: {query!r}"}

        # urllib is blocking; run it in a thread so we don't block the loop.
        html = await asyncio.to_thread(self._fetch, query)

        results = self._parse(html)
        if not results:
            yield {"kind": "note", "text": "no results parsed (page layout may have changed)"}
            yield {"kind": "result", "summary": f"No results for {query!r}.", "sources": []}
            return

        for r in results[: self.limit]:
            yield {
                "kind": "source",
                "url": r["url"],
                "title": r["title"],
                "snippet": r["snippet"],
                "score": None,
            }

        yield {
            "kind": "result",
            "summary": f"Found {len(results[: self.limit])} results for {query!r}.",
            "sources": [r["url"] for r in results[: self.limit]],
        }

    # --- internals --------------------------------------------------------

    @staticmethod
    def _fetch(query: str) -> str:
        url = DDG_HTML.format(q=urllib.parse.quote_plus(query))
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @staticmethod
    def _parse(html: str) -> list[dict[str, str]]:
        """Extract result blocks from DuckDuckGo's HTML page.

        The page structure is: each result is a link with class "result__a",
        followed by a snippet with class "result__snippet". We parse by regex
        because the stdlib has no HTML parser good enough for this, and
        adding a dependency would defeat the point of a zero-dep example.
        """
        results: list[dict[str, str]] = []

        # Links: <a ... class="result__a" href="URL">TITLE</a>
        link_re = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )
        # Snippets: <a ... class="result__snippet" ...>TEXT</a>
        snippet_re = re.compile(
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL | re.IGNORECASE,
        )

        links = link_re.findall(html)
        snippets = snippet_re.findall(html)

        for i, (href, title_html) in enumerate(links):
            url = DuckDuckGoProvider._clean_url(href)
            title = DuckDuckGoProvider._strip_tags(title_html)
            snippet = ""
            if i < len(snippets):
                snippet = DuckDuckGoProvider._strip_tags(snippets[i])
            if url and title:
                results.append({"url": url, "title": title, "snippet": snippet})

        return results

    @staticmethod
    def _clean_url(href: str) -> str:
        """DuckDuckGo wraps result links in a redirect. Unwrap when possible."""
        if href.startswith("//duckduckgo.com/l/?uddg="):
            parsed = urllib.parse.urlparse("https:" + href)
            qs = urllib.parse.parse_qs(parsed.query)
            if "uddg" in qs:
                return urllib.parse.unquote(qs["uddg"][0])
        if href.startswith("/l/?uddg="):
            qs = urllib.parse.parse_qs(href.split("?", 1)[1])
            if "uddg" in qs:
                return urllib.parse.unquote(qs["uddg"][0])
        return href

    @staticmethod
    def _strip_tags(s: str) -> str:
        s = re.sub(r"<[^>]+>", "", s)
        return unescape(s).strip()


async def main() -> None:
    query = " ".join(sys.argv[1:]) or "history of the printing press"

    session = Session(
        provider=DuckDuckGoProvider(limit=8),
        renderer=ConsoleRenderer(),
        speed=1.0,
    )

    await session.run(query)


if __name__ == "__main__":
    asyncio.run(main())
