# MRWA GeoJSON fixtures — Curtin envelope

Recorded: 2026-09-22, via `uv run --no-sync python scripts/record_fixtures.py`.

## Radius deviation from the plan (layer 12 was empty at 1.5 km)

The plan's default `RADIUS_M = 1500.0` produced **0 features for layer 12** (Pavement and Surfacing
State) around Curtin's Design building (`LAT, LON = -32.0018629, 115.8924599`). This was confirmed live
with `returnCountOnly=true` (not just an empty page: `count = 0`), so per task S0.T3 Step 2's documented
contingency, `RADIUS_M` was raised to **2500.0** and the whole script re-run (all four layers share one
envelope). At 2500 m, layer 12 returns 113 features.

Because the plan only names `*_curtin1500.geojson` files and does not authorize keeping that name for a
different radius, fixture files are named `layer{17,12,16,8}_curtin2500.geojson` instead. The envelope
constant documented below is accordingly `CURTIN_2500_ENVELOPE`, not the `CURTIN_1500_ENVELOPE` name
given in the task's Interfaces block — any later task/conftest referencing the original name must be
updated to match.

## `CURTIN_2500_ENVELOPE`

`(xmin, ymin, xmax, ymax)`, WGS84 lon/lat, as sent on the wire (`f"{v:.7f}"`, the exact string each
request's `geometry` parameter used):

```
(115.8659776, -32.0243207, 115.9189422, -31.9794051)
```

Unrounded floats printed by the script (`ENVELOPE = ...`), for reference:

```
(115.86597763352387, -32.024320679374775, 115.91894216647614, -31.979405120625223)
```

Centre: `LAT, LON = -32.0018629, 115.8924599` (Curtin's Design building). `RADIUS_M = 2500.0`.

## Feature counts and file sizes

Paged fetch counts (`len(features)`) were cross-checked against a separate `returnCountOnly=true` query
against the same envelope — all four matched exactly, confirming no page was silently truncated below
`resultRecordCount`.

| Layer | Name | Features | `returnCountOnly` | File | Bytes |
|---|---|---|---|---|---|
| 17 | Road Network | 1850 | 1850 | `layer17_curtin2500.geojson` | 1,657,997 |
| 12 | Pavement and Surfacing State | 113 | 113 | `layer12_curtin2500.geojson` | 132,469 |
| 16 | Road Hierarchy | 659 | 659 | `layer16_curtin2500.geojson` | 577,273 |
| 8 | Legal Speed Limit | 580 | 580 | `layer8_curtin2500.geojson` | 543,483 |

All four files are well under the 5 MB fixture limit; compact `json.dumps` separators were not needed.

## Sanity checks

- Every feature in every layer has `geometry.type == "LineString"` (no `MultiLineString`, no
  `geometry: null`) across all 1850 + 113 + 659 + 580 = 3202 features.
- Join keys `ROAD, CWY, START_SLK, END_SLK` are present in `properties` on every layer.
- Layer 16 carries `ROAD_HIERARCHY`; layer 8 carries `SPEED_LIMIT` (confirming S0.T2's findings).
- The `GEOLOC.STLength()` property key (noted as unusual in `docs/task_docs/source_verification.md`)
  survives GeoJSON serialization and is present on every feature in every layer.
- Layer 12 carries the pavement/surface width fields (`TOTAL_PAVE_WIDTH`, `TOTAL_SEAL_WIDTH`,
  `TRAFFICABLE_PAVE_WIDTH`, `TRAFFICABLE_SURF_WIDTH`, `TRAFFICABLE_WIDTH_DIFF`, plus shoulder/kerb
  fields) — the likely source for `WIDTH_M` / `WIDTH_SOURCE=mrwa_pavement`.

Fixtures are recorded snapshots of CC BY 4.0 Main Roads WA data; regenerate with
`uv run python scripts/record_fixtures.py`.
