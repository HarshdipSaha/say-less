"""Bias the recogniser toward the words actually in play.

Prospective: push a field's value set before the caller speaks, shrinking the
confidently-wrong bucket at source rather than trying to detect it afterwards.
Reactive: push the narrowed candidates immediately after a repair is asked.

`enabled` is a parameter rather than a module constant so the harness can run
both arms in one process and report the difference.
"""
from .moves import MoveKind, RepairMove
from .schema import KEYTERM_MAX_COUNT, KEYTERM_MAX_LEN, FieldSpec


def prospective_terms(expected: list[str], schema: dict[str, FieldSpec]) -> list[str]:
    seen, out = set(), []
    for name in expected:
        spec = schema.get(name)
        if not spec:
            continue
        for v in spec.values:
            k = v.lower()
            if k not in seen:
                seen.add(k)
                out.append(v[:KEYTERM_MAX_LEN])
    return out[:KEYTERM_MAX_COUNT]


def reactive_terms(move: RepairMove, enabled: bool = True) -> list[str]:
    if not enabled:
        return []
    if move.kind is MoveKind.RESTRICTED_OFFER and move.candidates:
        return [move.candidates[0], "yes", "no"]
    if move.kind is MoveKind.TWO_WAY_OFFER:
        return list(move.candidates)
    return []
