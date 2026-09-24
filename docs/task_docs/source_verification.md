# Source verification — MRWA `RoadAssets_DataPortal/MapServer`

**Date:** 2026-09-22 (task S0.T2, Sonnet implementer)
**Host used:** `gisservices.mainroads.wa.gov.au` (per plan §1; `mrgis.` was not tried — plan records
connection resets on that host from an earlier session).
**Command:** `uv run --no-sync python scripts/verify_layers.py` (network required; live results, not
mocked). Raw metadata saved to `tests/fixtures/layer{17,12,16,8}_metadata.json`.

## Layer summary

| Layer | Name (confirmed) | geometryType | wkid | maxRecordCount | supportsPagination | supportsOrderBy | supportsStatistics |
|---|---|---|---|---|---|---|---|
| 17 | Road Network | `esriGeometryPolyline` | 4283 | 2000 | `True` | `True` | `True` |
| 12 | Pavement and Surfacing State | `esriGeometryPolyline` | 4283 | 2000 | `True` | `True` | `True` |
| 16 | Road Hierarchy | `esriGeometryPolyline` | 4283 | 2000 | `True` | `True` | `True` |
| 8 | Legal Speed Limit | `esriGeometryPolyline` | 4283 | 2000 | `True` | `True` | `True` |

All four `meta["name"]` values matched the `LAYERS` dict in `scripts/verify_layers.py` exactly — no
`!! NAME MISMATCH` was printed for any layer. `wkid=4283` is GDA94, consistent with plan §1's note that
the source datum is GDA94 and differs from WGS84 by ≤ ~1.5 m; the extraction pipeline must still request
`outSR=4326` to get WGS84 lon/lat on the wire.

## Join keys present on every layer

`ROAD, CWY, START_SLK, END_SLK` are present as fields on all four layers (17, 12, 16, 8), confirmed by
direct lookup in each layer's field list. This is what makes the SLK-overlap join in S3.T1/S3.T2 possible.

## Confirmed attribute field names

```
HIERARCHY_FIELD = "ROAD_HIERARCHY"   # layer 16, type esriFieldTypeString, length 30
SPEED_FIELD     = "SPEED_LIMIT"      # layer 8,  type esriFieldTypeString, length 80
```

Both match the plan's `Likely` guesses (plan lines 146–147) exactly — **no rename needed**. Note for
S3.T2: `SPEED_LIMIT` is `esriFieldTypeString`, not numeric — expect free-text values (e.g. possible units
or qualifiers) rather than a clean integer km/h; do not assume it parses directly with `int()`.

## Layer 17 field count — deviation from the plan's script comment

The plan's script docstring/expected output says "layer 17 lists the 25 known fields (with
`GEOLOC.STLength()`)". The live response actually returns **26** fields for layer 17:

```
ROAD, ROAD_NAME, COMMON_USAGE_NAME, START_SLK, END_SLK, CWY, START_TRUE_DIST, END_TRUE_DIST,
NETWORK_TYPE, RA_NO, RA_NAME, LG_NO, LG_NAME, START_NODE_NO, START_NODE_NAME, END_NODE_NO,
END_NODE_NAME, DATUM_NE_ID, NM_BEGIN_MP, NM_END_MP, NETWORK_ELEMENT, ROUTE_NE_ID, GEOLOC, OBJECTID,
GEOLOC.STLength(), GlobalID
```

The extra field versus the plan's 25-name `ORIGINAL_COLUMNS` list (orchestrator_plan.md §3.3, line 190)
is `GEOLOC` — confirmed `"type": "esriFieldTypeGeometry"` in `tests/fixtures/layer17_metadata.json`, i.e.
the raw shape/geometry field, distinct from the computed pseudo-field `GEOLOC.STLength()` (confirmed
`"type": "esriFieldTypeDouble"`). `ORIGINAL_COLUMNS` already excludes `GEOLOC` (it only lists
`GEOLOCSTLength`), which is correct: `GEOLOC` is the geometry column, not tabular data, and should stay
excluded when S4.T1 builds `schema.py`.

Two more facts for S4.T1: (1) the live API names the field `GEOLOC.STLength()` (with the dot and
parens), not `GEOLOCSTLength` as written in §3.3 — S4.T1 must map the API name to the sanitized output
column name, not assume they match. (2) the API's field **order** is not `ORIGINAL_COLUMNS`' order —
live order ends `..., ROUTE_NE_ID, GEOLOC, OBJECTID, GEOLOC.STLength(), GlobalID`, whereas §3.3 fixes the
order as `..., ROUTE_NE_ID, OBJECTID, GlobalID, GEOLOCSTLength`. S4.T1/S4.T2 must explicitly reorder
output columns to the schema's fixed order rather than passing the API's field order through.

## Fixture files produced

| File | Size |
|---|---|
| `tests/fixtures/layer17_metadata.json` | 22,792 bytes (~23 KB) |
| `tests/fixtures/layer12_metadata.json` | 17,163 bytes (~17 KB) |
| `tests/fixtures/layer16_metadata.json` | 22,103 bytes (~22 KB) |
| `tests/fixtures/layer8_metadata.json` | 16,289 bytes (~16 KB) |

All well under the 5 MB fixture limit.
