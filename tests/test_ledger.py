import pytest

from searchlense.errors import LedgerError
from searchlense.events import note, source_found
from searchlense.ledger import Ledger


def test_append_assigns_increasing_sequence():
    l = Ledger()
    e0 = l.append(note("a"))
    e1 = l.append(note("b"))
    assert e0.sequence == 0
    assert e1.sequence == 1
    assert len(l) == 2


def test_get_returns_event():
    l = Ledger()
    l.append(note("a"))
    assert l.get(0).payload["text"] == "a"


def test_get_out_of_range_raises():
    l = Ledger()
    with pytest.raises(LedgerError):
        l.get(0)
    l.append(note("a"))
    with pytest.raises(LedgerError):
        l.get(5)
    with pytest.raises(LedgerError):
        l.get(-1)


def test_iteration_is_snapshot():
    l = Ledger()
    l.append(note("a"))
    snapshot = list(l)
    l.append(note("b"))
    assert len(snapshot) == 1


def test_slice():
    l = Ledger()
    for i in range(5):
        l.append(note(str(i)))
    assert [e.payload["text"] for e in l.slice(1, 3)] == ["1", "2"]
    assert len(l.slice()) == 5


def test_latest():
    l = Ledger()
    assert l.latest() is None
    l.append(note("a"))
    l.append(note("b"))
    assert l.latest().payload["text"] == "b"


def test_at_or_before_time():
    l = Ledger()
    e0 = l.append(note("a"))
    e1 = l.append(note("b"))
    e2 = l.append(note("c"))
    e0.timestamp = 100.0
    e1.timestamp = 200.0
    e2.timestamp = 300.0
    assert l.at_or_before_time(50.0) == -1
    assert l.at_or_before_time(150.0) == 0
    assert l.at_or_before_time(200.0) == 1
    assert l.at_or_before_time(1_000.0) == 2


def test_extend_and_clear():
    l = Ledger()
    l.extend([note("a"), note("b"), note("c")])
    assert len(l) == 3
    l.clear()
    assert len(l) == 0


def test_source_found_payload_intact():
    l = Ledger()
    e = l.append(source_found("https://x", "t", "s", 0.9))
    assert e.payload["score"] == 0.9
