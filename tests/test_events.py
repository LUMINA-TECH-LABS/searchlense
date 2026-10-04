from searchlense.events import (
    Event,
    EventType,
    error,
    image_found,
    note,
    query_formed,
    result_ready,
    session_end,
    session_start,
    snippet_extracted,
    source_found,
    video_found,
)


def test_event_to_dict_roundtrip():
    e = source_found("https://x", "Title", "snip", 0.5)
    d = e.to_dict()
    assert d["type"] == "source_found"
    assert d["payload"]["url"] == "https://x"
    e2 = Event.from_dict(d)
    assert e2.type == EventType.SOURCE_FOUND
    assert e2.payload == e.payload


def test_event_type_enum_values():
    assert EventType.SESSION_START.value == "session_start"
    assert EventType.SOURCE_FOUND.value == "source_found"
    assert EventType.IMAGE_FOUND.value == "image_found"
    assert EventType.VIDEO_FOUND.value == "video_found"
    assert EventType.RESULT_READY.value == "result_ready"
    assert EventType.SESSION_END.value == "session_end"


def test_constructors_populate_payload():
    assert session_start("q").payload == {"query": "q"}
    assert query_formed("q", "engine").payload == {"query": "q", "engine": "engine"}
    assert source_found("u", "t", "s", 1.0).payload["url"] == "u"
    assert snippet_extracted("u", "text").payload["text"] == "text"
    assert image_found("u").payload["url"] == "u"
    assert video_found("u").payload["url"] == "u"
    assert note("hi").payload == {"text": "hi"}
    assert error("boom", "here").payload == {"message": "boom", "where": "here"}
    assert result_ready("done").payload["summary"] == "done"
    assert session_end("complete").payload == {"reason": "complete"}


def test_event_sequence_default_is_minus_one():
    assert note("x").sequence == -1


def test_event_ids_are_unique():
    a = note("x")
    b = note("x")
    assert a.event_id != b.event_id
