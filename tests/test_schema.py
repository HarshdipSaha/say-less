import pytest
from sayless.schema import BOOKING_SCHEMA, FieldSpec, load_surnames


def test_booking_schema_has_the_four_spec_fields():
    assert set(BOOKING_SCHEMA) == {"day", "time", "service", "surname"}
    assert all(f.values for f in BOOKING_SCHEMA.values())


def test_surname_is_consequential():
    assert BOOKING_SCHEMA["surname"].consequential is True


def test_surname_file_is_large_enough_to_exercise_the_keyterm_cap():
    assert len(load_surnames()) >= 120, "corpus/surnames.txt must hold >= 120 names"


def test_field_rejects_an_empty_value_set():
    with pytest.raises(ValueError):
        FieldSpec(name="x", label="x", values=())


def test_keyterms_are_capped_at_the_api_limit():
    spec = FieldSpec("x", "x", tuple(f"v{i}" for i in range(150)))
    assert len(spec.keyterms()) == 100
    assert all(len(t) <= 50 for t in spec.keyterms())
