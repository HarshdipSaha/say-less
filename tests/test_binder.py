from sayless.binder import BinderCache, parse_binder_response
from sayless.evidence import BoundField


def test_parse_maps_spans_to_word_indices():
    payload = {"bindings": [{"field": "day", "value": "chewsday", "start": 13, "end": 21}]}
    bound = parse_binder_response(payload, "can I book a chewsday appointment",
                                  ["can", "I", "book", "a", "chewsday", "appointment"])
    assert bound == [BoundField("day", "chewsday", (4,))]


def test_parse_handles_a_multi_word_value():
    payload = {"bindings": [{"field": "service", "value": "beard trim", "start": 5, "end": 15}]}
    bound = parse_binder_response(payload, "book beard trim now",
                                  ["book", "beard", "trim", "now"])
    assert bound[0].word_indices == (1, 2)


def test_parse_ignores_unknown_fields():
    payload = {"bindings": [{"field": "zzz", "value": "x", "start": 0, "end": 1}]}
    assert parse_binder_response(payload, "x y", ["x", "y"]) == []


def test_parse_survives_a_missing_bindings_key():
    assert parse_binder_response({}, "x", ["x"]) == []


def test_cache_round_trips(tmp_path):
    cache = BinderCache(tmp_path / "c.json")
    cache.put("book tuesday", {"bindings": []})
    cache.save()
    assert BinderCache(tmp_path / "c.json").get("book tuesday") == {"bindings": []}


def test_lexical_fallback_recovers_a_value_the_model_dropped():
    """The binder model returned no bindings for these real SLURP / Appointment-
    Bench sentences (live, 2026-09-17). An exact in-set word must still bind."""
    from sayless.binder import lexical_fallback
    from sayless.schema import BOOKING_SCHEMA
    cases = {
        "Wait for Danielle's consultation. That's Dr. Barry": ("service", "consultation"),
        "What's the weather next Wednesday?": ("day", "Wednesday"),
        "Clear my 9 AM alarms": ("time", "nine am"),
        "book a hot towel shave please": ("service", "hot towel shave"),
    }
    for text, (field, value) in cases.items():
        got = {b.field: b.heard_value for b in lexical_fallback(text.split(), BOOKING_SCHEMA)}
        assert got.get(field) == value, text


def test_lexical_fallback_never_invents_or_corrects():
    """It only reports values already in the set, word for word: a garbled
    value, and anything surname-shaped, must come from the model or not at all."""
    from sayless.binder import lexical_fallback
    from sayless.schema import BOOKING_SCHEMA
    assert lexical_fallback("can I book a chewsday appointment".split(), BOOKING_SCHEMA) == []
    assert lexical_fallback("can I get a hairkut please".split(), BOOKING_SCHEMA) == []
    assert lexical_fallback("no that was long".split(), BOOKING_SCHEMA) == []
    assert lexical_fallback("my name is Green".split(), BOOKING_SCHEMA) == []


def test_bind_uses_the_fallback_only_when_the_model_binds_nothing(monkeypatch):
    import sayless.binder as binder
    from sayless.schema import BOOKING_SCHEMA

    class Cache:
        def __init__(self, payload): self.payload = payload
        def get(self, _): return self.payload

    words = "tell me what's happening next Thursday".split()
    text = " ".join(words)
    # Model bound a near-miss: keep it, so the planner can repair it.
    kept = binder.bind(text, words, BOOKING_SCHEMA, Cache(
        {"bindings": [{"field": "day", "value": "next Thursday", "start": 26, "end": 39}]}))
    assert [(b.field, b.heard_value) for b in kept] == [("day", "next Thursday")]
    # Model bound nothing: fall back to the exact in-set word.
    recovered = binder.bind(text, words, BOOKING_SCHEMA, Cache({"bindings": []}))
    assert [(b.field, b.heard_value) for b in recovered] == [("day", "Thursday")]
