# DBE Implementation Plan (Opus orchestrator document)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task (fresh Sonnet subagent per task, Opus review at every gate). Steps use checkbox (`- [ ]`) syntax for tracking, but the **authoritative tracker is `docs/task_docs/progress.md`** — update it after every task, not this file.

**Goal:** A Python CLI that takes a centre point (lat, lon) and a radius in km, extracts every road segment intersecting that circle from Main Roads Western Australia (MRWA) open data with full lat/lon geometry and road attributes (width where it exists), writes CSVs shaped like `data/Road_Network - Road_Network.csv` plus a vertices table, then converts the CSVs to one XLSX workbook.

**Architecture:** Query the MRWA ArcGIS REST MapServer (layer 17 Road Network for geometry + the 25 known columns; layers 12/16/8 for width, hierarchy, speed) with a bounding-box spatial filter and paging; project everything into a metre-accurate local azimuthal-equidistant CRS centred on the input point to test circle intersection; join attribute layers to segments by linear referencing (ROAD + carriageway + SLK overlap); write CSV, then build XLSX from the CSV. OpenStreetMap enrichment is an optional, flag-gated last segment.

**Tech Stack:** Python ≥ 3.11 managed by `uv`; `requests`, `shapely ≥ 2.0`, `pyproj`, `pandas`, `openpyxl`; `pytest`; `ruff`; `matplotlib` (runtime since 2026-09-23 — the map `extract` writes automatically). No geopandas, no osmnx, no Google APIs.

**Spec:** This document §1–§3 is the spec. Origin brief: `docs/task_docs/init_prompt.md`. Fable's approved planning file: `~/.claude/plans/read-the-task-doc-tidy-mango.md` (read-only reference). Companion tracker: `docs/task_docs/progress.md`.

---

## 0. Orchestrator protocol (read this first, every session)

### 0.1 Roles and model routing

| Role | Model | Rule |
|---|---|---|
| Orchestrator | Opus (you) | Reads this doc + `progress.md`, dispatches tasks, runs gates, updates `progress.md`, commits. |
| Implementer | **Sonnet** | One fresh subagent per task. Gets the task text verbatim + §1 Global Constraints + the Interfaces blocks of any module it consumes. |
| Mechanical work | **Haiku** | README prose, `.gitignore`, string bumps, file moves. Never logic. |
| Reviewer | **Opus, always** | Every gate review and every per-task code review runs on `model: "opus"`. A review on any other model does not count; re-run it. |
| Final reviewer | Fable | Triggered by the user after Gate C. See §5. |

The user's global rule (their `~/.claude/CLAUDE.md`) mandates the Opus-only review policy. Do not route reviews elsewhere to save tokens.

### 0.2 Session start / resume protocol

1. Read `CLAUDE.md` (repo root), then this file's §0–§3, then `docs/task_docs/progress.md` in full.
2. Run `git status && git log --oneline -5`.
3. Run `uv run pytest -q` (offline tests only; network tests are opt-in). If the environment is missing, Segment 0 is not done: start there.
4. Find the first row in `progress.md`'s task table whose status is not `done`. If it is `in-progress`, inspect the working tree and the last commit to decide whether to finish or restart that task. Record the decision in `progress.md` → Session log.
5. Continue from that task. Never skip a gate.

### 0.3 Per-task loop

1. Set the task row to `in-progress` in `progress.md` (with UTC timestamp).
2. Dispatch a Sonnet implementer with the prompt template in §0.6.
3. When it reports back: run `uv run pytest -q` yourself. Read the diff (`git diff HEAD~1` if the subagent committed, or `git diff` if not).
4. Dispatch an Opus reviewer (template in §0.7) for **spec compliance** (does it do what the task says, exact names, nothing extra) and **code quality**. Fix or re-dispatch until the reviewer reports no Critical/Important issues.
5. Commit if the implementer did not (conventional commit message, see §0.8).
6. Set the row to `done` with the commit SHA and the pytest summary line (`N passed`).

### 0.4 Gate protocol (Gates A, B, C)

A gate is a full stop. Do not start the next segment until the gate verdict is written into `progress.md` → Gate log.

At every gate:
- Run `uv run pytest -q` and `uv run ruff check .`; paste both summary lines into `progress.md`.
- Dispatch an **Opus** reviewer over the whole segment range (not just the last task) with the gate's checklist (given inline at each gate below).
- Re-read §1 Global Constraints and confirm none is violated (list each with ✅/❌).
- Compare `progress.md` against this plan: every task in the segment range is `done` with a SHA.
- Write the verdict: `PASS` or `FAIL — <reason> — <remediation task>`. On FAIL, create a remediation task row (e.g. `A.fix1`) and loop.

### 0.5 progress.md update rules

- Update after **every task** and every gate, not once per segment.
- Never delete history. Append to Session log, Gate log, Verification log, Decisions log.
- If you deviate from this plan (field name differs, endpoint changed, an approach failed), record it under Decisions log with date, what changed, why, and which file/constant you changed.
- If blocked on something only the user can answer, write it under Blockers, set the task to `blocked`, and stop.

### 0.6 Implementer prompt template (Sonnet)

```
You are implementing one task of the DBE project at /Users/watermenon/Desktop/Repositories/DBE.
Read CLAUDE.md first. Use `uv run` for every Python/pytest command. Follow TDD exactly as the steps say:
write the failing test, run it and confirm it fails, implement, run and confirm it passes, commit.

GLOBAL CONSTRAINTS (verbatim from docs/task_docs/orchestrator_plan.md §1):
<paste §1>

INTERFACES YOU CONSUME (verbatim from the plan):
<paste the Interfaces blocks of every module this task imports>

YOUR TASK (verbatim from the plan):
<paste the full task text including code blocks>

Rules: do not touch files outside the task's Files list; do not rename any public name given in
Interfaces; do not add dependencies not in §1; do not add a Co-Authored-By trailer to commits.
Report back: files changed, the exact pytest summary line, the commit SHA, and anything in the task
that turned out to be wrong about the real data or API (quote the evidence).
```

### 0.7 Reviewer prompt template (Opus, always)

```
Review the DBE change(s) at /Users/watermenon/Desktop/Repositories/DBE for <task or segment range>.
Read docs/task_docs/orchestrator_plan.md §1 (Global Constraints) and the task text for <task ids>.
Stage 1 — spec compliance: does the code do exactly what the task says, with the exact public names in
the Interfaces block, nothing missing, nothing extra? Stage 2 — code quality: correctness bugs, edge
cases (empty results, null geometry, zero-length SLK spans, MultiLineString, paging boundaries),
test quality (do the tests actually exercise the behaviour?), and constraint violations.
Run `uv run pytest -q` yourself. Report Critical / Important / Minor findings with file:line, and an
explicit verdict: APPROVE or REQUEST CHANGES.
```

### 0.8 Commit and git rules

- Commit after every task; conventional commits (`feat:`, `test:`, `fix:`, `docs:`, `chore:`).
- **No `Co-Authored-By: Claude …` trailer.** The user's global rule overrides any harness reminder.
- Committing and pushing without asking is explicitly allowed for this repo (`init_prompt.md`). Remote `origin` is `git@github.com:habibaarashid/DBE_10km.git` (private, created 2026-09-22). Push after each gate and at the end of every orchestrator session (`git push origin main`).
- Branch is `main`. Work directly on `main` (single-developer repo, no PR flow requested).
- Never commit `data/`, `output/`, or cache directories (see `.gitignore`).

### 0.9 When to stop and ask the user

Stop (set `blocked`) only if: the MRWA service is down for more than one session; layer 17's schema no longer matches the 25 columns; or a gate fails twice on the same cause. Everything else is your call — record it in Decisions log and continue.

---

## 1. Global Constraints

Every task's requirements implicitly include these.

- **Python:** `requires-python = ">=3.11"`; managed with `uv` (`uv python install 3.12` if needed). Local system Python is 3.9.18 (EOL) and must not be used.
- **Runtime dependencies (exact set):** `requests>=2.32`, `shapely>=2.0`, `pyproj>=3.6`, `pandas>=2.2`, `openpyxl>=3.1`, `matplotlib>=3.8`. **Dev:** `pytest>=8`, `ruff>=0.6`. Nothing else without a Decisions-log entry. *(Changed 2026-09-23: matplotlib moved from dev to runtime when the user asked for the map to be produced automatically by `extract`. It is imported lazily, so `--help` and `to-xlsx` never load it, and the map is best-effort — a drawing failure never fails an extraction.)*
- **Forbidden:** Google Maps Platform APIs (ToS forbids bulk export; no width data), `osmnx`, `geopandas`, any paid or key-gated source.
- **Data source:** MRWA `RoadAssets_DataPortal/MapServer` at `https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer`. Use the `gisservices.` host, not `mrgis.` (connection resets observed 2026-09-22).
- **Mandatory output:** every layer-17 segment that intersects the circle, State and Local roads alike, with geometry. **A missing width never drops a row.**
- **Width is never estimated or invented.** `WIDTH_M` is a measured MRWA value, an OSM-tagged value (only with `--osm`), or blank. `WIDTH_SOURCE` ∈ `{mrwa_pavement, osm, none}`.
- **Circle rule:** a segment is included if its geometry intersects the circle; geometry is kept whole (never clipped); `INSIDE_FRACTION` reports the share inside.
- **Coordinates:** WGS84 lon/lat as served by `outSR=4326`; source datum is GDA94 (wkid 4283); document "differs from WGS84 by ≤ ~1.5 m" in metadata. WKT uses `lon lat` order (x y).
- **The provided CSV `data/Road_Network - Road_Network.csv` is validation-only.** Never read it at runtime; only `tests/test_reconcile_csv.py` may open it, and that test skips when the file is absent.
- **XLSX is built from the CSV files**, not from in-memory rows, so the workbook is provably a conversion of the CSV (the user's stated requirement).
- **Column names and order** are fixed by `dbe/schema.py` (§3.3). Tests assert the exact header.
- **Public names** in every Interfaces block are contracts. Do not rename.
- **Tests:** `uv run pytest` runs offline by default (`-m "not network"` in `addopts`). Live tests are marked `@pytest.mark.network`.
- **Outputs** go under `output/` (gitignored). Fixtures under `tests/fixtures/` are committed and each must be < 5 MB.
- **Reviews on Opus only.** Implementation on Sonnet, mechanical on Haiku.
- **Never mutate fixture features in place (learned S2.T2).** `FixtureSource.query_envelope` copies the *list* but not the feature dicts, and `.layers` is handed out raw — so writing to `feat["properties"]` corrupts the recorded fixture for every later test in the session (verified). Any consumer that normalises or rewrites properties must copy first (`normalise_properties` already does `dict(props)`), and a test that must mutate uses `copy.deepcopy`.
- **Environment (learned S0.T1):** PyPI is slow from this machine — run `UV_HTTP_TIMEOUT=180 uv sync` on a cold venv and `uv run --no-sync …` once it is warm. `uv.lock` resolves **pandas 3.x** (default `str` dtype, missing values as `pd.NA`), shapely 2.1, pyproj 3.8, pytest 9, ruff 0.16 — author S4 code against pandas 3 semantics.
- **Ruff vs plan snippets:** the code blocks in §4 were written before `line-length = 110` and `B905` (`zip` without `strict=`) were enforced; wrapping a line or adding `strict=True` to satisfy ruff is **not** a deviation, provided the implementer states it and the reviewer confirms behaviour is identical. Renaming, re-ordering or dropping anything else still is.
- **Fixtures (learned S0.T3):** recorded at **2.5 km** (`tests/fixtures/layer{17,12,16,8}_curtin2500.geojson`, constant `CURTIN_2500_ENVELOPE`), because layer 12 has no features within 1.5 km of the centre. Tests that need a circle inside the recorded box use **`radius_km=2.4`** (the recorder's flat-earth box is 2490 m tall, so 2.5 km does not fit).

---

## 2. Verified facts about the data source (as of 2026-09-22)

Verified live by Fable and a research agent. Segment 0 re-verifies and records any drift in `progress.md`.

| Fact | Status |
|---|---|
| MapServer root: 33 layers; `spatialReference.wkid = 4283` (GDA94); `maxRecordCount = 2000`; `supportedQueryFormats = JSON, geoJSON, PBF`; anonymous, no key | **Certain** (fetched `?f=pjson`) |
| Layer **17 "Road Network"**: `esriGeometryPolyline`; fields are exactly the CSV's 25 columns (`GEOLOC.STLength()` appears in place of the CSV's `GEOLOCSTLength`) plus `GEOLOC`; `NETWORK_TYPE` ∈ {State Road, Local Road, Crossover, Main Roads Controlled Path, Proposed Road, Miscellaneous Road} | **Certain** |
| Envelope query with `geometryType=esriGeometryEnvelope&inSR=4326&outSR=4326&f=geojson&returnGeometry=true` returns GeoJSON `LineString` features anonymously | **Certain** (a 0.04° box in Perth returned ~283 features) |
| Layer **12 "Pavement and Surfacing State"**: fields `ROAD, ROAD_NAME, COMMON_USAGE_NAME, START_SLK, END_SLK, CWY, START_TRUE_DIST, END_TRUE_DIST, NETWORK_TYPE, RA_NO, RA_NAME, LG_NO, LG_NAME, TOTAL_PAVE_WIDTH, TOTAL_SEAL_WIDTH, TRAFFICABLE_SURF_WIDTH, TRAFFICABLE_PAVE_WIDTH, TRAFFICABLE_WIDTH_DIFF, SEALED_SHOULDER_L, SEALED_SHOULDER_R, UNSEALED_SHOULDER_L, UNSEALED_SHOULDER_R, NO_OF_LANES, KERB_L, KERB_R, SHOULDER_SEALED_L, SHOULDER_SEALED_R, SHOULDER_PAVEMENT_L, SHOULDER_PAVEMENT_R, UNSEALED, FLOODWAY, BRIDGE, ROUTE_NE_ID, GEOLOC, OBJECTID, GEOLOC.STLength(), GlobalID`; widths are `esriFieldTypeSingle` (metres), `NO_OF_LANES` is `esriFieldTypeSmallInteger` | **Certain** (fetched `?f=pjson`) |
| Layer 12 covers **State Road only** (distinct `NETWORK_TYPE` query returned only "State Road") | **Likely** (agent-verified once) |
| Layer **16 "Road Hierarchy"**: field `ROAD_HIERARCHY` (exact live values: Primary Distributor, Regional Distributor, Distributor A, Distributor B, Local Distributor, Access Road); covers State and Local | **Certain** (confirmed S0.T2, 2026-09-22) |
| Layer **8 "Legal Speed Limit"**: field `SPEED_LIMIT` is a **string with embedded units** (`10km/h` … `110km/h`, plus one free-text value) — never cast it to a number; covers State and Local | **Certain** (confirmed S0.T2, 2026-09-22) |
| Licence: Creative Commons Attribution (CC BY 4.0) per portal description | **Likely** — confirm text at `https://portal-mainroads.opendata.arcgis.com/datasets/mainroads::road-network/about` in a browser if convenient; not blocking |
| The provided CSV = 189,865 rows, all of WA (8 regions), 174,145 Local Road / 11,095 State Road; `CWY` ∈ {Single 178,793, Left 5,549, Right 5,523} | **Certain** (profiled locally) |
| Google Maps: no area-wide road geometry API, no width/lanes, ToS forbids bulk export | **Certain** |
| OSM `width` tag ≈ 1.4 % of highway ways globally, `lanes` ≈ 7.5 % (taginfo) | **Certain** globally, Perth-specific density unknown |

---

## 3. Design (the spec)

### 3.1 Inputs, outputs, CLI

```
uv run dbe extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km [--cache-dir DIR] [--no-xlsx] [--osm] [-v]
uv run dbe to-xlsx --roads output/curtin_10km/roads.csv --vertices output/curtin_10km/roads_vertices.csv --metadata output/curtin_10km/metadata.json --out output/curtin_10km/roads.xlsx
```

`extract` writes into `--out` (created if missing):

| File | Content |
|---|---|
| `roads.csv` | one row per layer-17 segment intersecting the circle; columns = `schema.OUTPUT_COLUMNS` |
| `roads_vertices.csv` | one row per vertex; columns = `schema.VERTEX_COLUMNS` |
| `metadata.json` | parameters, envelope, counts, sources, licence, datum note, `extracted_at_utc` |
| `roads.xlsx` | sheets `roads`, `vertices` (split `vertices_2`… past Excel's 1,048,576-row limit), `metadata`; built by reading the two CSVs back (unless `--no-xlsx`) |
| `cache/` | raw API page responses as JSON (default `--cache-dir` = `<out>/cache`); makes re-runs offline and resumable |

Exit code 0 on success, 1 on any error (message on stderr). Logging via `logging` to stderr, INFO by default, DEBUG with `-v`.

### 3.2 Spatial semantics

- `LocalProjection(lat, lon)` = azimuthal equidistant (`+proj=aeqd +lat_0=<lat> +lon_0=<lon> +datum=WGS84 +units=m`). Distances from the centre are exact; local distortion within 10–50 km is negligible for this purpose.
- Circle = `Point(0,0).buffer(radius_m, quad_segs=64)` in local metres.
- Envelope for the API = bounds of the circle polygon transformed back to WGS84: `(xmin=lon, ymin=lat, xmax, ymax)`.
- Inclusion test = `local_geom.distance(centre) <= radius_m` — *amended 2026-09-24 (Fable review): the original `local_geom.intersects(circle)` tested against the inscribed 256-gon, which is 0.753 m short of the true circle mid-chord at 10 km, and excluded two real streets 9,999.9 m from the centre. `INSIDE_FRACTION` still uses the polygon.*
- `INSIDE_FRACTION = local_geom.intersection(circle).length / local_geom.length` (0 for zero-length).
- `LENGTH_M = local_geom.length`; `DIST_TO_CENTRE_M = local_geom.distance(Point(0,0))`.
- Start/end = first vertex of the first part / last vertex of the last part, as served (MRWA digitising direction, which follows increasing SLK).
- `MultiLineString` is preserved as-is in WKT; vertices table carries a `PART` index.

### 3.3 Output schema (exact; `dbe/schema.py` is the single source of truth)

`ORIGINAL_COLUMNS` (25, identical to the provided CSV header, same order):
`ROAD, ROAD_NAME, COMMON_USAGE_NAME, START_SLK, END_SLK, CWY, START_TRUE_DIST, END_TRUE_DIST, NETWORK_TYPE, RA_NO, RA_NAME, LG_NO, LG_NAME, START_NODE_NO, START_NODE_NAME, END_NODE_NO, END_NODE_NAME, DATUM_NE_ID, NM_BEGIN_MP, NM_END_MP, NETWORK_ELEMENT, ROUTE_NE_ID, OBJECTID, GlobalID, GEOLOCSTLength`

`GEOMETRY_COLUMNS`: `START_LAT, START_LON, END_LAT, END_LON, VERTEX_COUNT, LENGTH_M, DIST_TO_CENTRE_M, INSIDE_FRACTION, GEOMETRY_WKT`

`ENRICH_COLUMNS`: `ROAD_HIERARCHY, SPEED_LIMIT, TOTAL_PAVE_WIDTH_M, TOTAL_SEAL_WIDTH_M, TRAFFICABLE_SURF_WIDTH_M, NO_OF_LANES, SEALED_SHOULDER_L_M, SEALED_SHOULDER_R_M, KERB_L, KERB_R, WIDTH_M, WIDTH_SOURCE`

`OSM_COLUMNS`: `OSM_WAY_ID, OSM_HIGHWAY, OSM_LANES, OSM_MAXSPEED, OSM_SURFACE` (blank unless `--osm`)

`PROVENANCE_COLUMNS`: `DATA_SOURCE, EXTRACTED_AT_UTC`

`OUTPUT_COLUMNS = ORIGINAL + GEOMETRY + ENRICH + OSM + PROVENANCE` (53 columns).

`VERTEX_COLUMNS`: `OBJECTID, NETWORK_ELEMENT, ROAD, ROAD_NAME, CWY, PART, SEQ, LAT, LON`

> **Why a width cannot leak onto a local road (S3.T2 review, 2026-09-23).** `enrich_segment` has no
> `NETWORK_TYPE` check, so *synthetically* a Local Road carrying `ROAD="H001"` would pick up a
> state-road width. It cannot happen with real data: across all 189,865 rows and 70,010 distinct
> road codes in the provided statewide CSV, **no code carries more than one `NETWORK_TYPE`**. A road
> code determines network type uniquely. This is an empirical invariant in one snapshot, not a
> schema guarantee — if defence in depth is ever wanted, the guard is a `NETWORK_TYPE` check in
> `enrich_segment`, not a change to the join.

Width semantics: `WIDTH_M = round(TOTAL_SEAL_WIDTH_M, 2)` when MRWA layer 12 matched (`WIDTH_SOURCE = mrwa_pavement`); else OSM `width` when `--osm` matched and parses (`osm`); else blank (`none`). Width columns from layer 12 are overlap-weighted means across matching pavement spans; `NO_OF_LANES`, `KERB_L/R`, `ROAD_HIERARCHY`, `SPEED_LIMIT` take the value of the span with the largest SLK overlap.

### 3.4 Data flow

```
cli.extract → LocalProjection → circle, envelope
           → MRWAClient.query_envelope(17|12|16|8, envelope)   (paged, cached)
           → for each layer-17 feature: normalise props → shapely geom → segment_metrics
                → keep if intersects → row (ORIGINAL + GEOMETRY) + enrich_segment(...) + provenance
                → vertices rows
           → export.write_csv(roads), write_csv(vertices), write_json(metadata)
           → export.csv_to_xlsx(roads.csv, vertices.csv, metadata.json → roads.xlsx)
```

### 3.5 File structure

```
pyproject.toml                 uv project; [project.scripts] dbe = "dbe.cli:main"; pytest addopts, markers; ruff config
README.md                      usage, data sources, licence/attribution, column dictionary (Segment 6)
CLAUDE.md                      repo conventions (exists; Segment 6 polishes)
.gitignore                     data/ output/ .venv/ __pycache__/ *.pyc .pytest_cache/ .ruff_cache/ *.egg-info/ .DS_Store
dbe/__init__.py         __version__ = "0.1.0"
dbe/__main__.py         `from dbe.cli import main; raise SystemExit(main())`
dbe/cli.py              argparse subcommands extract / to-xlsx; logging setup
dbe/geometry.py         LocalProjection, SegmentMetrics, geojson_to_line, segment_metrics, iter_vertices
dbe/mrwa_client.py      MRWAClient (paging, retries, cache), constants, normalise_properties
dbe/slk_join.py         SlkSpan, overlap_len, cwy_compatible, span_from_properties, index_by_road, overlapping, dominant_value, weighted_mean
dbe/enrich.py           field maps for layers 12/16/8, enrich_segment
dbe/schema.py           column lists, DATA_SOURCE, LICENCE, DATUM_NOTE
dbe/extract.py          RoadSource protocol, ExtractResult, extract()
dbe/export.py           write_csv, write_json, csv_to_xlsx
dbe/osm_client.py       (Segment 5) OsmWay, fetch_highways
dbe/osm_match.py        (Segment 5) normalise_name, match_ways, apply_osm
scripts/record_fixtures.py     records tests/fixtures/*.json from the live API (1.5 km envelope at Curtin)
dbe/plot.py             render_qa_plot(): the map, written automatically by `extract` (added 2026-09-23)
scripts/qa_plot.py             thin wrapper to re-render the map for an existing output directory
tests/conftest.py              fixture loaders, FixtureSource
tests/fixtures/                layer17_curtin2500.geojson, layer12_…, layer16_…, layer8_…, layer17_metadata.json, layer12_metadata.json, layer16_metadata.json, layer8_metadata.json
tests/test_geometry.py · test_mrwa_client.py · test_slk_join.py · test_enrich.py · test_extract.py · test_export.py · test_cli.py · test_live_smoke.py (network) · test_reconcile_csv.py (data-dependent, skips)
```

### 3.6 Error handling

- HTTP 429/5xx or connection errors → exponential backoff (1, 2, 4, 8, 16 s; max 5 attempts) then `MRWATransientError`.
- ArcGIS returns HTTP 200 with `{"error": {...}}` for bad requests → `MRWAError` immediately (no retry).
- Feature with `geometry: null` or empty `coordinates` → skipped, counted in `metadata.skipped_no_geometry`.
- Feature whose geometry is present but unusable — a one-coordinate line, an empty or one-coordinate part of a multi-part line, or a non-linear type — → skipped, the exception type logged, counted in `metadata.skipped_bad_geometry`. These raise from shapely or GEOS rather than failing a truthiness test, so the conversion is wrapped rather than the shapes enumerated (S4.T2 review, IMPORTANT-1).
- Unparseable SLK values → segment still emitted; enrichment columns blank; counted in `metadata.enrich_unparsed_slk`.
- Duplicate `OBJECTID` across pages → deduplicated; counted in `metadata.duplicates_dropped`.
- `GEOMETRY_WKT` longer than 32,767 characters (Excel cell limit) → CSV keeps it whole; XLSX writes the first 32,700 characters + `…TRUNCATED`; count in `metadata` and log a warning.
- Zero features from layer 17 → exit 1 with a clear message (`no road segments intersect the circle; check lat/lon order`).

### 3.7 Testing strategy

- Unit tests with synthetic shapes for geometry and SLK joins (deterministic numbers, tolerances stated).
- Client tests with a fake `Session` object (no network): paging boundaries, retry, error body, cache hit.
- Pipeline tests run `extract()` against recorded fixtures via `FixtureSource` (duck-typed `query_envelope`).
- One `network`-marked smoke test hits the live API for a 300 m envelope.
- `test_reconcile_csv.py` compares `output/curtin_10km/roads.csv` against the provided CSV: header parity on the first 25 columns and ≥ 99 % of extracted `NETWORK_ELEMENT` ids present in the CSV (tightened from 95 % at Gate C; measured 1.0000). Skips if either file is absent.

### 3.8 Sanity ranges for the Curtin 10 km run (reviewers check these)

| Quantity | Expected | Red flag |
|---|---|---|
| Layer-17 features returned for the envelope | 12k–45k | < 4k or > 100k |
| Segments intersecting the circle | 10k–35k | < 3k or > 80k |
| Pages fetched for layer 17 | 6–25 | 1 (paging broken) |
| Layer-12 features (State Road only) | 200–6,000 (measured 4,307 at 10 km) | 0 |
| Rows with `WIDTH_SOURCE = mrwa_pavement` | roughly equals the State Road row count (±20 %) | 0, or > State Road count |
| `NETWORK_TYPE` mix | Local Road ≫ State Road; a handful of Miscellaneous / Controlled Path | no Local Road rows |
| Vertices rows | 35k–150k (measured density ≈ 3.2 vertices per segment) | > 1,048,575 in one sheet without split |
| `INSIDE_FRACTION` | all in [0, 1]; most = 1.0; boundary rows < 1 | any value outside [0, 1] |
| Named roads present | Kent St, Manning Rd, Hayman Rd, Leach Hwy, Albany Hwy, Canning Hwy, Kwinana Fwy, Orrong Rd | any of the first five missing |

---

## 4. Segments and tasks

Task ids are `S<segment>.T<n>`. Each task ends in a commit. Interfaces blocks are contracts.

---

## Segment 0 — Environment and source verification (Sonnet)

### Task S0.T1: Project scaffold with uv

**Files:**
- Create: `pyproject.toml`, `dbe/__init__.py`, `dbe/__main__.py`, `tests/__init__.py`, `tests/test_smoke_import.py`
- Modify: `.gitignore` (exists), `CLAUDE.md` (exists — only add the "Commands" block if missing)

**Interfaces:**
- Produces: package `dbe` importable; `uv run pytest -q` works; `uv run dbe --help` will work once `cli.py` exists (S4.T3) — until then the script entry may fail, that is expected.

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "dbe"
version = "0.1.0"
description = "Extract road geometry and attributes inside a circle from Main Roads WA open data"
requires-python = ">=3.11"
dependencies = [
  "requests>=2.32",
  "shapely>=2.0",
  "pyproj>=3.6",
  "pandas>=2.2",
  "openpyxl>=3.1",
  "matplotlib>=3.8",  # moved from dev 2026-09-23: extract now writes the map automatically
]

[project.scripts]
dbe = "dbe.cli:main"

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.6"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["dbe"]

[tool.pytest.ini_options]
addopts = "-m 'not network'"
markers = [
  "network: hits the live MRWA / Overpass services (opt-in: uv run pytest -m network)",
]
testpaths = ["tests"]

[tool.ruff]
line-length = 110
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

- [ ] **Step 2: Create the package and a smoke test**

`dbe/__init__.py`:
```python
"""DBE: roads inside a circle, from Main Roads WA open data."""

__version__ = "0.1.0"
```

`dbe/__main__.py`:
```python
from dbe.cli import main

raise SystemExit(main())
```

`tests/__init__.py`: empty file.

`tests/test_smoke_import.py`:
```python
import dbe


def test_version_string():
    assert dbe.__version__ == "0.1.0"
```

- [ ] **Step 3: Install and run**

Run: `uv python install 3.12 && uv sync && uv run pytest -q`
Expected: `1 passed`. If `uv sync` complains about the `dbe.cli` script target, that is fine at this stage (the module arrives in S4.T4); if it blocks, temporarily create `dbe/cli.py` containing only `def main(argv=None) -> int:\n    raise SystemExit("cli not implemented yet")` and note it in progress.md.

- [ ] **Step 4: Confirm `.gitignore` contains** `data/`, `output/`, `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/`, `.DS_Store`, `uv.lock` is **not** ignored (commit it).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock dbe tests .gitignore .python-version 2>/dev/null
git commit -m "chore: scaffold dbe package with uv, pytest and ruff"
```

---

### Task S0.T2: Verify layer schemas and record metadata fixtures

**Files:**
- Create: `scripts/verify_layers.py`, `tests/fixtures/layer17_metadata.json`, `tests/fixtures/layer12_metadata.json`, `tests/fixtures/layer16_metadata.json`, `tests/fixtures/layer8_metadata.json`, `docs/task_docs/source_verification.md`

**Interfaces:**
- Produces: the confirmed field names for `ROAD_HIERARCHY` (layer 16) and `SPEED_LIMIT` (layer 8), and the `supportsPagination` flag — written to `docs/task_docs/source_verification.md` and to `progress.md` → Decisions log. S3.T2 reads those names.

- [ ] **Step 1: Write the script** (plain `requests`, no package imports yet)

```python
"""Fetch layer metadata for the four MRWA layers and print a schema summary. Network required."""
import json
import sys
from pathlib import Path

import requests

BASE = "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
LAYERS = {17: "Road Network", 12: "Pavement and Surfacing State", 16: "Road Hierarchy", 8: "Legal Speed Limit"}
OUT = Path("tests/fixtures")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for layer_id, expected_name in LAYERS.items():
        r = requests.get(f"{BASE}/{layer_id}", params={"f": "pjson"}, timeout=60,
                         headers={"User-Agent": "DBE/0.1 schema check"})
        r.raise_for_status()
        meta = r.json()
        (OUT / f"layer{layer_id}_metadata.json").write_text(json.dumps(meta, indent=2))
        fields = [f["name"] for f in meta.get("fields", [])]
        adv = meta.get("advancedQueryCapabilities", {})
        print(f"\n== layer {layer_id}: {meta.get('name')} (expected '{expected_name}')")
        print(f"   geometryType={meta.get('geometryType')} wkid={meta.get('extent', {}).get('spatialReference', {}).get('wkid')}"
              f" maxRecordCount={meta.get('maxRecordCount')}")
        print(f"   supportsPagination={adv.get('supportsPagination')} supportsOrderBy={adv.get('supportsOrderBy')}"
              f" supportsStatistics={adv.get('supportsStatistics')}")
        print(f"   fields ({len(fields)}): {', '.join(fields)}")
        if meta.get("name") != expected_name:
            print("   !! NAME MISMATCH", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run it**

Run: `uv run python scripts/verify_layers.py`
Expected: four blocks; layer 17 lists the 25 known fields (with `GEOLOC.STLength()`), layer 12 lists `TOTAL_SEAL_WIDTH` etc., `supportsPagination=True` for all four. Note the exact field that carries hierarchy on layer 16 and speed on layer 8.

- [ ] **Step 3: Write `docs/task_docs/source_verification.md`** — a dated table: layer id, name, geometryType, wkid, maxRecordCount, supportsPagination, the join keys present (`ROAD, CWY, START_SLK, END_SLK`), and the confirmed attribute field names: `HIERARCHY_FIELD = "<confirmed>"`, `SPEED_FIELD = "<confirmed>"`. If either differs from `ROAD_HIERARCHY` / `SPEED_LIMIT`, write the real name here **and** in `progress.md` → Decisions log; S3.T2 uses the confirmed names.

- [ ] **Step 4: Commit**

```bash
git add scripts/verify_layers.py tests/fixtures/layer*_metadata.json docs/task_docs/source_verification.md
git commit -m "chore: verify MRWA layer schemas and record metadata fixtures"
```

---

### Task S0.T3: Record feature fixtures for a 2.5 km envelope at Curtin (DONE — recorded at 2.5 km, see Decisions log)

**Files:**
- Create: `scripts/record_fixtures.py`, `tests/fixtures/layer17_curtin2500.geojson`, `tests/fixtures/layer12_curtin2500.geojson`, `tests/fixtures/layer16_curtin2500.geojson`, `tests/fixtures/layer8_curtin2500.geojson`, `tests/fixtures/README.md`

**Interfaces:**
- Produces: GeoJSON `FeatureCollection` files (all pages merged into one `features` array) that `tests/conftest.py` (S2.T2) loads. Envelope constant `CURTIN_2500_ENVELOPE` documented in `tests/fixtures/README.md` as the exact `(xmin, ymin, xmax, ymax)` used.

- [ ] **Step 1: Write the recorder** (standalone, plain `requests`; it must not import `dbe.geometry`, which does not exist yet — compute the envelope arithmetically)

```python
"""Record GeoJSON fixtures for a ~1.5 km box around Curtin's Design building. Network required."""
import json
import math
import time
from pathlib import Path

import requests

BASE = "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
LAT, LON, RADIUS_M = -32.0018629, 115.8924599, 2500.0
LAYERS = [17, 12, 16, 8]
OUT = Path("tests/fixtures")
PAGE = 2000

dlat = RADIUS_M / 111_320.0
dlon = RADIUS_M / (111_320.0 * math.cos(math.radians(LAT)))
ENVELOPE = (LON - dlon, LAT - dlat, LON + dlon, LAT + dlat)


def fetch_all(layer_id: int) -> list[dict]:
    feats: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "geometry": ",".join(f"{v:.7f}" for v in ENVELOPE),
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*", "returnGeometry": "true", "outSR": 4326,
            "f": "geojson", "orderByFields": "OBJECTID ASC",
            "resultOffset": offset, "resultRecordCount": PAGE,
        }
        r = requests.post(f"{BASE}/{layer_id}/query", data=params, timeout=120,
                          headers={"User-Agent": "DBE/0.1 fixture recorder"})
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        page = data.get("features", [])
        feats.extend(page)
        print(f"layer {layer_id}: offset {offset} -> {len(page)} features")
        if len(page) < PAGE:
            return feats
        offset += len(page)
        time.sleep(0.3)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for layer_id in LAYERS:
        feats = fetch_all(layer_id)
        path = OUT / f"layer{layer_id}_curtin2500.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        print(f"wrote {path} ({path.stat().st_size / 1e6:.2f} MB, {len(feats)} features)")
    print("ENVELOPE =", ENVELOPE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run it**

Run: `uv run python scripts/record_fixtures.py`
Expected (outcome 2026-09-22): at 1.5 km layer 12 returned **0 features** — the nearest pavement record is ~2.1 km from the centre — so `RADIUS_M` was raised to 2500 and re-run: layer 17 = 1,850 features (1.66 MB), layer 12 = 113 (State Road only), layer 16 = 659, layer 8 = 580; each file < 5 MB (if not, reduce `RADIUS_M` to 1000 and rename files `*_curtin1000.geojson`, updating every reference in later tasks — record the change in progress.md).

- [ ] **Step 3: Write `tests/fixtures/README.md`** with: the recording date, `ENVELOPE` printed by the script (7 decimals), feature counts per layer, file sizes, and the sentence "Fixtures are recorded snapshots of CC BY 4.0 Main Roads WA data; regenerate with `uv run python scripts/record_fixtures.py`."

- [ ] **Step 4: Commit**

```bash
git add scripts/record_fixtures.py tests/fixtures/
git commit -m "test: record MRWA GeoJSON fixtures for a 1.5 km envelope at Curtin"
```

---

## Segment 1 — Geometry core (Sonnet, TDD)

### Task S1.T1: LocalProjection, circle and envelope

**Files:**
- Create: `dbe/geometry.py`, `tests/test_geometry.py`

**Interfaces:**
- Produces:
  - `class LocalProjection:` `__init__(self, lat: float, lon: float)`; attributes `lat`, `lon`, `crs: pyproj.CRS`; methods `to_local(geom) -> geom`, `to_wgs84(geom) -> geom`, `circle(radius_m: float, quad_segs: int = 64) -> shapely.Polygon` (local metres, centred at (0,0)), `envelope_wgs84(radius_m: float) -> tuple[float, float, float, float]` returning `(xmin_lon, ymin_lat, xmax_lon, ymax_lat)`.

- [ ] **Step 1: Write the failing tests**

```python
import math

import pytest
from shapely.geometry import LineString, Point

from dbe.geometry import LocalProjection

CURTIN = (-32.0018629, 115.8924599)


def test_centre_maps_to_origin():
    proj = LocalProjection(*CURTIN)
    p = proj.to_local(Point(CURTIN[1], CURTIN[0]))  # shapely is (x=lon, y=lat)
    assert abs(p.x) < 1e-6 and abs(p.y) < 1e-6


def test_roundtrip_wgs84():
    proj = LocalProjection(*CURTIN)
    line = LineString([(115.88, -32.0), (115.9, -32.01)])
    back = proj.to_wgs84(proj.to_local(line))
    for (x0, y0), (x1, y1) in zip(line.coords, back.coords):
        assert abs(x0 - x1) < 1e-9 and abs(y0 - y1) < 1e-9


def test_circle_area_and_radius():
    proj = LocalProjection(*CURTIN)
    circle = proj.circle(1000.0)
    assert circle.area == pytest.approx(math.pi * 1000.0**2, rel=0.01)
    assert circle.bounds == pytest.approx((-1000.0, -1000.0, 1000.0, 1000.0), abs=1.0)


def test_envelope_spans_expected_degrees():
    proj = LocalProjection(*CURTIN)
    xmin, ymin, xmax, ymax = proj.envelope_wgs84(10_000.0)
    lat_half = (ymax - ymin) / 2
    lon_half = (xmax - xmin) / 2
    assert lat_half == pytest.approx(10_000 / 111_320, rel=0.02)
    assert lon_half == pytest.approx(10_000 / (111_320 * math.cos(math.radians(CURTIN[0]))), rel=0.02)
    assert xmin < CURTIN[1] < xmax and ymin < CURTIN[0] < ymax


def test_east_west_line_length_in_metres():
    proj = LocalProjection(*CURTIN)
    line = LineString([(115.89, -32.0), (115.90, -32.0)])  # 0.01 degrees of longitude at lat -32
    expected = 0.01 * 111_320 * math.cos(math.radians(32.0))
    assert proj.to_local(line).length == pytest.approx(expected, rel=0.01)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_geometry.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'dbe.geometry'`

- [ ] **Step 3: Implement**

```python
"""Metre-accurate local geometry via an azimuthal-equidistant projection centred on the query point."""
from __future__ import annotations

from pyproj import CRS, Transformer
from shapely.geometry import Point, Polygon
from shapely.ops import transform as _shp_transform

WGS84 = CRS.from_epsg(4326)


class LocalProjection:
    """Azimuthal equidistant projection centred on (lat, lon); units are metres, centre is (0, 0)."""

    def __init__(self, lat: float, lon: float) -> None:
        self.lat = float(lat)
        self.lon = float(lon)
        self.crs = CRS.from_proj4(f"+proj=aeqd +lat_0={self.lat} +lon_0={self.lon} +datum=WGS84 +units=m +no_defs")
        self._fwd = Transformer.from_crs(WGS84, self.crs, always_xy=True)
        self._inv = Transformer.from_crs(self.crs, WGS84, always_xy=True)

    def to_local(self, geom):
        return _shp_transform(self._fwd.transform, geom)

    def to_wgs84(self, geom):
        return _shp_transform(self._inv.transform, geom)

    def circle(self, radius_m: float, quad_segs: int = 64) -> Polygon:
        return Point(0.0, 0.0).buffer(float(radius_m), quad_segs=quad_segs)

    def envelope_wgs84(self, radius_m: float) -> tuple[float, float, float, float]:
        ring = self.to_wgs84(self.circle(radius_m))
        xmin, ymin, xmax, ymax = ring.bounds
        return (float(xmin), float(ymin), float(xmax), float(ymax))
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_geometry.py -q`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add dbe/geometry.py tests/test_geometry.py
git commit -m "feat(geometry): local AEQD projection with circle and WGS84 envelope"
```

---

### Task S1.T2: Segment metrics, GeoJSON parsing and vertex iteration

**Files:**
- Modify: `dbe/geometry.py`
- Test: `tests/test_geometry.py` (append)

**Interfaces:**
- Consumes: `LocalProjection` (S1.T1).
- Produces:
  - `@dataclass(frozen=True) class SegmentMetrics:` fields `intersects: bool, length_m: float, inside_fraction: float, dist_to_centre_m: float, start_lat: float, start_lon: float, end_lat: float, end_lon: float, vertex_count: int, wkt: str`
  - `def geojson_to_line(geometry: dict) -> LineString | MultiLineString` (raises `ValueError` for other types)
  - `def iter_vertices(geom) -> Iterator[tuple[int, int, float, float]]` yielding `(part, seq, lat, lon)`
  - `def segment_metrics(geom_wgs84, proj: LocalProjection, circle_local: Polygon) -> SegmentMetrics`

- [ ] **Step 1: Append failing tests**

```python
from shapely.geometry import MultiLineString

from dbe.geometry import geojson_to_line, iter_vertices, segment_metrics


def _proj_and_circle(radius_m=1000.0):
    proj = LocalProjection(*CURTIN)
    return proj, proj.circle(radius_m)


def _offset_line(proj, dx0, dy0, dx1, dy1):
    """Build a WGS84 line from local-metre offsets around the centre."""
    return proj.to_wgs84(LineString([(dx0, dy0), (dx1, dy1)]))


def test_geojson_to_line_accepts_line_and_multiline():
    ls = geojson_to_line({"type": "LineString", "coordinates": [[115.89, -32.0], [115.9, -32.0]]})
    assert ls.geom_type == "LineString"
    ml = geojson_to_line({"type": "MultiLineString",
                          "coordinates": [[[115.89, -32.0], [115.9, -32.0]], [[115.9, -32.0], [115.91, -32.01]]]})
    assert ml.geom_type == "MultiLineString"
    with pytest.raises(ValueError):
        geojson_to_line({"type": "Point", "coordinates": [115.89, -32.0]})


def test_iter_vertices_yields_part_seq_lat_lon():
    ml = MultiLineString([[(115.89, -32.0), (115.9, -32.0)], [(115.9, -32.0), (115.91, -32.01)]])
    rows = list(iter_vertices(ml))
    assert rows == [(0, 0, -32.0, 115.89), (0, 1, -32.0, 115.9), (1, 0, -32.0, 115.9), (1, 1, -32.01, 115.91)]


def test_fully_inside_segment():
    proj, circle = _proj_and_circle()
    line = _offset_line(proj, -200, 0, 200, 0)
    m = segment_metrics(line, proj, circle)
    assert m.intersects is True
    assert m.inside_fraction == pytest.approx(1.0)
    assert m.length_m == pytest.approx(400.0, rel=1e-3)
    assert m.dist_to_centre_m == pytest.approx(0.0, abs=0.5)
    assert m.vertex_count == 2


def test_half_inside_segment():
    proj, circle = _proj_and_circle()
    line = _offset_line(proj, 0, 500, 0, 1500)  # 1000 m long, crosses the 1000 m circle at 500 m
    m = segment_metrics(line, proj, circle)
    assert m.intersects is True
    assert m.inside_fraction == pytest.approx(0.5, abs=0.02)


def test_outside_segment():
    proj, circle = _proj_and_circle()
    line = _offset_line(proj, 1200, 1200, 1300, 1300)
    m = segment_metrics(line, proj, circle)
    assert m.intersects is False
    assert m.inside_fraction == 0.0
    assert m.dist_to_centre_m == pytest.approx(math.hypot(1200, 1200), rel=1e-3)


def test_start_end_and_wkt_use_lon_lat_order():
    proj, circle = _proj_and_circle()
    line = LineString([(115.89, -32.0), (115.9, -32.01)])
    m = segment_metrics(line, proj, circle)
    assert (m.start_lon, m.start_lat) == (115.89, -32.0)
    assert (m.end_lon, m.end_lat) == (115.9, -32.01)
    assert m.wkt.startswith("LINESTRING (115.89 -32")


def test_multiline_start_is_first_part_end_is_last_part():
    proj, circle = _proj_and_circle()
    ml = MultiLineString([[(115.89, -32.0), (115.895, -32.0)], [(115.9, -32.0), (115.91, -32.01)]])
    m = segment_metrics(ml, proj, circle)
    assert (m.start_lon, m.start_lat) == (115.89, -32.0)
    assert (m.end_lon, m.end_lat) == (115.91, -32.01)
    assert m.vertex_count == 4
    assert m.wkt.startswith("MULTILINESTRING")
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_geometry.py -q`
Expected: FAIL with `ImportError: cannot import name 'geojson_to_line'`

- [ ] **Step 3: Implement (append to `dbe/geometry.py`)**

```python
from collections.abc import Iterator
from dataclasses import dataclass

import shapely
from shapely.geometry import LineString, MultiLineString, shape


@dataclass(frozen=True)
class SegmentMetrics:
    intersects: bool
    length_m: float
    inside_fraction: float
    dist_to_centre_m: float
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    vertex_count: int
    wkt: str


def geojson_to_line(geometry: dict) -> LineString | MultiLineString:
    geom = shape(geometry)
    if geom.geom_type not in ("LineString", "MultiLineString"):
        raise ValueError(f"unsupported geometry type: {geom.geom_type}")
    return geom


def _parts(geom) -> list[LineString]:
    return list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]


def iter_vertices(geom) -> Iterator[tuple[int, int, float, float]]:
    """Yield (part, seq, lat, lon) for every vertex, parts and vertices in served order."""
    for part_idx, part in enumerate(_parts(geom)):
        for seq, (x, y) in enumerate(part.coords):
            yield part_idx, seq, float(y), float(x)


def segment_metrics(geom_wgs84, proj: LocalProjection, circle_local: Polygon) -> SegmentMetrics:
    local = proj.to_local(geom_wgs84)
    length = float(local.length)
    inter = local.intersection(circle_local)
    inside_len = 0.0 if inter.is_empty else float(inter.length)
    parts = _parts(geom_wgs84)
    first = parts[0].coords[0]
    last = parts[-1].coords[-1]
    return SegmentMetrics(
        intersects=bool(local.intersects(circle_local)),
        length_m=length,
        inside_fraction=(inside_len / length) if length > 0 else 0.0,
        dist_to_centre_m=float(local.distance(Point(0.0, 0.0))),
        start_lat=float(first[1]),
        start_lon=float(first[0]),
        end_lat=float(last[1]),
        end_lon=float(last[0]),
        vertex_count=sum(len(p.coords) for p in parts),
        wkt=shapely.to_wkt(geom_wgs84, rounding_precision=7),
    )
```

Move the new imports to the top of the module (ruff `I` rule) — `Iterator`, `dataclass`, `shapely`, `LineString`, `MultiLineString`, `shape` join the existing imports.

- [ ] **Step 4: Run to verify pass and lint**

Run: `uv run pytest tests/test_geometry.py -q && uv run ruff check dbe tests`
Expected: `12 passed`; ruff clean.

- [ ] **Step 5: Commit**

```bash
git add dbe/geometry.py tests/test_geometry.py
git commit -m "feat(geometry): segment metrics, GeoJSON parsing and vertex iteration"
```

---

## Segment 2 — MRWA ArcGIS client (Sonnet, TDD)

### Task S2.T1: MRWAClient with paging, retries and disk cache

**Files:**
- Create: `dbe/mrwa_client.py`, `tests/test_mrwa_client.py`

**Interfaces:**
- Produces:
  - constants `BASE_URL`, `LAYER_ROAD_NETWORK = 17`, `LAYER_PAVEMENT = 12`, `LAYER_HIERARCHY = 16`, `LAYER_SPEED = 8`, `PAGE_SIZE = 2000`, `USER_AGENT`
  - type alias `Envelope = tuple[float, float, float, float]`
  - exceptions `MRWAError(RuntimeError)` and `MRWATransientError(MRWAError)`
  - `class MRWAClient:` `__init__(self, session=None, base_url: str = BASE_URL, page_size: int = PAGE_SIZE, cache_dir: Path | None = None, sleep_s: float = 0.2, max_retries: int = 5, timeout_s: float = 90.0)`; `layer_metadata(self, layer_id: int) -> dict`; `query_envelope(self, layer_id: int, envelope: Envelope, out_fields: str = "*") -> list[dict]` returning GeoJSON feature dicts (`{"type": "Feature", "geometry": {...} | None, "properties": {...}}`), all pages merged, in server order.
  - `def normalise_properties(props: dict) -> dict` — copies the dict and renames any of `GEOLOC.STLength()`, `Shape__Length`, `SHAPE.STLength()` to `GEOLOCSTLength`.
- The session object is duck-typed: it needs `.get(url, params=, timeout=, headers=)` and `.post(url, data=, timeout=, headers=)` returning an object with `.status_code`, `.json()`, `.raise_for_status()`. Metadata uses GET; queries use POST (form-encoded) so long parameter lists never hit URL limits.

- [ ] **Step 1: Write the failing tests**

```python
import json

import pytest
import requests

from dbe.mrwa_client import (
    LAYER_ROAD_NETWORK,
    MRWAClient,
    MRWAError,
    MRWATransientError,
    normalise_properties,
)

ENV = (115.88, -32.01, 115.90, -31.99)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Serves a scripted list of responses; records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def _next(self, url, payload):
        self.calls.append((url, payload))
        if not self.responses:
            raise AssertionError("no scripted response left")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def get(self, url, params=None, timeout=None, headers=None):
        return self._next(url, params)

    def post(self, url, data=None, timeout=None, headers=None):
        return self._next(url, data)


def _feat(oid):
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[115.89, -32.0], [115.891, -32.0]]},
            "properties": {"OBJECTID": oid, "ROAD": "H001"}}


def _page(oids, exceeded=None):
    body = {"type": "FeatureCollection", "features": [_feat(o) for o in oids]}
    if exceeded is not None:
        body["exceededTransferLimit"] = exceeded
    return FakeResponse(body)


def test_pages_until_short_page():
    session = FakeSession([_page(range(3), exceeded=True), _page(range(3, 5))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    feats = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert [f["properties"]["OBJECTID"] for f in feats] == [0, 1, 2, 3, 4]
    assert len(session.calls) == 2
    url, params = session.calls[1]
    assert url.endswith("/17/query")
    assert params["resultOffset"] == 3 and params["resultRecordCount"] == 3
    assert params["f"] == "geojson" and params["outSR"] == 4326 and params["inSR"] == 4326
    assert params["geometryType"] == "esriGeometryEnvelope"
    assert params["geometry"] == "115.88,-32.01,115.9,-31.99"
    assert params["orderByFields"] == "OBJECTID ASC"


def test_single_short_page_stops_immediately():
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    assert len(client.query_envelope(LAYER_ROAD_NETWORK, ENV)) == 2
    assert len(session.calls) == 1


def test_retries_transient_then_succeeds():
    session = FakeSession([FakeResponse({}, status=503), requests.ConnectionError("boom"), _page(range(1))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=5)
    assert len(client.query_envelope(LAYER_ROAD_NETWORK, ENV)) == 1
    assert len(session.calls) == 3


def test_gives_up_after_max_retries():
    session = FakeSession([FakeResponse({}, status=503)] * 3)
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=3)
    with pytest.raises(MRWATransientError):
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)


def test_arcgis_error_body_raises_without_retry():
    session = FakeSession([FakeResponse({"error": {"code": 400, "message": "Invalid parameter"}})])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=5)
    with pytest.raises(MRWAError) as exc:
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert "Invalid parameter" in str(exc.value)
    assert len(session.calls) == 1


def test_cache_hit_skips_network(tmp_path):
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, cache_dir=tmp_path)
    first = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert len(list(tmp_path.glob("*.json"))) == 1
    client2 = MRWAClient(session=FakeSession([]), page_size=3, sleep_s=0, cache_dir=tmp_path)
    second = client2.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert first == second


def test_layer_metadata_uses_get_pjson():
    session = FakeSession([FakeResponse({"name": "Road Network", "fields": []})])
    client = MRWAClient(session=session, sleep_s=0)
    meta = client.layer_metadata(17)
    assert meta["name"] == "Road Network"
    url, params = session.calls[0]
    assert url.endswith("/17") and params == {"f": "pjson"}


def test_normalise_properties_renames_length_field():
    props = {"OBJECTID": 1, "GEOLOC.STLength()": 0.0003}
    out = normalise_properties(props)
    assert out == {"OBJECTID": 1, "GEOLOCSTLength": 0.0003}
    assert "GEOLOC.STLength()" in props  # original untouched
    assert normalise_properties({"GEOLOCSTLength": 1.0}) == {"GEOLOCSTLength": 1.0}
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_mrwa_client.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'dbe.mrwa_client'`

- [ ] **Step 3: Implement**

```python
"""Thin client for the Main Roads WA ArcGIS REST MapServer (open data, anonymous)."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
LAYER_ROAD_NETWORK = 17
LAYER_PAVEMENT = 12
LAYER_HIERARCHY = 16
LAYER_SPEED = 8
PAGE_SIZE = 2000
USER_AGENT = "DBE/0.1 (research tool; https://github.com/habibaarashid)"
TRANSIENT_STATUS = {429, 500, 502, 503, 504}
LENGTH_FIELD_ALIASES = ("GEOLOC.STLength()", "Shape__Length", "SHAPE.STLength()")
MAX_PAGES = 10_000

Envelope = tuple[float, float, float, float]


class MRWAError(RuntimeError):
    """Non-retryable error (bad request, schema problem, or retries exhausted)."""


class MRWATransientError(MRWAError):
    """Raised once a transient failure has exhausted its retries."""


def normalise_properties(props: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with the server's length field renamed to the CSV's GEOLOCSTLength."""
    out = dict(props)
    for alias in LENGTH_FIELD_ALIASES:
        if alias in out:
            out["GEOLOCSTLength"] = out.pop(alias)
            break
    return out


class MRWAClient:
    def __init__(
        self,
        session: Any | None = None,
        base_url: str = BASE_URL,
        page_size: int = PAGE_SIZE,
        cache_dir: Path | None = None,
        sleep_s: float = 0.2,
        max_retries: int = 5,
        timeout_s: float = 90.0,
    ) -> None:
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.page_size = int(page_size)
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.sleep_s = sleep_s
        self.max_retries = int(max_retries)
        self.timeout_s = timeout_s
        self._headers = {"User-Agent": USER_AGENT}

    # -- public -------------------------------------------------------------------------------

    def layer_metadata(self, layer_id: int) -> dict[str, Any]:
        return self._request("GET", f"{self.base_url}/{layer_id}", {"f": "pjson"})

    def query_envelope(self, layer_id: int, envelope: Envelope, out_fields: str = "*") -> list[dict[str, Any]]:
        xmin, ymin, xmax, ymax = envelope
        base = {
            "where": "1=1",
            "geometry": f"{xmin},{ymin},{xmax},{ymax}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
            "orderByFields": "OBJECTID ASC",
            "resultRecordCount": self.page_size,
        }
        url = f"{self.base_url}/{layer_id}/query"
        features: list[dict[str, Any]] = []
        offset = 0
        for page in range(MAX_PAGES):
            data = self._request("POST", url, {**base, "resultOffset": offset})
            page_feats = data.get("features", []) or []
            features.extend(page_feats)
            exceeded = bool(data.get("exceededTransferLimit") or data.get("properties", {}).get("exceededTransferLimit"))
            log.info("layer %s page %s: %s features (offset %s, exceeded=%s)", layer_id, page, len(page_feats), offset, exceeded)
            if not page_feats or (len(page_feats) < self.page_size and not exceeded):
                break
            offset += len(page_feats)
            if self.sleep_s:
                time.sleep(self.sleep_s)
        else:
            raise MRWAError(f"layer {layer_id}: exceeded {MAX_PAGES} pages; paging is not terminating")
        return features

    # -- internals ----------------------------------------------------------------------------

    def _request(self, method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        cache_path = self._cache_path(method, url, params)
        if cache_path is not None and cache_path.exists():
            log.debug("cache hit %s", cache_path.name)
            return json.loads(cache_path.read_text())
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, params=params, timeout=self.timeout_s, headers=self._headers)
                else:
                    resp = self.session.post(url, data=params, timeout=self.timeout_s, headers=self._headers)
                if resp.status_code in TRANSIENT_STATUS:
                    raise MRWATransientError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "error" in data:
                    raise MRWAError(f"ArcGIS error from {url}: {data['error']}")
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    cache_path.write_text(json.dumps(data))
                return data
            except MRWATransientError as exc:
                last_exc = exc
            except (requests.RequestException, ValueError) as exc:  # ValueError covers bad JSON
                last_exc = exc
            wait = min(2**attempt, 16)
            log.warning("%s %s failed (%s); retry %s/%s in %ss", method, url, last_exc, attempt + 1, self.max_retries, wait)
            if self.sleep_s:
                time.sleep(wait)
        raise MRWATransientError(f"giving up on {url} after {self.max_retries} attempts: {last_exc}")

    def _cache_path(self, method: str, url: str, params: dict[str, Any]) -> Path | None:
        if self.cache_dir is None:
            return None
        key_src = json.dumps([method, url, sorted((k, str(v)) for k, v in params.items())])
        key = hashlib.sha1(key_src.encode()).hexdigest()[:20]
        return self.cache_dir / f"{key}.json"
```

Note for the implementer: `MRWAError` raised inside the `try` for an ArcGIS error body is **not** caught by the `except` clauses (it is not a `MRWATransientError`, `RequestException` or `ValueError`), so it propagates immediately — that is the intended no-retry path. In tests `sleep_s=0` disables both the inter-page sleep and the retry back-off.

- [ ] **Step 4: Run to verify pass and lint**

Run: `uv run pytest tests/test_mrwa_client.py -q && uv run ruff check dbe tests`
Expected: `8 passed`; ruff clean.

- [ ] **Step 5: Commit**

```bash
git add dbe/mrwa_client.py tests/test_mrwa_client.py
git commit -m "feat(client): MRWA ArcGIS REST client with paging, retries and disk cache"
```

---

### Task S2.T2: Fixture loader, FixtureSource and a live smoke test

**Files:**
- Create: `tests/conftest.py`, `tests/test_fixtures_shape.py`, `tests/test_live_smoke.py`

**Interfaces:**
- Consumes: `MRWAClient`, `LocalProjection`.
- Produces (for later tests):
  - `tests/conftest.py`: `FIXTURES = Path(__file__).parent / "fixtures"`; `def load_fixture(layer_id: int) -> list[dict]` (reads `layer{id}_curtin2500.geojson` and returns `features`); `class FixtureSource:` `__init__(self, layers: dict[int, list[dict]])`, `query_envelope(self, layer_id, envelope, out_fields="*") -> list[dict]` (ignores the envelope, returns the recorded list; records calls in `self.calls`); pytest fixtures `fixture_source` (all four layers) and `curtin_2400` returning `dict(lat=-32.0018629, lon=115.8924599, radius_km=2.4)`.

- [ ] **Step 1: Write `tests/conftest.py`**

```python
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
CURTIN = dict(lat=-32.0018629, lon=115.8924599, radius_km=2.4)


def load_fixture(layer_id: int) -> list[dict]:
    path = FIXTURES / f"layer{layer_id}_curtin2500.geojson"
    return json.loads(path.read_text())["features"]


class FixtureSource:
    """Duck-typed stand-in for MRWAClient that serves recorded features."""

    def __init__(self, layers: dict[int, list[dict]]):
        self.layers = layers
        self.calls: list[tuple[int, tuple]] = []

    def query_envelope(self, layer_id: int, envelope, out_fields: str = "*") -> list[dict]:
        self.calls.append((layer_id, tuple(envelope)))
        return list(self.layers.get(layer_id, []))


@pytest.fixture(scope="session")
def fixture_source() -> FixtureSource:
    return FixtureSource({lid: load_fixture(lid) for lid in (17, 12, 16, 8)})


@pytest.fixture
def curtin_2400() -> dict:
    return dict(CURTIN)


@pytest.fixture(autouse=True)
def _reset_fixture_source_calls(request):
    """Clear FixtureSource.calls before each test.

    `fixture_source` is session-scoped for speed, so without this its `.calls` log would
    accumulate across tests and `calls[0]` would refer to some earlier test's first call.
    """
    if "fixture_source" in request.fixturenames:
        request.getfixturevalue("fixture_source").calls.clear()
```

> **Why the autouse reset exists (added 2026-09-23 after an Opus review of `50acb36`).** Without it,
> a test that makes one call observes the whole session's call log, and `calls[0]` belongs to an
> earlier test — verified empirically. S4.T2 asserts `fixture_source.calls[0][0] == 17`; without the
> reset that assertion is a tautology, and strengthening it plants an order-dependent flake.

- [ ] **Step 2: Write `tests/test_fixtures_shape.py`** (guards the recorded data so later tasks can rely on it)

```python
from dbe.mrwa_client import normalise_properties
from tests.conftest import load_fixture

EXPECTED_17 = [
    "ROAD", "ROAD_NAME", "COMMON_USAGE_NAME", "START_SLK", "END_SLK", "CWY", "START_TRUE_DIST", "END_TRUE_DIST",
    "NETWORK_TYPE", "RA_NO", "RA_NAME", "LG_NO", "LG_NAME", "START_NODE_NO", "START_NODE_NAME", "END_NODE_NO",
    "END_NODE_NAME", "DATUM_NE_ID", "NM_BEGIN_MP", "NM_END_MP", "NETWORK_ELEMENT", "ROUTE_NE_ID", "OBJECTID",
    "GlobalID", "GEOLOCSTLength",
]


def test_layer17_fixture_has_all_original_columns():
    feats = load_fixture(17)
    assert len(feats) > 100
    for i, feat in enumerate(feats):
        props = normalise_properties(feat["properties"])
        missing = [c for c in EXPECTED_17 if c not in props]
        assert missing == [], f"feature {i} is missing columns: {missing}"


def test_layer17_fixture_geometries_are_lines():
    feats = load_fixture(17)
    assert len(feats) > 100
    kinds = {f["geometry"]["type"] for f in feats if f.get("geometry")}
    assert kinds, "no feature carries a geometry"
    assert kinds <= {"LineString", "MultiLineString"}
    null_geometry = [i for i, f in enumerate(feats) if not f.get("geometry")]
    assert null_geometry == [], f"features with null geometry: {null_geometry[:10]}"


def test_layer12_fixture_has_width_fields_and_state_roads_only():
    feats = load_fixture(12)
    assert len(feats) > 0
    required = ("ROAD", "CWY", "START_SLK", "END_SLK", "TOTAL_SEAL_WIDTH", "NO_OF_LANES")
    for i, feat in enumerate(feats):
        missing = [c for c in required if c not in feat["properties"]]
        assert missing == [], f"feature {i} is missing columns: {missing}"
    assert {f["properties"].get("NETWORK_TYPE") for f in feats} <= {"State Road"}


def test_layer16_and_8_fixtures_have_join_keys():
    for lid in (16, 8):
        feats = load_fixture(lid)
        assert len(feats) > 0
        for i, feat in enumerate(feats):
            missing = [c for c in ("ROAD", "START_SLK", "END_SLK") if c not in feat["properties"]]
            assert missing == [], f"layer {lid} feature {i} is missing columns: {missing}"
```

If `test_layer12_fixture_has_width_fields_and_state_roads_only` fails on the `NETWORK_TYPE` assertion because layer 12 also carries Local Road rows, that is **good news**: record it in `progress.md` → Decisions log ("layer 12 has local-road widths too"), change the assertion to `assert len(kinds) >= 1`, and tell the orchestrator — §3.8's expectation for `WIDTH_SOURCE` counts changes.

- [ ] **Step 3: Write `tests/test_live_smoke.py`**

```python
import pytest

from dbe.geometry import LocalProjection
from dbe.mrwa_client import LAYER_ROAD_NETWORK, MRWAClient

pytestmark = pytest.mark.network


def test_live_small_envelope_returns_roads():
    proj = LocalProjection(-32.0018629, 115.8924599)
    env = proj.envelope_wgs84(300.0)
    feats = MRWAClient(sleep_s=0).query_envelope(LAYER_ROAD_NETWORK, env)
    assert len(feats) >= 1
    assert feats[0]["geometry"]["type"] in ("LineString", "MultiLineString")
    assert "ROAD" in feats[0]["properties"]
```

- [ ] **Step 4: Run offline and (once) online**

Run: `uv run pytest -q` → Expected: all previous tests plus `4 passed` from the fixture-shape file; the network test is deselected.
Run: `uv run pytest -m network -q` → Expected: `1 passed` (needs internet; if the service is down, note it in progress.md and continue — it is not a blocker for Gate A).

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py tests/test_fixtures_shape.py tests/test_live_smoke.py
git commit -m "test: fixture loader, FixtureSource and live smoke test"
```

---

## Gate A — Opus review of Segments 0–2

Checklist for the Opus reviewer (paste into §0.7 template):
1. `uv run pytest -q` passes; `uv run ruff check .` clean; `uv run pytest -m network -q` passed at least once in this segment (see Verification log).
2. `docs/task_docs/source_verification.md` exists and names the confirmed `HIERARCHY_FIELD` and `SPEED_FIELD`; `supportsPagination` recorded.
3. Fixtures: four `*_curtin2500.geojson` files each < 5 MB; layer 12 non-empty; README in `tests/fixtures/` present.
4. `geometry.py`: `always_xy=True` on both transformers; `envelope_wgs84` returns lon/lat order; `segment_metrics` handles zero-length geometry without division by zero; WKT rounding is 7 decimals.
5. `mrwa_client.py`: POST for queries, GET for metadata; ArcGIS `error` body is not retried; paging stops on short page *and* on empty page; cache key includes method, URL and all params; `MAX_PAGES` guard present.
6. No dependency outside §1; no reading of `data/` anywhere in `dbe/`.
7. `progress.md`: rows S0.T1–S2.T2 `done` with SHAs; Decisions log has entries for any field-name or radius change.

Verdict → `progress.md` → Gate log. On PASS, proceed to Segment 3.

### Gate A carried amendments (verdict PASS, 2026-09-23) — **the next orchestrator must action these**

Gate A passed with no Critical findings. Four Important and six Minor findings were raised, all
forward-looking: they affect the 10 km production run, not the correctness of Segments 0–2. Each is
recorded here at the task that must act on it. Two were independently re-verified by the orchestrator.

| Ref | Act at | What to do |
|---|---|---|
| **I1** | **S4.T5, before the 10 km run** | Make the disk cache crash-safe. |
| **I2** | S4.T2 | Pin the envelope the client is actually sent. |
| **I3** | S4.T5 | Cross-check the row count per layer. |
| **I4** | S4.T2 | Widen the skip guard to catch empty geometry. |
| **M1** | S4.T4 | Do not build the production client with `sleep_s=0`. |
| **M2/M3/M6** | Gate B | Sanity-table and threshold notes. |

**I1 — the cache is not crash-safe, and a corrupt entry is permanently fatal.** Verified by the
orchestrator: write a cache entry, truncate the file, re-query → `json.JSONDecodeError`, and the
network is **never attempted** (0 HTTP calls) because `json.loads(cache_path.read_text())` sits
outside the retry `try`. The 10 km run writes roughly 26 pages × 4 layers through `write_text`;
interrupt it once and every later run dies on the same poisoned page — destroying the resumability
the cache exists to provide (§3.1). Fix in `dbe/mrwa_client.py`:

```python
        if cache_path is not None and cache_path.exists():
            try:
                return json.loads(cache_path.read_text())
            except (ValueError, OSError) as exc:
                log.warning("discarding unreadable cache entry %s (%s); refetching", cache_path.name, exc)
                cache_path.unlink(missing_ok=True)
```

and make the write atomic so a partial file is never visible:

```python
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = cache_path.with_suffix(".json.tmp")
                    tmp.write_text(json.dumps(data))
                    tmp.replace(cache_path)
```

Add a test that truncates a cache entry and asserts the client refetches instead of raising.

**I2 — no offline test pins the envelope the client is sent.** `FixtureSource.query_envelope`
records the envelope into `.calls` but ignores it, returning all recorded features regardless, so
every fixture-driven test passes with an arbitrarily wrong envelope. The only guard is one 300 m
live smoke test. The seam is correct **today** (the gate proved the wire format round-trips
bit-identically, axis order is right, and a 200,000-azimuth geodesic circle escapes the box by at
most 4.8 mm at 10 km) — but nothing would catch a regression. In S4.T2's test, assert the envelope:

```python
    proj = LocalProjection(curtin_2400["lat"], curtin_2400["lon"])
    expected_env = proj.envelope_wgs84(curtin_2400["radius_km"] * 1000.0)
    assert [layer for layer, _ in fixture_source.calls] == [17, 12, 16, 8]
    for _, env in fixture_source.calls:
        assert env == pytest.approx(expected_env)
```

**I3 — silent truncation is possible if the service ever lowers `maxRecordCount`.** Paging
terminates on a short page, which is sound *only because* `PAGE_SIZE = 2000` equals the confirmed
`maxRecordCount = 2000`. A server capping pages at 1000 while omitting `exceededTransferLimit`
returns 1000 of 5000 features with no exception — a silent breach of §1's "every layer-17 segment
that intersects the circle is output", and §3.8's 12k–45k band is far too wide to notice. The
throwaway fixture recorder already guarded against this and the production client does not. In
S4.T5, before writing the CSV, issue one `returnCountOnly=true` query per layer and assert it
matches the fetched count; or clamp `page_size` to the layer's `maxRecordCount` from
`layer_metadata`.

**I4 — SUPERSEDED 2026-09-23 by a broader guard; the original text follows.** The enumerated
guard below closed only two of six malformed shapes. The S4.T2 review found four more that still
aborted the run — a one-coordinate line, an empty multi-part geometry, a one-coordinate part, and a
wrong geometry type — each raising from shapely or GEOS rather than failing the truthiness test.
Enumerating shapes is the wrong strategy for untrusted data from an external service, so
`extract()` now wraps the conversion in `try/except Exception`, logs the exception type, and counts
into a new `skipped_bad_geometry` metadata key. `seen.add(oid)` also moved below the geometry guards,
so a malformed copy of an OBJECTID can no longer consume the identifier and cause the real feature to
be dropped as a duplicate. Verified: all six shapes now skip cleanly and the row count is unchanged.

**I4 (original) — an empty-coordinates geometry crashes the run.** Verified by the orchestrator:
`geojson_to_line({"type": "LineString", "coordinates": []})` is accepted (it *is* a LineString) and
returns `LINESTRING EMPTY`, then `segment_metrics` hits `parts[0].coords[0]` → `IndexError`. §3.6
covers `geometry: null` only, and S4.T2's planned guard `if not feat.get("geometry")` does not fire
because **a dict with empty coordinates is truthy**. One such feature anywhere in the 10 km pull
aborts the run after minutes of fetching. Widen the guard in S4.T2:

```python
        if not (feat.get("geometry") or {}).get("coordinates"):
            skipped_no_geometry += 1
            continue
```

**M1 — `sleep_s=0` disables the retry back-off, not just the inter-page delay.** The guard is
`if self.sleep_s: time.sleep(wait)`, so a transient 503 becomes five rapid-fire requests at the
service. `tests/test_live_smoke.py` uses `MRWAClient(sleep_s=0)` and S4.T4 must not copy that idiom
into the production path — leave the default `sleep_s=0.2`.

**M2/M3/M6 — for the Gate B sanity table.** (a) The envelope carries zero margin; the residual risk
is the ~1.5 m GDA94/WGS84 shift excluding a segment whose only contact lies within ~1.5 m of a box
extreme, and such rows have `INSIDE_FRACTION ≈ 0`. (b) `MAX_PAGES = 10_000` is not a practical
runaway guard on a ~26-page run; consider 200 for production. (c) §3.8 gives page counts for layer
17 only — the paging path is on the critical path four times. Scaled from the fixtures by the 16×
area factor: layer 17 ≈ 15 pages, layer 16 ≈ 6, layer 8 ≈ 5, layer 12 ≈ 1.

**Forward risks judged SAFE TO CARRY by the gate** (do not spend time re-litigating): `INSIDE_FRACTION`
under-reports on self-overlapping geometry (always *under*, and it is a reported column only — row
inclusion uses `intersects`, so no row is ever dropped; S6.T1's README should state it is a lower
bound); a tangent segment giving `intersects=True, inside_fraction=0.0` (spec-conformant, and
S4.T2's `or DIST_TO_CENTRE_M <= …` clause already covers it — keep that clause); `iter_vertices`
raising on Z coordinates (unreachable — nothing sets `returnZ`, layer 17 has no `hasZ`, and all
15,299 fixture coordinates are 2-tuples; `x, y = coord[0], coord[1]` is free insurance at S4.T2);
`_parts` accepting a Point (gated, because S4.T2 routes every feature through `geojson_to_line`,
which rejects Point — this re-opens if any Segment 3–4 code calls `segment_metrics` directly).

---

## Segment 3 — Linear-referencing joins and enrichment (Sonnet, TDD)

### Task S3.T1: SLK overlap join primitives

**Files:**
- Create: `dbe/slk_join.py`, `tests/test_slk_join.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class SlkSpan:` `road: str, cwy: str, start_slk: float, end_slk: float, attrs: dict` (`attrs` excluded from `__eq__`/`__hash__` via `field(compare=False, hash=False, default_factory=dict)`)
  - `def overlap_len(a0: float, a1: float, b0: float, b1: float) -> float` (km; 0 if disjoint; order-insensitive)
  - `def cwy_compatible(a: str, b: str) -> bool` (equal, or either is `"Single"`)
  - `def span_from_properties(props: dict) -> SlkSpan | None` (None when ROAD/START_SLK/END_SLK missing or non-numeric; missing/empty CWY → `"Single"`)
  - `def index_by_road(spans: Iterable[SlkSpan]) -> dict[str, list[SlkSpan]]`
  - `def overlapping(target: SlkSpan, by_road: dict[str, list[SlkSpan]]) -> list[tuple[SlkSpan, float]]` — same road, compatible CWY, positive overlap; if any exact-CWY match exists, `Single` fallbacks are dropped; a zero-length target matches spans containing its SLK with weight 1.0.
    **Note the mixed unit, deliberately:** the returned weight is kilometres of overlap for a normal target but the sentinel `1.0` for a zero-length one. `weighted_mean` normalises, so the units cancel there; `dominant_value` compares weights directly, so in principle a multi-kilometre span could outrank a point match. It cannot arise today, because a zero-length target only ever matches spans that contain its SLK and every weight in that result set is the same `1.0`. Left as-is rather than normalised, because changing it would alter `weighted_mean`'s behaviour on point targets for no gain.
  - `def dominant_value(target, by_road, field_name: str)` → value from the overlapping span with the largest overlap whose value is not None/empty; else None
  - `def weighted_mean(target, by_road, field_name: str) -> float | None` → overlap-weighted mean of numeric values; None if nothing numeric
  - **The parameter is `field_name`, not `field`** — `field` would shadow `dataclasses.field`, which this module imports. Every S3.T2 call site passes it positionally, so the name is not load-bearing, but the Interfaces block and the Step 3 code must agree. (Flagged by the S3.T1 implementer; the Step 3 code was always `field_name`.)

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from dbe.slk_join import (
    SlkSpan,
    cwy_compatible,
    dominant_value,
    index_by_road,
    overlap_len,
    overlapping,
    span_from_properties,
    weighted_mean,
)


def _span(road, cwy, s, e, **attrs):
    return SlkSpan(road, cwy, s, e, attrs)


def test_overlap_len_basic_cases():
    assert overlap_len(0, 1, 0.5, 2) == pytest.approx(0.5)
    assert overlap_len(0.5, 2, 0, 1) == pytest.approx(0.5)
    assert overlap_len(0, 1, 1, 2) == 0.0
    assert overlap_len(0, 1, 2, 3) == 0.0
    assert overlap_len(1, 0, 0.25, 0.75) == pytest.approx(0.5)  # reversed input tolerated


def test_cwy_compatible():
    assert cwy_compatible("Left", "Left")
    assert cwy_compatible("Left", "Single") and cwy_compatible("Single", "Right")
    assert not cwy_compatible("Left", "Right")


def test_span_from_properties_handles_missing_and_bad_values():
    assert span_from_properties({"ROAD": "H001", "START_SLK": "0", "END_SLK": 0.3}) == _span("H001", "Single", 0.0, 0.3)
    assert span_from_properties({"ROAD": "H001", "CWY": "", "START_SLK": 0, "END_SLK": 1}).cwy == "Single"
    assert span_from_properties({"ROAD": "H001", "START_SLK": None, "END_SLK": 1}) is None
    assert span_from_properties({"START_SLK": 0, "END_SLK": 1}) is None
    assert span_from_properties({"ROAD": "H001", "START_SLK": "abc", "END_SLK": 1}) is None


def test_overlapping_prefers_exact_cwy_over_single():
    sources = index_by_road([
        _span("H001", "Single", 0, 10, w=5.0),
        _span("H001", "Left", 0, 10, w=7.0),
        _span("H002", "Left", 0, 10, w=9.0),
    ])
    target = _span("H001", "Left", 2, 4)
    matched = overlapping(target, sources)
    assert [s.attrs["w"] for s, _ in matched] == [7.0]
    target_right = _span("H001", "Right", 2, 4)
    assert [s.attrs["w"] for s, _ in overlapping(target_right, sources)] == [5.0]  # only the Single fallback


def test_overlapping_zero_length_target_matches_containing_span():
    sources = index_by_road([_span("H001", "Single", 0, 1, w=1.0), _span("H001", "Single", 1, 2, w=2.0)])
    matched = overlapping(_span("H001", "Single", 1.5, 1.5), sources)
    assert [(s.attrs["w"], ov) for s, ov in matched] == [(2.0, 1.0)]


def test_dominant_value_picks_largest_overlap_and_skips_nulls():
    sources = index_by_road([
        _span("H001", "Single", 0, 0.4, h="Access Road"),
        _span("H001", "Single", 0.4, 2.0, h="Distributor"),
        _span("H001", "Single", 0, 2.0, h=None),
    ])
    assert dominant_value(_span("H001", "Single", 0.0, 1.0), sources, "h") == "Distributor"
    assert dominant_value(_span("H999", "Single", 0.0, 1.0), sources, "h") is None


def test_weighted_mean_uses_overlap_weights():
    sources = index_by_road([
        _span("H001", "Single", 0, 1, w=10.0),
        _span("H001", "Single", 1, 4, w=20.0),
        _span("H001", "Single", 0, 4, w="not a number"),
    ])
    # target 0..2 overlaps 1 km of w=10 and 1 km of w=20 -> 15
    assert weighted_mean(_span("H001", "Single", 0, 2), sources, "w") == pytest.approx(15.0)
    # target 0..4 -> (10*1 + 20*3)/4 = 17.5
    assert weighted_mean(_span("H001", "Single", 0, 4), sources, "w") == pytest.approx(17.5)
    assert weighted_mean(_span("H001", "Single", 5, 6), sources, "w") is None
```

> **RESOLVED 2026-09-23 — see the box below.** The original text is kept for the record.
>
> **Open semantic question, must be settled before S4.T5 (from the S3.T1 review, I1).** When the
> target carriageway is `Single` but the only matching sources are `Left` and `Right`, the
> `exact or out` fallback returns **both**, so `weighted_mean` averages the two sides of a divided
> road and reports a 16 m road as 8 m. This never occurs in the 2.5 km fixtures — in fact the
> `cwy_compatible` wildcard never fires at all there, since every real match is exact-CWY (layer 12:
> 38 Single/Single, 14 Left/Left, 13 Right/Right). **Do not read that silence as safety:** the
> production run is a 10 km radius, where the fixture's evidence stops applying. Before S4.T5,
> decide what that case should mean — sum the carriageways, take the maximum, or leave it blank —
> and pin it with a test. Leaving it as an average is a defensible choice but must be a *chosen* one.

> **DECISION (2026-09-23): keep the overlap-weighted mean, and make any occurrence visible.**
>
> Options considered: average the carriageways (status quo), sum them, take the maximum, or blank
> the width. **Chosen: keep the mean.** An average of two *measured* carriageway widths is derived
> from real data, not invented, so it does not breach §1's "width is never estimated" rule — whereas
> summing invents a figure that ignores the median strip, and blanking discards measurements that
> genuinely exist. The mean's weakness is real but narrower: for a genuinely divided road it reports
> roughly one carriageway's width rather than the whole roadway.
>
> **Measured reachability: 0 occurrences in the 2.5 km fixtures** (orchestrator, 2026-09-23 — every
> `Single` segment that matches pavement matches `Single` pavement; the wildcard branch never fires).
> Pavement carriageway split is 58 Single / 28 Left / 27 Right.
>
> **Obligation on S4.T5:** count and report this case at 10 km. If it is non-zero, **stop and revisit
> before accepting the output** — do not silently ship halved widths. If it is zero, the question is
> academic and the decision costs nothing.

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_slk_join.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'dbe.slk_join'`

- [ ] **Step 3: Implement**

```python
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
    # A non-finite SLK is fatal, not merely odd: `max`/`min` fall through on NaN, so
    # `overlap_len(0, 10, nan, nan)` returns the FULL target length — the largest weight any span
    # can score. One corrupt record would then outrank every genuine one and silently rewrite the
    # width. stdlib `json` accepts bare NaN/Infinity, so the path is open. See S3.T1 review, C1.
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
            continue  # a NaN attribute would otherwise propagate into the CSV as the literal "nan"
        num += v * ov
        den += ov
    return (num / den) if den > 0.0 else None
```

- [ ] **Step 4: Run to verify pass and lint**

Run: `uv run pytest tests/test_slk_join.py -q && uv run ruff check dbe tests`
Expected: `7 passed`; ruff clean.

- [ ] **Step 5: Commit**

```bash
git add dbe/slk_join.py tests/test_slk_join.py
git commit -m "feat(slk): linear-referencing overlap joins with CWY-aware matching"
```

---

### Task S3.T2: Enrichment from layers 12 / 16 / 8 with width provenance

**Files:**
- Create: `dbe/enrich.py`, `tests/test_enrich.py`

**Interfaces:**
- Consumes: everything in `slk_join.py`; `tests/conftest.py` fixtures; confirmed field names from `docs/task_docs/source_verification.md`.
- Produces:
  - constants `HIERARCHY_FIELD = "ROAD_HIERARCHY"`, `SPEED_FIELD = "SPEED_LIMIT"` — both **confirmed correct** in S0.T2, no rename needed. Real `ROAD_HIERARCHY` values in the fixtures: `Access Road`, `Distributor A`, `Distributor B`, `Local Distributor`, `Primary Distributor` (plus `Regional Distributor` in the service renderer). Real `SPEED_LIMIT` values are **strings with units**: `30km/h` … `70km/h`, plus the free-text `50km/h applies in built up areas or 110km/h outside built up areas` — **never cast to a number**; `PAVEMENT_MEAN_FIELDS: dict[str, str]` (source → output), `PAVEMENT_DOMINANT_FIELDS: dict[str, str]`, `WIDTH_SOURCE_MRWA = "mrwa_pavement"`, `WIDTH_SOURCE_NONE = "none"`, `ENRICH_COLUMNS: list[str]` (exactly the 12 names in §3.3, same order)
  - `@dataclass class EnrichIndex:` `pavement: dict[str, list[SlkSpan]]`, `hierarchy: dict[str, list[SlkSpan]]`, `speed: dict[str, list[SlkSpan]]`; classmethod `from_features(pavement: list[dict], hierarchy: list[dict], speed: list[dict]) -> EnrichIndex` (builds spans via `span_from_properties`, skipping None)
  - `def enrich_segment(props: dict, index: EnrichIndex) -> dict` → dict with exactly the `ENRICH_COLUMNS` keys

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from dbe.enrich import ENRICH_COLUMNS, EnrichIndex, enrich_segment

EXPECTED_COLUMNS = [
    "ROAD_HIERARCHY", "SPEED_LIMIT", "TOTAL_PAVE_WIDTH_M", "TOTAL_SEAL_WIDTH_M", "TRAFFICABLE_SURF_WIDTH_M",
    "NO_OF_LANES", "SEALED_SHOULDER_L_M", "SEALED_SHOULDER_R_M", "KERB_L", "KERB_R", "WIDTH_M", "WIDTH_SOURCE",
]


def _f(**props):
    return {"type": "Feature", "geometry": None, "properties": props}


def _index():
    pavement = [
        _f(ROAD="H001", CWY="Left", START_SLK=0.0, END_SLK=1.0, TOTAL_PAVE_WIDTH=12.0, TOTAL_SEAL_WIDTH=10.0,
           TRAFFICABLE_SURF_WIDTH=9.0, NO_OF_LANES=3, SEALED_SHOULDER_L=0.5, SEALED_SHOULDER_R=1.0, KERB_L="Y", KERB_R="N"),
        _f(ROAD="H001", CWY="Left", START_SLK=1.0, END_SLK=3.0, TOTAL_PAVE_WIDTH=8.0, TOTAL_SEAL_WIDTH=7.0,
           TRAFFICABLE_SURF_WIDTH=7.0, NO_OF_LANES=2, SEALED_SHOULDER_L=0.0, SEALED_SHOULDER_R=0.0, KERB_L="N", KERB_R="N"),
    ]
    hierarchy = [_f(ROAD="H001", CWY="Single", START_SLK=0.0, END_SLK=5.0, ROAD_HIERARCHY="Primary Distributor"),
                 _f(ROAD="1010001", CWY="Single", START_SLK=0.0, END_SLK=5.0, ROAD_HIERARCHY="Access Road")]
    # SPEED_LIMIT is esriFieldTypeString with the units embedded — confirmed in S0.T2 and
    # re-confirmed against the fixtures: real values are "30km/h" … "70km/h" plus one free-text
    # value. Never cast it to a number; the synthetic data mirrors the real form deliberately.
    speed = [_f(ROAD="H001", CWY="Single", START_SLK=0.0, END_SLK=5.0, SPEED_LIMIT="70km/h"),
             _f(ROAD="1010001", CWY="Single", START_SLK=0.0, END_SLK=0.5, SPEED_LIMIT="50km/h")]
    return EnrichIndex.from_features(pavement, hierarchy, speed)


def test_columns_constant_matches_spec():
    assert ENRICH_COLUMNS == EXPECTED_COLUMNS


def test_state_road_gets_weighted_widths_and_dominant_categoricals():
    out = enrich_segment({"ROAD": "H001", "CWY": "Left", "START_SLK": 0.0, "END_SLK": 2.0}, _index())
    assert list(out.keys()) == EXPECTED_COLUMNS
    assert out["TOTAL_SEAL_WIDTH_M"] == pytest.approx(8.5)   # (10*1 + 7*1) / 2
    assert out["TOTAL_PAVE_WIDTH_M"] == pytest.approx(10.0)
    # These five columns previously had their key asserted but never their value. Because
    # `enrich_segment` seeds its output with `dict.fromkeys(ENRICH_COLUMNS)`, the key-order
    # assertion passes no matter what is written to them — so deleting the SEALED_SHOULDER_R
    # mapping (every right shoulder vanishes from all 1850 rows) or swapping left for right both
    # passed the entire suite. Verified 2026-09-23. The asymmetric expected values are
    # load-bearing: were they equal, a swap would still go undetected.
    assert out["TRAFFICABLE_SURF_WIDTH_M"] == pytest.approx(8.0)
    assert out["SEALED_SHOULDER_L_M"] == pytest.approx(0.25)
    assert out["SEALED_SHOULDER_R_M"] == pytest.approx(0.5)
    assert out["KERB_L"] == "Y"
    assert out["KERB_R"] == "N"
    # Both pavement spans overlap the target by exactly 1 km. `dominant_value` compares with a
    # strict `>`, so the FIRST span encountered wins — deterministic, and pinned here so a refactor
    # cannot silently change the tie-break.
    assert out["NO_OF_LANES"] == 3
    assert out["ROAD_HIERARCHY"] == "Primary Distributor"
    assert out["SPEED_LIMIT"] == "70km/h"
    assert out["WIDTH_M"] == 8.5 and out["WIDTH_SOURCE"] == "mrwa_pavement"


def test_local_road_has_hierarchy_and_speed_but_no_width():
    out = enrich_segment({"ROAD": "1010001", "CWY": "Single", "START_SLK": 0.0, "END_SLK": 0.3}, _index())
    assert out["ROAD_HIERARCHY"] == "Access Road"
    assert out["SPEED_LIMIT"] == "50km/h"
    assert out["TOTAL_SEAL_WIDTH_M"] is None and out["WIDTH_M"] is None
    assert out["WIDTH_SOURCE"] == "none"


def test_unparseable_slk_yields_all_blank_but_correct_keys():
    out = enrich_segment({"ROAD": "H001", "CWY": "Left", "START_SLK": None, "END_SLK": 2.0}, _index())
    assert list(out.keys()) == EXPECTED_COLUMNS
    assert all(v is None for k, v in out.items() if k != "WIDTH_SOURCE")
    assert out["WIDTH_SOURCE"] == "none"


def test_road_absent_from_every_layer_yields_blank_columns_not_missing_keys():
    """A parseable road that matches nothing takes a different branch from an unparseable SLK.

    The output must still carry all twelve keys in order — S4.T2 builds CSV rows straight from
    these keys, so a missing one would shift every subsequent column in the file.
    """
    out = enrich_segment({"ROAD": "ZZZ999", "CWY": "Single", "START_SLK": 0.0, "END_SLK": 1.0}, _index())
    assert list(out.keys()) == EXPECTED_COLUMNS
    assert all(v is None for k, v in out.items() if k != "WIDTH_SOURCE")
    assert out["WIDTH_SOURCE"] == "none"


def test_width_is_rounded_to_two_decimals():
    idx = EnrichIndex.from_features(
        [_f(ROAD="H001", CWY="Single", START_SLK=0, END_SLK=1, TOTAL_SEAL_WIDTH=7.333333)], [], [])
    out = enrich_segment({"ROAD": "H001", "CWY": "Single", "START_SLK": 0, "END_SLK": 1}, idx)
    assert out["WIDTH_M"] == 7.33 and out["TOTAL_SEAL_WIDTH_M"] == 7.33


def test_fixture_state_roads_get_widths(fixture_source):
    """Measured against the real 2.5 km fixtures on 2026-09-23, not guessed.

    State roads 65/65 get a width, local roads 0/1763 do, hierarchy 1850/1850, and local-road
    speed 1683/1763. The earlier `>= 0.8` thresholds were placeholders that would have passed
    while a fifth of the data silently went missing.

    THE EXACT COUNTS BELOW ARE TIED TO THE COMMITTED FIXTURES. If they are ever regenerated
    (`uv run python scripts/record_fixtures.py`, e.g. at a different radius or after MRWA updates
    the layers), these numbers must be re-measured, not deleted — otherwise four assertions fail
    at once with no hint of why. The structural counts (state/local split, width coverage) should
    hold; the speed-coverage figure is the one expected to drift.
    """
    idx = EnrichIndex.from_features(fixture_source.layers[12], fixture_source.layers[16], fixture_source.layers[8])
    feats = fixture_source.layers[17]
    state = [f["properties"] for f in feats if f["properties"].get("NETWORK_TYPE") == "State Road"]
    local = [f["properties"] for f in feats if f["properties"].get("NETWORK_TYPE") == "Local Road"]
    assert len(state) == 65 and len(local) == 1763

    # Every state road gets a measured width from layer 12.
    state_widths = [enrich_segment(p, idx)["WIDTH_M"] for p in state]
    assert all(w is not None for w in state_widths)
    assert all(3.0 <= w <= 40.0 for w in state_widths)

    # No local road EVER gets a width: layer 12 is State Road only, and a width is never invented.
    # This is the guard on the project's central constraint — see §1 "Width is never estimated".
    local_enriched = [enrich_segment(p, idx) for p in local]
    assert all(e["WIDTH_M"] is None for e in local_enriched)
    assert {e["WIDTH_SOURCE"] for e in local_enriched} == {"none"}
    assert {enrich_segment(p, idx)["WIDTH_SOURCE"] for p in state} == {"mrwa_pavement"}

    # Hierarchy covers the whole network, state and local alike.
    assert all(e["ROAD_HIERARCHY"] is not None for e in local_enriched)
    assert all(enrich_segment(p, idx)["ROAD_HIERARCHY"] is not None for p in state)

    # Speed is a string carrying its units, and is not universal on local roads.
    speeds = {e["SPEED_LIMIT"] for e in local_enriched if e["SPEED_LIMIT"] is not None}
    assert speeds and all(isinstance(v, str) and "km/h" in v for v in speeds)
    # 1683 of 1763 measured 2026-09-23. Deliberately a band, not an equality: unlike the
    # structural counts above, this one tracks how many local roads happen to carry a speed
    # record, which can drift on a service refresh without anything being wrong.
    covered = sum(e["SPEED_LIMIT"] is not None for e in local_enriched)
    assert covered > 1600
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_enrich.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'dbe.enrich'`

- [ ] **Step 3: Implement**

```python
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
PAVEMENT_DOMINANT_FIELDS: dict[str, str] = {"NO_OF_LANES": "NO_OF_LANES", "KERB_L": "KERB_L", "KERB_R": "KERB_R"}

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
        return cls(index_by_road(_spans(pavement)), index_by_road(_spans(hierarchy)), index_by_road(_spans(speed)))


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
```

- [ ] **Step 4: Run to verify pass and lint**

Run: `uv run pytest tests/test_enrich.py -q && uv run ruff check dbe tests`
Expected: `6 passed`; ruff clean. If `test_fixture_state_roads_get_widths` fails on the 0.8 ratio, print the unmatched State Road `ROAD`/`CWY`/SLK values and compare with layer 12 rows for the same road before changing anything — a CWY mismatch pattern (e.g. layer 12 uses `Single` where 17 uses `Left`/`Right`) is handled by `cwy_compatible`; an SLK offset pattern is a real finding → Decisions log.

- [ ] **Step 5: Commit**

```bash
git add dbe/enrich.py tests/test_enrich.py
git commit -m "feat(enrich): width, hierarchy and speed enrichment with WIDTH_SOURCE provenance"
```

---

## Segment 4 — Schema, pipeline, export, CLI, end-to-end (Sonnet, TDD)

### Task S4.T1: Column contract in `schema.py`

**Files:**
- Create: `dbe/schema.py`, `tests/test_schema.py`

**Interfaces:**
- Consumes: `dbe.enrich.ENRICH_COLUMNS`.
- Produces: `ORIGINAL_COLUMNS` (25), `GEOMETRY_COLUMNS` (9), `ENRICH_COLUMNS` (re-exported, 12), `OSM_COLUMNS` (5), `PROVENANCE_COLUMNS` (2), `OUTPUT_COLUMNS` (53), `VERTEX_COLUMNS` (9), `ID_COLUMNS` (columns kept as text in XLSX), `DATA_SOURCE: str`, `LICENCE: str`, `DATUM_NOTE: str`, `OSM_ATTRIBUTION: str`.

- [ ] **Step 1: Write the failing test**

```python
from dbe import schema
from dbe.enrich import ENRICH_COLUMNS

ORIGINAL = [
    "ROAD",
    "ROAD_NAME",
    "COMMON_USAGE_NAME",
    "START_SLK",
    "END_SLK",
    "CWY",
    "START_TRUE_DIST",
    "END_TRUE_DIST",
    "NETWORK_TYPE",
    "RA_NO",
    "RA_NAME",
    "LG_NO",
    "LG_NAME",
    "START_NODE_NO",
    "START_NODE_NAME",
    "END_NODE_NO",
    "END_NODE_NAME",
    "DATUM_NE_ID",
    "NM_BEGIN_MP",
    "NM_END_MP",
    "NETWORK_ELEMENT",
    "ROUTE_NE_ID",
    "OBJECTID",
    "GlobalID",
    "GEOLOCSTLength",
]


def test_original_columns_match_provided_csv_header():
    assert schema.ORIGINAL_COLUMNS == ORIGINAL


def test_output_columns_composition_and_uniqueness():
    assert schema.OUTPUT_COLUMNS == (
        schema.ORIGINAL_COLUMNS
        + schema.GEOMETRY_COLUMNS
        + schema.ENRICH_COLUMNS
        + schema.OSM_COLUMNS
        + schema.PROVENANCE_COLUMNS
    )
    assert len(schema.OUTPUT_COLUMNS) == 53
    assert len(set(schema.OUTPUT_COLUMNS)) == 53
    assert schema.ENRICH_COLUMNS == ENRICH_COLUMNS
    assert schema.GEOMETRY_COLUMNS == [
        "START_LAT",
        "START_LON",
        "END_LAT",
        "END_LON",
        "VERTEX_COUNT",
        "LENGTH_M",
        "DIST_TO_CENTRE_M",
        "INSIDE_FRACTION",
        "GEOMETRY_WKT",
    ]
    assert schema.OSM_COLUMNS == ["OSM_WAY_ID", "OSM_HIGHWAY", "OSM_LANES", "OSM_MAXSPEED", "OSM_SURFACE"]
    assert schema.PROVENANCE_COLUMNS == ["DATA_SOURCE", "EXTRACTED_AT_UTC"]


def test_vertex_columns_and_text_ids():
    assert schema.VERTEX_COLUMNS == [
        "OBJECTID",
        "NETWORK_ELEMENT",
        "ROAD",
        "ROAD_NAME",
        "CWY",
        "PART",
        "SEQ",
        "LAT",
        "LON",
    ]
    assert set(schema.ID_COLUMNS) <= set(schema.OUTPUT_COLUMNS) | set(schema.VERTEX_COLUMNS)
    assert "ROAD" in schema.ID_COLUMNS and "GlobalID" in schema.ID_COLUMNS
    assert "Main Roads" in schema.DATA_SOURCE and "CC BY" in schema.LICENCE and "GDA94" in schema.DATUM_NOTE
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_schema.py -q` → `ImportError: cannot import name 'schema' from 'dbe'`. Note this is an `ImportError`, **not** a `ModuleNotFoundError`: the test's first line is `from dbe import schema`, which routes through CPython's `_handle_fromlist`, and that catches the inner `ModuleNotFoundError` so the `IMPORT_FROM` bytecode raises the parent class instead. `import dbe.schema` would give the other message.

- [ ] **Step 3: Implement**

```python
"""Single source of truth for output columns and provenance strings."""

from __future__ import annotations

from dbe.enrich import ENRICH_COLUMNS

ORIGINAL_COLUMNS: list[str] = [
    "ROAD",
    "ROAD_NAME",
    "COMMON_USAGE_NAME",
    "START_SLK",
    "END_SLK",
    "CWY",
    "START_TRUE_DIST",
    "END_TRUE_DIST",
    "NETWORK_TYPE",
    "RA_NO",
    "RA_NAME",
    "LG_NO",
    "LG_NAME",
    "START_NODE_NO",
    "START_NODE_NAME",
    "END_NODE_NO",
    "END_NODE_NAME",
    "DATUM_NE_ID",
    "NM_BEGIN_MP",
    "NM_END_MP",
    "NETWORK_ELEMENT",
    "ROUTE_NE_ID",
    "OBJECTID",
    "GlobalID",
    "GEOLOCSTLength",
]
GEOMETRY_COLUMNS: list[str] = [
    "START_LAT",
    "START_LON",
    "END_LAT",
    "END_LON",
    "VERTEX_COUNT",
    "LENGTH_M",
    "DIST_TO_CENTRE_M",
    "INSIDE_FRACTION",
    "GEOMETRY_WKT",
]
OSM_COLUMNS: list[str] = ["OSM_WAY_ID", "OSM_HIGHWAY", "OSM_LANES", "OSM_MAXSPEED", "OSM_SURFACE"]
PROVENANCE_COLUMNS: list[str] = ["DATA_SOURCE", "EXTRACTED_AT_UTC"]
OUTPUT_COLUMNS: list[str] = (
    ORIGINAL_COLUMNS + GEOMETRY_COLUMNS + ENRICH_COLUMNS + OSM_COLUMNS + PROVENANCE_COLUMNS
)
VERTEX_COLUMNS: list[str] = [
    "OBJECTID",
    "NETWORK_ELEMENT",
    "ROAD",
    "ROAD_NAME",
    "CWY",
    "PART",
    "SEQ",
    "LAT",
    "LON",
]

# Kept as text when the CSV is loaded for XLSX conversion (ids that look numeric but are labels).
ID_COLUMNS: list[str] = [
    "ROAD",
    "RA_NO",
    "LG_NO",
    "START_NODE_NO",
    "END_NODE_NO",
    "DATUM_NE_ID",
    "NETWORK_ELEMENT",
    "ROUTE_NE_ID",
    "GlobalID",
    "OSM_WAY_ID",
    "CWY",
    "KERB_L",
    "KERB_R",
    "WIDTH_SOURCE",
]

DATA_SOURCE = (
    "Main Roads Western Australia Open Data — RoadAssets_DataPortal/MapServer layers 17 (Road Network), "
    "12 (Pavement and Surfacing State), 16 (Road Hierarchy), 8 (Legal Speed Limit)"
)
LICENCE = (
    "Main Roads WA open data: Creative Commons Attribution 4.0 (CC BY 4.0). "
    "Attribution: © Main Roads Western Australia."
)
DATUM_NOTE = (
    "Coordinates are WGS84 (EPSG:4326) as served with outSR=4326; the source datum is GDA94 (EPSG:4283). "
    "The two differ by at most ~1.5 m in Western Australia."
)
OSM_ATTRIBUTION = "OpenStreetMap enrichment (only with --osm): © OpenStreetMap contributors, ODbL 1.0."
```

- [ ] **Step 4: Run** — `uv run pytest tests/test_schema.py -q && uv run ruff check dbe tests` → `3 passed`, clean.

- [ ] **Step 5: Commit** — `git add dbe/schema.py tests/test_schema.py && git commit -m "feat(schema): fixed 53-column output contract and provenance strings"`

---

### Task S4.T2: The `extract()` pipeline

**Files:**
- Create: `dbe/extract.py`, `tests/test_extract.py`

**Interfaces:**
- Consumes: `LocalProjection`, `geojson_to_line`, `segment_metrics`, `iter_vertices` (geometry); `normalise_properties`, layer constants (mrwa_client); `EnrichIndex`, `enrich_segment` (enrich); `schema.*`; `tests.conftest.FixtureSource`.
- Produces:
  - `class RoadSource(Protocol):` `def query_envelope(self, layer_id: int, envelope, out_fields: str = "*") -> list[dict]: ...`
  - `class NoRoadsFound(RuntimeError)`
  - `@dataclass class ExtractResult:` `roads: list[dict]`, `vertices: list[dict]`, `metadata: dict`
  - `def extract(lat: float, lon: float, radius_km: float, source: RoadSource, with_osm: bool = False) -> ExtractResult` — `with_osm` is accepted now and wired in S5.T2; until then it must be ignored.
  - `metadata` keys (all present, always): `centre_lat, centre_lon, radius_km, envelope_wgs84 (list of 4), extracted_at_utc, features_returned_layer17, segments_intersecting, segments_outside_circle, skipped_no_geometry, skipped_bad_geometry, duplicates_dropped, enrich_duplicates_dropped, enrich_unparsed_slk, features_layer12, features_layer16, features_layer8, network_type_counts (dict), width_source_counts (dict), vertices_rows, data_source, licence, datum_note, osm_enabled (bool), osm_attribution (str or None), dbe_version`.

- [ ] **Step 1: Write the failing tests**

```python
import copy

import pytest

from dbe import schema
from dbe.extract import ExtractResult, NoRoadsFound, extract
from tests.conftest import FixtureSource


def test_extract_from_fixtures_produces_contract_rows(fixture_source, curtin_2400):
    res = extract(source=fixture_source, **curtin_2400)
    assert isinstance(res, ExtractResult)
    assert len(res.roads) > 50
    for row in res.roads:
        assert list(row.keys()) == schema.OUTPUT_COLUMNS
        assert 0.0 <= row["INSIDE_FRACTION"] <= 1.0
        assert row["INSIDE_FRACTION"] > 0.0 or row["DIST_TO_CENTRE_M"] <= 2400.0 + 1.0
        assert row["WIDTH_SOURCE"] in ("mrwa_pavement", "none")
        assert row["GEOMETRY_WKT"].startswith(("LINESTRING", "MULTILINESTRING"))
        assert row["DATA_SOURCE"] == schema.DATA_SOURCE
    for v in res.vertices:
        assert list(v.keys()) == schema.VERTEX_COLUMNS
    assert res.metadata["segments_intersecting"] == len(res.roads)
    assert res.metadata["vertices_rows"] == len(res.vertices) == sum(r["VERTEX_COUNT"] for r in res.roads)
    assert res.metadata["network_type_counts"].get("Local Road", 0) > 0
    assert res.metadata["osm_enabled"] is False
    assert [c for c in fixture_source.calls] and fixture_source.calls[0][0] == 17


def test_rows_are_sorted_by_road_cwy_start_slk(fixture_source, curtin_2400):
    res = extract(source=fixture_source, **curtin_2400)
    keys = [(str(r["ROAD"]), str(r["CWY"]), float(r["START_SLK"])) for r in res.roads]
    assert keys == sorted(keys)


def test_segments_outside_circle_are_dropped(fixture_source):
    small = extract(lat=-32.0018629, lon=115.8924599, radius_km=0.3, source=fixture_source)
    big = extract(lat=-32.0018629, lon=115.8924599, radius_km=2.4, source=fixture_source)
    assert 0 < len(small.roads) < len(big.roads)
    assert small.metadata["segments_outside_circle"] > 0


def test_duplicates_and_null_geometry_are_counted(fixture_source, curtin_2400):
    feats = copy.deepcopy(fixture_source.layers[17])
    feats.append(copy.deepcopy(feats[0]))  # duplicate OBJECTID
    feats.append({"type": "Feature", "geometry": None, "properties": {"OBJECTID": -1, "ROAD": "X"}})
    src = FixtureSource({**fixture_source.layers, 17: feats})
    res = extract(source=src, **curtin_2400)
    assert res.metadata["duplicates_dropped"] == 1
    assert res.metadata["skipped_no_geometry"] == 1


def test_no_roads_raises(curtin_2400):
    with pytest.raises(NoRoadsFound):
        extract(source=FixtureSource({17: [], 12: [], 16: [], 8: []}), **curtin_2400)
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_extract.py -q` → `ModuleNotFoundError: No module named 'dbe.extract'`

- [ ] **Step 3: Implement**

```python
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
    index = EnrichIndex.from_features(feats12, feats16, feats8)

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
        "osm_enabled": bool(with_osm),
        "osm_attribution": None,
        "dbe_version": __version__,
    }
    log.info("kept %s of %s segments (%s vertices)", len(roads), len(feats17), len(vertices))
    return ExtractResult(roads, vertices, metadata)
```

- [ ] **Step 4: Run** — `uv run pytest tests/test_extract.py -q && uv run ruff check dbe tests` → `5 passed`, clean.

- [ ] **Step 5: Commit** — `git add dbe/extract.py tests/test_extract.py && git commit -m "feat(extract): circle-filtered extraction pipeline with enrichment and vertices"`

---

### Task S4.T3: Export — CSV, metadata JSON, and CSV→XLSX conversion

**Files:**
- Create: `dbe/export.py`, `tests/test_export.py`

**Interfaces:**
- Consumes: `schema.*`.
- Produces:
  - `EXCEL_MAX_ROWS = 1_048_576`, `EXCEL_MAX_CELL_CHARS = 32_767`
  - `def write_csv(rows: list[dict], columns: list[str], path: Path) -> Path` (utf-8, `newline=""`, `csv.DictWriter` with `extrasaction="ignore"`, header always written even for zero rows; `None` → empty cell)
  - `def write_json(obj: dict, path: Path) -> Path` (indent 2, `default=str`)
  - `def csv_to_xlsx(roads_csv: Path, vertices_csv: Path, metadata_json: Path, xlsx_path: Path, max_rows: int = EXCEL_MAX_ROWS) -> dict` — reads the CSVs with pandas (`dtype=str` for `schema.ID_COLUMNS`, `keep_default_na=False, na_values=[""]`), writes sheets `roads`, `vertices` (then `vertices_2`, `vertices_3`… each ≤ `max_rows - 1` data rows), `metadata` (two columns `key`, `value`, nested dicts JSON-encoded); truncates any cell > `EXCEL_MAX_CELL_CHARS` to the first 32,700 chars + `…TRUNCATED`; returns `{"sheets": [...], "roads_rows": n, "vertices_rows": n, "truncated_cells": n}`.

- [ ] **Step 1: Write the failing tests**

```python
import csv
import json

from openpyxl import load_workbook

from dbe import schema
from dbe.export import EXCEL_MAX_CELL_CHARS, csv_to_xlsx, write_csv, write_json


def _road_row(i, wkt="LINESTRING (115.89 -32, 115.9 -32)"):
    row = dict.fromkeys(schema.OUTPUT_COLUMNS)
    row.update(
        ROAD="H001",
        ROAD_NAME="Albany Hwy",
        CWY="Left",
        START_SLK=0.0,
        END_SLK=0.3,
        OBJECTID=i,
        NETWORK_ELEMENT=f"H001/{i}-L",
        GlobalID="{ABC}",
        GEOMETRY_WKT=wkt,
        WIDTH_SOURCE="none",
        INSIDE_FRACTION=1.0,
        DATA_SOURCE=schema.DATA_SOURCE,
        EXTRACTED_AT_UTC="2026-09-22T00:00:00+00:00",
    )
    return row


def _vertex_rows(n):
    return [
        {
            "OBJECTID": 1,
            "NETWORK_ELEMENT": "H001/1-L",
            "ROAD": "H001",
            "ROAD_NAME": "Albany Hwy",
            "CWY": "Left",
            "PART": 0,
            "SEQ": s,
            "LAT": -32.0,
            "LON": 115.89 + s * 1e-4,
        }
        for s in range(n)
    ]


def test_write_csv_header_order_and_none_as_empty(tmp_path):
    path = write_csv([_road_row(1)], schema.OUTPUT_COLUMNS, tmp_path / "roads.csv")
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == schema.OUTPUT_COLUMNS
    assert rows[1][schema.OUTPUT_COLUMNS.index("WIDTH_M")] == ""
    assert rows[1][0] == "H001"


def test_write_csv_zero_rows_still_writes_header(tmp_path):
    path = write_csv([], schema.VERTEX_COLUMNS, tmp_path / "v.csv")
    assert path.read_text().strip() == ",".join(schema.VERTEX_COLUMNS)


def test_csv_to_xlsx_sheets_and_counts(tmp_path):
    roads = tmp_path / "roads.csv"
    verts = tmp_path / "roads_vertices.csv"
    meta = tmp_path / "metadata.json"
    write_csv([_road_row(1), _road_row(2)], schema.OUTPUT_COLUMNS, roads)
    write_csv(_vertex_rows(5), schema.VERTEX_COLUMNS, verts)
    write_json({"radius_km": 10, "network_type_counts": {"Local Road": 2}}, meta)
    report = csv_to_xlsx(roads, verts, meta, tmp_path / "roads.xlsx")
    wb = load_workbook(tmp_path / "roads.xlsx", read_only=True)
    assert wb.sheetnames == ["roads", "vertices", "metadata"]
    ws = wb["roads"]
    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    assert header == schema.OUTPUT_COLUMNS
    assert ws.max_row == 3 and wb["vertices"].max_row == 6
    assert report == {
        "sheets": ["roads", "vertices", "metadata"],
        "roads_rows": 2,
        "vertices_rows": 5,
        "truncated_cells": 0,
    }
    meta_rows = {r[0].value: r[1].value for r in wb["metadata"].iter_rows(min_row=2)}
    assert meta_rows["radius_km"] in (10, "10")
    assert json.loads(meta_rows["network_type_counts"]) == {"Local Road": 2}


def test_csv_to_xlsx_keeps_ids_as_text(tmp_path):
    row = _road_row(1)
    row.update(ROAD="1010001", LG_NO="101")
    write_csv([row], schema.OUTPUT_COLUMNS, tmp_path / "r.csv")
    write_csv([], schema.VERTEX_COLUMNS, tmp_path / "v.csv")
    write_json({}, tmp_path / "m.json")
    csv_to_xlsx(tmp_path / "r.csv", tmp_path / "v.csv", tmp_path / "m.json", tmp_path / "o.xlsx")
    ws = load_workbook(tmp_path / "o.xlsx", read_only=True)["roads"]
    values = [c.value for c in list(ws.iter_rows(min_row=2, max_row=2))[0]]
    assert values[schema.OUTPUT_COLUMNS.index("ROAD")] == "1010001"
    assert values[schema.OUTPUT_COLUMNS.index("LG_NO")] == "101"


def test_csv_to_xlsx_splits_vertices_and_truncates_long_cells(tmp_path):
    long_wkt = "LINESTRING (" + ", ".join(f"115.{i:05d} -32.0" for i in range(4000)) + ")"
    assert len(long_wkt) > EXCEL_MAX_CELL_CHARS
    write_csv([_road_row(1, wkt=long_wkt)], schema.OUTPUT_COLUMNS, tmp_path / "r.csv")
    write_csv(_vertex_rows(7), schema.VERTEX_COLUMNS, tmp_path / "v.csv")
    write_json({}, tmp_path / "m.json")
    report = csv_to_xlsx(
        tmp_path / "r.csv", tmp_path / "v.csv", tmp_path / "m.json", tmp_path / "o.xlsx", max_rows=4
    )
    wb = load_workbook(tmp_path / "o.xlsx", read_only=True)
    assert wb.sheetnames == ["roads", "vertices", "vertices_2", "vertices_3", "metadata"]
    assert report["truncated_cells"] == 1 and report["vertices_rows"] == 7
    cell = list(wb["roads"].iter_rows(min_row=2, max_row=2))[0][
        schema.OUTPUT_COLUMNS.index("GEOMETRY_WKT")
    ].value
    assert cell.endswith("…TRUNCATED") and len(cell) <= EXCEL_MAX_CELL_CHARS
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_export.py -q` → `ModuleNotFoundError: No module named 'dbe.export'`

- [ ] **Step 3: Implement**

```python
"""Writers: CSV (source of truth), metadata JSON, and CSV → XLSX conversion."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from dbe import schema

log = logging.getLogger(__name__)

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_CELL_CHARS = 32_767
_TRUNCATE_AT = 32_700
_TRUNCATE_MARK = "…TRUNCATED"


def write_csv(rows: list[dict[str, Any]], columns: list[str], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: ("" if row.get(c) is None else row.get(c)) for c in columns})
    return path


def write_json(obj: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    return path


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a produced CSV back without pandas reinterpreting its contents.

    `keep_default_na=False, na_values=[""]` is LOAD-BEARING, not incidental. With pandas'
    defaults, the literal text "nan" (and "NA", "null", "None", "N/A" …) is coerced to a missing
    value, so a road genuinely named or labelled with one of those strings would silently become
    blank in the XLSX while the CSV still showed it. Only an empty cell means absent here.
    Do not "simplify" these kwargs away — see the S3.T1 fix review, MINOR-3.
    """
    dtype = {c: str for c in schema.ID_COLUMNS}
    return pd.read_csv(path, dtype=dtype, keep_default_na=False, na_values=[""], encoding="utf-8")


def _truncate_long_cells(df: pd.DataFrame) -> int:
    count = 0
    for col in df.columns:
        if not (pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object):
            # pandas 3 uses a dedicated `str` dtype, so `!= object` alone would skip every text column
            continue
        lengths = df[col].astype(str).str.len()
        mask = lengths > EXCEL_MAX_CELL_CHARS
        if mask.any():
            count += int(mask.sum())
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.slice(0, _TRUNCATE_AT) + _TRUNCATE_MARK
    return count


def csv_to_xlsx(
    roads_csv: Path, vertices_csv: Path, metadata_json: Path, xlsx_path: Path, max_rows: int = EXCEL_MAX_ROWS
) -> dict[str, Any]:
    roads = _read_csv(Path(roads_csv))
    vertices = _read_csv(Path(vertices_csv))
    metadata = (
        json.loads(Path(metadata_json).read_text(encoding="utf-8")) if Path(metadata_json).exists() else {}
    )
    truncated = _truncate_long_cells(roads)
    chunk = max(1, max_rows - 1)  # header occupies one row
    sheets: list[str] = []
    xlsx_path = Path(xlsx_path)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
        roads.to_excel(xw, sheet_name="roads", index=False)
        sheets.append("roads")
        for i, start in enumerate(range(0, max(len(vertices), 1), chunk)):
            name = "vertices" if i == 0 else f"vertices_{i + 1}"
            vertices.iloc[start : start + chunk].to_excel(xw, sheet_name=name, index=False)
            sheets.append(name)
        meta_rows = [(k, json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in metadata.items()]
        pd.DataFrame(meta_rows, columns=["key", "value"]).to_excel(xw, sheet_name="metadata", index=False)
        sheets.append("metadata")
    if truncated:
        log.warning(
            "%s cell(s) exceeded Excel's %s-char limit and were truncated in the XLSX (CSV is complete)",
            truncated,
            EXCEL_MAX_CELL_CHARS,
        )
    return {
        "sheets": sheets,
        "roads_rows": int(len(roads)),
        "vertices_rows": int(len(vertices)),
        "truncated_cells": truncated,
    }
```

- [ ] **Step 4: Run** — `uv run pytest tests/test_export.py -q && uv run ruff check dbe tests` → `5 passed`, clean. If pandas emits a `FutureWarning` about dtype downcasting in `_truncate_long_cells`, replace `df.loc[mask, col] = …` with `df[col] = df[col].where(~mask, df[col].astype(str).str.slice(0, _TRUNCATE_AT) + _TRUNCATE_MARK)`.

- [ ] **Step 5: Commit** — `git add dbe/export.py tests/test_export.py && git commit -m "feat(export): CSV writers, metadata JSON and CSV-to-XLSX conversion with Excel guards"`

---

### Task S4.T4: CLI with `extract` and `to-xlsx`

**Files:**
- Create: `dbe/cli.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `MRWAClient`, `extract`, `NoRoadsFound`, `write_csv`, `write_json`, `csv_to_xlsx`, `schema`.
- Produces: `def build_parser() -> argparse.ArgumentParser`; `def main(argv: list[str] | None = None) -> int`; `def run_extract(args) -> dict` (returns paths + counts; builds `MRWAClient(cache_dir=args.cache_dir)` via module-level name `MRWAClient` so tests can monkeypatch `dbe.cli.MRWAClient`); `def run_to_xlsx(args) -> dict`; output file names inside `--out`: `roads.csv`, `roads_vertices.csv`, `metadata.json`, `roads.xlsx`, `cache/`.
- `extract` flags: `--lat` (float, required), `--lon` (float, required), `--radius-km` (float, required, > 0), `--out` (default `output/run`), `--cache-dir` (default `<out>/cache`), `--no-xlsx`, `--osm` (accepted; wired in S5.T2), `-v/--verbose`.
- `to-xlsx` flags: `--roads`, `--vertices`, `--metadata`, `--out` (all required).

- [ ] **Step 1: Write the failing tests**

```python
import csv
import json

from openpyxl import load_workbook

from dbe import cli, schema
from tests.conftest import FixtureSource


def test_extract_writes_all_outputs(tmp_path, fixture_source, monkeypatch):
    monkeypatch.setattr(cli, "MRWAClient", lambda **kwargs: fixture_source)
    out = tmp_path / "run"
    rc = cli.main(
        ["extract", "--lat", "-32.0018629", "--lon", "115.8924599", "--radius-km", "1.0", "--out", str(out)]
    )
    assert rc == 0
    for name in ("roads.csv", "roads_vertices.csv", "metadata.json", "roads.xlsx"):
        assert (out / name).exists(), name
    with (out / "roads.csv").open(newline="") as fh:
        header = next(csv.reader(fh))
    assert header == schema.OUTPUT_COLUMNS
    meta = json.loads((out / "metadata.json").read_text())
    assert meta["radius_km"] == 1.0 and meta["segments_intersecting"] > 0
    assert load_workbook(out / "roads.xlsx", read_only=True).sheetnames[0] == "roads"


def test_no_xlsx_flag(tmp_path, fixture_source, monkeypatch):
    monkeypatch.setattr(cli, "MRWAClient", lambda **kwargs: fixture_source)
    out = tmp_path / "run"
    assert (
        cli.main(
            [
                "extract",
                "--lat",
                "-32.0018629",
                "--lon",
                "115.8924599",
                "--radius-km",
                "1.0",
                "--out",
                str(out),
                "--no-xlsx",
            ]
        )
        == 0
    )
    assert not (out / "roads.xlsx").exists()


def test_to_xlsx_subcommand(tmp_path, fixture_source, monkeypatch):
    monkeypatch.setattr(cli, "MRWAClient", lambda **kwargs: fixture_source)
    out = tmp_path / "run"
    cli.main(
        [
            "extract",
            "--lat",
            "-32.0018629",
            "--lon",
            "115.8924599",
            "--radius-km",
            "1.0",
            "--out",
            str(out),
            "--no-xlsx",
        ]
    )
    rc = cli.main(
        [
            "to-xlsx",
            "--roads",
            str(out / "roads.csv"),
            "--vertices",
            str(out / "roads_vertices.csv"),
            "--metadata",
            str(out / "metadata.json"),
            "--out",
            str(out / "converted.xlsx"),
        ]
    )
    assert rc == 0 and (out / "converted.xlsx").exists()


def test_no_roads_returns_exit_code_1(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "MRWAClient", lambda **kwargs: FixtureSource({17: [], 12: [], 16: [], 8: []}))
    rc = cli.main(
        ["extract", "--lat", "-32.0", "--lon", "115.89", "--radius-km", "1.0", "--out", str(tmp_path / "x")]
    )
    assert rc == 1
    assert "no road segments" in capsys.readouterr().err.lower()


def test_negative_radius_rejected(tmp_path):
    rc = cli.main(
        ["extract", "--lat", "-32.0", "--lon", "115.89", "--radius-km", "-1", "--out", str(tmp_path / "x")]
    )
    assert rc == 2
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_cli.py -q` → `ModuleNotFoundError: No module named 'dbe.cli'` (or the placeholder from S0.T1 failing every test).

- [ ] **Step 3: Implement**

```python
"""Command-line interface: `dbe extract …` and `dbe to-xlsx …`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dbe import __version__, schema
from dbe.export import csv_to_xlsx, write_csv, write_json
from dbe.extract import NoRoadsFound, extract
from dbe.mrwa_client import MRWAClient, MRWAError  # MRWAClient is monkeypatched in tests

log = logging.getLogger("dbe")

ROADS_CSV = "roads.csv"
VERTICES_CSV = "roads_vertices.csv"
METADATA_JSON = "metadata.json"
ROADS_XLSX = "roads.xlsx"


def _positive(value: str) -> float:
    f = float(value)
    if f <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return f


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dbe", description="Roads inside a circle, from Main Roads WA open data."
    )
    p.add_argument("--version", action="version", version=f"dbe {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    ex = sub.add_parser(
        "extract", help="query MRWA, write roads.csv / roads_vertices.csv / metadata.json (+ roads.xlsx)"
    )
    ex.add_argument("--lat", type=float, required=True, help="centre latitude, e.g. -32.0018629")
    ex.add_argument("--lon", type=float, required=True, help="centre longitude, e.g. 115.8924599")
    ex.add_argument("--radius-km", type=_positive, required=True, help="radius in kilometres, e.g. 10")
    ex.add_argument("--out", type=Path, default=Path("output/run"), help="output directory")
    ex.add_argument("--cache-dir", type=Path, default=None, help="raw API cache (default: <out>/cache)")
    ex.add_argument("--no-xlsx", action="store_true", help="skip the XLSX conversion")
    ex.add_argument(
        "--osm", action="store_true", help="enrich with OpenStreetMap width/lanes where MRWA has none"
    )
    ex.add_argument("-v", "--verbose", action="store_true")
    ex.set_defaults(func=run_extract)

    tx = sub.add_parser(
        "to-xlsx", help="convert an existing roads.csv + roads_vertices.csv (+ metadata.json) to XLSX"
    )
    tx.add_argument("--roads", type=Path, required=True)
    tx.add_argument("--vertices", type=Path, required=True)
    tx.add_argument("--metadata", type=Path, required=True)
    tx.add_argument("--out", type=Path, required=True)
    tx.add_argument("-v", "--verbose", action="store_true")
    tx.set_defaults(func=run_to_xlsx)
    return p


def run_extract(args: argparse.Namespace) -> dict:
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    cache_dir = args.cache_dir or (out / "cache")
    client = MRWAClient(cache_dir=cache_dir)
    result = extract(args.lat, args.lon, args.radius_km, source=client, with_osm=args.osm)
    roads_csv = write_csv(result.roads, schema.OUTPUT_COLUMNS, out / ROADS_CSV)
    vertices_csv = write_csv(result.vertices, schema.VERTEX_COLUMNS, out / VERTICES_CSV)
    metadata_json = write_json(result.metadata, out / METADATA_JSON)
    report = {
        "roads_csv": str(roads_csv),
        "vertices_csv": str(vertices_csv),
        "metadata_json": str(metadata_json),
        "segments": len(result.roads),
        "vertices": len(result.vertices),
    }
    if not args.no_xlsx:
        xlsx_report = csv_to_xlsx(roads_csv, vertices_csv, metadata_json, out / ROADS_XLSX)
        report["xlsx"] = str(out / ROADS_XLSX)
        report["xlsx_sheets"] = xlsx_report["sheets"]
    log.info("done: %s segments, %s vertices -> %s", len(result.roads), len(result.vertices), out)
    return report


def run_to_xlsx(args: argparse.Namespace) -> dict:
    report = csv_to_xlsx(args.roads, args.vertices, args.metadata, args.out)
    log.info("wrote %s (%s)", args.out, ", ".join(report["sheets"]))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors, 0 on --help/--version
        return int(exc.code or 0)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        args.func(args)
        return 0
    except NoRoadsFound as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except MRWAError as exc:
        print(f"error: MRWA service problem: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
```

- [ ] **Step 4: Run** — `uv run pytest -q && uv run ruff check .` → all tests pass (`5` new), clean. Also `uv run dbe --help` prints usage.

- [ ] **Step 5: Commit** — `git add dbe/cli.py tests/test_cli.py && git commit -m "feat(cli): extract and to-xlsx subcommands"`

---

### Task S4.T5: Curtin 10 km end-to-end run, reconciliation test, QA plot

**Files:**
- Create: `tests/test_reconcile_csv.py`, `scripts/qa_plot.py`, `docs/task_docs/e2e_curtin_10km.md`
- Generates (not committed): `output/curtin_10km/{roads.csv, roads_vertices.csv, metadata.json, roads.xlsx, qa_plot.png, cache/}`

**Interfaces:**
- Consumes: the CLI; `LocalProjection`; `data/Road_Network - Road_Network.csv` (this test only).

- [ ] **Step 1: Run the real extraction** (internet; 5–20 minutes depending on paging)

Run: `uv run dbe extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km -v 2>&1 | tee output/curtin_10km_run.log`
Expected: exit 0; log shows paging for layer 17 (several pages of 2000) and non-zero counts for layers 12/16/8; `metadata.json` values inside §3.8 ranges. If any red flag in §3.8 fires, stop and write it to `progress.md` → Blockers with the metadata values; do not "fix" numbers by changing the plan.

- [ ] **Step 2: Write the reconciliation test**

```python
"""Validation-only comparison against the user's provided statewide CSV. Skips when inputs are absent."""

import csv
from pathlib import Path

import pytest

from dbe import schema

PROVIDED = Path("data/Road_Network - Road_Network.csv")
EXTRACTED = Path("output/curtin_10km/roads.csv")

pytestmark = pytest.mark.skipif(
    not (PROVIDED.exists() and EXTRACTED.exists()),
    reason="needs data/Road_Network - Road_Network.csv and output/curtin_10km/roads.csv",
)


def _header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return next(csv.reader(fh))


def _column_set(path: Path, column: str) -> set[str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return {row[column] for row in csv.DictReader(fh)}


def test_first_25_columns_match_provided_header():
    assert _header(EXTRACTED)[:25] == _header(PROVIDED) == schema.ORIGINAL_COLUMNS


def test_extracted_network_elements_exist_in_provided_csv():
    provided = _column_set(PROVIDED, "NETWORK_ELEMENT")
    extracted = _column_set(EXTRACTED, "NETWORK_ELEMENT")
    assert extracted, "no extracted rows"
    matched = extracted & provided
    ratio = len(matched) / len(extracted)
    print(
        f"\nextracted={len(extracted)} matched={len(matched)} "
        f"new_since_export={len(extracted - provided)} ratio={ratio:.4f}"
    )
    assert ratio >= 0.95


def test_every_extracted_row_is_metropolitan():
    with EXTRACTED.open(newline="", encoding="utf-8") as fh:
        regions = {row["RA_NAME"] for row in csv.DictReader(fh)}
    assert regions <= {"Metropolitan"}
```

Run: `uv run pytest tests/test_reconcile_csv.py -q -s` → `3 passed` with the printed counts; copy the printed line into `progress.md` → Verification log.

- [ ] **Step 3: Write `scripts/qa_plot.py`** — before writing it, load the `dataviz` skill if it is available in the session; keep the plot simple and legible.

```python
"""Render roads.csv as a PNG for reviewers.

Segments are coloured by NETWORK_TYPE with the query circle drawn in black.
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from shapely import wkt  # noqa: E402

from dbe.geometry import LocalProjection  # noqa: E402

# Colours are the validated default palette of the dataviz skill, checked with its validator in
# `--pairs all` mode. On a map any road type can sit beside any other, so every pair must stay
# distinguishable, not just neighbours in the legend. Result for these four: worst colour-blind
# separation 13.0 (magenta vs blue, target >= 8), worst normal-vision separation 16.3 (violet vs
# blue, floor 15).
#
# The previous palette failed: its grey for Miscellaneous roads read as colourless and scored 11.6
# against the Local blue, below the floor even for full colour vision. The best contrast-only
# alternative (blue, green, violet, red) was rejected because its weakest pair was red vs green at
# 7.2 — the classic colour-blind confusion, and exactly the pair that would sit side by side if
# state highways were red and the paths running beside them green.
#
# Draw order and line weight are part of the fix, not decoration. Types were previously drawn
# alphabetically, which put State Roads last and on top of the Controlled Paths that parallel them,
# burying the path. Now the paths draw last. Every type but State was also drawn at the same hairline
# as the 19,741 local streets, so the two small categories vanished into the grid.
#
#   type                          colour     width  zorder  role
STYLES = {
    "Local Road": ("#2a78d6", 0.35, 1),  # blue: the dense background grid, thinnest
    "Miscellaneous Road": ("#e87ba4", 0.9, 2),  # magenta: campus, carpark and industrial roads
    "State Road": ("#4a3aa7", 1.4, 3),  # violet: the arterial skeleton, thickest
    "Main Roads Controlled Path": ("#008300", 0.9, 4),  # green: drawn last so it shows beside State
}
# Proposed Road and Crossover are rare (34 and 3 records statewide; none in the Curtin run). A fifth
# and sixth hue would exceed what the palette validates on all pairs, so they share one neutral and
# are told apart by line pattern instead: from the four hues above by being patterned at all, and
# from each other by a different pattern. (A first version gave both the same dash, which made their
# two legend entries identical — the exact problem this palette exists to fix.) Any other unexpected
# type falls back to the same neutral with a dash-dot pattern.
OTHER_STYLE = ("#6b6a66", 0.9, 5)
OTHER_DASHES = {
    "Proposed Road": (0, (4, 2)),  # dashed
    "Crossover": (0, (1, 1.5)),  # dotted
}
OTHER_DASH_FALLBACK = (0, (4, 1.5, 1, 1.5))  # dash-dot
LEGEND_ORDER = ["State Road", "Local Road", "Main Roads Controlled Path", "Miscellaneous Road"]


def _dash_for(ntype: str):
    """Solid for the four validated hues; a distinct pattern for each rare neutral type."""
    if ntype in STYLES:
        return "solid"
    return OTHER_DASHES.get(ntype, OTHER_DASH_FALLBACK)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out-dir", type=Path, required=True, help="directory holding roads.csv and metadata.json"
    )
    args = ap.parse_args()
    roads = pd.read_csv(
        args.out_dir / "roads.csv",
        usecols=["NETWORK_TYPE", "GEOMETRY_WKT"],
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    meta = json.loads((args.out_dir / "metadata.json").read_text())
    fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
    counts = roads["NETWORK_TYPE"].value_counts()
    for ntype, group in roads.groupby("NETWORK_TYPE"):
        colour, lw, z = STYLES.get(ntype, OTHER_STYLE)
        dash = _dash_for(ntype)
        for w in group["GEOMETRY_WKT"]:
            geom = wkt.loads(w)
            parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
            for part in parts:
                xs, ys = part.xy
                ax.plot(xs, ys, color=colour, linewidth=lw, linestyle=dash, zorder=z,
                        solid_capstyle="round")
    # Legend in a fixed, meaningful order rather than groupby's alphabetical one. Types absent from
    # this run are omitted, so the legend never advertises a colour the map does not use.
    for ntype in LEGEND_ORDER + sorted(set(counts.index) - set(LEGEND_ORDER)):
        if ntype not in counts:
            continue
        colour, _, _ = STYLES.get(ntype, OTHER_STYLE)
        ax.plot([], [], color=colour, linewidth=2.5, linestyle=_dash_for(ntype),
                label=f"{ntype} ({counts[ntype]:,})")
    proj = LocalProjection(meta["centre_lat"], meta["centre_lon"])
    ring = proj.to_wgs84(proj.circle(meta["radius_km"] * 1000.0)).exterior
    ax.plot(*ring.xy, color="black", linewidth=1.2, linestyle="--", label=f"{meta['radius_km']} km radius")
    ax.plot(meta["centre_lon"], meta["centre_lat"], marker="+", color="black", markersize=12)
    ax.set_aspect(1.0 / math.cos(math.radians(meta["centre_lat"])))
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(
        f"DBE — {meta['segments_intersecting']} segments, extracted {meta['extracted_at_utc']}"
    )
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    fig.tight_layout()
    out = args.out_dir / "qa_plot.png"
    fig.savefig(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

> **Superseded 2026-09-23 — the rendering moved into the package.** At the user's request `extract` now writes
> the map automatically, so the drawing code below now lives in `dbe/plot.py` as `render_qa_plot()`, and
> `scripts/qa_plot.py` is a thin wrapper for re-rendering an existing output directory. The package version also
> uses `matplotlib.figure.Figure` rather than `pyplot` (no global backend state in library code), and one
> `LineCollection` per road type rather than one `ax.plot` call per segment — 8.6 s down to about 2 s on the
> 10 km data. The block below is kept as the record of what S4.T5 built.
>
> **Palette revised 2026-09-23 at the user's request** — the original colours were hard to tell
> apart. The block above is the revised script: a palette validated for maps, where every road
> type can sit beside every other, plus fixed draw order and line weights. See the comment block
> at the top of the script for the measurements behind each choice.

Run: `uv run python scripts/qa_plot.py --out-dir output/curtin_10km` → `wrote output/curtin_10km/qa_plot.png`. Open the PNG (the Read tool renders images): the circle must be visibly filled with a street grid, the Swan River should appear as a road-free band north-west of centre, State Roads (red) should trace Albany Hwy, Leach Hwy, Canning Hwy, Kwinana Fwy, and segments should extend slightly past the dashed circle (whole geometry kept).

- [ ] **Step 4: Write `docs/task_docs/e2e_curtin_10km.md`** — paste the `metadata.json` contents (counts only, not the envelope) as a table, the reconciliation printout, the XLSX sheet list and row counts (open with `uv run python -c "from openpyxl import load_workbook; wb=load_workbook('output/curtin_10km/roads.xlsx', read_only=True); print([(ws.title, ws.max_row) for ws in wb])"`), and five spot-check rows (Kent St, Manning Rd, Hayman Rd, Leach Hwy, Albany Hwy: `ROAD, ROAD_NAME, CWY, START_LAT, START_LON, WIDTH_M, WIDTH_SOURCE, ROAD_HIERARCHY, SPEED_LIMIT`) via `uv run python -c "import pandas as pd; df=pd.read_csv('output/curtin_10km/roads.csv'); print(df[df.ROAD_NAME.isin(['Kent St','Manning Rd','Hayman Rd','Leach Hwy','Albany Hwy'])].groupby('ROAD_NAME').head(1)[['ROAD','ROAD_NAME','CWY','START_LAT','START_LON','WIDTH_M','WIDTH_SOURCE','ROAD_HIERARCHY','SPEED_LIMIT']].to_string())"`. State plainly which of the five were missing, if any.

- [ ] **Step 5: Commit**

```bash
git add tests/test_reconcile_csv.py scripts/qa_plot.py docs/task_docs/e2e_curtin_10km.md
git commit -m "test: reconciliation against provided CSV, QA plot script and e2e record for Curtin 10 km"
```

---

### Measured at the first real 10 km run (2026-09-23) — use these, not the pre-run estimates

The §3.8 ranges above were calibrated before any production data existed. The live run gives:

| Quantity | Measured |
|---|---|
| Wall clock | 185 s, exit 0 |
| Layer-17 features fetched / distinct | 28,142 / 26,974 |
| Segments intersecting | 21,643 |
| Pages, layer 17 | 15 |
| Vertices rows | 85,118 |
| Measured widths | 1,202, all State Road, 3.34–30.7 m |
| `duplicates_dropped` (layer 17) | **1,168** |
| `enrich_duplicates_dropped` (layers 12/16/8) | **622** (135 + 376 + 111) |
| `skipped_no_geometry` / `skipped_bad_geometry` | 0 / 0 |
| Reconciliation against the provided CSV | 21,558 of 21,558 matched, ratio 1.0000 |
| Divided-carriageway cases | **0** — the decision's condition is discharged |

**Two findings the run itself produced.** The live service returns **short pages while still setting
its overflow flag** (1,881 and 1,976 features where 2,000 was requested), so terminating on a short
page alone would have stopped after page 1 and silently returned ~7% of the data. And paging a live
spatial query returns duplicate records — 1,168 on layer 17 — so de-duplication is load-bearing in
production, not defensive decoration. The enrichment layers were initially not de-duplicated, which
double-weighted 10 widths by 0.07–0.58 m; fixed in `4d2ebf5`.

## Gate B — Opus review of Segments 3–4 plus end-to-end verification

Checklist for the Opus reviewer:
1. `uv run pytest -q` all pass; `uv run ruff check .` clean; `uv run pytest tests/test_reconcile_csv.py -q -s` passes with ratio ≥ 0.95 (paste the printed line).
2. Re-run the extraction yourself from cache (fast): `uv run dbe extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km` — it must reproduce the same `segments_intersecting`.
3. Every §3.8 sanity range: list each with the observed value and ✅/❌. Any ❌ is a FAIL unless a Decisions-log entry explains why the range, not the code, was wrong.
4. Open `output/curtin_10km/qa_plot.png` and describe what you see in the Gate log (street grid fills the circle; river gap; red State Roads on the known highways; segments overhang the circle).
5. Open `roads.xlsx` sheet list and header; confirm `roads` header == `schema.OUTPUT_COLUMNS`, `vertices` header == `schema.VERTEX_COLUMNS`, `metadata` sheet present; confirm the XLSX was produced from the CSV (code path `csv_to_xlsx` reads the CSV files — not in-memory rows).
6. Spot-check in `roads.csv`: Kent St, Manning Rd, Hayman Rd exist with `NETWORK_TYPE = Local Road`, `WIDTH_SOURCE = none`, non-empty `ROAD_HIERARCHY`; Leach Hwy and Albany Hwy rows have `WIDTH_SOURCE = mrwa_pavement` and plausible `WIDTH_M` (6–25 m) and `NO_OF_LANES` (1–4 per carriageway).
7. Read `extract.py` for: duplicate handling before the geometry check (so a duplicate with null geometry is counted once), rows built strictly from `schema.OUTPUT_COLUMNS`, `with_osm` accepted but inert.
8. Read `export.py`: `csv_to_xlsx` never touches `ExtractResult`; ID columns stay text; row-split and truncation guards tested.
9. Constraints §1: no `data/` read outside `tests/test_reconcile_csv.py` (`grep -rn "Road_Network" dbe/` must be empty); no new dependencies.
10. `progress.md`: S3.T1–S4.T5 `done` with SHAs; Verification log has the e2e counts, reconciliation line and XLSX sheet counts.

Verdict → `progress.md` → Gate log. On PASS the **mandatory deliverable is complete**; Segments 5–6 add optional enrichment and documentation.

### Gate B carried amendments (verdict PASS, 2026-09-23) — **action these in Segments 5–6**

Gate B passed with no Critical findings. The blocking item was tracker drift, closed in `eab46f5`.
Four Important and eight Minor findings are carried. **I4 is the one with user-facing consequences.**

| Ref | Act at | What to do |
|---|---|---|
| **I4** | **S6.T1 at the latest** | `--osm` is inert but advertised. |
| **I2** | S6 | Split the `roads` sheet like `vertices`. |
| **I3** | S6.T1 | Document a practical maximum radius. |
| **M2** | S6 or a plan note | Define the `dominant_value` tie-break. |
| **M3/M6** | Gate C checklist | Two §3.8 rows are mis-specified. |
| **M1** | Gate A checklist wording | The checklist is wrong, not the code. |
| **M4/M5/M7/M8** | S6.T1 | Naming, the run record, a blank-column guard, a cosmetic sleep. |

**I4 — `--osm` is inert but advertised, and reports itself as enabled.** `cli.py` advertises it as
"enrich with OpenStreetMap width/lanes where MRWA has none", and `extract()` sets
`metadata["osm_enabled"] = bool(with_osm)`, but nothing consumes the flag and nothing warns. A user
who sees that only 5.55% of rows carry a width could re-run with `--osm`, read `osm_enabled: true`
and conclude OSM was consulted and had nothing to add. **If Segment 5 is skipped, the help text must
say "not implemented" and the flag must either warn or be removed.**

**I2 — `csv_to_xlsx` splits the vertices sheet but never the roads sheet.** Past Excel's row cap the
run completes the expensive extraction, writes both CSVs, then dies with a bare openpyxl
`ValueError` and produces no workbook. The reviewer deliberately declined to name the radius at
which this bites, noting that linear-in-area extrapolation is exactly the reasoning that produced
the bad layer-12 band. The defect is the asymmetry — vertices has a split and a test, roads has
neither.

**I3 — the pipeline is entirely in memory.** `csv_to_xlsx` alone peaked at **733 MB** and 22 s for
this run; `extract()` additionally holds every feature, row and vertex. Neither the plan nor the CLI
states a practical maximum radius, so a large run is OOM-killed with no diagnostic.

**M2 — `dominant_value` ties break on paging order and floating-point noise.** 13 rows of 21,643 had
exact-float ties on advisory columns, and one row's lane count is decided by a 7e-18 difference
between `0.019999999999999997` and `0.020000000000000004`. `WIDTH_M` is unaffected — a weighted mean
is order-independent. §3.3 should state a deterministic tie-break (largest value, or longest source
span).

**M3 — §3.8's named-roads row produces a false alarm.** `Orrong Rd` has **0** rows under
`ROAD_NAME` but **54** under `COMMON_USAGE_NAME`; MRWA gazettes it as `Rivervale Wattle Grove Link`
and `Graham Farmer Fwy`. Likewise 38 `Albany Hwy` rows carry `COMMON_USAGE_NAME = "Shepperton Rd"`.
Change the row to "present in `ROAD_NAME` **or** `COMMON_USAGE_NAME`".

**M6 — the ±20% width band is not diagnostic.** It would pass while 240 state roads silently lost
their width. The measured figure is **100.0%** — every State Road row has a width and every width row
is a State Road. Tighten to "every State Road row has a width, or name the exceptions".

**M1 — the Gate A checklist's own wording is wrong.** It says a duplicate with null geometry must be
counted once as a duplicate. `seen.add(oid)` deliberately sits *after* the geometry guards, because
`test_a_geometryless_twin_does_not_suppress_the_real_feature` pins the more important property: a
malformed twin must not consume the OBJECTID and suppress the real feature. Accounting versus data
loss — the code chose correctly. Amend the checklist, not the code.

**M4** — `features_returned_layer17` reports the raw paged count including duplicates, overstating by
4.1% in a user-facing file; consider `features_fetched_` / `features_distinct_`. **M5** — the e2e
record contradicts the commit that followed it. **M7** — nothing guards against a silently renamed
source field; all 25 original columns are currently populated (worst `END_NODE_NO` at 99.59%), so a
`metadata.empty_columns` list would make future degradation visible. **M8** — `query_envelope` sleeps
between pages even on a full cache hit, costing ~6 s of a 34 s cached re-run.

**Recommended for the handoff:** state width coverage as **1,202 / 21,643 (5.55%)** prominently,
with the reason — Main Roads publishes measured pavement width for state roads only — rather than
letting the user discover it by sorting the column.

---

## Segment 5 — OPTIONAL: OpenStreetMap enrichment (Sonnet, TDD)

> **DECISION 2026-09-23: SKIPPED, on a measurement.** A single Overpass probe over the same 10 km
> circle returned **70,561 highway ways**, of which **685 (0.97%)** carry a `width` tag and only
> **371** carry both a width and a name, which is what the planned matcher needs. Against **20,441
> rows with no width**, a perfect match of every one of those 371 would close under 2% of the gap —
> and the real figure would be far lower, because OSM's "highway" population includes footpaths,
> cycleways and service roads that do not correspond to Main Roads segments at all, and name-plus-
> proximity matching is lossy.
>
> **The deciding factor is not the low yield but the licence.** OpenStreetMap is ODbL, whose
> share-alike terms attach to any derived database. Mixing it into the output would encumber the
> user's file for a sub-2% improvement on an attribute they described as "not mandatory but good to
> have". Main Roads data alone is CC BY 4.0, which is materially less restrictive.
> *(Withdrawn at Gate C, 2026-09-23: the skip holds on yield alone, the licence is a second reason, and the choice is the user's. Left as written for the record.)*
>
> **Consequence:** the `--osm` flag must not remain advertised and inert (Gate B finding I4). S6.T1
> makes the help text say so and the flag refuse rather than silently no-op. **Reversible:** this
> segment stays in the plan; rerun the probe and revisit if OSM width coverage improves.

**Skippable.** The mandatory deliverable is complete after Gate B. Run this segment only if the user wants it or if Gate B's `width_source_counts` shows the user would benefit (it fills `WIDTH_M` for local roads only where OSM happens to carry a `width` tag — expect a few percent at best). If skipped, mark both rows `skipped` in `progress.md` with the reason, and make sure README states that `--osm` is not implemented (S6.T1).

### Task S5.T1: Overpass client

**Files:**
- Create: `dbe/osm_client.py`, `tests/test_osm_client.py`

**Interfaces:**
- Produces: `OVERPASS_URL = "https://overpass-api.de/api/interpreter"`, `OVERPASS_MIRRORS = ["https://overpass.kumi.systems/api/interpreter"]`; `@dataclass(frozen=True) class OsmWay:` `id: int, tags: dict[str, str], coords: tuple[tuple[float, float], ...]` (lon, lat pairs — same axis order as shapely); `def build_query(lat: float, lon: float, radius_m: float, timeout_s: int = 180) -> str`; `def parse_overpass(payload: dict) -> list[OsmWay]` (skips ways without `geometry`); `def fetch_highways(lat, lon, radius_m, session=None, endpoints: list[str] | None = None, timeout_s: int = 180, sleep_s: float = 1.0) -> list[OsmWay]` — POST `data={"data": query}` with `User-Agent`; on HTTP 429/504 or connection error wait `sleep_s * 30` then try the next endpoint; raise `OsmError(RuntimeError)` after all endpoints fail.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
import requests

from dbe.osm_client import OsmError, OsmWay, build_query, fetch_highways, parse_overpass


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def post(self, url, data=None, timeout=None, headers=None):
        self.calls.append((url, data))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


PAYLOAD = {"elements": [
    {"type": "way", "id": 11, "tags": {"highway": "residential", "name": "Kent Street", "width": "7.5"},
     "geometry": [{"lat": -32.0, "lon": 115.89}, {"lat": -32.001, "lon": 115.891}]},
    {"type": "way", "id": 12, "tags": {"highway": "service"}},  # no geometry -> skipped
    {"type": "node", "id": 5, "lat": -32.0, "lon": 115.89},
]}


def test_build_query_contains_around_and_geom():
    q = build_query(-32.0018629, 115.8924599, 10_000)
    assert 'way["highway"](around:10000,-32.0018629,115.8924599);' in q
    assert "out geom;" in q and "[out:json]" in q and "[timeout:180]" in q


def test_parse_overpass_returns_ways_with_lon_lat_coords():
    ways = parse_overpass(PAYLOAD)
    assert ways == [OsmWay(11, {"highway": "residential", "name": "Kent Street", "width": "7.5"},
                           ((115.89, -32.0), (115.891, -32.001)))]


def test_fetch_falls_back_to_mirror_on_429():
    session = FakeSession([FakeResponse({}, status=429), FakeResponse(PAYLOAD)])
    ways = fetch_highways(-32.0, 115.89, 500, session=session, endpoints=["https://a/x", "https://b/x"], sleep_s=0)
    assert len(ways) == 1 and session.calls[1][0] == "https://b/x"
    assert session.calls[0][1]["data"].startswith("[out:json]")


def test_fetch_raises_after_all_endpoints_fail():
    session = FakeSession([requests.ConnectionError("down"), FakeResponse({}, status=504)])
    with pytest.raises(OsmError):
        fetch_highways(-32.0, 115.89, 500, session=session, endpoints=["https://a/x", "https://b/x"], sleep_s=0)
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_osm_client.py -q` → `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
"""Minimal Overpass API client for highway ways with inline geometry."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

import requests

log = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_MIRRORS = ["https://overpass.kumi.systems/api/interpreter"]
USER_AGENT = "DBE/0.1 (research tool; https://github.com/habibaarashid)"
RETRY_STATUS = {429, 502, 503, 504}


class OsmError(RuntimeError):
    pass


@dataclass(frozen=True)
class OsmWay:
    id: int
    tags: dict[str, str]
    coords: tuple[tuple[float, float], ...]  # (lon, lat)


def build_query(lat: float, lon: float, radius_m: float, timeout_s: int = 180) -> str:
    return (f"[out:json][timeout:{timeout_s}];\n"
            f'way["highway"](around:{int(radius_m)},{lat},{lon});\n'
            "out geom;")


def parse_overpass(payload: dict[str, Any]) -> list[OsmWay]:
    ways: list[OsmWay] = []
    for el in payload.get("elements", []):
        if el.get("type") != "way" or not el.get("geometry"):
            continue
        coords = tuple((float(p["lon"]), float(p["lat"])) for p in el["geometry"])
        ways.append(OsmWay(int(el["id"]), dict(el.get("tags") or {}), coords))
    return ways


def fetch_highways(lat: float, lon: float, radius_m: float, session: Any | None = None,
                   endpoints: list[str] | None = None, timeout_s: int = 180, sleep_s: float = 1.0) -> list[OsmWay]:
    session = session or requests.Session()
    endpoints = endpoints or [OVERPASS_URL, *OVERPASS_MIRRORS]
    query = build_query(lat, lon, radius_m, timeout_s)
    last: Exception | None = None
    for url in endpoints:
        try:
            resp = session.post(url, data={"data": query}, timeout=timeout_s + 30, headers={"User-Agent": USER_AGENT})
            if resp.status_code in RETRY_STATUS:
                raise OsmError(f"{url} returned HTTP {resp.status_code}")
            resp.raise_for_status()
            ways = parse_overpass(resp.json())
            log.info("overpass %s: %s highway ways", url, len(ways))
            return ways
        except (requests.RequestException, OsmError, ValueError) as exc:
            last = exc
            log.warning("overpass %s failed: %s", url, exc)
            if sleep_s:
                time.sleep(sleep_s * 30)
    raise OsmError(f"all Overpass endpoints failed: {last}")
```

- [ ] **Step 4: Run** — `uv run pytest tests/test_osm_client.py -q && uv run ruff check dbe tests` → `4 passed`, clean.

- [ ] **Step 5: Commit** — `git add dbe/osm_client.py tests/test_osm_client.py && git commit -m "feat(osm): Overpass client with mirror fallback"`

---

### Task S5.T2: Match OSM ways to MRWA segments and wire `--osm`

**Files:**
- Create: `dbe/osm_match.py`, `tests/test_osm_match.py`
- Modify: `dbe/extract.py` (the `with_osm` branch), `tests/test_extract.py` (append one test)

**Interfaces:**
- Consumes: `OsmWay`, `fetch_highways`; `LocalProjection`; `schema.OSM_COLUMNS`, `schema.OSM_ATTRIBUTION`.
- Produces:
  - `ABBREVIATIONS: dict[str, str]` = `{"rd": "road", "st": "street", "hwy": "highway", "ave": "avenue", "av": "avenue", "dr": "drive", "pl": "place", "cres": "crescent", "ct": "court", "tce": "terrace", "bvd": "boulevard", "blvd": "boulevard", "fwy": "freeway", "pde": "parade", "cl": "close", "gr": "grove", "la": "lane", "wy": "way", "cct": "circuit", "esp": "esplanade"}`
  - `def normalise_name(name: str | None) -> str` (lowercase, strip punctuation, expand abbreviations word-by-word, collapse spaces; `""` for None)
  - `def parse_width_m(value: str | None) -> float | None` (accepts `"7.5"`, `"7.5 m"`, `"7,5"`; None otherwise)
  - `class OsmMatcher:` `__init__(self, ways: list[OsmWay], proj: LocalProjection, buffer_m: float = 15.0, min_share: float = 0.5)`; `match(self, road_name: str | None, geom_wgs84) -> OsmWay | None` — candidates are ways whose normalised name equals the segment's normalised `ROAD_NAME` (empty names never match); choose the candidate maximising the length of the segment that lies within `buffer_m` of the way (in local metres); require that share ≥ `min_share`.
  - `def osm_columns_for(way: OsmWay | None) -> dict` → the five `OSM_COLUMNS` (`OSM_WAY_ID` int, others tag strings or None).
  - In `extract.py`: when `with_osm` is True, after the MRWA rows are built, call `fetch_highways(lat, lon, radius_m + 200)`, build `OsmMatcher`, and for every row set the OSM columns; if `row["WIDTH_M"] is None` and `parse_width_m(tags.get("width"))` is not None → set `WIDTH_M` (rounded 2 dp) and `WIDTH_SOURCE = "osm"`. Set `metadata["osm_enabled"] = True`, `metadata["osm_attribution"] = schema.OSM_ATTRIBUTION`, `metadata["osm_ways_fetched"]`, `metadata["osm_matched_segments"]`, and recompute `width_source_counts`. The fetch function must be referenced as a module attribute (`from dbe import osm_client` … `osm_client.fetch_highways(...)`) so tests can monkeypatch it.

- [ ] **Step 1: Write the failing tests**

```python
from shapely.geometry import LineString

from dbe.geometry import LocalProjection
from dbe.osm_client import OsmWay
from dbe.osm_match import OsmMatcher, normalise_name, osm_columns_for, parse_width_m

CURTIN = (-32.0018629, 115.8924599)


def test_normalise_name_expands_abbreviations():
    assert normalise_name("Kent St") == normalise_name("Kent Street") == "kent street"
    assert normalise_name("Leach Hwy") == "leach highway"
    assert normalise_name("Manning Rd.") == "manning road"
    assert normalise_name(None) == ""


def test_parse_width_m():
    assert parse_width_m("7.5") == 7.5 and parse_width_m("7.5 m") == 7.5 and parse_width_m("7,5") == 7.5
    assert parse_width_m("wide") is None and parse_width_m(None) is None


def _local_line(proj, pts):
    return proj.to_wgs84(LineString(pts))


def test_matcher_picks_overlapping_way_with_same_name():
    proj = LocalProjection(*CURTIN)
    near = _local_line(proj, [(0, 5), (300, 5)])          # 5 m north of the segment, same name
    far = _local_line(proj, [(0, 200), (300, 200)])       # same name but 200 m away
    other = _local_line(proj, [(0, 0), (300, 0)])         # perfect overlap but different name
    ways = [OsmWay(1, {"name": "Kent Street", "width": "7.5"}, tuple(near.coords)),
            OsmWay(2, {"name": "Kent Street"}, tuple(far.coords)),
            OsmWay(3, {"name": "Hayman Road"}, tuple(other.coords))]
    matcher = OsmMatcher(ways, proj)
    segment = _local_line(proj, [(0, 0), (300, 0)])
    assert matcher.match("Kent St", segment).id == 1
    assert matcher.match("Nowhere Rd", segment) is None
    assert matcher.match(None, segment) is None


def test_matcher_rejects_low_share():
    proj = LocalProjection(*CURTIN)
    short = _local_line(proj, [(0, 5), (50, 5)])  # covers only 50 of 300 m
    matcher = OsmMatcher([OsmWay(1, {"name": "Kent Street"}, tuple(short.coords))], proj, min_share=0.5)
    assert matcher.match("Kent St", _local_line(proj, [(0, 0), (300, 0)])) is None


def test_osm_columns_for():
    assert osm_columns_for(None) == {"OSM_WAY_ID": None, "OSM_HIGHWAY": None, "OSM_LANES": None,
                                     "OSM_MAXSPEED": None, "OSM_SURFACE": None}
    way = OsmWay(9, {"highway": "residential", "lanes": "2", "maxspeed": "50", "surface": "asphalt"}, ())
    assert osm_columns_for(way) == {"OSM_WAY_ID": 9, "OSM_HIGHWAY": "residential", "OSM_LANES": "2",
                                    "OSM_MAXSPEED": "50", "OSM_SURFACE": "asphalt"}
```

Append to `tests/test_extract.py`:

```python
def test_with_osm_fills_width_only_where_missing(fixture_source, curtin_2400, monkeypatch):
    from shapely import wkt

    from dbe import extract as extract_mod
    from dbe.osm_client import OsmWay

    base = extract(source=fixture_source, **curtin_2400)
    local = next(r for r in base.roads if r["WIDTH_SOURCE"] == "none" and r["ROAD_NAME"])
    state = next((r for r in base.roads if r["WIDTH_SOURCE"] == "mrwa_pavement"), None)
    ways = [OsmWay(101, {"name": local["ROAD_NAME"], "highway": "residential", "width": "6.8"},
                   tuple(wkt.loads(local["GEOMETRY_WKT"]).coords) if not local["GEOMETRY_WKT"].startswith("MULTI")
                   else tuple(list(wkt.loads(local["GEOMETRY_WKT"]).geoms)[0].coords))]
    if state is not None:
        ways.append(OsmWay(102, {"name": state["ROAD_NAME"], "highway": "trunk", "width": "99"},
                           tuple(wkt.loads(state["GEOMETRY_WKT"]).coords) if not state["GEOMETRY_WKT"].startswith("MULTI")
                           else tuple(list(wkt.loads(state["GEOMETRY_WKT"]).geoms)[0].coords)))
    monkeypatch.setattr(extract_mod.osm_client, "fetch_highways", lambda *a, **k: ways)
    res = extract(source=fixture_source, with_osm=True, **curtin_2400)
    row = next(r for r in res.roads if r["OBJECTID"] == local["OBJECTID"])
    assert row["WIDTH_M"] == 6.8 and row["WIDTH_SOURCE"] == "osm" and row["OSM_WAY_ID"] == 101
    if state is not None:
        srow = next(r for r in res.roads if r["OBJECTID"] == state["OBJECTID"])
        assert srow["WIDTH_SOURCE"] == "mrwa_pavement" and srow["WIDTH_M"] != 99  # MRWA wins
    assert res.metadata["osm_enabled"] is True and res.metadata["osm_attribution"]
    assert res.metadata["width_source_counts"].get("osm", 0) >= 1
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_osm_match.py tests/test_extract.py -q` → `ModuleNotFoundError` / `AttributeError: module 'dbe.extract' has no attribute 'osm_client'`

- [ ] **Step 3: Implement `osm_match.py`**

```python
"""Match OpenStreetMap ways to MRWA segments by name and proximity; expose OSM tag columns."""
from __future__ import annotations

import re
from collections import defaultdict

from shapely.geometry import LineString

from dbe.geometry import LocalProjection
from dbe.osm_client import OsmWay

ABBREVIATIONS: dict[str, str] = {
    "rd": "road", "st": "street", "hwy": "highway", "ave": "avenue", "av": "avenue", "dr": "drive", "pl": "place",
    "cres": "crescent", "ct": "court", "tce": "terrace", "bvd": "boulevard", "blvd": "boulevard", "fwy": "freeway",
    "pde": "parade", "cl": "close", "gr": "grove", "la": "lane", "wy": "way", "cct": "circuit", "esp": "esplanade",
}
_PUNCT = re.compile(r"[^a-z0-9 ]+")
_WIDTH = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*(?:m|metres|meters)?\s*$", re.IGNORECASE)


def normalise_name(name: str | None) -> str:
    if not name:
        return ""
    words = _PUNCT.sub(" ", name.lower()).split()
    return " ".join(ABBREVIATIONS.get(w, w) for w in words)


def parse_width_m(value: str | None) -> float | None:
    if value is None:
        return None
    m = _WIDTH.match(str(value))
    return float(m.group(1).replace(",", ".")) if m else None


def osm_columns_for(way: OsmWay | None) -> dict:
    if way is None:
        return {"OSM_WAY_ID": None, "OSM_HIGHWAY": None, "OSM_LANES": None, "OSM_MAXSPEED": None, "OSM_SURFACE": None}
    t = way.tags
    return {"OSM_WAY_ID": way.id, "OSM_HIGHWAY": t.get("highway"), "OSM_LANES": t.get("lanes"),
            "OSM_MAXSPEED": t.get("maxspeed"), "OSM_SURFACE": t.get("surface")}


class OsmMatcher:
    def __init__(self, ways: list[OsmWay], proj: LocalProjection, buffer_m: float = 15.0, min_share: float = 0.5) -> None:
        self.proj = proj
        self.buffer_m = buffer_m
        self.min_share = min_share
        self._by_name: dict[str, list[tuple[OsmWay, object]]] = defaultdict(list)
        for way in ways:
            key = normalise_name(way.tags.get("name"))
            if key and len(way.coords) >= 2:
                local = proj.to_local(LineString(way.coords)).buffer(buffer_m)
                self._by_name[key].append((way, local))

    def match(self, road_name: str | None, geom_wgs84) -> OsmWay | None:
        key = normalise_name(road_name)
        if not key or key not in self._by_name:
            return None
        local_seg = self.proj.to_local(geom_wgs84)
        if local_seg.length <= 0:
            return None
        best, best_share = None, 0.0
        for way, buffered in self._by_name[key]:
            share = local_seg.intersection(buffered).length / local_seg.length
            if share > best_share:
                best, best_share = way, share
        return best if best_share >= self.min_share else None
```

- [ ] **Step 4: Wire `with_osm` in `extract.py`** — add `from dbe import osm_client` and `from dbe.osm_match import OsmMatcher, osm_columns_for, parse_width_m` at the top; keep a `geoms: dict[oid, geom]` map while building rows; then, before sorting:

```python
    osm_ways_fetched = osm_matched = 0
    if with_osm:
        ways = osm_client.fetch_highways(lat, lon, radius_m + 200.0)
        osm_ways_fetched = len(ways)
        matcher = OsmMatcher(ways, proj)
        for row in roads:
            way = matcher.match(row.get("ROAD_NAME"), geoms[row["OBJECTID"]])
            row.update(osm_columns_for(way))
            if way is not None:
                osm_matched += 1
                if row["WIDTH_M"] is None:
                    w = parse_width_m(way.tags.get("width"))
                    if w is not None:
                        row["WIDTH_M"] = round(w, 2)
                        row["WIDTH_SOURCE"] = "osm"
```

and extend `metadata` with `"osm_ways_fetched": osm_ways_fetched, "osm_matched_segments": osm_matched`, set `"osm_attribution": schema.OSM_ATTRIBUTION if with_osm else None`, and compute `width_source_counts` **after** this block.

- [ ] **Step 5: Run** — `uv run pytest -q && uv run ruff check .` → all pass (`5` new in osm_match, `1` new in extract), clean. Then one live run: `uv run dbe extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km_osm --osm` (Overpass may take 1–3 minutes for 10 km); record `osm_ways_fetched`, `osm_matched_segments` and `width_source_counts` in `progress.md` → Verification log. Honest expectation: `osm` widths on a small percentage of local roads.

- [ ] **Step 6: Commit** — `git add dbe/osm_match.py dbe/extract.py tests/test_osm_match.py tests/test_extract.py && git commit -m "feat(osm): name+proximity matching, --osm fills width only where MRWA has none"`

---

## Segment 6 — Documentation and vault (Haiku + Opus)

### Task S6.T1: README and CLAUDE.md polish (Haiku)

**Files:**
- Create: `README.md`
- Modify: `CLAUDE.md` (only if commands or file names changed during the build)

- [ ] **Step 1: Write `README.md`** with these sections, in this order, using real values from `output/curtin_10km/metadata.json` and `docs/task_docs/e2e_curtin_10km.md`:
  1. **What it does** (two sentences) and the exact Curtin command.
  2. **Install**: `uv sync`; Python ≥ 3.11.
  3. **Usage**: both subcommands with every flag, one line each.
  4. **Outputs**: table of the four files; sheet list of the XLSX; note that XLSX is a conversion of the CSV and that cells over 32,767 characters are truncated only in the XLSX.
  5. **Column dictionary**: every `OUTPUT_COLUMNS` entry with one-line meaning and unit; every `VERTEX_COLUMNS` entry. Mark the 25 original columns as "as served by MRWA layer 17".
  6. **Width — read this**: width is measured for State Roads only (MRWA layer 12); local roads are blank unless `--osm` finds a tagged width; never estimated; `WIDTH_SOURCE` values.
  7. **Circle rule**: intersects, whole geometry kept, `INSIDE_FRACTION`.
  8. **Data sources and licences**: MRWA CC BY 4.0 attribution line, GDA94/WGS84 note, OSM ODbL attribution (state "not implemented" if Segment 5 was skipped).
  9. **Validation**: what `tests/test_reconcile_csv.py` checks and the last observed ratio.
  10. **Development**: `uv run pytest -q`, `-m network`, `ruff`, fixture regeneration, `scripts/qa_plot.py`.

- [ ] **Step 2: Commit** — `git add README.md CLAUDE.md && git commit -m "docs: README with column dictionary, width caveats and licences"`

---

### Task S6.T2: Vault worklog entry and handoff note (Opus)

**Files:**
- Modify: `/Users/watermenon/Desktop/Repositories/Vault/Vault/05-Projects/DBE/DBE.md` (append under `## Worklog`, newest first; tick the done items under `## Open questions / next`; fill `remote:` if a GitHub remote exists)
- Create: `docs/task_docs/handoff_to_fable.md`

- [ ] **Step 1: Read the vault rules first**: `Vault/CLAUDE.md` §13 and `Vault/05-Projects/CLAUDE.md`. Then append one worklog entry:

```markdown
### DD-MMM-YYYY — Build complete through Gate C
- **Did:** <segments completed, test count, e2e counts: segments, vertices, width_source_counts>
- **Decisions:** <link any new decision note created during the build, or "none beyond [[MRWA ArcGIS Over Google Maps and OSM]]">
- **Learned:** <real findings from progress.md Decisions log: confirmed field names, paging behaviour, CWY match patterns, OSM match rate>
- **Next:** Fable end-to-end review; <open items>
- **Links:** [progress](file:///Users/watermenon/Desktop/Repositories/DBE/docs/task_docs/progress.md) · [e2e record](file:///Users/watermenon/Desktop/Repositories/DBE/docs/task_docs/e2e_curtin_10km.md) · commit <sha>
```

If a genuinely new architectural decision was made during the build (e.g. a paging fallback became the primary path), create a decision note from `_templates/decision.md` in `05-Projects/DBE/decisions/` with `project: "[[DBE]]"` and link it from the hub's `## Key decisions`. Do not commit the vault.

- [ ] **Step 2: Write `docs/task_docs/handoff_to_fable.md`**: final commit SHA; `uv run pytest -q` and `ruff` summary lines; the e2e metadata counts; the list of every Decisions-log entry (one line each); anything skipped and why; anything you are not confident about (be specific — Fable will look there first).

- [ ] **Step 3: Commit** — `git add docs/task_docs/handoff_to_fable.md && git commit -m "docs: handoff note for Fable review"`

---

## Gate C — Opus final review and completion

Checklist for the Opus reviewer:
1. Fresh clone check: `git stash -u || true; uv sync && uv run pytest -q && uv run ruff check .` all clean; then `git stash pop` if anything was stashed.
2. Every task row in `progress.md` is `done` or (Segment 5 only) `skipped` with a reason; every gate has a PASS entry.
3. README column dictionary matches `schema.OUTPUT_COLUMNS` exactly (count 53, same order). **Do not use a substring test** — `c in readme_text` passes even with whole tables deleted, because several column names (`LAT`, `LON`, `ROAD`) are substrings of others. Gate C (2026-09-23) found the original check here "gives the right answer by luck". Parse the leading backticked token of each table row instead, and compare the resulting sequence to `schema.OUTPUT_COLUMNS + schema.VERTEX_COLUMNS` for both membership and order.
4. `init_prompt.md` requirements, each with ✅: two inputs (centre + radius) → lat/lon of all roads in the circle → CSV in the provided format (25 original columns first) → extra road info incl. width → free, current source → CSV converted to XLSX.
5. Constraints §1 re-checked line by line.
6. `handoff_to_fable.md` exists and is honest about gaps.
7. Set `progress.md` → Status → Overall `complete — awaiting Fable review`, and write the Gate C entry.

---

## 5. Fable handoff (final review — user triggers this)

Fable's review scope, so the orchestrator knows what will be checked:
- Re-run the Curtin 10 km extraction from a **cold cache** (`--cache-dir` pointing at an empty directory) and compare `segments_intersecting` with the recorded value (drift of a few rows is acceptable — the live layer changes; a large drift is not).
- Independently verify five random rows' geometry against the MRWA REST service by `OBJECTID` (`/17/query?objectIds=<id>&outFields=ROAD,NETWORK_ELEMENT&returnGeometry=true&outSR=4326&f=geojson`) and confirm the WKT matches to 7 decimals.
- Independently verify two State Road widths against layer 12 for the same `ROAD`/SLK span.
- Read every Decisions-log entry and check each was applied consistently in code, tests, README and metadata.
- Open the XLSX and confirm sheet contents equal the CSV contents (row counts, a sampled row).
- Review the vault hub, decision note and worklog for accuracy against `progress.md`.

---

## 6. Vault protocol (summary — the vault's own `CLAUDE.md` is the authority)

- Hub: `Vault/05-Projects/DBE/DBE.md` (exists; created 2026-09-22). Append worklog entries newest first, `### DD-MMM-YYYY — title`, with `Did / Decisions / Learned / Next / Links` bullets. Never paste code.
- Decisions: `Vault/05-Projects/DBE/decisions/<Title Case>.md` from `_templates/decision.md`; `project: "[[DBE]]"`; `> [!important] Decision` callout; link from the hub's `## Key decisions`.
- Concepts: `Vault/04-Concepts/Linear Referencing.md` exists; extend it rather than duplicating if SLK behaviour is learned.
- Never commit or push the vault; `obsidian-git` does that while Obsidian is open.

---

## Appendix A — ArcGIS REST query reference (verified 2026-09-22)

```text
POST https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer/17/query
  where=1=1
  geometry=115.786,-32.092,115.999,-31.912          # xmin,ymin,xmax,ymax in lon/lat
  geometryType=esriGeometryEnvelope
  inSR=4326
  spatialRel=esriSpatialRelIntersects
  outFields=*
  returnGeometry=true
  outSR=4326
  f=geojson
  orderByFields=OBJECTID ASC
  resultOffset=0
  resultRecordCount=2000

GET  …/MapServer/17?f=pjson                          # layer metadata: fields, maxRecordCount, advancedQueryCapabilities
GET  …/MapServer?f=pjson                             # service metadata: 33 layers
```

Response (geojson): `{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"LineString","coordinates":[[lon,lat],…]},"properties":{"ROAD":"H001",…,"GEOLOC.STLength()":0.0003}}],"exceededTransferLimit":true}` — the `exceededTransferLimit` flag may appear at top level or under `properties`; the client treats a page shorter than `resultRecordCount` as the last page regardless.

## Appendix B — Known risks and fallbacks

| Risk | Signal | Fallback |
|---|---|---|
| Paging unsupported (`supportsPagination: false`) | S0.T2 metadata; page 2 returns an error | Query `returnIdsOnly=true` for the envelope, then fetch `objectIds=` in chunks of ≤ 2000 via POST. Implement inside `MRWAClient.query_envelope`, keep the public signature. Record in Decisions log. |
| `orderByFields` rejected | ArcGIS error mentioning orderBy | Drop `orderByFields`; rely on `resultOffset` (stable enough on a static layer) and the OBJECTID de-duplication in `extract()`. |
| Layer 12 CWY values do not align with layer 17 (`Single` vs `Left/Right`) | `test_fixture_state_roads_get_widths` ratio < 0.8 | Already handled by `cwy_compatible`; if the pattern is SLK offsets instead, print examples and stop for a Decisions-log entry. |
| GeoJSON output returns `MultiLineString` for some segments | `VERTEX_COUNT` > coords of first part | Handled (`PART` column, WKT `MULTILINESTRING`). |
| Service throttles (429) during the 10 km run | client warnings, back-off | Cache makes re-runs cheap; raise `sleep_s` to 1.0 via a Decisions-log entry if throttling repeats. |
| Excel limits | truncation warning / sheet split | Handled in `csv_to_xlsx`; CSV remains complete. |
| Overpass timeouts on 10 km | `OsmError` | Mirror fallback; reduce to `[timeout:300]`; or skip Segment 5 — it is optional. |
| Layer schemas drift after 2026-09-22 | `test_fixtures_shape.py` or S0.T2 output differs | Re-record fixtures; update `enrich.py` field constants; Decisions log. |
