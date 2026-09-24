"""Orchestrates one extraction: query → filter by circle → enrich → rows."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from dbe import __version__, schema
from dbe.enrich import EnrichIndex, enrich_segment
from dbe.geometry import LocalProjection, geojson_to_line, iter_vertices, segment_metrics
from dbe.mrwa_client import (
    LAYER_HIERARCHY,
    LAYER_PAVEMENT,
    LAYER_ROAD_NETWORK,
    LAYER_SPEED,
    normalise_properties,
)
from dbe.slk_join import span_from_properties

log = logging.getLogger(__name__)


class RoadSource(Protocol):
    def query_envelope(self, layer_id: int, envelope, out_fields: str = "*") -> list[dict]: ...


class NoRoadsFound(RuntimeError):
    """Layer 17 returned nothing inside the circle."""


def _dedupe_by_objectid(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop repeated OBJECTIDs, keeping first occurrence.

    Live paging over a spatial query returns a small number of records twice — measured at 135,
    376 and 111 duplicates on layers 12, 16 and 8 in the 10 km run. A duplicated span would be
    counted twice in `weighted_mean`, skewing the width it produces. Layer 17 has always been
    de-duplicated by its `seen` set; this gives the enrichment layers the same guarantee.
    """
    seen: set[Any] = set()
    out: list[dict[str, Any]] = []
    for feat in features:
        oid = (feat.get("properties") or {}).get("OBJECTID")
        if oid is not None:
            if oid in seen:
                continue
            seen.add(oid)
        out.append(feat)
    return out


@dataclass
class ExtractResult:
    roads: list[dict[str, Any]]
    vertices: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


def _sort_key(row: dict[str, Any]) -> tuple[str, str, float]:
    try:
        slk = float(row.get("START_SLK") or 0.0)
    except (TypeError, ValueError):
        slk = 0.0
    return (str(row.get("ROAD") or ""), str(row.get("CWY") or ""), slk)


def extract(
    lat: float, lon: float, radius_km: float, source: RoadSource, with_osm: bool = False
) -> ExtractResult:
    proj = LocalProjection(lat, lon)
    radius_m = float(radius_km) * 1000.0
    circle = proj.circle(radius_m)
    envelope = proj.envelope_wgs84(radius_m)
    extracted_at = datetime.now(UTC).isoformat(timespec="seconds")

    log.info("querying MRWA layers for envelope %s", envelope)
    feats17 = source.query_envelope(LAYER_ROAD_NETWORK, envelope)
    feats12 = source.query_envelope(LAYER_PAVEMENT, envelope)
    feats16 = source.query_envelope(LAYER_HIERARCHY, envelope)
    feats8 = source.query_envelope(LAYER_SPEED, envelope)
    deduped12 = _dedupe_by_objectid(feats12)
    deduped16 = _dedupe_by_objectid(feats16)
    deduped8 = _dedupe_by_objectid(feats8)
    enrich_duplicates_dropped = (
        (len(feats12) - len(deduped12)) + (len(feats16) - len(deduped16)) + (len(feats8) - len(deduped8))
    )
    index = EnrichIndex.from_features(deduped12, deduped16, deduped8)

    roads: list[dict[str, Any]] = []
    vertices: list[dict[str, Any]] = []
    seen: set[Any] = set()
    skipped_no_geometry = duplicates = outside = unparsed_slk = skipped_bad_geometry = 0

    for feat in feats17:
        props = normalise_properties(feat.get("properties") or {})
        oid = props.get("OBJECTID")
        if oid in seen:
            duplicates += 1
            continue
        if not (feat.get("geometry") or {}).get("coordinates"):
            skipped_no_geometry += 1
            continue
        # The cheap guard above catches null and empty geometry. Anything else malformed — a
        # one-coordinate line, an empty MultiLineString part, a wrong geometry type — raises from
        # shapely or GEOS, and the exception types are not worth enumerating: this is untrusted
        # data from an external service, and an unhandled raise here aborts a run that has already
        # spent minutes fetching. A broad catch is correct; the log names the type so nothing hides.
        try:
            geom = geojson_to_line(feat["geometry"])
            m = segment_metrics(geom, proj, circle)
        except Exception as exc:  # deliberately broad; see comment above
            log.warning("skipping OBJECTID %s: unusable geometry (%s: %s)", oid, type(exc).__name__, exc)
            skipped_bad_geometry += 1
            continue
        seen.add(oid)
        if not m.intersects:
            outside += 1
            continue
        enrichment = enrich_segment(props, index)
        # Count segments whose SLK could not be parsed at all, not merely those with a null
        # START_SLK: a non-numeric value like "abc" also fails to parse but is not None, so the
        # obvious `props.get("START_SLK") is None` test silently undercounts. (0 such rows exist
        # in the 2.5 km fixtures, so this is precision, not a live bug.)
        if span_from_properties(props) is None:
            unparsed_slk += 1
        row: dict[str, Any] = {c: props.get(c) for c in schema.ORIGINAL_COLUMNS}
        row.update(
            {
                "START_LAT": m.start_lat,
                "START_LON": m.start_lon,
                "END_LAT": m.end_lat,
                "END_LON": m.end_lon,
                "VERTEX_COUNT": m.vertex_count,
                "LENGTH_M": round(m.length_m, 2),
                "DIST_TO_CENTRE_M": round(m.dist_to_centre_m, 2),
                "INSIDE_FRACTION": round(m.inside_fraction, 4),
                "GEOMETRY_WKT": m.wkt,
            }
        )
        row.update(enrichment)
        row.update(dict.fromkeys(schema.OSM_COLUMNS))
        row.update({"DATA_SOURCE": schema.DATA_SOURCE, "EXTRACTED_AT_UTC": extracted_at})
        roads.append({c: row.get(c) for c in schema.OUTPUT_COLUMNS})
        for part, seq, vlat, vlon in iter_vertices(geom):
            vertices.append(
                {
                    "OBJECTID": oid,
                    "NETWORK_ELEMENT": props.get("NETWORK_ELEMENT"),
                    "ROAD": props.get("ROAD"),
                    "ROAD_NAME": props.get("ROAD_NAME"),
                    "CWY": props.get("CWY"),
                    "PART": part,
                    "SEQ": seq,
                    "LAT": vlat,
                    "LON": vlon,
                }
            )

    if not roads:
        raise NoRoadsFound(
            f"no road segments intersect a {radius_km} km circle at ({lat}, {lon}); "
            "check the lat/lon order and that the point is in Western Australia"
        )

    roads.sort(key=_sort_key)
    order = {r["OBJECTID"]: i for i, r in enumerate(roads)}
    vertices.sort(key=lambda v: (order[v["OBJECTID"]], v["PART"], v["SEQ"]))

    metadata: dict[str, Any] = {
        "centre_lat": lat,
        "centre_lon": lon,
        "radius_km": radius_km,
        "envelope_wgs84": list(envelope),
        "extracted_at_utc": extracted_at,
        "features_returned_layer17": len(feats17),
        "segments_intersecting": len(roads),
        "segments_outside_circle": outside,
        "skipped_no_geometry": skipped_no_geometry,
        "skipped_bad_geometry": skipped_bad_geometry,
        "duplicates_dropped": duplicates,
        "enrich_duplicates_dropped": enrich_duplicates_dropped,
        "enrich_unparsed_slk": unparsed_slk,
        "features_layer12": len(feats12),
        "features_layer16": len(feats16),
        "features_layer8": len(feats8),
        "network_type_counts": dict(Counter(r["NETWORK_TYPE"] for r in roads)),
        "width_source_counts": dict(Counter(r["WIDTH_SOURCE"] for r in roads)),
        "vertices_rows": len(vertices),
        "data_source": schema.DATA_SOURCE,
        "licence": schema.LICENCE,
        "datum_note": schema.DATUM_NOTE,
        "osm_enabled": False,  # OSM enrichment is not implemented; see the Segment 5 skip decision
        "osm_attribution": None,
        "dbe_version": __version__,
    }
    log.info("kept %s of %s segments (%s vertices)", len(roads), len(feats17), len(vertices))
    return ExtractResult(roads, vertices, metadata)
