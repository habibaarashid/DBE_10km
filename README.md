# RoadMapper

Extracts every road segment inside a circle — a centre point and a radius in kilometres — from Main
Roads Western Australia (MRWA) open data, with full lat/lon geometry and road attributes (width where
it exists). Output is written first as CSV, then converted to a single XLSX workbook. Data source: the
MRWA ArcGIS `RoadAssets_DataPortal` MapServer (Road Network, Pavement and Surfacing, Road Hierarchy and
Legal Speed Limit layers) — no Google Maps APIs are used.

## Quick start

```bash
uv sync   # creates .venv and installs dependencies (Python >= 3.11; uv installs 3.12 if needed)

uv run roadmapper extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km
```

This is the project's reference run: a 10 km circle around Curtin University. It queries the live MRWA
service, took about 3 minutes wall clock (185 s) end to end, and writes `roads.csv`, `roads_vertices.csv`,
`metadata.json`, `roads.xlsx` and a map, `qa_plot.png`, into `output/curtin_10km/`. The raw API responses are cached under
`output/curtin_10km/cache/`, so a re-run with the same `--out` (or the same `--cache-dir`) is served from
disk and finishes in well under a minute — no network calls are repeated for pages already fetched.

**The cache never expires.** A re-run into the same `--out` is an offline replay of the pages fetched the first
time, and it stamps a *new* `EXTRACTED_AT_UTC` on every row, so the timestamp says when the file was written, not
when the data was fetched. For current data, delete `cache/` or point `--cache-dir` at an empty directory.

## Usage

```
roadmapper extract --lat LAT --lon LON --radius-km KM --out DIR [--cache-dir DIR] [--no-xlsx] [--no-plot] [--osm] [-v]
```

| Flag | Meaning |
|---|---|
| `--lat` | centre latitude, decimal degrees (required) |
| `--lon` | centre longitude, decimal degrees (required) |
| `--radius-km` | circle radius in kilometres, must be > 0 (required) |
| `--out` | output directory, created if missing (default `output/run`) |
| `--cache-dir` | raw API page cache directory (default `<out>/cache`) |
| `--no-xlsx` | write the CSVs and metadata only, skip building `roads.xlsx`. Any `roads.xlsx` left in `--out` by an earlier run is removed, since it would describe a different run. |
| `--no-plot` | skip the map, `qa_plot.png`. The map is written by default, including when `--no-xlsx` is used. Any `qa_plot.png` left in `--out` by an earlier run is removed. |
| `--osm` | **not implemented.** OpenStreetMap enrichment was built out as a design, then deliberately skipped (see "Width", below). Passing this flag makes `extract` refuse immediately with an explanatory message and exit code 1 — it does not run a degraded extraction or silently do nothing. |
| `-v` / `--verbose` | debug-level logging to stderr (default is INFO) |

```
roadmapper to-xlsx --roads FILE --vertices FILE --metadata FILE --out FILE
```

| Flag | Meaning |
|---|---|
| `--roads` | path to a `roads.csv` produced by `extract` (required) |
| `--vertices` | path to the matching `roads_vertices.csv` (required) |
| `--metadata` | path to the matching `metadata.json` (required) |
| `--out` | path to write the `.xlsx` workbook to (required) |
| `-v` / `--verbose` | debug-level logging to stderr |

`to-xlsx` lets you rebuild the workbook from the CSVs alone (e.g. after hand-editing a cell, or if
`--no-xlsx` was used originally) without re-querying MRWA.

## What you get

From the reference Curtin 10 km run (`output/curtin_10km/`):

| File | Size | Content |
|---|---|---|
| `roads.csv` | 15.4 MB (16,165,303 bytes) | 21,645 road segments, one row per segment, columns = the 53-column schema below |
| `roads_vertices.csv` | 7.6 MB (7,982,007 bytes) | 85,122 vertices, one row per vertex of every segment's geometry |
| `metadata.json` | 1.4 KB (1,445 bytes) | run parameters, envelope, counts, data source, licence, datum note |
| `roads.xlsx` | 10.5 MB (11,049,054 bytes) | the three sheets below, built by reading the two CSVs back in (the workbook is built by reading the CSVs back, not from a separate in-memory export: every text cell is identical, and every numeric cell agrees to within 1e-14 relative — the workbook writer keeps 16 significant digits, so a 17-digit coordinate cannot round-trip exactly) |
| `qa_plot.png` | 1.2 MB | a map of every segment, coloured by road type, with the query circle drawn dashed. Built by reading `roads.csv` and `metadata.json` back from disk, so it shows what was actually written. The road-type colours were checked with a colour-blindness validator for a map, where any road type can sit beside any other; see the comment at the top of `roadmapper/plot.py`. |

**On a successful run, every file in `--out` belongs to that run.** That is the rule, and three things enforce it.
The map is drawn after the CSVs and metadata are safely on disk, and it is best-effort: if drawing fails for any
reason, the run still succeeds and exits 0 with every CSV intact, logs a warning saying no map was written, and
removes any `qa_plot.png` left from an earlier run. Skipping the map or the workbook with `--no-plot` or `--no-xlsx`
likewise removes a leftover copy, logging that it did, so re-using an output directory never leaves a map or
workbook of a different area sitting beside new CSVs. Both files can be rebuilt from the CSVs, so nothing is lost.
If a leftover cannot be removed, the run still succeeds and logs a warning naming the file.

**A run that fails can leave files that do not describe it.** The rule above holds only when `extract` exits 0. When it exits 1 the output directory is not tidied, and three cases are worth knowing: if the workbook step fails before writing — for example because `roads.xlsx` is open in Excel — the *previous* run's workbook stays beside the new CSVs; if it fails part-way, a *partial* workbook from this run can be left, readable but missing its later sheets, because the spreadsheet library saves on the way out even on an error; and if no roads are found, the previous run's files all survive untouched. In every case the command exits 1 and prints an error, so the failure is visible — but **after a failed run, trust the CSVs' timestamps, not the directory's contents.** Re-running successfully, or `to-xlsx` from the CSVs, restores a consistent set.

`roads.xlsx` sheets:

| Sheet | Rows of data (excl. header) |
|---|---|
| `roads` | 21,645 |
| `vertices` | 85,122 |
| `metadata` | 25 |

The vertices sheet is split into `vertices_2`, `vertices_3`… once a run passes Excel's 1,048,576-row
limit; the `roads` sheet is not (see "Known limits").

## Column dictionary

Column names and order come from `roadmapper/schema.py`, the single source of truth — this list mirrors
it exactly. `roads.csv` / the `roads` sheet has 53 columns in five groups; `roads_vertices.csv` / the
`vertices` sheet has the 9 columns listed last.

### Original Main Roads columns (25) — as served by the source, unchanged

These are exactly the 25 columns of MRWA's own Road Network layer (layer 17), same names, same order,
same values — except `OBJECTID` and `GlobalID`, which ArcGIS regenerates every time the layer is republished: in the
reference run every row differs from the user's statewide export on those two columns and agrees on the other 23
(checked row by row in the final review). Join across exports on `NETWORK_ELEMENT`, never on `OBJECTID`. `START_SLK`/`END_SLK`/`START_TRUE_DIST`/`END_TRUE_DIST` use MRWA's linear-referencing
convention (SLK = "straight-line kilometrage" measured along the road); this tool does not compute or
modify them.

| Column | Meaning | Unit / type |
|---|---|---|
| `ROAD` | MRWA road code (e.g. `H001`), the road identifier used throughout MRWA data | code |
| `ROAD_NAME` | gazetted road name | text |
| `COMMON_USAGE_NAME` | the name the road is commonly known by, when it differs from `ROAD_NAME` (e.g. a highway that carries a different street name through a suburb) | text |
| `START_SLK` | straight-line kilometrage at the segment's start | km |
| `END_SLK` | straight-line kilometrage at the segment's end | km |
| `CWY` | carriageway: `Single`, `Left` or `Right` | category |
| `START_TRUE_DIST` | true distance (SLK adjusted for gazettal discontinuities) at the segment's start | km |
| `END_TRUE_DIST` | true distance at the segment's end | km |
| `NETWORK_TYPE` | road classification: `State Road`, `Local Road`, `Crossover`, `Main Roads Controlled Path`, `Proposed Road`, `Miscellaneous Road` | category |
| `RA_NO` | region authority number | code |
| `RA_NAME` | region authority name (e.g. `Metropolitan`); blank on a small number of rows — see "Validation" | text |
| `LG_NO` | local government area number | code |
| `LG_NAME` | local government area name | text |
| `START_NODE_NO` | network node id at the segment's start | id |
| `START_NODE_NAME` | name of the node/intersection at the segment's start | text |
| `END_NODE_NO` | network node id at the segment's end | id |
| `END_NODE_NAME` | name of the node/intersection at the segment's end | text |
| `DATUM_NE_ID` | network element id of the linear-referencing datum this segment's SLK is measured against | id |
| `NM_BEGIN_MP` | network model begin measure point; an MRWA internal linear-referencing value, not independently documented by the source — treat as opaque, not as a distance to compute from | numeric, source-defined |
| `NM_END_MP` | network model end measure point, same caveat as `NM_BEGIN_MP` | numeric, source-defined |
| `NETWORK_ELEMENT` | unique id of this road network element (this is the join key used against the user's own statewide export — see "Validation") | id |
| `ROUTE_NE_ID` | network element id of the route this segment belongs to | id |
| `OBJECTID` | ArcGIS feature id (MRWA's internal `OBJECT_ID` alias); used by this tool for paging and de-duplication | id |
| `GlobalID` | ArcGIS global unique identifier (GUID) | id |
| `GEOLOCSTLength` | geometry length as computed and stored by the source itself (the source field is literally named `GEOLOC.STLength()`; this tool renames it to a valid CSV/XLSX header). **Not metres:** it is the planar length in the source's geographic coordinate system, so its unit is decimal degrees — about 1e-5 of `LENGTH_M` (which is metres, computed independently in a local metric projection). Your own statewide export carries the same values. Use `LENGTH_M` for a length | decimal degrees, source-computed |

### Geometry columns (9) — added by this tool

| Column | Meaning | Unit |
|---|---|---|
| `START_LAT` | latitude of the segment's first vertex | WGS84 degrees |
| `START_LON` | longitude of the segment's first vertex | WGS84 degrees |
| `END_LAT` | latitude of the segment's last vertex | WGS84 degrees |
| `END_LON` | longitude of the segment's last vertex | WGS84 degrees |
| `VERTEX_COUNT` | number of vertices in the segment's geometry, summed across all parts | count |
| `LENGTH_M` | length of the segment's geometry, computed in a local azimuthal-equidistant projection centred on the query point | metres |
| `DIST_TO_CENTRE_M` | shortest distance from the segment's geometry to the query centre point | metres |
| `INSIDE_FRACTION` | share of the segment's length that lies inside the circle (see "How the circle works") | 0–1 |
| `GEOMETRY_WKT` | the full geometry as Well-Known Text (`LINESTRING`/`MULTILINESTRING`), longitude-then-latitude order | WGS84, text |

### Enrichment columns (12) — joined from MRWA layers 12, 16, 8

Joined to each Road Network segment by linear referencing (road + carriageway + SLK overlap) against
MRWA's Pavement and Surfacing (layer 12), Road Hierarchy (layer 16) and Legal Speed Limit (layer 8)
layers. Where a segment overlaps more than one source span, the width/shoulder columns are an
overlap-length-weighted mean and the categorical columns (`NO_OF_LANES`, `KERB_L`, `KERB_R`,
`ROAD_HIERARCHY`, `SPEED_LIMIT`) take the value of the span with the largest overlap ("dominant value" —
see "Known limits" for the tie-break rule).

| Column | Meaning | Unit |
|---|---|---|
| `ROAD_HIERARCHY` | road hierarchy classification (e.g. `Distributor A`, `Access Road`) | category |
| `SPEED_LIMIT` | legal speed limit **as a string with embedded units** (e.g. `"60km/h"`, or free text like `"50km/h applies in built up areas or 110km/h outside built up areas"`) — never cast this to a number without parsing it first | text |
| `TOTAL_PAVE_WIDTH_M` | overlap-weighted mean total pavement width (State Roads only — see "Width") | metres |
| `TOTAL_SEAL_WIDTH_M` | overlap-weighted mean total seal width; this is also the value copied into `WIDTH_M` when a match exists | metres |
| `TRAFFICABLE_SURF_WIDTH_M` | overlap-weighted mean trafficable surface width | metres |
| `NO_OF_LANES` | number of lanes, dominant value | count |
| `SEALED_SHOULDER_L_M` | overlap-weighted mean sealed shoulder width, left side | metres |
| `SEALED_SHOULDER_R_M` | overlap-weighted mean sealed shoulder width, right side | metres |
| `KERB_L` | kerb present, left side, dominant value | category (source-coded) |
| `KERB_R` | kerb present, right side, dominant value | category (source-coded) |
| `WIDTH_M` | this tool's headline width figure: `round(TOTAL_SEAL_WIDTH_M, 2)` when a layer-12 match exists, else blank. **Never estimated** — see "Width" | metres |
| `WIDTH_SOURCE` | provenance of `WIDTH_M`: `mrwa_pavement` (measured) or `none` (blank) — those are the only two values `WIDTH_SOURCE` takes in this build, since `--osm` refuses — see "Width" | category |

### OpenStreetMap columns (5) — always blank in this build

OSM enrichment was specified in the project plan (Segment 5, as `roadmapper/osm_client.py` and
`roadmapper/osm_match.py`) but was never built — Segment 5 was skipped before either file was written,
on a measurement, not abandoned mid-implementation. See "Width" for why. All five columns are always
blank; the `--osm` flag that would have populated them refuses instead of running.

| Column | Meaning | Unit |
|---|---|---|
| `OSM_WAY_ID` | OpenStreetMap way id | id, always blank |
| `OSM_HIGHWAY` | OSM `highway` tag value | text, always blank |
| `OSM_LANES` | OSM `lanes` tag value | text, always blank |
| `OSM_MAXSPEED` | OSM `maxspeed` tag value | text, always blank |
| `OSM_SURFACE` | OSM `surface` tag value | text, always blank |

### Provenance columns (2)

| Column | Meaning | Unit |
|---|---|---|
| `DATA_SOURCE` | fixed string naming the MRWA layers this row was built from | text |
| `EXTRACTED_AT_UTC` | UTC timestamp of the extraction run that produced this row | ISO-8601 |

### Vertex columns (9) — `roads_vertices.csv` / the `vertices` sheet

One row per vertex of every segment's geometry, in served order. `OBJECTID` and `NETWORK_ELEMENT` are
foreign keys back to the matching row in `roads.csv`.

| Column | Meaning | Unit |
|---|---|---|
| `OBJECTID` | the parent segment's `OBJECTID` | id |
| `NETWORK_ELEMENT` | the parent segment's `NETWORK_ELEMENT` | id |
| `ROAD` | the parent segment's road code | code |
| `ROAD_NAME` | the parent segment's road name | text |
| `CWY` | the parent segment's carriageway | category |
| `PART` | part index within a `MultiLineString` geometry (`0` for the first or only part) | index |
| `SEQ` | vertex sequence number within its part, in served order | index |
| `LAT` | vertex latitude | WGS84 degrees |
| `LON` | vertex longitude | WGS84 degrees |

## Width — read this before using the data

**Only 1,202 of 21,645 rows (5.55%) carry a width.** This is not missing data or a bug — it is what
exists. Main Roads publishes measured pavement width (`TOTAL_SEAL_WIDTH`, layer 12) for **State Roads
only**. In the Curtin 10 km circle, all 4,172 distinct layer-12 pavement records (4,307 fetched, 135 of them paging
duplicates) are State Road — zero are Local Road. Every one of the 1,202 State Road rows in the output got a width (100% coverage of what exists),
and no Local Road can have one, because Main Roads does not measure or publish it for local roads.

**No width is ever estimated.** `WIDTH_M` is either a real measured value with `WIDTH_SOURCE =
mrwa_pavement`, or blank with `WIDTH_SOURCE = none`. There is no interpolation, no default, no fallback
guess.

**Where pavement records overlap each other, `WIDTH_M` is a blend.** Layer 12 occasionally holds two records
covering the same stretch of the same carriageway with different seal widths, and carries no date or status
field to choose between them; the overlap-weighted mean then blends both. In the reference run this happens on
4 of 1,202 width rows, all on Albany Hwy (`H001`) between SLK 1.27 and 1.49, where records of 9.8 m and
12.1–12.9 m overlap. Separately, the exact-carriageway preference can leave part of a segment uncovered by any
matched span (1 row, `H017` Right, 86% covered). Both are listed in `docs/task_docs/fable_review.md`.

**On a genuinely divided road, `WIDTH_M` can under-report.** When a `Single`-carriageway segment's only
matching pavement records are `Left` and `Right` spans (not `Single`), the join returns both and
`WIDTH_M` is their overlap-weighted mean — reporting roughly one carriageway's width rather than the
whole roadway. This is a deliberate choice (an average of two measured widths, not an invented figure)
and it occurred in **0 of 21,645 rows** in the 10 km production run.

**OpenStreetMap was measured as an alternative and rejected.** A live Overpass query over the same
circle found `width` on only 685 of 70,561 OSM ways (0.97%), and only 371 of those also carried a `name`
tag (matching OSM ways to MRWA roads needs both). Even a perfect match on all 371 candidates would have
closed under 2% of the 20,443-row width gap. OpenStreetMap is also licensed ODbL, whose share-alike
terms attach to any database derived from it, whereas Main Roads data alone is CC BY 4.0. OSM enrichment
was specified but never implemented — no `osm_client.py` or `osm_match.py` was written — and `--osm`
refuses immediately rather than running a half-finished enrichment.

**That trade-off is yours to make, not this tool's.** It was decided during the build without asking you.
If a few hundred more widths matter more to you than keeping the output under CC BY 4.0 alone, the
enrichment can still be built: the full specification remains in `docs/task_docs/orchestrator_plan.md`,
Segment 5. Expect widths on roughly 371 additional segments at best, and the ODbL obligations on the result.

**Every free statewide source has been checked, not just the obvious one.** Gate C examined all 33 Main
Roads open-data layers, not only the four this tool reads. Only layers 12, 13 and 26 carry any width field.
Layer 26 holds bridges and culverts as points. Layer 13 ("Pavement Detail") is a polyline layer with
per-lane widths and the same join keys as layer 12 — but it holds **zero** Local Road records statewide
across 45,993 features. So 5.55% is the ceiling for any single free statewide WA source, not a shortfall
in this tool. Individual councils may publish local-road widths for their own areas; that has not been
checked, and would mean one source per council rather than one for the state.

## The metadata sheet and `metadata.json`

Each run also records how it went. Most keys are self-explanatory; these need a note:

| Key | Meaning |
|---|---|
| `features_returned_layer17` | Raw features fetched, **including duplicates** — 28,142 for the Curtin run. This overstates the real count by about 4%; see the next two rows. |
| `duplicates_dropped` | Records the service returned twice while paging — 1,168. Paging a live spatial query does this; they are removed. |
| `segments_intersecting` | Rows actually written — 21,645. 28,142 − 1,168 = 26,974 distinct features in the bounding box; 5,329 fall outside the circle; 21,645 remain. |
| `enrich_duplicates_dropped` | The same duplicate removal applied to the width, hierarchy and speed layers — 622. |
| `features_layer12`, `features_layer16`, `features_layer8` | Raw features fetched for the enrichment layers, **including paging duplicates**: 4,307 / 10,312 / 9,576 for the Curtin run, of which 4,172 / 9,936 / 9,465 are distinct. |
| `skipped_no_geometry`, `skipped_bad_geometry` | Features dropped because their geometry was absent or malformed. Both 0 for the Curtin run. |
| `width_source_counts` | How many rows have a measured width (`mrwa_pavement`) and how many do not (`none`). |
| `osm_enabled` | Always `false`; OpenStreetMap enrichment is not implemented. |

## How the circle works

A segment is included in the output if its geometry comes within the radius of the centre point — an exact
distance test against the true circle — not only if it is fully contained. The geometry is kept **whole**, never clipped at the circle boundary, so segments visibly
overhang the edge of the circle in the output (confirmed in the QA plot). `INSIDE_FRACTION` reports the
share of the segment's length that actually lies inside the circle (0–1); most rows are exactly `1.0`.
`INSIDE_FRACTION` is measured against a 256-sided polygon inscribed in the circle, so a boundary-crossing segment
can lose up to about 0.75 m of counted length per crossing at 10 km (the worst under-report on the reference run
is 0.043), and a segment that only grazes the circle inside that 0.75 m sliver is included with `INSIDE_FRACTION = 0`. The first three reviews tested *inclusion* against that polygon
too and missed two streets 9,999.9 m from the centre; the final review changed inclusion to the exact distance.
On a segment whose geometry doubles back on itself, `INSIDE_FRACTION` can under-report the true inside
share — it is a reported column only, never used to decide inclusion, so this never drops a row.

## Coordinates

Coordinates are WGS84 longitude/latitude, as served by the source (`outSR=4326`). The source datum is
GDA94 (EPSG:4283); the two differ by at most about 1.5 m in Western Australia. `GEOMETRY_WKT` uses
longitude-then-latitude (x, y) order, matching the WKT standard, not the (lat, lon) order used in
conversation.

## Known limits

- **A large enough radius produces CSVs but no workbook.** `csv_to_xlsx` splits the `vertices` sheet
  into `vertices_2`, `vertices_3`… once it passes Excel's 1,048,576-row limit, but the `roads` sheet has
  no such split. A radius large enough to push `roads.csv` past that row count will finish the
  (expensive) extraction, write both CSVs successfully, then fail to produce `roads.xlsx`.
- **No measured maximum radius; expect memory to scale with area.** The whole pipeline runs in memory —
  `extract()` holds every feature, row and vertex, and the CSV→XLSX conversion alone peaked at 733 MB for the
  10 km run. Nothing beyond 10 km has been run. Road counts in built-up areas grow roughly with area, so budget
  about four times the memory (~3 GB) for 20 km and nine times for 30 km — an extrapolation from one data
  point, not a measurement. Nothing prevents a large run from being killed for memory before it finishes.
- **Ties in the dominant-value columns are not always deterministic.** When two enrichment spans overlap
  a segment equally, `dominant_value` breaks the tie by source ordering; in 13 of 21,643 rows in the
  first production run, the tie was actually broken by floating-point noise between two values that should
  have been equal (e.g. a difference on the order of `1e-17`). This affects `NO_OF_LANES` and
  `SPEED_LIMIT`/`ROAD_HIERARCHY`-type advisory columns only — `WIDTH_M` is a weighted mean, which is
  order-independent, so it is never affected.

## Data sources and licence

- **Main Roads Western Australia Open Data** — `RoadAssets_DataPortal` MapServer, four layers:
  - **17 — Road Network** (geometry and the 25 original columns)
  - **12 — Pavement and Surfacing State** (width, lanes, shoulders, kerb — State Roads only)
  - **16 — Road Hierarchy** (`ROAD_HIERARCHY`)
  - **8 — Legal Speed Limit** (`SPEED_LIMIT`)
- **Licence:** Creative Commons Attribution 4.0 (CC BY 4.0). Attribution: **© Main Roads Western
  Australia.**
- **No Google Maps API is used.** Google's terms of service forbid bulk export of their map data, and
  Google publishes no road width data at all — both requirements this tool has, so Google was never a
  viable source regardless of cost.
- OpenStreetMap is **not** a data source in this build (see "Width"); if it were, it would require
  attribution to © OpenStreetMap contributors under the ODbL 1.0 licence.

## Validation

`tests/test_reconcile_csv.py` compares `output/curtin_10km/roads.csv` against a statewide CSV export the
user supplied independently (`data/Road_Network - Road_Network.csv`, validation-only — never read at
runtime, and the test skips entirely if either file is absent). Three checks:

1. The first 25 columns of `roads.csv` match `schema.ORIGINAL_COLUMNS` and the provided CSV's header,
   exactly and in order.
2. Every distinct `NETWORK_ELEMENT` id extracted must appear in the statewide export, at a ratio of at
   least 0.99. **Last observed result: 21,560 of 21,560 distinct extracted ids matched (ratio 1.0000)** —
   every road this tool extracted is a road the user's own export already knew about.
3. No row's `RA_NAME` is a region other than `Metropolitan` (blank is accepted — 2 of 21,645 rows have a
   genuine gap in the source data, not a foreign region leaking in).

## Development

```bash
uv run --no-sync pytest -q              # offline tests (network tests excluded by default)
uv run --no-sync pytest -m network -q   # opt-in live smoke test against the real MRWA service
uv run --no-sync ruff check .           # lint

# Regenerate the committed test fixtures from the live service (~2.5 km box at Curtin):
uv run --no-sync python scripts/record_fixtures.py

# Re-render the map for an existing output directory, e.g. after changing the styling in
# roadmapper/plot.py. (`extract` already writes it automatically; this is only for re-drawing.)
uv run --no-sync python scripts/qa_plot.py --out-dir output/curtin_10km
```
