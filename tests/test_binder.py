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
