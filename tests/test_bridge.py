"""Tests for the stdio bridge, driven in-process."""

import asyncio
import io
import json

import pytest

from searchlense.bridge import _BridgeRenderer
from searchlense.events import source_found


@pytest.mark.asyncio
async def test_json_renderer_writes_one_line_per_event():
    buf = io.StringIO()
    r = _BridgeRenderer(buf, fmt="json")
    await r.render(source_found("https://x", "T", "s", 0.5))
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["type"] == "source_found"
    assert obj["payload"]["url"] == "https://x"


@pytest.mark.asyncio
async def test_tsv_renderer_writes_tabs():
    buf = io.StringIO()
    r = _BridgeRenderer(buf, fmt="tsv")
    await r.render(source_found("https://x", "T", "s", 0.5))
    line = buf.getvalue().strip()
    parts = line.split("\t")
    # sequence, type, timestamp, then key=val pairs
    assert parts[0] == "-1"
    assert parts[1] == "source_found"
    assert any(p.startswith("url=") for p in parts)
    assert any(p.startswith("title=") for p in parts)


@pytest.mark.asyncio
async def test_tsv_renderer_url_encodes_special_chars():
    buf = io.StringIO()
    r = _BridgeRenderer(buf, fmt="tsv")
    await r.render(source_found("https://x/a b", "T\tX", "s", None))
    line = buf.getvalue().strip()
    assert "\t" in line
    # The embedded tab in title must be encoded
    assert "title=T%09X" in line
