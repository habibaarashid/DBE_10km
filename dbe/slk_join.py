"""Linear-referencing (SLK) overlap joins between MRWA layers keyed by ROAD + carriageway + SLK range."""
from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

SINGLE = "Single"


@dataclass(frozen=True)
class SlkSpan:
    road: str
    cwy: str
    start_slk: float
    end_slk: float
    attrs: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def length(self) -> float:
        return abs(self.end_slk - self.start_slk)


def overlap_len(a0: float, a1: float, b0: float, b1: float) -> float:
    lo = max(min(a0, a1), min(b0, b1))
    hi = min(max(a0, a1), max(b0, b1))
    return max(0.0, hi - lo)


def cwy_compatible(a: str, b: str) -> bool:
    return a == b or a == SINGLE or b == SINGLE


def span_from_properties(props: dict[str, Any]) -> SlkSpan | None:
    road = props.get("ROAD")
    if road in (None, ""):
        return None
    try:
        start = float(props["START_SLK"])
        end = float(props["END_SLK"])
    except (KeyError, TypeError, ValueError):
        return None
    if not (math.isfinite(start) and math.isfinite(end)):
        return None
    cwy = props.get("CWY") or SINGLE
    return SlkSpan(str(road), str(cwy), start, end, props)


def index_by_road(spans: Iterable[SlkSpan]) -> dict[str, list[SlkSpan]]:
    by_road: dict[str, list[SlkSpan]] = defaultdict(list)
    for s in spans:
        by_road[s.road].append(s)
    return dict(by_road)


def overlapping(target: SlkSpan, by_road: dict[str, list[SlkSpan]]) -> list[tuple[SlkSpan, float]]:
    out: list[tuple[SlkSpan, float]] = []
    point_target = target.length == 0.0
    for s in by_road.get(target.road, []):
        if not cwy_compatible(target.cwy, s.cwy):
            continue
        if point_target:
            lo, hi = min(s.start_slk, s.end_slk), max(s.start_slk, s.end_slk)
            ov = 1.0 if lo <= target.start_slk <= hi else 0.0
        else:
            ov = overlap_len(target.start_slk, target.end_slk, s.start_slk, s.end_slk)
        if ov > 0.0:
            out.append((s, ov))
    exact = [(s, ov) for s, ov in out if s.cwy == target.cwy]
    return exact or out


def _present(value: Any) -> bool:
    """True when a value is real data rather than absence.

    A zero is data (a zero sealed shoulder is a measurement), so this deliberately tests against
    `""` rather than using truthiness. A non-finite float is NOT data: NaN passes every naive
    emptiness test and would otherwise reach the CSV as the literal "nan".
    """
    if value is None or value == "":
        return False
    return not (isinstance(value, float) and not math.isfinite(value))


def dominant_value(target: SlkSpan, by_road: dict[str, list[SlkSpan]], field_name: str) -> Any | None:
    best: Any | None = None
    best_ov = 0.0
    for s, ov in overlapping(target, by_road):
        value = s.attrs.get(field_name)
        if _present(value) and ov > best_ov:
            best, best_ov = value, ov
    return best


def weighted_mean(target: SlkSpan, by_road: dict[str, list[SlkSpan]], field_name: str) -> float | None:
    num = den = 0.0
    for s, ov in overlapping(target, by_road):
        value = s.attrs.get(field_name)
        if not _present(value):
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(v):
            continue
        num += v * ov
        den += ov
    return (num / den) if den > 0.0 else None
