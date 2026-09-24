"""Attach width / hierarchy / speed attributes to Road Network segments via SLK overlap joins."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dbe.slk_join import SlkSpan, dominant_value, index_by_road, span_from_properties, weighted_mean

# Confirmed in docs/task_docs/source_verification.md (Task S0.T2). Change here if the service differs.
HIERARCHY_FIELD = "ROAD_HIERARCHY"
SPEED_FIELD = "SPEED_LIMIT"

PAVEMENT_MEAN_FIELDS: dict[str, str] = {
    "TOTAL_PAVE_WIDTH": "TOTAL_PAVE_WIDTH_M",
    "TOTAL_SEAL_WIDTH": "TOTAL_SEAL_WIDTH_M",
    "TRAFFICABLE_SURF_WIDTH": "TRAFFICABLE_SURF_WIDTH_M",
    "SEALED_SHOULDER_L": "SEALED_SHOULDER_L_M",
    "SEALED_SHOULDER_R": "SEALED_SHOULDER_R_M",
}
PAVEMENT_DOMINANT_FIELDS: dict[str, str] = {
    "NO_OF_LANES": "NO_OF_LANES", "KERB_L": "KERB_L", "KERB_R": "KERB_R",
}

WIDTH_SOURCE_MRWA = "mrwa_pavement"
WIDTH_SOURCE_NONE = "none"

ENRICH_COLUMNS: list[str] = [
    "ROAD_HIERARCHY", "SPEED_LIMIT",
    "TOTAL_PAVE_WIDTH_M", "TOTAL_SEAL_WIDTH_M", "TRAFFICABLE_SURF_WIDTH_M", "NO_OF_LANES",
    "SEALED_SHOULDER_L_M", "SEALED_SHOULDER_R_M", "KERB_L", "KERB_R",
    "WIDTH_M", "WIDTH_SOURCE",
]


def _spans(features: list[dict[str, Any]]) -> list[SlkSpan]:
    out: list[SlkSpan] = []
    for f in features:
        span = span_from_properties(f.get("properties") or {})
        if span is not None:
            out.append(span)
    return out


@dataclass
class EnrichIndex:
    pavement: dict[str, list[SlkSpan]]
    hierarchy: dict[str, list[SlkSpan]]
    speed: dict[str, list[SlkSpan]]

    @classmethod
    def from_features(cls, pavement: list[dict], hierarchy: list[dict], speed: list[dict]) -> EnrichIndex:
        return cls(
            index_by_road(_spans(pavement)), index_by_road(_spans(hierarchy)), index_by_road(_spans(speed))
        )


def _round2(value: float | None) -> float | None:
    return None if value is None else round(value, 2)


def enrich_segment(props: dict[str, Any], index: EnrichIndex) -> dict[str, Any]:
    out: dict[str, Any] = dict.fromkeys(ENRICH_COLUMNS)
    out["WIDTH_SOURCE"] = WIDTH_SOURCE_NONE
    target = span_from_properties(props)
    if target is None:
        return out
    for src, col in PAVEMENT_MEAN_FIELDS.items():
        out[col] = _round2(weighted_mean(target, index.pavement, src))
    for src, col in PAVEMENT_DOMINANT_FIELDS.items():
        out[col] = dominant_value(target, index.pavement, src)
    out["ROAD_HIERARCHY"] = dominant_value(target, index.hierarchy, HIERARCHY_FIELD)
    out["SPEED_LIMIT"] = dominant_value(target, index.speed, SPEED_FIELD)
    if out["TOTAL_SEAL_WIDTH_M"] is not None:
        out["WIDTH_M"] = out["TOTAL_SEAL_WIDTH_M"]
        out["WIDTH_SOURCE"] = WIDTH_SOURCE_MRWA
    return out
