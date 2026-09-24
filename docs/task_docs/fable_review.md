# DBE — Fable end-to-end review

**Date:** 2026-09-24. **Reviewed:** `main` at `9685d0c` (clean tree, equal to `origin/main`). **Scope:** plan §5 plus `handoff_to_fable.md` §6, plus checks that use a reference none of the three gates used — the true circle, the pavement geometry, and the user's own statewide CSV.

## Verdict

**As shipped: not a pass.** Two streets inside the 10 km circle were excluded because inclusion was tested against a 256-sided polygon *inscribed* in the circle. Every earlier completeness proof queried the live service with that same polygon, so none could see it. Everything else found is documentation, hardening, or records.

**After the fixes below: PASS.** The fixes are committed as `e13c2d7` (geometry), `8d2e37e` (export), `a0849d0` (cli) and `af6431e` (docs), and pushed. Opus review of the diff: **two REQUEST CHANGES rounds, both closed — see the addendum at the end.**

Confidence tags: `[Certain]` = reproduced here with the numbers shown; `[Likely]` = strong inference.

## What was checked, with results

| # | Check | Result |
|---|---|---|
| A1 | Fresh clone → `uv sync`, `pytest -q`, `ruff`, `pytest -m network` | `94 passed, 3 skipped, 1 deselected` (3 skips = the data-dependent reconciliation tests, absent in a clone); `All checks passed!`; `1 passed`. After the fixes, in-repo: **`103 passed, 1 deselected`**, ruff clean. |
| A2 | Reconciliation test in-repo | before: `21558/21558 ratio=1.0000`; after regeneration: **`21560/21560 ratio=1.0000`**, `regions: {'Metropolitan': 21643, '': 2}` |
| A3 | **SLK join spatial validity** — distance from each of the 1,202 width rows' geometry to every matched layer-12 span's geometry (AEQD, from cache) | median 0.01 m, p99 0.05 m, max 47.06 m (a divided highway's offset carriageway); **0 rows > 50 m**. No SLK-equation mis-join. |
| A10 | **Excluded layer-17 features inside the true circle** (5,331 candidates from cache) | **2**: `100718972` Wrexham St (`1190098/5-S`) and `100719378` Fifth St (`1190201/2-S`), both 9,999.912 m from the centre; polygon inradius 9,999.247 m (sagitta 0.753 m); kept rows previously maxed at 9,999.34 m. Next excluded feature is at 10,000.20 m. → **F10 `[Certain]`** |
| A11 | Σ(matched span overlap)/segment SLK length | min 0.859, median 1.000, **max 1.500; 4 rows > 1.0, all with disagreeing seal widths** (see F11); 1 row < 0.9 |
| A4 | Width invariants | `WIDTH_M == round(seal, 2)` and `WIDTH_M is None ⇔ WIDTH_SOURCE == none` hold on all rows; 0 non-state rows with a width. Seal > pavement on 117 rows and trafficable > seal on 130 rows — **a source property**: 315 and 227 of the 4,307 raw layer-12 records already have it. Width/lane outside 2.5–7 m on 87 rows (wide 2-lane roads with parking; informational). |
| A5 | Non-simple geometries | **10** rows (`100719992`, `100828427`, `100828623`, `100828624`, `100828626`, `100828629`, `100828630`, `100828631`, `100828949`, `100828958`); `INSIDE_FRACTION` may under-report on these. 0 MultiLineStrings. |
| A6 | **Value-level reconciliation vs the user's CSV**, all 25 original columns | all 21,643 rows matched on (`NETWORK_ELEMENT`, `CWY`, `START_SLK`). `OBJECTID` and `GlobalID` differ on **every** row (ArcGIS regenerates them per publication). The other 23 columns agree; the only differences are formatting — `RA_NO` `7` vs `07`, node numbers, and `GEOLOCSTLength` (the user's export rounds to 3 significant figures, e.g. `8.76E-05`). |
| A7 | XLSX vs CSV, every cell, both sheets | roads 21,645 × 53 and vertices 85,122 × 9: **0 text mismatches, 0 blank mismatches, 0 id columns coerced**; numeric cells all within 1e-9 relative (see F14). Metadata sheet 25 rows. |
| A9 | `metadata.json` identities | `28,142 − 1,168 − 5,329 = 21,645` ✓; vertices = Σ`VERTEX_COUNT` = file rows ✓; type and width counters ✓. `features_layer12/16/8` are raw counts (4,307 / 10,312 / 9,576; distinct 4,172 / 9,936 / 9,465). |
| A12 | `to-xlsx` with `--roads`/`--vertices` swapped and a missing `--metadata` | before the fix: **exit 0**, `roads` sheet held vertices, `metadata` sheet empty → **F12 `[Certain]`** |
| B1 | Cold-cache live re-run of the shipped code into a scratch directory | exit 0 in **139 s**; 21,643 segments / 85,118 vertices; `roads.csv` **identical to the reference apart from `EXTRACTED_AT_UTC`**. No service drift in the intervening day. |
| B2 | Live `returnIdsOnly` with the 257-point polygon | 21,643 ids, 0 missing, 0 extra — relative to the polygon, which is the point. |
| B3 | 5 random rows re-fetched by `OBJECTID` | WKT equal at 7 dp, vertices rows equal, start/end equal — 5 of 5. |
| B4 | 3 widths re-derived by a `where ROAD=… AND SLK overlaps` query (not the envelope), own overlap code | `H727` 3.34 m ✓, `H016` 30.7 m ✓; `H001` Left 1.04–1.24: CSV 10.15 vs live 10.16 — the exact mean is 10.155 and the two paths sit on either side of the rounding boundary because the cached geojson carries float32 artefacts (`6.0999999`) and the live `f=json` does not. Not a defect. |
| B5 | **Datum-margin check**: `returnIdsOnly` on the envelope padded +50 m and +200 m, geometry of every extra id fetched and tested against the true circle | 5,510 / 6,159 extra ids; **exactly 2 inside the true circle — the F10 pair**. The zero-margin envelope loses nothing else. |
| B6 | Licence text | `copyrightText` is empty on the MapServer and layer 17; the portal page is script-rendered. CC BY 4.0 stays `[Likely]` on the portal's dataset description, as plan §2 recorded. |
| C1 | Decisions-log consistency | every entry applied in code/tests/README/metadata except the records drift in F4. |
| C2 | `init_prompt.md` requirements | two inputs ✓ · lat/lon of all roads in the circle ✓ (after F10) · CSV in the provided 25-column shape ✓ · extra info incl. width ✓ (best-effort, per the user's planning answer) · free, current source ✓ (qualified by F3) · CSV → XLSX ✓. |

## Findings

**F10 `[Certain]` — Important — two roads inside the circle were excluded.** Inclusion was `local.intersects(circle_polygon)` with `quad_segs=64`. The S1.T1 review recorded the 0.753 m sagitta as "spec-conformant, no change" without checking whether a real road sat in the band; two did. Gates B and C proved the row set equal to *the polygon's*. Not Critical, because both rows lie 0.09 m inside a boundary whose datum uncertainty is ±1.5 m and no interior road is missing — but the user-facing claim "every road segment inside a circle" was false as written. **Fixed** in `dbe/geometry.py`: inclusion is `dist_to_centre_m <= radius_m`, with the radius read exactly from the buffer's bounds; the polygon still serves `INSIDE_FRACTION` (it can under-count up to ~0.75 m per boundary crossing at 10 km — worst 0.043 on the reference run per the Opus review — and a segment included only inside the band reports 0.0). Two tests pin the mid-chord band at 0.99995 R (included) and 1.00005 R (excluded). **Reference output regenerated from the original cache:** 21,643 → **21,645** rows, 85,118 → **85,122** vertices, outside 5,331 → 5,329; both streets present at `DIST_TO_CENTRE_M` 9,999.91, `INSIDE_FRACTION` 0.0. Plan §3.2 amended.

**F11 `[Certain]` — four `WIDTH_M` values blend overlapping, disagreeing pavement records.** Layer 12 holds records that overlap each other on the same carriageway, with no date or status field to choose between them; the overlap-weighted mean blends them. Rows: `100817373` H001 Left 1.29–1.43 (coverage 1.43, `WIDTH_M` 11.28 from records at 9.8 / 10.8 / 12.1 m); `100817374` H001 Left 1.37–1.49 (1.50, 11.43); `100817757` H001 Right 1.27–1.43 (1.375, 10.51); `100817758` H001 Right 1.37–1.49 (1.50, 10.70). Also `100821374` H017 Right 42.2–43.05: only 86 % of its SLK range is covered because the exact-carriageway preference discards a `Single` span. Same-logic re-derivation cannot see this and the spatial check passes (all records are on the road). **Documented** in the README's Width section; no schema change without the user's say. Deferred option: a `width_rows_with_overlapping_spans` metadata counter.

**F1 `[Certain]` — `GEOLOCSTLength` is in degrees, not metres.** Ratio to `LENGTH_M` is 9.0e-6–1.06e-5 on every row (planar length in the source's GDA94 geographic CRS); the user's own export has the same values. README said "metres" and "may differ slightly". **Fixed** in the README column dictionary.

**F2 `[Certain]` — swapped lat/lon died with a pyproj traceback.** `LocalProjection(115.89, -32.0)` raises `CRSError`, not caught by `cli.main`; the promised "check lat/lon order" message lived in `NoRoadsFound`, unreachable for any WA swap; `nan`/`inf` inputs took the same path. **Fixed** in `dbe/cli.py` with argparse types (`_latitude`, `_longitude`, finite `_positive`) and a swap hint; tests added. The `--osm` refusal text no longer claims the Curtin percentage for every centre.

**F12 `[Certain]` — `to-xlsx` validated nothing.** Swapped inputs produced a mislabelled workbook with exit 0; a missing metadata file silently became `{}`. **Fixed** in `dbe/export.py` (`_require_header` against `schema`, metadata must exist); tests added.

**F3 `[Certain]` — the cache never expires, hits are not logged, and a replay stamps a fresh `EXTRACTED_AT_UTC`.** Re-running into the same `--out` is an offline replay with a new timestamp on every row; the brief asked for an up-to-date source. **Documented** in the README (how to refresh). Deferred: `pages_from_cache` / `pages_fetched_live` counters in metadata and an INFO log line per cache hit.

**F14 `[Certain]`, corrected mid-review — "XLSX equals CSV" is a tolerance claim by nature of the format.** The second-opinion agent attributed the ~1e-14 residuals to pandas' fast float parser and said `float_precision="round_trip"` removes them. The kwarg is correct and was applied (roads-sheet inexact cells fell 78,687 → 66,683), but the rest comes from the XLSX writer serialising numbers to 16 significant digits (`%.16g`) (`115.9970610960001` for `115.99706109600005`), which no reader can undo. README now says "agrees to within 1e-14 relative" instead of "provably a conversion".

**F4 `[Certain]` — records still carried the withdrawn "licence was the deciding factor" framing** (tracker row S5.T2, Decisions entry, plan Segment 5 preamble, repo `CLAUDE.md`), and the README/plan still said the reconciliation threshold was 0.95/95 % while the test asserts 0.99. **Fixed**: row reworded; dated addenda under the Decisions entry and the plan preamble (history left intact); `CLAUDE.md` line; README and plan §3.7 thresholds.

**F15 `[Certain]` — user-facing counts included paging duplicates.** "4,307 layer-12 records" is raw; 4,172 distinct. **Fixed** in the README Width section and metadata table.

**F5 `[Certain]`** vault hub Stack line still listed OpenStreetMap as an optional source — fixed. **F6 `[Certain]`** minors: README paragraph glue fixed; `with_osm` dead parameter and `openpyxl.IllegalCharacterError` escaping `cli.main` recorded, not fixed (no WA data triggers the latter: 0 control characters in 189,865 statewide rows). **F7 `[Certain]`** closed: the duplicated `NETWORK_ELEMENT` ids exist in the user's export too (328 ids, 682 rows; `H001/382-R` twice). **F8 `[Likely]`** carried I2/I3 triage is right — memory (733 MB at 21.6 k rows) bites long before Excel's row cap (~48× rows); README now carries a labelled scaling estimate. **F9 `[Certain]`** neither CSV has a BOM; the em-dash in every row's `DATA_SOURCE` will mojibake in Excel's *CSV* import on a cp1252 locale (the XLSX is unaffected) — recorded; cure is an ASCII hyphen in `schema.DATA_SOURCE`. **F13 `[Certain]`** CSV/JSON writes are not atomic — recorded with carried item #6; recommended fix is the cache's tmp + `os.replace` pattern.

**Handoff accuracy.** `handoff_to_fable.md` §1 said 83 tests; the suite was 94 offline + 3 data-dependent + 1 network at `9685d0c` (the auto-plot work added tests after Gate C). Its §6 item 2 ("re-run the polygon id diff") is the check that could not have found F10. A supersession note now heads that file.

## Process notes

- Every reviewer prior to this one — three gates, ~20 per-task reviews — used the code's own circle polygon as the reference for completeness. The defect was in the reference, so repetition could not find it; a different reference (the true circle via padded envelopes) found it in one query. Rule worth keeping: **a completeness proof must use a reference the code did not build.**
- The second-opinion agent's two headline findings (F10, F11) both reproduced exactly; its F14 explanation was half right and was corrected by looking at the raw XML. Treat agent findings as hypotheses until the numbers are reproduced.
- Widths were verified three independent ways this time (same-logic re-derivation, a different query path, spatial co-location) and all agree except the four blended rows, which no width check could flag without the coverage ratio.

## Deferred, recommended (not done, to keep the change small)

1. Atomic `write_csv` / `write_json` / workbook writes (F13, carried #6).
2. Cache-hit counters in metadata and an INFO line per cache hit (F3).
3. `width_rows_with_overlapping_spans` metadata counter, or a `WIDTH_COVERAGE` column (F11 — schema change, user's call).
4. ASCII hyphen in `schema.DATA_SOURCE` (F9).
5. Remove the five always-blank OSM columns (schema change, user's call).

## Addendum — Opus review of the diff

**Round 1 — REQUEST CHANGES.** All four code fixes judged correct; mutations run in a scratch copy: reverting the inclusion test, removing `_require_header`, allowing `{}` metadata, reverting the argparse types and removing `isfinite` all failed their new tests. Three mutations survived: a radius 0.1 m short (band test too loose), removing `float_precision="round_trip"` (unpinned), disabling the longitude range check (untested). **Important:** the `INSIDE_FRACTION` error bound I had written ("7.5e-5 of a segment's length") was false — the polygon loses up to ~0.75 m per boundary crossing, worst under-report 0.043 across the 377 boundary rows. README claims for the circle rule, `GEOLOCSTLength` and the cache were checked and confirmed. **Fixed:** bound reworded in README and the docstring; `--lon 200` / `--lat 95` cases added; the export comment no longer claims exactness.

**Round 2 — REQUEST CHANGES on one item.** The Important and two Minors confirmed fixed; the band test at factor 0.99999 still passed with the radius 0.1 m short because the test point sat exactly at the mutated radius. Reviewer prescribed factors 0.999995 / 1.000005 and verified them in a scratch copy. Nit: openpyxl writes `%.16g`, so "16 significant digits", not "15–16". **Fixed:** factors applied, wording tightened. I then ran the reviewer's own mutation (`bounds[2] * 0.99999`) against the working tree: `1 failed, 14 passed`; restored: `103 passed, 1 deselected`, ruff clean. The last one-line change was not sent for a third Opus round — the reviewer had already specified and verified it; the user can ask for one.
