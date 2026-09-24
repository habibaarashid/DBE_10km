# DBE — Progress Tracker

> **Authoritative state of the build.** The Opus orchestrator updates this file after **every task and every gate**. To resume after an interruption: read `docs/task_docs/orchestrator_plan.md` §0–§3, then this file top to bottom, then `git log --oneline -5`, then `uv run pytest -q`, then continue from the first task below that is not `done`.

## Status

| Field | Value |
|---|---|
| Overall | **`complete — Fable review PASSED after fixes`** (2026-09-24). Segments 0–4 and 6 complete; Segment 5 skipped on a measurement; Gates A, B, C PASSED; the Fable review found two boundary roads excluded and fixed the inclusion test — see `docs/task_docs/fable_review.md`. Fixes committed as `e13c2d7`, `8d2e37e`, `a0849d0`, `af6431e` and pushed. |
| Current segment | none — build complete |
| Current task | none — build complete and reviewed |
| Last code commit | `a0849d0` — `fix(cli): validate --lat/--lon ranges and finiteness with a swap hint` (docs at `af6431e`) |
| Last updated (UTC) | 2026-09-24, Fable end-to-end review complete |
| Blockers | none |
| ✅ Discharged | The `curtin1500` → `curtin2500` cascade warning that sat here is **resolved**: the plan text itself was corrected in `868908a`, so S2.T2 was dispatched with correct names. Nothing to re-apply. |

Status vocabulary for task rows: `pending` · `in-progress` · `done` · `blocked` · `skipped` (only allowed for Segment 5 tasks, with a reason).

## Task table

| Task | Title | Owner model | Status | Commit | Tests (pytest summary) | Notes |
|---|---|---|---|---|---|---|
| S0.T1 | Project scaffold with uv | Sonnet | done | `e46431e` | `1 passed in 0.01s` | reviewed APPROVE (Opus); `uv.lock` amended in by orchestrator |
| S0.T2 | Verify layer schemas, record metadata fixtures | Sonnet | done | `3ddd99d` + `28e1809` | `1 passed in 0.02s` | reviewed APPROVE (Opus); `ROAD_HIERARCHY` / `SPEED_LIMIT` both confirmed |
| S0.T3 | Record 2.5 km feature fixtures at Curtin | Sonnet | done | `693315c` | `1 passed in 0.02s` | reviewed APPROVE (Opus); **radius escalated 1.5 → 2.5 km, files are `*_curtin2500.geojson`** |
| S1.T1 | LocalProjection, circle, envelope | Sonnet | done | `26fd72b` | `6 passed in 0.39s` | reviewed APPROVE (Opus); AEQD verified geodesically exact (error < 1e-9 m) |
| S1.T2 | Segment metrics, GeoJSON parsing, vertices | Sonnet | done | `7764393` + `40cf0b6` | `14 passed in 0.23s` | both commits reviewed APPROVE (Opus); one Important finding raised and closed by `40cf0b6` |
| S2.T1 | MRWAClient: paging, retries, cache | Sonnet | done | `7edb78e` + `44e5d24` | `26 passed in 0.23s` | reviewed REQUEST CHANGES then **APPROVE** (Opus, both on Opus); 1 Important finding raised and closed by `44e5d24`; live sanity call passed; 4 Minor items carried forward |
| S2.T2 | Fixture loader, FixtureSource, live smoke test | Sonnet | done | `50acb36` + `132c90a` | `30 passed, 1 deselected in 0.23s` | reviewed **APPROVE** (Opus). 3 Important findings, all defects in the **plan's own code blocks**, not the implementation; 2 fixed in code by `132c90a`, 1 recorded as a global constraint. Live `-m network` → `1 passed` (satisfies Gate A item 1). |
| S2.T2.fix1 | Reset `FixtureSource.calls`; check every fixture feature | Sonnet | done | `132c90a` | `30 passed, 1 deselected in 0.23s` | remediation of Important findings I1 and I3; 4 mutation proofs by the implementer, 2 re-verified independently by the orchestrator |
| **Gate A** | Opus review of Segments 0–2 | **Opus** | done | `cfdf48d` (amendments) | `30 passed, 1 deselected in 0.23s` | **PASS** — no Critical; 4 Important + 6 Minor, all forward-looking, carried as plan amendments. Verdict in Gate log. |
| S3.T1 | SLK overlap join primitives | Sonnet | done | `613d632` + `f1c7f83` | `37 passed` | reviewed **APPROVE** (Opus). 1 Critical + 3 Important, **all defects in the plan's code**, not the implementation, which was byte-exact. Real-data check: 65/65 State Roads get a width, 0/1763 Local. |
| S3.T1.fix1 | Reject non-finite SLK that would hijack the join | Sonnet | done | `6f58aa4` | `41 passed, 1 deselected in 0.22s` | closes Critical C1; adds 4 tests incl. the zero-preservation invariant that no test previously pinned |
| S3.T1.fix2 | Treat non-finite values as absent in `dominant_value` too | Sonnet | done | `a3829f3` | `43 passed, 1 deselected` | closed the half-guarded gap the fix1 implementer flagged |
| S3.T2 | Enrichment (layers 12/16/8) + WIDTH_SOURCE | Sonnet | done | `1e2b04c` | `49 passed, 1 deselected in 0.32s` | reviewed **APPROVE** (Opus). Token-level diff vs the plan: only the 7 disclosed ruff wraps. 1 Important finding = a coverage gap in the **plan's** test block, routed to a fix. |
| S3.T1.fix3 | Pin the inner non-finite guard; demonstrate the hijack | Sonnet | done | `bece1c4` | `49 passed, 1 deselected` | mutation proof: removing the inner guard now fails the suite (it previously survived). Implementer also caught a **false claim in the orchestrator's own docstring** — there is no second defence; the factory is the only guard |
| S3.T2.fix1 | Value-assert the 5 unchecked enrichment columns | Sonnet | done | `24bc879` | `50 passed, 1 deselected in 0.33s` | all 4 mutations killed; orchestrator independently re-ran the two it had proved silent — both now fail |
| S4.T1 | schema.py column contract | Sonnet | done | `ab5082a` | `53 passed, 1 deselected` | **zero deviations** — first task in the build needing none, after the plan's Segment 4 blocks were pre-formatted. `ORIGINAL_COLUMNS` verified identical to the real 189,865-row CSV header. |
| S4.T2 | extract() pipeline | Sonnet | done | `45ec165` | `7 passed` (file) | Gate A amendments **I4** (empty-coordinates guard) and **I2** (envelope pinning) applied and tested. Diff vs plan = exactly the I4 line. Opus review dispatched. |
| S4.T3 | export: CSV, metadata JSON, CSV→XLSX | Sonnet | done | `7224f7b` | `5 passed` (file) | zero deviations. Proved the XLSX re-reads the CSV (hand-edited a cell on disk, it carried through), that `nan`/`NA`/`null`/`N/A` survive as text, and that a 68,011-char cell truncates in XLSX only. Opus review dispatched. |
| S4.T4 | CLI (`extract`, `to-xlsx`) | Sonnet | done | `6f278cb` | `5 passed` (file) | zero deviations. Amendment **M1** honoured: production client keeps the default back-off. `python -m dbe` works for the first time since S0.T1. |
| S4.T4a | Gate A **I1**: crash-safe disk cache | Sonnet | done | `439f6f2` + `0e18db0` | `72 passed, 1 deselected in 7.12s` | corrupt entries now self-heal; writes are atomic. My first atomicity test was worthless (passed with the fix reverted); replaced with one proven to bite both ways. |
| S4.T5 | Curtin 10 km e2e run, reconciliation test, QA plot | Sonnet | done | `a5e9084` + `4d2ebf5` + `bf583d0` | `80 passed, 1 deselected` | **live run: 185 s, exit 0, 21,643 segments, 85,118 vertices.** Reconciliation 21,558/21,558, ratio 1.0000. |
| S4.T4b | Catch malformed geometry; fix de-dup ordering | Sonnet | done | `e7c3274` | `76 passed` | the enumerated I4 guard closed 2 of 6 bad shapes; now catches the failure instead |
| S4.T3.fix1 | Pin NA-like text and the vertices seam | Sonnet | done | `60ea149` | `78 passed` | the load-bearing CSV option had zero coverage |
| S4.T5.fix1 | De-duplicate enrichment layers; accept blank region | Sonnet | done | `4d2ebf5` | `80 passed, 1 deselected in 5.81s` | 622 duplicate spans were double-weighting 10 widths |
| **Gate B** | Opus review + e2e verification | **Opus** | done | `bf583d0` | `80 passed, 1 deselected in 5.95s` | **PASS** — no Critical. Live service confirmed the row set is exactly right: 0 missing, 0 extra. Verdict in Gate log. |
| S5.T1 | OPTIONAL: Overpass client | Sonnet | skipped | | | **skipped on a measurement** — see Decisions log 2026-09-23. 685 of 70,561 OSM ways in the circle carry a width (0.97%); only 371 also carry a name. |
| S5.T2 | OPTIONAL: OSM matching + `--osm` wiring | Sonnet | skipped | | | same decision. Skipped on yield (371 usable OSM candidates against a 20,441-row gap); the ODbL licence was a second reason, not the deciding one — that framing was withdrawn at Gate C, and the choice is the user's to reverse. |
| S6.T0 | Gate B **I4**: `--osm` refuses instead of lying | Sonnet + Opus | done | `171e219` | `83 passed, 1 deselected` | became mandatory when Segment 5 was skipped. Verified: reverting the guard fails the new test; the real CLI exits 1 with the reason and writes nothing. |
| S6.T1 | README, CLAUDE.md polish | Sonnet | done | `ff1ba0b` + `c189a42` | `83 passed, 1 deselected` | 295 lines; all **62** columns documented, verified by a backticked-term check rather than a substring test. Implementer self-caught a false claim in its own draft and corrected a now-false line in `CLAUDE.md`. |
| S6.T2 | Vault worklog entry + handoff note | Opus | done | `11acca1` | `83 passed, 1 deselected` | handoff written directly after the delegated agent stalled. **Corrected after Gate C** for overclaiming — see Gate log. |
| **Gate C** | Opus final review, mark complete | **Opus** | done | this commit | `83 passed, 1 deselected` | **PASS**, conditional on this tracker edit. Found the handoff overclaiming and a placeholder threshold it called fixed. Verdict in Gate log. |

## Gate log

_Newest first. Format: `### Gate X — YYYY-MM-DD HH:MM UTC — PASS | FAIL` then the checklist results, pytest + ruff summary lines, findings, remediation tasks._

### Fable review — 2026-09-24 — **PASS after fixes** (not a pass as shipped)

Full record: `docs/task_docs/fable_review.md`. **As shipped at `9685d0c`, two streets inside the 10 km circle were excluded** — Wrexham St and Fifth St, 9,999.912 m from the centre — because inclusion tested against the inscribed 256-gon (inradius 9,999.247 m). Every earlier completeness proof queried the service with that same polygon and so could not see it; a padded-envelope query against the true circle found it in one call. Fixed: inclusion is now the exact distance to the centre; the reference output regenerated from the original cache is **21,645 rows / 85,122 vertices**, reconciliation **21,560 / 21,560**. Also fixed: `to-xlsx` accepted swapped inputs silently; a swapped lat/lon died with a pyproj traceback; `GEOLOCSTLength` was documented as metres (it is degrees); four records still called the licence "the deciding factor"; README/plan quoted a 0.95 threshold against a 0.99 test. Documented, not fixed: four `WIDTH_M` values blend overlapping disagreeing layer-12 records (all `H001`, SLK 1.27–1.49); the cache never expires and a replay re-stamps `EXTRACTED_AT_UTC`; XLSX numerics agree to 1e-14, not exactly, by nature of the format. Verified clean: SLK join spatially co-located on all 1,202 width rows (max 47 m, a divided carriageway); XLSX vs CSV 0 text mismatches over every cell; all 25 original columns agree with the user's export except `OBJECTID`/`GlobalID`, which differ on every row by publication; live cold-cache re-run byte-identical apart from the timestamp. **Suite after fixes: `103 passed, 1 deselected`; ruff clean.** Opus review of the diff: two REQUEST CHANGES rounds (a false `INSIDE_FRACTION` error bound I wrote; a band test too loose to catch a 0.1 m radius error), both closed and re-verified — addendum in the review file.

### Gate C — 2026-09-23 — **PASS, conditional on this tracker edit**

Final gate, fresh Opus reviewer. Gate B verified the deliverable; **Gate C's job was different — whether the project honestly delivers what the user asked for, and whether its own records tell the truth.** On the deliverable it found nothing. On the records it found real problems, all now corrected.

**The deliverable, re-verified independently:** the reviewer rebuilt the 257-point circle from the shipped `LocalProjection` and ran its own live `returnIdsOnly` query — **21,643 ids, 0 missing, 0 extra**. It re-ran the extraction from a copy of the warm cache: `roads.csv` came out **byte-identical** apart from the timestamp. It compared **every** cell of both XLSX sheets against the CSV, not a sample: 0 text mismatches. It re-derived **14 widths** from live layer 12 with its own weighted-mean code, including the maximum (30.7 m) and minimum (3.34 m): **all 14 reproduce to the cent.**

**The width ceiling, established rather than assumed.** The reviewer examined **all 33 MRWA open-data layers**, not the four the plan named. Only layers 12, 13 and 26 carry width fields. **Layer 13 "Pavement Detail" had never been checked** — a polyline layer with per-lane widths and the same join keys as layer 12, and a name without "State" in it. It holds **0 Local Road records statewide across 45,993 features.** Layer 26 is bridges and culverts as points. So **5.55% is the ceiling for any free statewide WA source**, now shown by evidence. It also re-ran the OSM probe live and reproduced all three figures exactly (70,561 · 685 · 371), so the Segment 5 skip rested on a sound measurement.

**Checklist: 5 of 6 ✅.** Item 2 (every row done or skipped) failed as the files stood — S6.T2 `pending` despite its deliverables existing, a duplicated S4.T4a row, status not advanced. **Closed by this commit.** Item 3 was verified properly: the reviewer parsed the leading backticked token of every table row and confirmed all 62 columns in exact schema order, noting the plan's own prescribed substring check "gives the right answer by luck".

**What Gate C found wrong in the records — each corrected in this session:**

- **I-1 — the handoff called a failure mode fixed that was still in the suite.** It listed "thresholds written as placeholders and left as if measured" as corrected. `tests/test_reconcile_csv.py` — the only test that reads the real deliverable — still asserted `ratio >= 0.95` against a measured 1.0000, which would stay green with ~1,077 of 21,558 ids corrupted, and the README presented 0.95 as a designed tolerance. **Now 0.99, with the reason recorded:** exactly 1.0 is unachievable because roads added after the user's export legitimately will not match.
- **I-2 — the handoff's headline overclaimed.** It said the defects were "in the plan's code, not the implementations". Two of its five examples were not plan code: the worthless cache test came from a dispatch prompt written mid-build, and tracker drift is orchestrator bookkeeping. **The reviewer's framing is exact: text that read as the orchestrator taking the blame actually filed orchestrator-side defects under "the plan", which cleared the orchestrator more than the record does.** Rewritten.
- **The licence judgement was made for the user without asking them.** "The deciding factor was the licence" was bolded in four documents. The reviewer: *"a defensible engineering call, but the output file and the licence exposure are the user's, and the user was never asked. The skip holds up on yield alone."* **The README now says the choice is theirs and how to reverse it.**
- **M-1** — the handoff said 85 rows share a `NETWORK_ELEMENT`; the real figure is **164 rows in 79 groups**. 85 was the excess. The reviewer also closed the open question: every group has distinct SLK ranges and no identical geometries — consecutive sub-segments of one element. Harmless.
- **M-6** — the "not mandatory but good to have" quote had no verbatim record in the repo, while `init_prompt.md` calls width "required". **Now anchored verbatim in the Decisions log below.**
- **M-3** — `metadata.json` was undocumented, including the known-misleading `features_returned_layer17`. The README now explains every key that needs it.
- **M-8** — smaller inaccuracies: a commit count that only held for one range, a cached re-run time (34 s stated, 38.7 s measured), and a claim that an oversized roads sheet "dies with a bare openpyxl error" when the CLI in fact catches it and exits cleanly — an inaccuracy that leaned self-critical, and was still wrong.

**Carried, not blocking:** M-2 (the XLSX truncation count is returned but never written to `metadata.json`, because metadata is written before conversion runs — no effect today, the longest WKT is 8.7× under the limit); M-4 (`schema.OSM_ATTRIBUTION` is dead code); M-7 (the plan's Gate C checklist still prescribes the weak substring check).

**The reviewer's summary for the user, adopted:** the deliverable is complete and reproduces; only 5.55% of rows have a width and that is the ceiling for any free WA source, not a shortfall; and one decision — declining OpenStreetMap — was made on the user's behalf and is theirs to reverse.

### Gate B — 2026-09-23 — **PASS**

Reviewed by a fresh Opus reviewer over `da46c04..HEAD`. **This is the first gate that could check the deliverable rather than infer it**, and the headline result is the strongest evidence the project has produced.

**The row set is provably complete.** The reviewer asked the live service to return the OBJECTIDs of every layer-17 feature intersecting **the exact 257-point circle polygon the code builds** (`returnIdsOnly`). The service returned **21,643 ids — 0 missing, 0 extra, set-identical to `roads.csv`.** That property cannot be self-attested from the output; it needed the source of truth. It also subsumes the earlier `returnCountOnly` truncation check, which tested the envelope by proxy. Corroborating: 26,974 distinct fetched → 21,643 kept = 80.2%, against 4/π ≈ 78.5% for a box-to-inscribed-circle area ratio, so the envelope is tight with no over-fetch pathology.

**Commands (reviewer's own):** `pytest -q` → `80 passed, 1 deselected in 5.95s` · `ruff check .` → clean · `pytest -m network -q` → `1 passed` · reconciliation → `3 passed`, printing `extracted=21558 matched=21558 new_since_export=0 ratio=1.0000` and `regions: {'Metropolitan': 21641, '': 2}`.

**Independent re-verification, beyond the checklist:** every one of the 21,643 `GEOMETRY_WKT` values re-projected and confirmed to intersect the circle, with `LENGTH_M`, `DIST_TO_CENTRE_M` and `INSIDE_FRACTION` reproducing to within 0.5 m / 0.002 and **0 mismatches**; `START_LAT/LON` and `END_LAT/LON` equal to the first and last WKT vertices and the first and last vertices-table rows for **all 21,643 rows, 0 exceptions**; Σ`VERTEX_COUNT` = 85,118 exactly. **Five segments fetched live by OBJECTID** — a 2-vertex street, a 3-vertex highway, a 22-vertex path, the 151-vertex maximum and the most distant boundary row — every coordinate matching to 7 decimal places.

**Width verified as the honest maximum, not a shortfall.** All **4,307 layer-12 features in the envelope are State Road — 100%, 0 Local** (read from the cached responses, upgrading plan §2's "Likely" to Certain). Coverage of what exists is **100%**: every one of the 1,202 State Road rows got a width and every width row is a State Road — the same set, not merely similar counts. `WIDTH_SOURCE` has exactly two states with **zero contradictions** across all rows. Nothing invented: `H001` Left SLK 0.03–0.08 matches three live pavement spans and the overlap-weighted mean re-derives to **11.76 m**, exactly the CSV value.

**Checklist: 9 of 10 ✅. Item 10 (tracker parity) ❌ — closed by this commit.** The tracker had drifted 11 commits: S4.T5 still `pending`, S3.T1.fix2 still `in-progress`, no Segment-4 Decisions entries, no e2e Verification entry. Nothing in `dbe/` or `output/` was implicated; the gate could not honestly be *recorded* as PASS until it was fixed.

**Findings — no Critical.** Four Important, eight Minor, all carried as plan amendments:
- **I2** — `csv_to_xlsx` splits the vertices sheet but never the roads sheet, so a large-enough radius completes the expensive extraction, writes both CSVs, then dies with a cryptic openpyxl error and no workbook. The reviewer explicitly declined to name the radius, noting that linear-in-area extrapolation is exactly the reasoning that produced the bad layer-12 band.
- **I3** — the pipeline is entirely in memory; `csv_to_xlsx` alone peaks at **733 MB** for this run. No practical maximum radius is documented anywhere.
- **I4** — `--osm` is inert but advertised in the help text, and `metadata.json` reports `osm_enabled: true` when passed. A user seeing 5.55% width coverage could re-run with it and wrongly conclude OSM had nothing to add. Must be fixed by S6.T1 at the latest.
- **M1** — the checklist's own wording about null-geometry duplicates is wrong, not the code: `seen.add` sits after the geometry guards deliberately, and a test pins that a malformed twin must not suppress a real feature. Amend the checklist.
- **M2** — `dominant_value` ties are broken by paging order and, in 13 rows, by floating-point noise: one row's lane count is decided by a 7e-18 difference. Advisory columns only; `WIDTH_M` is order-independent.
- **M3** — §3.8's named-roads row is mis-specified: `Orrong Rd` has 0 rows by `ROAD_NAME` but 54 by `COMMON_USAGE_NAME`, so a literal reading reports a missing arterial that is present.
- **M4** — `features_returned_layer17` reports the raw paged count including duplicates, overstating by 4.1% in a user-facing file.
- **M5** — the e2e record contradicts the commit that followed it in four places.
- **M6** — the ±20% width band would pass while 240 state roads silently lost their width; the true figure is 100%.
- **M7/M8** — no guard against a silently renamed source field (all 25 columns currently populated); inter-page sleep fires even on a full cache hit.

**The line the reviewer singled out as most consequential:** `mrwa_client.py:111` advances the paging offset by the number of features actually returned, not by the requested page size. **14 of the 15 layer-17 pages came back short while still setting the overflow flag** (1,658 · 1,794 · 1,904 · 1,744 · 1,986 · 2,000 · 1,942 · 1,959 · 1,998 · 1,939 · 1,881 · 1,976 · 1,994 · 1,993 · 1,374). Advancing by the requested size would have skipped records silently. The 1,168 duplicates are the price of erring in the safe direction, and the polygon id diff proves the direction was right.

**Blocking item closed by this commit; everything else carried.** Proceed to Segment 5 (optional) or Segment 6.

### Gate A — 2026-09-23 — **PASS**

Reviewed by a fresh Opus reviewer with no prior context in this build, over the full range `ec26c01..HEAD` (Segments 0, 1 and 2 as a whole — every earlier review looked at one task in isolation). It re-verified all seven checklist items independently rather than accepting the orchestrator's evidence, including re-running the live network call itself.

**Commands (reviewer's own runs):** `uv run --no-sync pytest -q` → `30 passed, 1 deselected in 0.23s` · `uv run --no-sync ruff check .` → `All checks passed!` · `uv run --no-sync pytest -m network -q` → `1 passed, 30 deselected in 1.16s`.

| Item | Verdict | Reviewer's own evidence |
|---|---|---|
| 1 — tests, lint, live run | **PASS** | all three commands above re-run by the reviewer; item 1 does not rest on the Verification log |
| 2 — source verification doc | **PASS** | 74 lines; `HIERARCHY_FIELD = "ROAD_HIERARCHY"` (line 31), `SPEED_FIELD = "SPEED_LIMIT"` (line 32), `supportsPagination` column `True` for all four layers (line 11) |
| 3 — fixtures | **PASS** | four `*_curtin2500.geojson`, all ≪ 5 MB (1.66 / 0.58 / 0.54 / 0.13 MB); layer 12 loaded = 113 features, all LineString, one uniform key-set; `tests/fixtures/README.md` present; `git diff HEAD -- tests/fixtures/` empty |
| 4 — `geometry.py` | **PASS** | `always_xy=True` on both transformers; bounds numerically confirmed lon∈112–129, lat∈−36…−13; zero-length guard gives `0.0` with no `ZeroDivisionError`; `rounding_precision=7` pinned by test |
| 5 — `mrwa_client.py` | **PASS** | POST/GET split pinned; ArcGIS `error` path makes **exactly 1** HTTP call; **paging driven to 45,000 features over 23 pages** against a realistic stub, offsets `[0, 2000, … 44000]`, complete and ordered — the committed suite only ever exercises 2 pages; cache key covers method, URL and all params; `MAX_PAGES` raises `MRWAError` |
| 6 — dependencies | **PASS** | no `Road_Network`, `.csv`, `data/` or `open(` anywhere in `dbe/` or `scripts/`; lockfile free of `geopandas`, `osmnx`, `fiona`, `rtree`, `pyogrio`, `googlemaps`; `git ls-files data/` empty |
| 7 — tracker | **PASS** (with M5) | all eleven SHAs resolve and their subjects match; `git log ec26c01..HEAD --format=%B \| grep -i co-authored` → no match. Two staleness items fixed in this edit. |

**Findings: no Critical. Four Important, six Minor — none blocks the gate.** All are forward-looking, affecting the 10 km production run rather than the correctness of what is committed. Full text and exact fixes are in the plan under **"Gate A carried amendments"**, placed immediately after the Gate A checklist so the next orchestrator reads them in context.

- **I1 — the disk cache is not crash-safe and a corrupt entry is permanently fatal.** *Orchestrator re-verified:* truncate a cache file, re-query → `json.JSONDecodeError`, and the network is **never attempted** (0 HTTP calls) because the `json.loads` sits outside the retry `try`. Act at **S4.T5, before the 10 km run** — this destroys exactly the resumability the cache exists for, and this project has already lost one session mid-run.
- **I2 — no offline test pins the envelope the client is sent.** `FixtureSource` records the envelope but ignores it, so every fixture-driven test would pass with an arbitrarily wrong envelope; the only guard is one 300 m live call. The seam is *correct today* — the reviewer proved the wire format round-trips bit-identically, axis order is right, and a 200,000-azimuth geodesic circle escapes the box by at most **4.8 mm** at 10 km — but nothing would catch a regression. Act at S4.T2.
- **I3 — silent truncation is possible if the service lowers `maxRecordCount`.** Short-page termination is sound only because `PAGE_SIZE == maxRecordCount == 2000`. A server capping at 1000 without `exceededTransferLimit` returns 1000 of 5000 features silently, breaching §1. Act at S4.T5 with a `returnCountOnly` cross-check.
- **I4 — an empty-coordinates geometry crashes the run.** *Orchestrator re-verified:* `{"type": "LineString", "coordinates": []}` is accepted, yields `LINESTRING EMPTY`, then `IndexError` in `segment_metrics`. The planned guard `if not feat.get("geometry")` does **not** fire because the dict is truthy. One such feature aborts the 10 km run after minutes of fetching. Act at S4.T2.
- **Minor:** M1 `sleep_s=0` disables the retry back-off as well as the inter-page delay (S4.T4 must not copy the smoke test's idiom); M2 zero envelope margin vs the ~1.5 m datum shift; M3 `MAX_PAGES = 10_000` is not a practical guard on a ~26-page run; M5 two tracker staleness items (**both fixed in this edit**); M6 §3.8 gives page counts for layer 17 only, but paging is on the critical path for four layers (≈ 15 / 6 / 5 / 1 pages).

**Four forward risks from earlier reviews were judged SAFE TO CARRY**, each reproduced rather than assumed: `INSIDE_FRACTION` under-reporting on self-overlapping geometry (error is always *under*, and it is a reported column only — inclusion uses `intersects`, so no row is ever dropped); the tangent case giving `intersects=True, inside_fraction=0.0` (spec-conformant; S4.T2's `or DIST_TO_CENTRE_M <= …` clause covers it); `iter_vertices` on Z coordinates (unreachable — nothing sets `returnZ`, all 15,299 fixture coordinates are 2-tuples); `_parts` accepting a Point (gated by `geojson_to_line`, which rejects it).

**What the whole-segment view added that no per-task review could:** the paging path was driven to 45,000 features over 23 pages for the first time (the suite only exercises 2); the envelope→circle seam was proven correct and simultaneously proven untestable offline; `MultiLineString` was confirmed to work end to end despite being absent from every fixture, so the synthetic tests must stay; and every real-data figure in the Decisions log was independently re-derived and matched exactly — 1262 of 1850 intersecting at r=2400, 1159 at `inside_fraction == 1.0`, 0 zero-length, 0 duplicate OBJECTIDs, longest WKT 920 chars.

**Reviewer housekeeping:** modified no file, committed nothing, pushed nothing; probe scripts lived outside the repo; `git status --short --untracked-files=all` empty; one live call, the existing 300 m smoke test.

**On PASS: proceed to Segment 3 (S3.T1).** I1 must be actioned before S4.T5.

## Decisions log

_Newest first. Every deviation from the plan, every confirmed fact that replaced a "Likely", every constant changed._

### 2026-09-23 — Automatic map: Opus re-review APPROVE; two false claims corrected, six Minor items carried

The re-review of `7ea545c`, `96b46c3` and `4730dd0` returned **APPROVE**, no Critical or Important findings. Its load-bearing reason: every run that exits 0 now leaves either a current artifact or a logged warning naming a stale one, checked across `--no-plot`, `--no-xlsx`, both together, a render failure, a render failure whose cleanup also fails, and a failed stale-file removal.

**Two of its Minor findings were false claims, corrected in this session:**
- **A test assertion labelled "Decisive, order-independent" could not fail.** It read the matplotlib logger's *effective* level after the `finally` had restored it, so it inherited the root logger's restored WARNING and passed with the fix removed. The test only worked through a private matplotlib cache reset plus a records check. **Now it reads the logger's own `.level` before the restore**; the test sets it to NOTSET first, so it can only be WARNING if `main()` set it. Proven: with the fix, the cache reset *and* the records check all removed, run as the whole file rather than in isolation, it fails with "main() must quieten matplotlib under -v". It no longer depends on a private attribute to mean anything.
- **The README overclaimed.** It stated every file in `--out` belongs to the run that just finished. That holds only for runs that exit 0. On exit 1: a workbook step that fails before writing leaves the *previous* workbook; one that fails part-way leaves a *partial* workbook from this run, readable but missing later sheets, because pandas' `ExcelWriter` saves on the way out even on an exception; and `NoRoadsFound` leaves the previous run's files untouched. **The claim is now scoped to successful runs, and all three cases are stated.** The partial-workbook case predates the automatic map.

**Also corrected:** the plan contradicted itself — §1 listed matplotlib as runtime while its S0.T1 pyproject block still left it out of `dependencies`. All three now agree with `pyproject.toml`.

**Carried, deliberately not fixed** — each is test coverage for behaviour that is already correct, and none can mislead a user today:
1. Plot-before-XLSX order is unpinned; swapping the two blocks passes all tests. The order matters: after a swap, an XLSX failure would leave new CSVs beside the *old* map.
2. The dashed-line capstyle is unpinned; forcing it round passes, though the code's own comment says that smears the two rare types' dash patterns into each other.
3. The success log line and the render-failure cleanup warning are both in the code and both untested.
4. Miscellaneous Road is outside the tested zorder chain, and `OTHER_STYLE`'s zorder is unpinned.
5. The render-failure warning says "stale/partial" without the "does NOT describe this run" wording `_remove_stale` uses for the same situation.
6. **Atomic workbook writes.** Writing `roads.xlsx` to a temporary file and renaming it into place — the pattern already used for the API cache — would eliminate the partial-workbook case. It is outside the scope of the user's request and touches `export.py`, reviewed and approved in Segment 4. Recommended as a follow-up.

### 2026-09-23 — matplotlib moved from a development to a runtime dependency (post-completion, user request)

**Why.** The user asked, verbatim: *"ensure the plot is also created automatically when extracted in the output if used like this for example: `uv run dbe extract --lat -31.945300 --lon 115.860065 --radius-km 10 --out output/perth_10km --no-xlsx -v`"*. The map had been a separate manual step, and matplotlib a development-only dependency listed in §1 as "QA plot only". Making `extract` produce the map means matplotlib must be present at runtime; "ensure" rules out leaving it optional. §1 requires a Decisions-log entry for any dependency change; this is it.

**What was changed alongside, and why each part.**
- **Lazy import.** `dbe/cli.py` imports neither matplotlib nor `dbe.plot` at load, so `dbe --help` and `to-xlsx` never pay for it. Verified by the reviewer: after all three `--help` invocations, `sys.modules` contains neither.
- **Best-effort, not a hard step.** The CSVs are the deliverable; the map is a reviewer aid, and the user's own example uses `--no-xlsx`, leaving the CSVs as the entire output. A drawing failure logs a warning and the run exits 0 with every CSV intact. **This is not the inert-feature anti-pattern the `--osm` flag embodied** — that flag *claimed* success while doing nothing. Here a failure is reported plainly and nothing claims a map was made. The reviewer confirmed the broad `except` does not mask a real regression: making `render_qa_plot` raise on every call fails three tests.
- **No stale artifacts.** A failed render removes any `qa_plot.png` left from an earlier run into the same directory (implementer's own catch). The Opus review of `02af7b8` then found `--no-plot` — and, by the same logic, `--no-xlsx` — left the previous run's map or workbook beside new CSVs, silently describing a different area. Closed in the follow-up fix. **The rule: any derived file present in `--out` belongs to the run that just finished.**
- **Rendering moved into the package** as `dbe/plot.py`, using `matplotlib.figure.Figure` rather than `pyplot` (no global backend state in library code) and one `LineCollection` per road type rather than one call per segment: **8.4 s → 1.6 s** on the 10 km data, measured by the reviewer. Old and new Curtin renders differ in 304 of 2.25 million pixels, all anti-aliasing where State Roads and Controlled Paths overlap.

**Two corrections to the orchestrator's own brief, both caught by the implementer:** a stale map surviving a failed render, and the claim that a `LineCollection` "maps exactly" onto the previous design — a blanket `capstyle="round"` would have rounded every dash cap and smeared the dotted pattern.

**A regression this change introduced, found by running the user's command:** under `-v`, **2,859 of 2,925 log lines (98%) were matplotlib scoring every installed font**, burying the 34 lines about the extraction. Before the change `-v` produced about 66 lines. Quietened in the follow-up fix. **Every test had passed** — no test ran `-v`, which is exactly how the user invokes it.

**Verified end to end** with the user's exact command against the live service: exit 0 in 90 s, 22,863 segments, 82,333 vertices, `qa_plot.png` written beside the CSVs and no workbook. 1,195 of 1,195 State Road rows carry a measured width.

### 2026-09-23 — The user's own words on width, anchored verbatim (Gate C, M-6)

Gate C found that a quote used to justify skipping Segment 5 existed in the repo only as the orchestrator's paraphrase. Both of the user's statements are recorded here exactly, because they point in different directions and the later one governs.

**The original brief** (`docs/task_docs/init_prompt.md`, verbatim):
> "the csv file that i have provided has all the road length, start point etc but it doesnt really specify the coordinate/shape of the roads. And this has data for all the roads in Western Australia. this data is from the roads that fall inside the 10km radius area with the center point being curtin school of design and built environment building (Centre point: -32.0018629, 115.8924599) but do not contain the exact start and end coordinates and the width of those roads which are required"

**The user's answer during planning**, to the question of how the script should fill width for local roads (verbatim, from the planning session on 2026-09-22):
> "extra info like road widths are not mandatory but good to have, but data on all roads including local roads are mandatory"

**How these were reconciled:** the brief lists width among things "required"; the planning answer, given in direct response to being told width exists only for state roads, relaxes it to best-effort while making coverage of all roads, local included, the hard requirement. The build followed the later, more specific answer: every road is output, and a missing width never drops a row. **The Segment 5 skip leaned on that answer, and a reader should weigh it knowing the brief said "required".**

The user's other three planning answers, also verbatim: output shape — "Segment rows + vertices table (Recommended)"; circle rule — "Intersects, keep whole geometry (Recommended)"; role of the provided CSV — "Validation only (Recommended)".

### 2026-09-23 — Segment 5 SKIPPED on a measurement (orchestrator session 4, Opus)

The plan marks Segment 5 optional and skippable "with reason". Rather than reason from the plan's global taginfo figure, the orchestrator measured the actual Curtin circle with one Overpass query:

| Tag | Ways carrying it | Share of 70,561 |
|---|---|---|
| `width` | **685** | 0.97% |
| `lanes` | 10,735 | 15.21% |
| `maxspeed` | 12,943 | 18.34% |
| `surface` | 36,593 | 51.86% |
| `name` | 23,497 | 33.30% |
| **both `width` and `name`** (what the matcher needs) | **371** | 0.53% |

**Yield:** 20,441 rows currently lack a width. A perfect match of all 371 candidates would close under 2% of that gap, and the true figure would be far lower — OSM's `highway` population (70,561 ways) includes footpaths, cycleways and service roads that have no Main Roads counterpart, against 21,643 MRWA segments, so the two populations do not align; name-plus-proximity matching is lossy on top.

**The deciding factor was the licence, not the yield.** OpenStreetMap is ODbL, whose share-alike terms attach to any derived database. Encumbering the user's output for a sub-2% improvement on an attribute they explicitly called "not mandatory but good to have" is a bad trade. Main Roads alone is CC BY 4.0, materially less restrictive.

> **Addendum, Fable review 2026-09-24.** The bolded sentence above was withdrawn at Gate C (see the Gate C entry): the skip holds on yield alone, the licence is a second reason, and the user was never asked — the choice is theirs. The text is left as written so the record shows what was claimed at the time.

**Consequence:** Gate B finding I4 is now mandatory rather than advisory. `--osm` cannot remain advertised and inert while reporting `osm_enabled: true` — a user seeing 5.55% width coverage would reasonably try it and conclude OSM had nothing to add. S6.T1 must make the help text state it is not implemented and the flag fail loudly.

**Reversible:** the segment stays in the plan with its full task text. Re-run the probe and revisit if OSM width coverage improves.

### 2026-09-23 — Segment 4 deviations (orchestrator session 4, Opus)

Five deviations, each recorded here per §0.5.

**1. The plan's Segment 4 code blocks were reformatted to the repo's lint width (`d0f5ec0`).** 33 lines exceeded `line-length = 110`, which would have forced five implementers into hand-wraps, each costing a reviewer a behaviour-equivalence check — three segments of review time had already gone to exactly that. Every block was formatted with `ruff format` and verified **AST-identical** before and after; four long string literals ruff cannot split were wrapped by hand. **The claim "pre-formatted and lint-clean" was initially overstated:** `ruff format` does not sort imports, so an import I had myself inserted for an unrelated fix broke the isort rule and the S4.T2 implementer hit `I001`. It stopped and reported rather than reformatting. All ten blocks were then run through `ruff check` with the repo's full select list; that was the only violation (`13c3cb6`).

**2. Gate A amendment I4 was insufficient and was replaced (`e7c3274`).** The enumerated guard `(feat.get("geometry") or {}).get("coordinates")` closed two of six malformed geometry shapes. Four still aborted the whole run: a one-coordinate line and a one-coordinate multi-part (both `GEOSException`), an empty multi-part part (`IndexError`), and a wrong geometry type (`ValueError`). Enumerating shapes is the wrong strategy for untrusted data from an external service, so `extract()` now wraps the conversion in a broad `except`, logs the exception type and counts a new `skipped_bad_geometry` metadata key. **Also in that commit:** `seen.add(oid)` moved below the geometry guards, because a malformed copy arriving first would otherwise consume the OBJECTID and cause the real feature to be dropped as a duplicate — measured at 1,261 rows instead of 1,262, with the counters still summing so metadata showed nothing.

**3. The enrichment layers are now de-duplicated (`4d2ebf5`).** Layer 17 had always been de-duplicated; layers 12/16/8 were passed raw into `EnrichIndex.from_features`. The live run proved this matters: paging a live spatial query returned **622 duplicate spans** across those three layers, double-weighting 10 widths by 0.07–0.58 m. Both values were overlap-weighted means of genuinely matched spans, so nothing was invented either way, but a duplicated span counted twice is simply wrong and the asymmetry with layer 17 was indefensible. New metadata key `enrich_duplicates_dropped`.

**4. A reconciliation assertion was relaxed (`4d2ebf5`).** `test_every_extracted_row_is_metropolitan` failed on the live output because **2 rows of 21,643** — both `P020`, "Graham Farmer Fwy PSP", a Main Roads Controlled Path — carry an empty `RA_NAME`, `RA_NO`, `LG_NO` and `LG_NAME` in the live layer. That is a gap in the source data, not a leak from another region. The test now asserts that no *foreign* region appears, which is the assertion's real intent; blank is not the same as wrong. **This is a weakening made after seeing the data, and it is named as such.**

**5. §3.8's layer-12 range was widened from 200–3,000 to 200–6,000 (`bf583d0`).** The observed value was 4,307. The original band was extrapolated linearly by area from the 2.5 km fixture box, which sits in a low-state-road pocket near Curtin; the freeways only enter between 2.5 km and 10 km and pavement records are finer-grained near interchanges. The row that actually tests join health — width coverage against the State Road count — hit a perfect 1.000. **The widening happened after the run, so that row is no longer independent evidence**, and the Gate B reviewer said so.

**Confirmed facts that replaced a "Likely":** plan §2 recorded layer 12 as State-Road-only on the strength of a single agent check. The Gate B reviewer read all **4,307 layer-12 features in the 10 km envelope from the cached responses: 100% State Road, 0 Local.** No local road in this circle could have had a measured width. That is now Certain for this radius.

### 2026-09-23 — S3.T2 approved; two review findings, both gaps in the plan's tests (orchestrator session 4, Opus)

**S3.T2 — APPROVE.** The reviewer diffed the committed files against the plan's Step 1 and Step 3 blocks at **token level**: 481 vs 482 tokens in `enrich.py` and 912 vs 913 in the test file, the sole deltas being the two disclosed collateral trailing commas. All 7 ruff wraps map 1:1 to the only 7 plan lines exceeding 110 characters. Nothing undisclosed. All 12 public names match the Interfaces block.

**Important — 5 of the 12 `ENRICH_COLUMNS` have their key asserted but never their value.** `TRAFFICABLE_SURF_WIDTH_M`, `SEALED_SHOULDER_L_M`, `SEALED_SHOULDER_R_M`, `KERB_L` and `KERB_R` are never value-checked anywhere in the suite. Because `enrich_segment` seeds its output with `dict.fromkeys(ENRICH_COLUMNS)`, the key-order assertion passes no matter what is written to those columns — **or whether anything is written at all**. Four mutants survive the whole suite as a result:

| Mutant | Effect on the deliverable | Detected? |
|---|---|---|
| Drop `SEALED_SHOULDER_R` from the mean loop | every right sealed-shoulder value vanishes, all 1850 rows | **no** |
| Swap the `SEALED_SHOULDER_L`/`_R` output mappings | every shoulder reported on the wrong side | **no** |
| Swap `KERB_L`/`KERB_R` | every kerb reported on the wrong side | **no** |
| Source `TRAFFICABLE_SURF_WIDTH_M` from the wrong field | wrong surface width throughout | **no** |

The synthetic fixture already carries the data to catch all four (`SEALED_SHOULDER_L` 0.5/0.0 → 0.25, `_R` 1.0/0.0 → 0.5, `TRAFFICABLE_SURF_WIDTH` 9.0/7.0 → 8.0, `KERB_L="Y"`, `KERB_R="N"`), so the remedy is five assertion lines and no fixture change. Routed to **S3.T2.fix1**; the commit itself is correct and was approved.

**Also untested: the "road absent from every index" branch.** `test_unparseable_slk_yields_all_blank_but_correct_keys` only covers `target is None`. A parseable road that simply matches nothing takes a different path, and returns correctly, but nothing pins it. Folded into the same fix.

**Mutation score 11/13 = 85%**, with one mutant correctly excluded as provably equivalent (duplicating every span scales `weighted_mean`'s numerator and denominator identically, and the strict `>` keeps the first of the tied duplicates). Both genuine survivors share the root cause above. The reviewer also disclosed and corrected a false-negative sweep caused by stale bytecode — worth knowing: mutation runs need `PYTHONDONTWRITEBYTECODE=1` and a cleared `__pycache__`, or same-byte-size mutants report as survivors incorrectly.

**The provenance contract is inviolable — verified both directions.** Across all 1850 fixture rows plus 5 degenerate synthetic cases, `WIDTH_M is None` if and only if `WIDTH_SOURCE == "none"`, with 0 violations.

**Minor — a ROAD-code collision could leak a width, but cannot in practice.** `enrich_segment` has no `NETWORK_TYPE` check, so synthetically a Local Road carrying `ROAD="H001"` picks up a state-road width. The reviewer checked the provided statewide CSV **read-only, for validation only** (§1 forbids reading it at runtime; no code path does): across all 189,865 rows and 70,010 distinct ROAD codes, **0 carry more than one `NETWORK_TYPE`**. A road code determines network type uniquely statewide, so the leak is unreachable with real data. That is an empirical invariant in one snapshot, not a schema guarantee.

**Minor — an infinitesimal overlap yields a full-strength width.** A 1 µm overlap between a segment and a pavement span produces a full-confidence width, because `weighted_mean` normalises and the weight cancels when it is the only match. Exact touching correctly yields no match. §3.3 specifies no minimum-overlap rule, so this is the plan's semantics rather than a defect — but it is now on the record.

**Zero is preserved as a measurement:** a zero seal width yields `WIDTH_M = 0.0` with `WIDTH_SOURCE = "mrwa_pavement"`, not a blank. No layer-12 fixture row currently has one, so the "unsealed state road reports 0.0" case is hypothetical, but the semantics are deliberate.

---

### 2026-09-23 — S3.T1 fix review: a guard that no test pins is a guard that gets deleted (orchestrator session 4, Opus)

The review of `6f58aa4` + `a3829f3` returned **REQUEST CHANGES** on a test-only gap. `dbe/slk_join.py` is correct and unchanged.

**Important — mutation M3: deleting the `math.isfinite` guard inside `weighted_mean` leaves all 49 tests passing.** The guard now *looks* redundant, because `_present` rejects non-finite floats one call earlier. It is not: `weighted_mean` calls `float(value)` on any type, so the **string** `"nan"` passes `_present` as an ordinary non-empty string and only the inner guard stops it. The consequence is worse than first stated — it is not one bad term but **whole-segment poisoning**: `weighted_mean` returns `nan` for the entire target even when other spans carry good measurements, putting a wrong width in the output. Unpinned, a future simplification pass deletes it and the suite stays green. Fixed in **S3.T1.fix3**.

**Minor — a test did not demonstrate its own claim.** `test_non_finite_source_span_cannot_hijack_the_join` built its index from the *good* spans only, so the corrupt span never entered it; the only assertion doing work was `assert corrupt is None`. The hijack figures in its docstring were true but undemonstrated. Also fixed in fix3.

**Useful specifics the review established.** The hijack is asymmetric and needs only **one** NaN: `overlap_len(0, 10, nan, 5.0)` returns 10 (full-target), while `overlap_len(0, 10, 5.0, nan)` returns 0.0 and a NaN *target* silently no-matches. `overlap_len(0, 10, inf, -inf)` also returns 10. A path the original report missed: `json.loads('1e400')` yields `inf` with **no error**, and the guard closes that too. The invariant "no non-finite SLK inside an `SlkSpan`" is enforced **at the factory by convention**, not structurally — only two construction sites exist, one guarded and one the test helper. `_present`'s `isinstance(value, float)` misses `np.float32`, `Decimal("NaN")` and `complex`, all unreachable here because `attrs` comes from stdlib `json`.

**The guards are provably inert on real data:** re-running the join with the pre-fix module over 8 enrichment fields × 1850 segments produced **0 differing rows**.

**Downstream consequence recorded in the plan (`8bb856d`):** pandas' default NA handling coerces the literal text `nan`, `NA`, `null`, `None` and `N/A` to missing values. The S4.T3 reader already passed `keep_default_na=False, na_values=[""]` but did not say why, and the QA plot script omitted it entirely. Both now carry it with the reason, so a road genuinely labelled with one of those strings cannot silently blank out in the XLSX while reading correctly in the CSV.

### 2026-09-23 — S3.T1 review: a NaN could silently rewrite a road's width (orchestrator session 4, Opus)

The Opus review of `613d632` returned **APPROVE** with one Critical and three Important findings. Same pattern as S2.T2, now for the fourth time in this build: the reviewer diffed `dbe/slk_join.py` against the plan's Step 3 block and found it **byte-identical, `diff` exit 0** — so every defect is in the specification, not the implementation. The test file had exactly one disclosed ruff wrap (a 120-char assert).

**C1 (Critical) — a non-finite SLK hijacks the join. FIXED in `6f58aa4`; plan amended in `f2e4110`.**
Python's `max`/`min` fall through on NaN, so `overlap_len(0, 10, nan, nan)` returns **10.0 — the full target length**, the largest weight any span can score. One corrupt source record therefore outranks every genuine one. Orchestrator-verified end to end:

| | width | lanes |
|---|---|---|
| truth | 10.44 m | 4 |
| with one NaN span present | **6.72 m** | **1** |

No exception, no warning — a plausible-looking wrong width, which §1 names as this project's worst failure mode. **The path is open**, not theoretical: `float(nan)` succeeds, `float("NaN")` parses the *string* form, and stdlib `json` accepts bare `NaN`/`Infinity` literals by default — used by both `resp.json()` and the cache read. The asymmetry matters: NaN in the *source* hijacks; NaN in the *target* silently no-matches. **0 occurrences in all four fixtures**, so latent rather than live. Fixed anyway: the guard is two lines and the alternative is silent corruption of the deliverable. `span_from_properties` now rejects non-finite SLK, and `weighted_mean` skips non-finite values.

**Follow-on gap, caught by the fix1 implementer and confirmed: `dominant_value` was left unguarded** — the same defect class one function over. It returned `nan` unchanged while `weighted_mean` returned `None`. Since `dominant_value` supplies `NO_OF_LANES`, `KERB_L/R`, `ROAD_HIERARCHY` and `SPEED_LIMIT`, that is a bogus lane count reaching the CSV. Closed in fix2 by moving the guard into `_present`, which both consumers share. The in-loop guard in `weighted_mean` stays: it is not redundant, because `weighted_mean` calls `float()` on strings, so the *string* `"nan"` passes `_present` and only the inner guard stops it.

**I3 — the zero-preservation invariant was completely untested.** Mutating `_present` to `bool(value)` survived the entire suite. The code was already correct (orchestrator-verified: `0`, `0.0` and `False` all survive; `""` and `None` do not), but nothing protected it, and real zeros exist — `UNSEALED_SHOULDER_L/R` are `0` in all 113 layer-12 records. A zero sealed shoulder is a measurement, not a missing value. Now pinned.

**I1 — the divided-road averaging question is DEFERRED, not resolved.** When the target carriageway is `Single` but the only sources are `Left` and `Right`, `exact or out` returns both and `weighted_mean` averages them, reporting a 16 m divided road as 8 m. It never occurs in the fixtures — in fact the `cwy_compatible` wildcard **never fires at all** there, since every real match is exact-CWY (layer 12: 38 Single/Single, 14 Left/Left, 13 Right/Right). That silence is not evidence: the fixtures cover 2.5 km and production covers 10 km. Recorded in the plan at S3.T1 as a decision that must be made before S4.T5 — sum, maximum, or blank — rather than guessed now.

**I2 — the tie-break is deterministic but on input order, not contract.** Confirmed stable across `PYTHONHASHSEED` values. A real tie exists in the fixtures (`H001 Left 4.79–4.9`, two layer-12 spans at overlap 0.04), but all three dominant fields agree on both spans, so **0 output columns are currently order-dependent**. Latent: for real data the winner is decided by ArcGIS result ordering, which is not a stable contract.

**Also confirmed by the review:** all 1850 layer-17 features parse, 0 rejected — 65 State, 1763 Local, 22 Miscellaneous. The 22 Miscellaneous (Curtin campus links, carparks, laneways) have **zero ROAD-code collisions** with State or Local roads, so none can pick up a bogus width; they return blank width, hierarchy and speed. `slk_join.py` never writes through `attrs`, so the by-reference storage is safe today, though S4's `EnrichIndex.from_features` receives raw fixture lists and any future in-place normaliser would corrupt them — the S2.T2 lesson again.

### 2026-09-23 — Pre-dispatch probe of S3.T2 found three defects in the plan's own tests (orchestrator session 4, Opus)

Gate A's lesson was that the plan's code blocks are where the defects live, so before dispatching Segment 3 the orchestrator measured the actual join behaviour against the committed fixtures rather than trusting the thresholds it had written. Three defects surfaced. Corrected in `4d82c81` and `d9cd021`, **before** any implementer saw the task.

**Measured join coverage (2.5 km fixtures, 2026-09-23):**

| Join | Measured | The plan asserted |
|---|---|---|
| State road → `TOTAL_SEAL_WIDTH` (layer 12) | **65 / 65 = 1.000** | `>= 0.8` |
| Local road → `TOTAL_SEAL_WIDTH` (layer 12) | **0 / 1763 = 0.000** | *not tested at all* |
| State road → `ROAD_HIERARCHY` (layer 16) | 65 / 65 = 1.000 | not tested |
| Local road → `ROAD_HIERARCHY` (layer 16) | **1763 / 1763 = 1.000** | `>= 0.8` |
| Local road → `SPEED_LIMIT` (layer 8) | 1683 / 1763 = 0.955 | not tested |

**Defect 1 — the `>= 0.8` thresholds were placeholders, not measurements.** The real rates are 1.000. A threshold of 0.8 would have passed while **a fifth of the width data silently went missing** — precisely the failure mode that is hardest to notice, because the suite stays green. Replaced with exact structural assertions (`len(state) == 65`, all widths present, all in 3–40 m).

**Defect 2 — nothing asserted that local roads never receive a width.** This is the project's *central* constraint (§1: "Width is never estimated or invented"; the user's own decision was that width is best-effort but must never be invented), and it had no test. Now guarded directly: `all(e["WIDTH_M"] is None ...)` and `{e["WIDTH_SOURCE"] for e in local} == {"none"}` over all 1763 local roads, plus `== {"mrwa_pavement"}` over all 65 state roads.

**Defect 3 — the synthetic speed data used integers; the real field is a string with units embedded.** The plan's fixture had `SPEED_LIMIT=70` and asserted `== 70`. Confirmed real values in the layer-8 fixture: `30km/h`, `40km/h`, `60km/h`, `70km/h`, and the free-text `50km/h applies in built up areas or 110km/h outside built up areas`. The test would have passed against data shaped nothing like production. Synthetic data now uses `"70km/h"` / `"50km/h"` and the test asserts every emitted value is a string containing `km/h`. **`SPEED_LIMIT` must never be cast to a number** — the twelfth value is unparseable by design.

**Also corrected:** `assert out["NO_OF_LANES"] in (2, 3)` ("either is acceptable") was vacuous — with `dominant_value`'s strict `>`, equal overlaps deterministically give the first span, so it is pinned to `== 3` with the tie-break documented. The exact fixture counts now carry a docstring warning that regenerating the fixtures requires re-measuring them rather than deleting the assertions. The speed-coverage figure is deliberately a band (`> 1600`) rather than an equality, because unlike the structural counts it can drift on a service refresh without anything being wrong. `ROAD_HIERARCHY`'s real value set is recorded on the S3.T2 interfaces: `Access Road`, `Distributor A`, `Distributor B`, `Local Distributor`, `Primary Distributor`.

### 2026-09-23 — S2.T2 review: three defects found in the PLAN's code, not the implementation (orchestrator session 4, Opus)

The Opus review of `50acb36` returned **APPROVE** while raising three Important findings. That combination is correct and deliberate: the reviewer diffed the committed files against the plan's own Step-1/2/3 code blocks and found `tests/conftest.py` and `tests/test_live_smoke.py` **byte-identical**, with `tests/test_fixtures_shape.py` differing only in a ruff reflow of `EXPECTED_17` that it proved element-for-element equivalent (25 items, order-sensitive equality). **The implementer transcribed the contract exactly; the defects are in the contract.** Requesting changes would have meant asking it to deviate from the spec it was told not to deviate from. All three were re-verified empirically by the orchestrator before any action was taken.

**I1 — `FixtureSource.calls` leaked across tests. FIXED in code (`132c90a`).** `fixture_source` is `scope="session"` and `.calls` was never reset. Orchestrator probe: test A made 2 calls, test B made **1** call yet observed `len(calls) == 3` with `calls[0] == (17, (1.0, 2.0, 3.0, 4.0))` — test A's first call. The danger was not a broken assertion but a **vacuous** one: plan S4.T2 asserts `fixture_source.calls[0][0] == 17`, and because `extract()` always queries layer 17 first, that passes under every ordering **even if the test's own code never called the source at all**. Any natural strengthening (`len(calls) == 4`, or matching `calls[0][1]` to this test's envelope) would pass in isolation and fail in a full run — an order-dependent flake planted for Segment 4. Fix keeps session scope (it avoids re-reading 2.9 MB per test) and adds an autouse function-scoped `_reset_fixture_source_calls` that clears the log only for tests that actually request the fixture.

**I2 — `query_envelope` shares feature dicts. NOT a code change; recorded as a global constraint (`1945c76`).** `list(self.layers.get(layer_id, []))` copies the list but not the dicts inside, and `.layers` is handed out raw. Orchestrator probe: after `feats[0]["properties"]["ROAD"] = "CORRUPTED"`, a second `query_envelope` returned `"CORRUPTED"` and the recorded fixture stayed corrupted for the session. Latent rather than live — `normalise_properties` already does `dict(props)` and the plan's S4.T2 test deep-copies before mutating — but plan line ~1613 passes `.layers` raw into `EnrichIndex.from_features`, so a future in-place normaliser would poison every later test. Deep-copying inside `query_envelope` would itself deviate from the contracted "returns the recorded list", so the fix is a **§1 Global Constraint**: never mutate fixture features in place; copy first.

**I3 — the fixture-shape tests were single-sample and could pass vacuously. FIXED in code (`132c90a`).** Three of four inspected only `feats[0]`, so a ragged schema mid-file sailed through; the reviewer demonstrated survivors at layer-17 index 50, layer-12 index 5 and layer-16 index 5. Worse, `test_layer17_fixture_geometries_are_lines` built `kinds` from a comprehension that filters out null geometries, and **`set() <= {"LineString", "MultiLineString"}` is `True`** — so it passed on a fixture whose features were *all* null-geometry, and on an empty fixture. Orchestrator confirmed the `set()` vacuity directly. All four tests now iterate every feature and report the offending index; the geometry test additionally asserts `len(feats) > 100`, `assert kinds`, and an explicit empty null-geometry list.

**Plan amended in `1945c76`** so a future re-run cannot reintroduce any of this: the S2.T2 conftest block now carries the autouse reset (with a comment explaining why), the four test bodies are the hardened versions, and §1 carries the no-in-place-mutation constraint.

**Scope note carried forward to S4.T2 (from the fix implementer, worth keeping):** `_reset_fixture_source_calls` is function-scoped autouse, so it runs before the test body and before function-scoped fixtures, but **after** session- and module-scoped ones. S4.T2's `calls[0][0] == 17` will therefore only observe what it expects if the `query_envelope` calls originate in the test body or a function-scoped fixture. A module-scoped fixture making calls would have them wiped before the test reads them. Harmless today (only `fixture_source` is session-scoped and it records nothing itself).

### 2026-09-22 — S2.T1 MRWA client: three sanctioned additive tests, one Important finding closed (orchestrator session 3, Opus)

**Production code is character-for-character the plan's §4 S2.T1 Step 3 block apart from five ruff wraps.** The Opus reviewer extracted the plan's code block by line range and diffed it against the committed file: the only hunks are the wraps. `dbe/mrwa_client.py` blob `10ea2723…` is identical at `7edb78e`, `44e5d24` and `HEAD` — the fix commit did not touch production code.

| Wrapped for `line-length = 110` | Before → after | Proof of equivalence |
|---|---|---|
| `BASE_URL` | 114 → 107 | single **parenthesised literal**, NOT concatenation; plan literal vs committed literal compared by `repr` → byte-identical |
| `def query_envelope(...)` signature | 111 → 70 | pure line split, no token change |
| `exceeded = bool(...)` | 121 → 108 | same two operands, same `or`, same short-circuit order |
| `log.info(...)` | 129 → 73 | 5 args, order and values unchanged |
| `log.warning(...)` | 124 → 56 | 6 args, order and values unchanged |
| `_feat` return dict (**test file**) | 118 → 63 | both versions `exec`'d and compared: `plan_dict == commit_dict` → `True` for oid 0, 7, 2000 |

The sixth wrap (`_feat`) was **not** in the orchestrator's known-items list and was self-disclosed by the implementer — the plan's own test helper is 118 characters. Also removed: `import json` from the test file, which the plan's Step 1 listing declares but never uses (ruff **F401**). Added: `import dbe.mrwa_client` at module level, required for the `MAX_PAGES` monkeypatch.

**Three tests were added on orchestrator instruction, beyond the plan's 8 — the plan's "8 passed" is superseded, not drifted.** Gate A item 5 names five clauses the client must satisfy; the plan's own 8 tests pinned only three of them. Added: `test_exceeded_flag_under_properties_continues_paging`, `test_empty_page_terminates_even_with_exceeded_flag_set`, `test_max_pages_guard_raises_mrwa_error`. **The obvious version of the first is vacuous** and was headed off in the prompt: with a *full* page, `len(page_feats) < self.page_size` is already `False` and `and` short-circuits, so the nested flag is never read — the test must use a **short** page carrying `properties.exceededTransferLimit`. File-scoped count went 8 → 11 → **12** after the fix; full suite **26**.

**An Important review finding was raised and CLOSED inside this task — commit `44e5d24`, test-only.** Mutating `dbe/mrwa_client.py:111` from `offset += len(page_feats)` to `offset += self.page_size` **survived all 11 tests**. Against a real ArcGIS that honours `resultOffset` and truncates pages (10 records, `page_size=5`, server capping at 3/page) the mutant fetches offsets `[0, 5, 10]` and returns **6 of 10 features, silently missing OBJECTIDs 3, 4, 8, 9** — a direct violation of §1's "every layer-17 segment that intersects the circle", with no error raised. It is not broken on today's default path only because `PAGE_SIZE = 2000` equals the confirmed `maxRecordCount = 2000`, so pages are never short; but `page_size` is a **constructor parameter** and S4.T2's `extract()` constructs the client, so a single "fewer round-trips" tweak to `page_size > 2000` would make every page short-with-exceeded and the unpinned arithmetic the sole code path. Closed by one assertion (`session.calls[1][1]["resultOffset"] == 3`) plus two Minor coverage fixes in the same commit: `FakeSession` now records the HTTP verb in a parallel `self.methods` list (the `(url, payload)` shape of `self.calls` is deliberately unchanged, so no existing assertion moved), and a new `test_paged_query_caches_each_page_separately` exercises paging *with* `cache_dir` set. **Purely additive — no existing assertion was deleted or weakened** (reviewer confirmed by reading the full diff, not the line counts).

**Mutation score over `dbe/mrwa_client.py`: 6 of 10 killed before the fix, 16 of 19 after** (independently reproduced by the Opus reviewer in an isolated scratch copy, after validating the harness with a deliberate fatal mutant). All five Gate A item 5 clauses are now pinned by tests; before `44e5d24` the POST/GET clause and the cache-key clause were not.

**Three surviving mutants, all judged non-blocking:**
1. **`offset = len(page_feats)` (assignment instead of `+=`) survives** — with `offset` starting at 0 and only two pages scripted, `=` and `+=` both yield 3. On three pages it fetches offsets `[0, 3, 3, 3, …]` and re-fetches page 2 forever. **Minor, not a re-opened Important, because it fails loudly on both paths**: uncached it makes 10,000 HTTP calls then raises `MRWAError: exceeded 10000 pages`; cached it makes 2 HTTP calls then spins 9,998 times on cache hits (0.46 s) before the same error. It never yields a short, wrong result set. **Carry-forward, one line, strictly stronger than what is committed:** extend `test_exceeded_flag_under_properties_continues_paging` to three scripted pages and replace the single assertion with `assert [c[1]["resultOffset"] for c in session.calls] == [0, 3, 6]`, which kills this and the whole `±1`/no-advance class together. **Fold into S2.T2 or Gate A.**
2. **Dropping *method* (but not params) from the cache key survives** — an equivalent mutant in practice: the client's only two call shapes are GET `/{id}` with `{"f": "pjson"}` and POST `/{id}/query` with a 12-key dict, so URL and params already differ and no genuine collision exists. Gate A item 5's "key includes method" is still satisfied by the committed code.
3. **`sha1(...)[:20]` → `[:4]` survives** — no "correct" truncation length is pinnable; 80 bits is ample. The reviewer tried and **could not construct two genuinely different requests that collide** under `str(v)` coercion: `4326` and `"4326"` do hash alike, but every param is built internally with a fixed type, so it is unreachable from the declared API.

**Four Minor defects accepted as plan-verbatim and carried forward — none fixed, all named so a later segment can act:**
- `mrwa_client.py:99` — `data.get("properties", {}).get(...)` raises a raw **`AttributeError`** when `properties` is present but `None` or a list. Not an `MRWAError`; escapes both `except` clauses. Only reachable when the top-level flag is falsy. Fails loudly, not silently.
- `mrwa_client.py:146-157` — **the final failed attempt still sleeps before giving up.** Back-off is `[1, 2, 4, 8, 16]` = 31 s with defaults, matching §3.6, but the trailing 16 s is spent after the last attempt: ~64 s of pure waste across four layers on a fully-failed run. Invisible in tests (`sleep_s=0`).
- `mrwa_client.py:132-134` / `:144` — **a hard 4xx is retried.** `raise_for_status()` raises `requests.HTTPError`, caught by the `RequestException` clause, retried 5× and finally reported as `MRWATransientError`. Verified: a 404 produces 5 HTTP calls. Contradicts `MRWAError`'s own docstring ("Non-retryable error (bad request…)").
- `mrwa_client.py:140` vs `:124` — **the cache write is non-atomic `write_text` and the hit-path `json.loads` sits outside the retry `try`.** A file truncated by a crash or a full disk raises `JSONDecodeError` on every subsequent run with **no self-heal**. Fix when touched: tmp file + `os.replace`, or wrap the read. This one has the worst failure mode of the four and is worth doing before the 10 km production run in S4.T5.
- Also unpinned by any test (noted, no action): `headers=self._headers`, the `USER_AGENT` value and `timeout=self.timeout_s` — the plan's own `FakeSession` accepts and discards those kwargs.

**Live sanity call against the real service (orchestrator, not a subagent), using the committed client:** `MRWAClient(sleep_s=0).query_envelope(17, LocalProjection(-32.0018629, 115.8924599).envelope_wgs84(300.0))` → **8 features in 0.90 s**, all `LineString`, **every coordinate a 2-tuple** (confirms the no-`returnZ` instruction held and S1.T2 forward-risk #3 cannot fire), and the properties carry **`GEOLOC.STLength()`** — the live name, matching `LENGTH_FIELD_ALIASES[0]`, so `normalise_properties` targets the right field. Envelope `(115.8892850022238, -32.00456836018353, 115.8956347977762, -31.99915743866129)`. `cache_dir` was left unset so nothing wrote into the repo tree.

**Nothing in the plan turned out to be wrong about the live API in this task.** The only inaccuracies were in the plan's own snippets: six over-length lines and one unused import, all of which §1's ruff allowance already covers.

### 2026-09-22 — S1.T2 segment metrics: first contact with real data (orchestrator session 2, Opus)

**Deviations from the plan's literal text, all proven behaviour-identical.** The implementation body (`@dataclass SegmentMetrics` onward in `dbe/geometry.py`) is **character-for-character identical** to the plan's §4 S1.T2 Step 3 block, verified programmatically. The test additions are character-for-character identical to Step 1 with exactly two differences: (a) `strict=False` → **`strict=True`** in `test_roundtrip_wgs84`, ordered by the orchestrator after the S1.T1 review (it removes a vacuous-pass hole; the transform preserves vertex count, so `strict=True` is satisfiable); (b) `tests/test_geometry.py:63` — the plan's MultiLineString coordinate literal is **114 characters**, over `line-length = 110`, so it was hoisted into an `ml_coords` local. The reviewer evaluated both dicts: `plan_dict == commit_dict` → `True`.

**An Important review finding was raised and CLOSED inside this task — commit `40cf0b6`.** `test_start_end_and_wkt_use_lon_lat_order` asserted only `m.wkt.startswith("LINESTRING (115.89 -32")`, and `115.89` renders identically at precision 2, 7 and 12 because trailing zeros are trimmed — so **nothing pinned `rounding_precision=7`**. Mutating `dbe/geometry.py` to `rounding_precision=2` survived all 12 tests at a measured cost of **716.8 m maximum coordinate error** on real fixture data. Since WKT geometry is the project's primary deliverable, this was closed rather than carried forward. `40cf0b6` adds `test_wkt_rounds_coordinates_to_seven_decimal_places`, which feeds an 11-decimal input (`115.89245991234`) so precision 7 genuinely rounds it, and asserts the exact rendered string. **Orchestrator-verified by independent mutation:** precision 2 → fail, 6 → fail, 8 → fail, 12 → fail, 7 → `14 passed`. The production `dbe/geometry.py` was NOT modified (`git diff` clean); only the test changed.

**Protocol note on `40cf0b6`.** It was committed on the strength of the orchestrator's own mutation check before an Opus reviewer had seen it — a gap against §0.3 step 4, which closes the loop with the reviewer, not with the orchestrator. **Closed retrospectively:** a dedicated Opus review of `40cf0b6` returned **APPROVE, no Critical/Important**, independently reproducing the mutation matrix (precision 2/6/8/12 all fail, 7 passes) and confirming production code byte-identical (`dbe/geometry.py` blob hash `16384f2c…` unchanged across `7764393`, `40cf0b6` and `HEAD`), 12 insertions / **0 deletions** so nothing could have been altered or removed, and no trailer. It added two facts the first check did not: **omitting the argument entirely** renders at shapely's default of 6 and also fails the test, and the asserted string is a **unique fingerprint for precision 7** (every neighbouring precision 5–12 yields a distinct string), not merely a "not 2 and not 12" sieve. **One Minor left open, documentation-only:** the comment at `tests/test_geometry.py:113-117` justifies the input by naming only precisions 2 and 12, which could invite a future reader to trim the input to something that only survives that contrast and silently weaken the pin. Suggested wording when the file is next touched: "…differs at every other precision (verified 2, 6, 8, 12 and the default 6)." Not worth its own commit now.

**Why the suite is 14, not the plan's 12.** Plan S1.T2 Step 4 expects `12 passed` file-scoped. `tests/test_geometry.py` now holds **13** tests (5 from S1.T1 + 7 from S1.T2 + 1 from the `40cf0b6` fix) and the full suite is **14** with `tests/test_smoke_import.py`. This is the fix commit, not drift — no planned test was dropped.

**First contact with real data — `segment_metrics` over all 1850 layer-17 fixture features** (`LocalProjection(-32.0018629, 115.8924599)`, `circle(2400)`). Every §3.8 sanity range that is checkable at this scale passes:
| Quantity | Measured |
|---|---|
| `intersects=True` | 1262 of 1850 (588 outside — expected; the fixture envelope is a ±2500 m **box**, whose corners reach ~3536 m) |
| `inside_fraction` range | **0.0 – 1.0; zero values outside [0,1]** (§3.8's red flag does not fire) |
| `inside_fraction == 1.0` | 1159 of 1262 — matches §3.8's "most = 1.0" |
| `length_m` range | 9.675 m – 898.655 m; **zero features with `length_m == 0`** (none even below 1.0 m) |
| `dist_to_centre_m` range | 61.29 m – 3465.31 m |
| Total vertices | 5909 (`iter_vertices` row count == summed `vertex_count`, 0 mismatches); 2–40 per feature |
| Longest `GEOMETRY_WKT` | **920 chars** (median 61, p99 360) — **35.6× headroom** under §3.6's 32,767 Excel limit |
| WKT round-trip through `from_wkt` | max coordinate error **5.0e-8° = 7.22 mm**; zero features emit scientific notation |

**Forward risks — recorded, NOT blocking (orchestrator scope ended at S1.T2):**
1. **`inside_fraction` UNDER-reports on self-overlapping geometry.** GEOS nodes and dissolves the overlay, so a fully-inside line that doubles back on itself reports **0.500**, and a MultiLineString with three identical parts reports **0.333**. The error direction is always *under*, never over, so **§3.8's "any value outside [0, 1]" red flag can never detect it.** Zero occurrences in layer 17 at 2.5 km (0 of 1850 features are non-simple, 0 have duplicate consecutive vertices), but a 10 km pull could contain some. If it matters later, the check is `local.is_simple`, or compare `unary_union` lengths.
2. **A tangent segment yields `intersects=True, inside_fraction=0.0`** with a non-zero `length_m` (reproduced synthetically; 0 occurrences in the fixtures). §3.4's "keep if intersects" would emit such a row. **Downstream consumers must not assume `intersects ⇒ inside_fraction > 0`.**
3. **`iter_vertices` raises `ValueError: too many values to unpack` on any Z coordinate** — `for seq, (x, y) in enumerate(part.coords)`. All 3202 features across all four fixtures are strictly 2D (arity histogram `{2: 15299}`), and layer-17 metadata has **`hasZ` absent (= false)**, `hasM: True`. `hasM` is irrelevant because `f=geojson` carries no M channel and ArcGIS `returnZ` defaults to false. **Action for S2.T1: do not set `returnZ=true`.** Nothing in the plan suggests it should.
4. **`_parts` returns `[geom]` for anything that is not a MultiLineString**, so `segment_metrics` called on un-gated geometry misbehaves: a **Point passes silently** (`length_m=0.0, vertex_count=1, intersects=True`), a Polygon raises `NotImplementedError`. Acceptable while `geojson_to_line` is the documented gate (§3.4 routes every feature through it); a hazard only if a later task bypasses it.
5. **§3.8's vertex-row range may be miscalibrated. — ✅ DISCHARGED 2026-09-22 in `868908a`**, which recalibrated §3.8 to `35k–150k (measured density ≈ 3.2 vertices per segment)`. The text below is kept for the record; the concern no longer applies.** Measured density is **3.19 vertices per feature** (5909 / 1850). Against §3.8's 12k–45k expected layer-17 features at 10 km that projects to roughly **38k–144k vertex rows**, whose low end falls *below* §3.8's stated 60k–600k floor. Consequences: the range may want revisiting at Gate B, and **the Excel 1,048,575-row sheet-split path in S4.T3 is very unlikely to fire** (keep it anyway).
6. **Non-simple geometry does exist in MRWA data** — 3 features each in layers 16 and 8. Those layers feed the SLK join, not `segment_metrics`, so it does not apply here; recorded because the assumption "MRWA lines are always simple" is not free.
7. **Two surviving mutants remain, both Minor and both unreachable on current data:** dropping the `if length > 0 else 0.0` zero-length guard in `dbe/geometry.py` survives the suite (no zero-length feature exists to catch it), and `rounding_precision=12` — now killed by `40cf0b6`. Overall mutation score after the fix: **15 of 17 killed.** The suite is genuinely strong; the residual gap is narrow and named.

### 2026-09-22 — S1.T1 geometry core verified (orchestrator session 2, Opus)

**Two deviations from the plan's snippets, both proven behaviour-identical.**
- `dbe/geometry.py:17-18` — the plan's single `self.crs = CRS.from_proj4(f"…")` line is **115 characters** (the implementer's report said 118; the reviewer's programmatic count is authoritative), over this repo's `line-length = 110`. Split into a `proj4 = f"…"` local plus `CRS.from_proj4(proj4)`. The f-string literal is byte-identical to the plan's (verified by string comparison, not by eye).
- `tests/test_geometry.py:22` — the plan's `zip(line.coords, back.coords)` trips ruff bugbear **B905** (`zip()` without `strict=`) under this repo's `select = ["E","F","I","B","UP"]`. `strict=False` was added, which is exactly bare `zip`'s default. **`strict=True` would have been the better pick at identical lint cost** — the reviewer demonstrated that with `strict=False` an empty `to_wgs84` result makes `test_roundtrip_wgs84` pass vacuously (zero iterations, the assert never runs), while `strict=True` raises. Both iterables are the same line's coords, so a length mismatch is always a genuine bug. **Instructed S1.T2 to flip it to `strict=True` while it is appending to that file.**

**AEQD is geodesically exact and fit for the 10 km run** (orchestrator-commissioned verification against `pyproj.Geod(ellps="WGS84").inv`, PROJ 9.8.1). Radial distance from the centre matches the true geodesic to **< 1e-9 m** at 1 km, 10 km and 50 km. The plan's own flat-earth `expected` in `test_east_west_line_length_in_metres` is the inaccurate one — it is off by **-0.884 m** against a true geodesic of 944.931418 m, which the `rel=0.01` tolerance absorbs. Tangential (worst-case) distortion follows `(d/R)²/6`: **4.11e-7 at 10 km** (0.41 mm per km of segment), 1.03e-5 at 50 km. A 10 km-long segment sitting 10 km out is wrong by ~4 mm. Throughput: `to_local` runs at 60 µs/feature (111 ms over the 1850-feature fixture) → ~2.1 s at §3.8's 35,000-segment upper bound. Not a concern.

**`envelope_wgs84` does NOT under-cover** — the earlier S0.T3 concern does not apply to it. Shapely places buffer vertices at exact multiples of 2π/256 starting at angle 0, so vertices land precisely on both axes and the local bounds are exactly `(-r,-r,r,r)` to the last bit. After reprojection the true circle's maximum excursion outside the returned box is **4.8 mm at r = 10,000 m** (north/south 0.000 m; the east/west 4.8 mm arises because the true circle's easternmost longitude falls at azimuth ≈ 90.056°, where no vertex sits). That is ~2000× smaller than the S0.T3 recorder's 9.7 m flat-earth shortfall and an order of magnitude below the ~1.5 m GDA94↔WGS84 datum offset already documented in §1. **No action.**

**Forward risks — recorded, not acted on (orchestrator scope ended at S1.T2):**
1. **The plan's own test tolerances are too loose to pin envelope sizing.** Mutation testing of `tests/test_geometry.py` showed all 5 tests still pass under: an envelope shrunk 1.8 % (~180 m at 10 km), an envelope shifted ~100 m, and a spherical earth (`+R=6371008.8`) substituted for WGS84. `rel=0.02` at 10 km is ±200 m, so **this suite could not have caught the S0.T3 flat-earth bug** (9.7 m ≈ 0.1 %). The weakest assertion is `circle.bounds == approx((-1000,-1000,1000,1000), abs=1.0)` (`tests/test_geometry.py:29`), which has **zero discriminating power** — it passes even at `quad_segs=1` (a square), because a vertex always lands on each axis. `circle.area` at `rel=0.01` passes from `quad_segs=8` upward and so does not pin `quad_segs=64` (true error there is 1.0e-4, 100× tighter than the tolerance). If a later segment hardens envelope sizing, tighten these against a `pyproj.Geod` reference instead of the `111_320` flat-earth constants. **These tolerances are verbatim from the plan — not an implementer defect.**
2. **Inclusion-circle sagitta.** The circle used for the intersects test is an inscribed 256-gon, so its mid-chord sagitta is `r(1 - cos(π/256))` = **0.753 m at r = 10,000 m** (0.075 m at 1 km). A segment whose closest approach is between 9,999.25 m and 10,000 m can be excluded. `quad_segs=64` is mandated by §3.2, so this is spec-conformant and sits below the ~1.5 m datum noise floor. **Recorded, no change recommended.**
3. **`envelope_wgs84` degenerates at the antimeridian and the poles** — `LocalProjection(0, 179.99).envelope_wgs84(50_000)` returns an inverted box spanning the globe the wrong way, and `LocalProjection(89.9, 0)` misses the pole. **Cannot fire in this project** (WA spans lon ~112–129, lat ~-35 to -13). Recorded only so nobody reuses `geometry.py` elsewhere without noticing.
4. **No test asserts `proj.lat`, `proj.lon` or `proj.crs`**, though all three are named in the S1.T1 Interfaces block (the plan's own test list omits them). A later task consuming `proj.crs` has no regression guard.
5. **`CRS.from_proj4` f-string has no locale or notation hazard** (checked): Python float→str is locale-independent (verified under `de_DE.UTF-8`); `1e-05` scientific notation parses correctly; `nan`/`inf`/`1e16` raise `CRSError` at construction, which is correct fail-fast behaviour — input validation belongs to the S4 CLI task.
6. **`shapely.ops.transform` handles everything §3.2 needs:** empty geometries round-trip cleanly, `MultiLineString` works, `GeometryCollection` works, polygons with holes work, and **Z coordinates pass through unchanged** (correct — both CRSs are ellipsoidal-height WGS84).

### 2026-09-22 — S0.T3 fixture radius escalated 1.5 km → 2.5 km (orchestrator session 2, Opus) — **RATIFIED**

**What changed.** Plan S0.T3 Step 2's contingency fired: at `RADIUS_M = 1500` **layer 12 (Pavement and Surfacing State) returned 0 features**, so the recorder was re-run at `RADIUS_M = 2500.0`. The plan's own "Expected" note claiming "Leach Hwy and Manning Rd corridors lie inside 1.5 km" is **wrong for this centre** — confirmed three ways: a live `returnCountOnly=true` query on the exact 1500 m envelope returned `{"count": 0}`; the Opus reviewer's offline haversine over the recorded fixture found 0 of 113 features within 1500 m; and the orchestrator's own AEQD re-projection puts the **nearest layer-12 vertex at 2125.5 m** from the centre. Without width data the whole `WIDTH_SOURCE = mrwa_pavement` path would be untestable, so the escalation was necessary, not cosmetic.

**Naming.** Fixtures are `tests/fixtures/layer{17,12,16,8}_curtin2500.geojson` and the documented constant is **`CURTIN_2500_ENVELOPE`**, deviating from the S0.T3 Interfaces block's `CURTIN_1500_ENVELOPE`. The plan authorised a rename on the *oversize* branch but not on the *layer-12-empty* branch, and §1 says Interfaces names are contracts — so this rename is **hereby ratified by the orchestrator** rather than taken as implicitly allowed. Reverting is strictly worse: a file called `curtin1500` holding a 2500 m envelope is a lie. Anyone reading §1's "do not rename" rule against this entry should treat this entry as the newer authority for these four filenames and this one constant, and nothing else.

**Recorded envelope (`CURTIN_2500_ENVELOPE`), wire precision `.7f`:**
`(115.8659776, -32.0243207, 115.9189422, -31.9794051)` — centre `-32.0018629, 115.8924599`, `RADIUS_M = 2500.0`.

**Recorded contents** (orchestrator-verified from the committed bytes, not from the implementer's prose): layer 17 = 1850 features / 1,657,997 B · layer 12 = 113 / 132,469 B · layer 16 = 659 / 577,273 B · layer 8 = 580 / 543,483 B. All four are `FeatureCollection`s, all 3202 features are `LineString`, **zero `MultiLineString`, zero `geometry: null`, zero duplicate `OBJECTID`**, `OBJECTID` ascending. All far under the 5 MB cap; the compact-`separators` escalation was never needed.

> **⚠ MANDATORY BEFORE DISPATCHING S2.T2.** The plan text is now stale in ten places. Pasting it verbatim into the S2.T2 implementer prompt produces a test suite that **passes green while covering nothing** — the plan's `test_with_osm_fills_width_only_where_missing` guards its assertions behind `if state is not None:`, so a zero-width-row fixture set fails silently. Apply this table when writing that prompt:
>
> | Plan line | What it says | Must become |
> |---|---|---|
> | 240 | §3.7 file map `layer17_curtin1500.geojson` | `…_curtin2500.geojson` |
> | 452 | S0.T3 Interfaces `CURTIN_1500_ENVELOPE` | `CURTIN_2500_ENVELOPE` |
> | 1167 | S2.T2 Interfaces: `load_fixture` path **and** the `curtin_1500` fixture | filename **and** `radius_km` |
> | 1182 | S2.T2 conftest `FIXTURES / f"layer{id}_curtin1500.geojson"` | `…_curtin2500.geojson` |
> | 1204 | S2.T2 conftest `def curtin_1500()` / `CURTIN = dict(…, radius_km=1.5)` | `def curtin_2400()` / **`radius_km=2.4`** |
> | 1294 | Gate A item 3, "four `*_curtin1500.geojson` files" | `*_curtin2500.geojson` |
> | 1836, 1856, 1869, 1874, 1879, 1881 | S2.T3 `test_extract.py` fixture params | `curtin_2400` |
> | 1843 | `assert … DIST_TO_CENTRE_M <= 1500.0 + 1.0` | **`2400.0 + 1.0`** |
> | 2782, 2788, 2799 | S3.x `test_with_osm_…` fixture params | `curtin_2400` |
>
> Plan lines 715 (`_offset_line(…, 1500)`) and 1268 (`envelope_wgs84(300.0)`) are unrelated uses of those numbers — **leave them alone.**

**Why `radius_km = 2.4` and not 2.5** — this is measured, not rounded for comfort. The recorder uses the plan's flat-earth constants (`dlat = RADIUS_M / 111_320`), which under-size the box in latitude: the recorded box's true half-extents are **east/west 2502.3 m but north/south only 2490.3 m**. So a 2500 m circle does **not** fit inside the data actually recorded, and a test at `radius_km=2.5` would silently ask for roads in two slivers at due north and due south that were never fetched. Orchestrator-verified with the production AEQD `envelope_wgs84`: at 2500 m `fits_inside_recorded=False`; at 2450 m and 2400 m `fits_inside_recorded=True`. **2.4 km is the safe round value.** Layer-12 coverage at 2.4 km is 37 of 113 features — comfortably non-empty, so the width path stays exercised.

**Flat-earth constant — do not copy it into `geometry.py`.** The `111_320` arithmetic lives only in `scripts/record_fixtures.py` and in S1.T1's test assertions (plan lines 585–586, which use `rel=0.02` — the 0.39 % latitude error is well inside that, so no test change is needed). Production `envelope_wgs84` (plan line 634) correctly takes the bounds of the reprojected AEQD buffer instead. If the flat-earth formula ever migrated into `geometry.py`, it would under-cover the 10 km run by ~39 m in latitude and silently drop roads, violating §1's "every layer-17 segment that intersects the circle".

**Other S0.T3 findings.** The recorder's `len(page) < PAGE` paging-termination rule is sound *only because* `PAGE = 2000` equals the confirmed `maxRecordCount = 2000`; it cannot detect a future lowering of `maxRecordCount` the way ArcGIS's `exceededTransferLimit` flag could. The implementer compensated by cross-checking every layer count against an independent `returnCountOnly=true` query — all four matched. **S2.T1's production client must not inherit this weakness:** Gate A item 5 already requires it to stop on a short page *and* an empty page and to carry a `MAX_PAGES` guard. The recorder has no `MAX_PAGES`; acceptable for a one-shot script.

**All fixture geometries are `LineString`.** No `MultiLineString` appears anywhere in the recorded data, so S1.T2's and S2.T2's `MultiLineString` handling can only ever be exercised by synthetic test shapes. Keep those synthetic tests — do not delete them as "untested in fixtures"; §3.2 still requires MultiLineString support, and the wider 10 km production run may well return some.

### 2026-09-22 — S0.T2 confirmed source facts (orchestrator session 2, Opus)
All of the following were re-derived by the orchestrator directly from the committed JSON fixtures, not taken from the implementer's prose. Plan §2's two "Likely" rows are now **Certain**.
- **`HIERARCHY_FIELD = "ROAD_HIERARCHY"`** — layer 16 "Road Hierarchy", `esriFieldTypeString`, length 30, `domain: null`. Matches the plan's guess; **no rename needed in S3.T2.**
- **`SPEED_FIELD = "SPEED_LIMIT"`** — layer 8 "Legal Speed Limit", `esriFieldTypeString`, length 80, `domain: null`. Matches the plan's guess; **no rename needed in S3.T2.**
- **`supportsPagination = true` on all four layers** (17, 12, 16, 8), as are `supportsOrderBy` and `supportsStatistics`. `maxRecordCount = 2000` and `geometryType = esriGeometryPolyline` on all four; `extent.spatialReference.wkid = 4283` (GDA94) on all four. The `resultOffset`/`resultRecordCount` paging strategy in S2.T1 is therefore safe.
- **Join keys `ROAD, CWY, START_SLK, END_SLK` are present on all four layers** — the linear-referencing join in S3.T1/S3.T2 has its keys everywhere it needs them.
- **`SPEED_LIMIT` is a STRING, not a number.** Layer 8's renderer enumerates 12 values: `10km/h, 20km/h, 30km/h, 40km/h, 50km/h, 60km/h, 70km/h, 80km/h, 90km/h, 100km/h, 110km/h` plus the free-text `50km/h applies in built up areas or 110km/h outside built up areas`. **S3.T2 must not assume `int()` parses this** — the units are embedded and the twelfth value is unparseable.
- **`ROAD_HIERARCHY` real value set (6, from layer 16's renderer):** `Primary Distributor, Regional Distributor, Distributor A, Distributor B, Local Distributor, Access Road`. Plan §2 line 146 wrote these as "District Distributor A/B" — **the live values have no "District" prefix.** Correct the expectation in S3.T2.
- **Layer 17 serves 26 fields, not 25** — the 25 of `ORIGINAL_COLUMNS` plus the raw `GEOLOC` geometry field (`esriFieldTypeGeometry`). §3.3 already excludes `GEOLOC`, so no schema change; noted for S4.T1.
- **The live field is literally `GEOLOC.STLength()` (dot + parens), while `ORIGINAL_COLUMNS` calls it `GEOLOCSTLength`.** S4.T1/S4.T2 must **rename** it, not match it literally. The live field order also differs from `ORIGINAL_COLUMNS` (live ends `… ROUTE_NE_ID, GEOLOC, OBJECTID, GEOLOC.STLength(), GlobalID`), so the pipeline must reorder explicitly rather than pass the API's order through.
- **Deviation from the plan's snippet (cosmetic only):** `scripts/verify_layers.py` wraps the `LAYERS` dict, both `print(...)` calls and the `requests.get(...)` call, and hoists a `wkid` local, to satisfy this repo's own `line-length = 110` ruff rule which the plan's snippet violated. The Opus reviewer proved equivalence by replaying both versions against a stubbed `requests`: identical stdout, stderr, exit code, call arguments and written bytes.
- **Second commit `28e1809`** re-grounds one `GEOLOC` claim in `source_verification.md` in the fixture JSON; in scope for S0.T2, no unrelated work.

### 2026-09-22 — S0.T1 (orchestrator session 2, Opus)
- **PyPI is reachable, but slow — `uv sync` needs `UV_HTTP_TIMEOUT` raised.** The Sonnet implementer reported `uv sync` as a hard network block (three failed attempts against `pypi.org/simple/shapely` and `.../matplotlib`). The orchestrator re-tested: `curl https://pypi.org/simple/shapely/` returns HTTP 200 in ~8.3 s, and `UV_HTTP_TIMEOUT=180 uv sync` completed in 1 m 21 s, installing 22 packages. **Not a blocker.** Standing instruction for every later task and session: run `UV_HTTP_TIMEOUT=180 uv sync` on a cold venv, and use `uv run --no-sync ...` once the venv is warm.
- **`uv.lock` was amended into `e46431e` by the orchestrator.** The implementer's commit predated the successful sync, so the lock did not exist when it committed; the orchestrator ran `uv sync`, then `git add uv.lock && git commit --amend --no-edit`. No `Co-Authored-By` trailer (verified with `git show -s --format=%B`).
- **`dbe/cli.py` was correctly NOT created.** Plan S0.T1 Step 3's escape hatch never triggered — `uv sync` installs the console script without importing the target. The module stays for S4.T4. (Plan erratum: Step 3 says the CLI "arrives in S4.T3"; §3.5 and the task table both say **S4.T4**. S4.T4 is correct.)
- **`.gitignore` and `CLAUDE.md` were not modified** — both already satisfied the task's Step 4 / "only if missing" conditions (verified by the Opus reviewer).
- **pandas resolved to 3.0.6, not 2.x** (§1 pins only `pandas>=2.2`). pandas 3.0 makes `str` the default dtype and surfaces missing values as `pd.NA` rather than `np.nan`, which changes how blank cells round-trip through `to_csv`/`read_csv`. This bears directly on the "a missing width never drops a row" constraint and on S4.T3's CSV→XLSX conversion; recorded now so those tasks are authored against 3.0 semantics. Other locked versions: requests 2.34.2, shapely 2.1.2, pyproj 3.8.0, openpyxl 3.1.5, pytest 9.1.1, ruff 0.16.8, matplotlib 3.11.2. No forbidden package (geopandas/osmnx/Google/fiona/rtree) present in `uv.lock`.

### 2026-09-22 — Planning decisions (Fable, with user answers)
- **Data source:** Main Roads WA `RoadAssets_DataPortal/MapServer` (layers 17, 12, 16, 8). Google Maps rejected (no area geometry API, no width, ToS forbids bulk export). OSM demoted to optional enrichment (width tag ≈ 1.4 % coverage globally).
- **User: geometry for all roads incl. local is mandatory; width is best-effort.** → `WIDTH_SOURCE` provenance column; no estimated widths ever.
- **User: output = segment rows + separate vertices table.**
- **User: circle rule = intersects, keep whole geometry**, `INSIDE_FRACTION` column.
- **User: provided CSV is validation-only** (`tests/test_reconcile_csv.py`), never a runtime input.
- **Fable:** plain `requests` + `shapely` + `pyproj`, no geopandas/osmnx; AEQD local projection centred on the query point; POST for ArcGIS queries; XLSX built from the CSV files.
- **Fable:** Python ≥ 3.11 via `uv` (system 3.9.18 is EOL). Branch renamed `master` → `main` at the first commit (no remote existed).

## Blockers

_(none)_

## Verification log

_Newest first. Every `uv run pytest` / `ruff` / e2e run that a task or gate relied on: date, command, summary line, counts._

### 2026-09-24 — Fable end-to-end review
- Fresh clone at `9685d0c`: `UV_HTTP_TIMEOUT=180 uv sync` ok · `uv run pytest -q` → `94 passed, 3 skipped, 1 deselected in 41.11s` · `ruff check .` → `All checks passed!` · `pytest -m network -q` → `1 passed`.
- In-repo after fixes: `pytest -q` → **`103 passed, 1 deselected in 9.36s`**; `ruff check .` clean; `tests/test_reconcile_csv.py -s` → `extracted=21560 matched=21560 new_since_export=0 ratio=1.0000`, `3 passed`.
- Live cold-cache re-run, shipped code: `extract … --radius-km 10 --out output/review_curtin_10km --cache-dir <scratch>` → exit 0, **139 s**, 21,643 / 85,118, `roads.csv` identical to the reference apart from `EXTRACTED_AT_UTC`.
- Regeneration from the original cache with the fixed inclusion: exit 0, 37 s, **21,645 segments, 85,122 vertices**, outside 5,329; `roads.csv` 16,165,303 B · `roads_vertices.csv` 7,982,007 B · `roads.xlsx` 11,049,054 B.
- Live: polygon `returnIdsOnly` 21,643 / 0 / 0; padded envelopes +50 m / +200 m → 2 extra ids inside the true circle (the fixed pair) and no others; 5 rows by `OBJECTID` exact; 3 widths by where-clause: 2 exact, 1 at a rounding boundary (10.155).

### 2026-09-23 — Segment 4 and the first production run (orchestrator session 4, Opus)

**The live 10 km extraction** — `dbe extract --lat -32.0018629 --lon 115.8924599 --radius-km 10 --out output/curtin_10km`: **185 s wall, exit 0.**

| Quantity | Value |
|---|---|
| Layer-17 features fetched / distinct | 28,142 / 26,974 |
| Segments intersecting (rows in `roads.csv`) | **21,643** |
| Vertices rows | **85,118** (= Σ`VERTEX_COUNT` exactly) |
| Pages, layer 17 | 15 (14 of them short but flagged as overflowing) |
| Measured widths | **1,202**, all State Road, 3.34–30.7 m |
| Rows given a width they lack | **0** |
| `duplicates_dropped` (layer 17) | 1,168 |
| `enrich_duplicates_dropped` (layers 12/16/8) | 622 (135 + 376 + 111) |
| `skipped_no_geometry` / `skipped_bad_geometry` | 0 / 0 |
| `INSIDE_FRACTION` | all within [0,1]; 21,268 (98.3%) exactly 1.0; min 0.0011 |
| Divided-carriageway cases | **0** — the decision's condition is discharged |

**Reconciliation against the user's provided statewide CSV:** `extracted=21558 matched=21558 new_since_export=0 ratio=1.0000`, plus `regions: {'Metropolitan': 21641, '': 2}`.

**Output files:** `roads.csv` 16.2 MB · `roads_vertices.csv` 8.0 MB · `roads.xlsx` 11.0 MB (sheets `roads` 21,644 rows, `vertices` 85,119, `metadata` 26) · `metadata.json` · `qa_plot.png` 1.2 MB · `cache/`.

**Orchestrator's own checks:** row count on disk equals `segments_intersecting`; 53-column header; all 21,643 OBJECTIDs distinct; every row carries a WKT geometry; 0 non-state rows with a width; QA plot read directly and confirmed to show a filled street grid, the freeway skeleton with interchange loops, genuine road-free voids at the river and airport, and segments overhanging the dashed boundary.

**Suite:** `80 passed, 1 deselected in 5.81s`; `ruff check .` clean; `pytest -m network -q` → `1 passed`. No `Co-Authored-By` trailer on any commit in the range.

### 2026-09-23 — Segment 3 close-out (orchestrator session 4, Opus)
- Final state: `uv run --no-sync pytest -q` → **`50 passed, 1 deselected in 0.20s`**; `uv run --no-sync ruff check .` → `All checks passed!`; tree clean; `git log ec26c01..HEAD --format=%B | grep -i co-authored` → no match across all commits.
- **Orchestrator's own mutation runs, before and after the fix** (`PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider`, `enrich.py` restored from a backup after each):
  | Mutation | Before `24bc879` | After |
  |---|---|---|
  | drop the `SEALED_SHOULDER_R` mapping | `49 passed` — silent | **`1 failed, 49 passed`** |
  | swap `KERB_L` / `KERB_R` | `49 passed` — silent | **`1 failed, 49 passed`** |
- Orchestrator re-ran the enrichment over all 1850 real layer-17 features through the committed modules: 65 measured widths (all `State Road`, 6.4–19.6 m), `WIDTH_SOURCE` = State 65 `mrwa_pavement` / Local 1763 `none` / Misc 22 `none`, **0 local roads with a width**, 5 hierarchy values, 5 speed values all strings, and the source layers byte-identical afterwards.
- Independent real-data check through the committed `slk_join`: 65/65 State Roads find a layer-12 width span, 0/1763 Local Roads do.

### 2026-09-23 — S2.T2 + Gate A evidence (orchestrator session 4, Opus — primary session, not a subagent)

**S2.T2, all three parties' numbers agree:**
- `uv run --no-sync pytest -q` → **`30 passed, 1 deselected in 0.59s`** (orchestrator) / `30 passed, 1 deselected in 0.26s` (implementer). 26 pre-existing + 4 new fixture-shape tests; the network test correctly deselected by `addopts`.
- `uv run --no-sync pytest -m network -q` → **`1 passed, 30 deselected in 1.14s`** (orchestrator) / `1 passed, 30 deselected in 1.67s` (implementer). Live call to the real MRWA service. **This is the run Gate A item 1 requires — no prior pytest network run existed, only S2.T1's ad-hoc Python one-liner.**
- `uv run --no-sync ruff check .` → `All checks passed!`
- `git show --stat 50acb36` → exactly 3 files, **89 insertions, 0 deletions** — no pre-existing file modified.
- Trailer check `git log 9b7febc..HEAD --format=%B | grep -i co-authored` → no match. (Noted because the harness attribution reminder changed this session to request `Co-Authored-By: Claude Opus 5`; the user's global CLAUDE.md forbids it and takes precedence. The implementer prompt carried an explicit prohibition.)
- Long-line scan `awk 'length > 110'` over the three new test files and all of `dbe/` → no output.
- Working tree clean after the commit.

**Gate A evidence gathered directly by the orchestrator (not delegated), items 2–6:**
- **Item 2 —** `docs/task_docs/source_verification.md` exists (4,245 B) and literally names `HIERARCHY_FIELD = "ROAD_HIERARCHY"` (layer 16, `esriFieldTypeString`, length 30) at line 31 and `SPEED_FIELD = "SPEED_LIMIT"` (layer 8, `esriFieldTypeString`, length 80) at line 32, with a `supportsPagination` column in the layer table at line 11. **PASS**
- **Item 3 —** four `*_curtin2500.geojson` fixtures, all well under 5 MB: layer 12 = 0.13 MB (113 features, non-empty), layer 16 = 0.55 MB, layer 17 = 1.58 MB, layer 8 = 0.52 MB; `tests/fixtures/README.md` present. **PASS**
- **Item 4 —** `dbe/geometry.py`: `always_xy=True` on **both** transformers (lines 23, 24); `envelope_wgs84` returns `ring.bounds` i.e. lon/lat order (line 35 ff.); zero-length guard `(inside_len / length) if length > 0 else 0.0` present (line 84); `shapely.to_wkt(..., rounding_precision=7)` (line 91). **PASS**
- **Item 5 —** `dbe/mrwa_client.py`: `session.post` for queries (line 131) and `session.get` for metadata (line 129); ArcGIS `error` body raises `MRWAError` (line 137), which is deliberately **not** in the retry `except` clauses, so it does not retry; paging terminates on empty page *and* short page via `if not page_feats or (len(page_feats) < self.page_size and not exceeded)` (line 109); cache key covers method, URL and all params (line 163); `MAX_PAGES = 10_000` guard present and raising (lines 26, 94, 115). **PASS**
- **Item 6 —** `grep -rn "Road_Network\|data/\|\.csv" dbe/` → **no matches**, so nothing in the package reads the provided CSV. Package imports are only stdlib plus `requests`, `shapely`, `pyproj` — no dependency outside §1. `uv.lock` contains no `geopandas`, `osmnx`, `fiona`, `rtree` or `googlemaps`. **PASS**
- **Known and expected, not a finding:** `uv run --no-sync python -m dbe` raises `ModuleNotFoundError: No module named 'dbe.cli'`, and `pyproject.toml` declares the console script `dbe = "dbe.cli:main"`. `cli.py` is scheduled for **S4.T4**; this is the planned intermediate state, recorded so the Gate A reviewer does not report it as a defect.

### 2026-09-22 17:25 UTC — S2.T1 (implementer + Opus reviewer + fix `44e5d24` + Opus re-review)
- Session baseline, before any work: `uv run --no-sync pytest -q` → `14 passed in 0.15s`; `uv run --no-sync ruff check .` → `All checks passed!`; clean tree at `868908a`
- TDD red: `uv run --no-sync pytest tests/test_mrwa_client.py -q` → `ModuleNotFoundError: No module named 'dbe.mrwa_client'`
- TDD green after `7edb78e`, file-scoped: `11 passed in 0.07s`; full suite `25 passed in 0.16s` (implementer) / `25 passed in 0.16s` (orchestrator) / `25 passed in 0.17s` (reviewer)
- After fix `44e5d24`, file-scoped: `12 passed in 0.09s`; full suite **`26 passed in 0.23s`** (orchestrator) / `26 passed in 0.22s` (implementer) / `26 passed in 0.24s` (reviewer)
- `uv run --no-sync ruff check .` → `All checks passed!` (all three parties)
- Orchestrator long-line check: `awk 'length > 110' dbe/mrwa_client.py tests/test_mrwa_client.py` → no output
- Orchestrator `grep -rn returnZ dbe/ tests/` → no match (S1.T2 forward-risk #3 discharged)
- Orchestrator trailer check: `git log --format='%B' -2` → both messages single-line, **no `Co-Authored-By`**; `git show --stat` confirms `7edb78e` touches only the two new files and `44e5d24` only `tests/test_mrwa_client.py`
- **Live sanity call (orchestrator, real service):** `curl` preflight on layer 17 `?f=pjson` → HTTP 200 in 1.58 s. Then `MRWAClient(sleep_s=0).query_envelope(17, LocalProjection(-32.0018629, 115.8924599).envelope_wgs84(300.0))` → **8 features in 0.90 s**, geometry types `{LineString}`, coordinate arity `{2}`, `ROAD` present, length field present as `GEOLOC.STLength()`. `cache_dir` unset, so nothing written into the repo.
- **Reviewer mutation score over `dbe/mrwa_client.py`: 6 of 10 killed before `44e5d24`, 16 of 19 after.** Harness validated each time with a deliberate fatal mutant (`return features` → `return []`, kills 5–6 tests) before any result was trusted. Survivors: `offset = len(page_feats)` assignment, cache key dropping *method* only, `sha1[:4]`.
- Implementer's own 3-mutant matrix (M4 offset, M6 verb swap, M9 cache key) was **independently reproduced by the Opus reviewer** and matched exactly; `git diff dbe/mrwa_client.py` empty after every mutation run
- Reviewer blob-hash check: `dbe/mrwa_client.py` = `10ea2723…` at `7edb78e`, `44e5d24` and `HEAD` — the fix commit provably did not touch production code
- **Reviewer process note, recorded for reuse:** its first probe batch silently accumulated unreverted mutants (a backup was written as `mrwa_client.bak2` instead of `mrwa_client.py.bak2`, so every restore was a no-op). It caught this from implausibly uniform results and rebuilt the harness; the reported GET/POST answers come from the clean re-run. **Anyone reusing this mutation-harness pattern must assert the restore actually restored.**

### 2026-09-22 16:35 UTC — S1.T2 (implementer + Opus reviewer + fix `40cf0b6`)
- TDD red: `uv run --no-sync pytest tests/test_geometry.py -q` → `ImportError: cannot import name 'geojson_to_line' from 'dbe.geometry'` / `1 error in 0.58s`
- TDD green, file-scoped: `12 passed in 0.41s`; full suite before the fix: `13 passed in 0.26s`
- After fix `40cf0b6`: `uv run --no-sync pytest -q` → **`14 passed in 0.23s`** (orchestrator) / `14 passed in 0.31s` (implementer)
- `uv run --no-sync ruff check .` → `All checks passed!`
- **Orchestrator mutation check of the new WKT test** (each run mutates `rounding_precision` in `dbe/geometry.py`, then restores it): precision 2 → `1 failed, 12 passed` · 6 → `1 failed, 12 passed` · 8 → `1 failed, 12 passed` · 12 → `1 failed, 12 passed` · restored 7 → `14 passed`. `git diff dbe/geometry.py` clean afterwards.
- Reviewer mutation score over `dbe/geometry.py`: 14 of 17 mutants killed before the fix, 15 of 17 after. Killed include: WKT built from local instead of WGS84 coords, `inside_fraction` hardcoded to 1.0, lat/lon swapped in `iter_vertices`, start/end swapped, distance measured in degrees, `_parts` dropping the MultiLineString branch, `geojson_to_line` accepting any type.
- Reviewer run of `segment_metrics` over all 1850 real layer-17 features — full numbers in the Decisions log (relayed from the reviewer, not independently re-derived by the orchestrator)
- Retrospective Opus review of the fix commit `40cf0b6` alone → APPROVE, no Critical/Important; independently reproduced the mutation matrix and confirmed `dbe/geometry.py` blob hash unchanged across `7764393`, `40cf0b6` and `HEAD`

### 2026-09-22 16:15 UTC — S1.T1 (implementer + Opus reviewer)
- TDD red: `uv run --no-sync pytest tests/test_geometry.py -q` → `ModuleNotFoundError: No module named 'dbe.geometry'` / `1 error in 1.27s`
- TDD green, file-scoped: `uv run --no-sync pytest tests/test_geometry.py -q` → `5 passed in 0.47s`
- Full suite: `uv run --no-sync pytest -q` → `6 passed in 0.39s` (orchestrator) / `6 passed in 0.41s` (reviewer)
- `uv run --no-sync ruff check .` → `All checks passed!`
- Reviewer geodesic check vs `pyproj.Geod(ellps="WGS84").inv`: radial error < 1e-9 m at 1 km / 10 km / 50 km; east-west test line AEQD 944.931418 m = geodesic 944.931418 m (plan's flat-earth `expected` is off by -0.884 m)
- Reviewer envelope containment check vs a 200,000-azimuth geodesic circle at r = 10,000 m: north/south shortfall 0.000000 m, east/west 0.004791 m
- Reviewer mutation test of `tests/test_geometry.py`: 5/5 still pass under a 1.8 % envelope shrink, a ~100 m envelope shift, and a spherical earth — see Decisions log

### 2026-09-22 16:00 UTC — S0.T3 (implementer + Opus reviewer + orchestrator)
- `uv run --no-sync pytest -q` → `1 passed in 0.02s`
- `uv run --no-sync ruff check .` → `All checks passed!`
- Live `returnCountOnly=true` cross-check, 1500 m envelope: L17 569 · **L12 0** · L16 216 · L8 212
- Live `returnCountOnly=true` cross-check, 2500 m envelope: L17 1850 · **L12 113** · L16 659 · L8 580 — every count matched the paged fetch exactly (no silent truncation)
- Fixture sizes: layer17 1,657,997 B · layer12 132,469 B · layer16 577,273 B · layer8 543,483 B (cap 5 MB)
- Orchestrator AEQD check of the recorded box: half-extents east/west 2502.3 m, north/south 2490.3 m; `envelope_wgs84(2500)` fits = **False**, `envelope_wgs84(2450)` = True, `envelope_wgs84(2400)` = True
- Orchestrator layer-12 distance profile: nearest vertex 2125.5 m; features with a vertex within 1500 m = **0**, within 2400 m = 37, within 2500 m = 41
- Reviewer `diff -u` of the plan's S0.T3 snippet against the committed recorder: exactly three hunks (docstring, `RADIUS_M`, output filename); every request parameter character-identical

### 2026-09-22 15:45 UTC — S0.T2 (implementer + Opus reviewer)
- `uv run --no-sync pytest -q` → `1 passed in 0.02s`
- `uv run --no-sync ruff check .` → `All checks passed!`
- Fixture sizes (all far under the 5 MB cap): layer17 22,792 B · layer12 17,163 B · layer16 22,103 B · layer8 16,289 B
- Reviewer equivalence test: plan snippet vs committed `scripts/verify_layers.py` replayed against a stubbed `requests` → identical stdout, stderr, exit code, call args and written bytes (both an OK run and a forced name-mismatch run). Forced HTTP 500 on layer 16 → traceback on stderr, exit 1, partial fixture set (loud, not silent).

### 2026-09-22 15:30 UTC — S0.T1 (orchestrator + Opus reviewer)
- `UV_HTTP_TIMEOUT=180 uv sync` → `Prepared 19 packages in 1m 21s` / `Installed 22 packages in 77ms`
- `uv run pytest -q` → `1 passed in 0.01s`
- `uv run --no-sync pytest -q` (reviewer) → `1 passed in 0.00s`
- `uv run --no-sync ruff check .` (reviewer) → `All checks passed!`
- `uv run --no-sync pytest -q -m network` (reviewer, marker plumbing check) → `1 deselected in 0.00s`

## Session log

_Newest first. One entry per orchestrator session: start time, what was resumed, what was completed, where it stopped and why._

### 2026-09-24 — Fable end-to-end review (Fable 5.1, user-triggered)

Planned in plan mode (read-only), user approved fixing the inclusion defect rather than documenting it, then executed. Ran Phases A (offline), B (live) and C (records) per `~/.claude/plans/…dreamy-karp.md`; wrote `docs/task_docs/fable_review.md`; applied the fixes directly (small, all files already in context) instead of dispatching a Sonnet implementer, to save tokens at the user's request; dispatched one Opus review of the whole diff. Held every change uncommitted at the user's explicit instruction until they said "commit and push"; then committed per fix (`e13c2d7` geometry, `8d2e37e` export, `a0849d0` cli, `af6431e` docs), no trailer, and pushed. Next action: none; deferred recommendations are listed in the review file.

### 2026-09-22 ~17:00–17:30 UTC — Orchestrator session 3 (Opus) — S2.T1 complete; session cut off by usage limit

**Scope, as instructed by the user:** complete exactly S2.T1 and stop. Honoured — S2.T2 and Gate A were not started.

**Resumed from:** clean tree at `868908a` (plan corrections), `14 passed`.

**Completed:** S2.T1 `MRWAClient` — implemented on Sonnet (`7edb78e`), reviewed on Opus (REQUEST CHANGES: paging-offset arithmetic, HTTP verb and per-page cache key were not pinned by tests), fixed with three test-only additions (`44e5d24`), re-reviewed on Opus → APPROVE. Full suite `26 passed`, ruff clean, no `Co-Authored-By` trailers. Live sanity call against the real service: 8 layer-17 features for a 300 m envelope at Curtin in 0.90 s. Details in the Decisions log and Verification log entries above.

**Stopped at:** the orchestrator hit the Claude usage limit (HTTP 429 on Opus) after writing the Verification log entry and before writing this Session log entry, committing `progress.md`, or pushing. Fable verified the repo state on 2026-09-23 (`26 passed`, ruff clean, two unpushed commits, no trailers), wrote this entry, committed and pushed. **Next action: S2.T2** (fixture loader, `FixtureSource`, live smoke test — using the `curtin2500` fixtures and `curtin_2400` / `radius_km=2.4` per the corrected plan), then Gate A.

### 2026-09-22 15:20–16:38 UTC — Orchestrator session 2 (Opus) — Segments 0 and 1 complete

**Scope of this session, as instructed by the user:** complete S0.T1–S0.T3 and S1.T1–S1.T2, then stop. **Do not start Segment 2 or Gate A.** That instruction was honoured — Gate A has not been run and no Segment 2 work was started.

**Resumed from:** a clean tree on `main` at `ec26c01`, with every task row `pending`. Ran the §0.2 start protocol (CLAUDE.md, plan §0–§3, this file, `git status && git log`).

**Completed (5 tasks, 7 commits, each implemented on Sonnet and reviewed on Opus — no review ran on any other model):**
| Task | Commit(s) | Reviewer verdict |
|---|---|---|
| S0.T1 scaffold | `e46431e` | APPROVE, no Critical/Important |
| S0.T2 layer schemas | `3ddd99d`, `28e1809` | APPROVE, no Critical/Important |
| S0.T3 fixtures | `693315c` | APPROVE, no Critical; 2 Important items were orchestrator actions, both discharged in this file |
| S1.T1 LocalProjection | `26fd72b` | APPROVE, no Critical/Important |
| S1.T2 segment metrics | `7764393`, `40cf0b6` | APPROVE; 1 Important finding raised **and closed** by `40cf0b6` |

Final state: `uv run --no-sync pytest -q` → **`14 passed`**; `uv run --no-sync ruff check .` → **`All checks passed!`**; working tree clean apart from this file.

**Three things in the plan turned out to be wrong about the real service or data.** All three are recorded in full in the Decisions log:
1. **Layer 12 has no coverage within 1.5 km of the centre** (nearest vertex 2125.5 m), contradicting the plan's "Leach Hwy and Manning Rd corridors lie inside 1.5 km". Fixtures were re-recorded at 2.5 km and renamed `*_curtin2500.geojson`. **This cascades into ten places in the plan — see the ⚠ row in the Status table.**
2. **`GEOLOC.STLength()` is the live field name**, not `GEOLOCSTLength` as §3.3 writes it, and the live field order differs from `ORIGINAL_COLUMNS`. S4.T1/S4.T2 must rename and reorder explicitly.
3. **`ROAD_HIERARCHY`'s live values are `Distributor A` / `Distributor B`**, not "District Distributor A/B" as §2 line 146 claims; and **`SPEED_LIMIT` is a string with embedded units** (`60km/h`), not a number, with one free-text value that will never parse.

**A false blocker was raised and disproved.** The S0.T1 implementer reported `uv sync` as a hard PyPI network block and recommended marking the task `blocked`. The orchestrator re-tested rather than accepting it: `curl https://pypi.org/simple/shapely/` returned HTTP 200 in 8.3 s, and `UV_HTTP_TIMEOUT=180 uv sync` completed in 1 m 21 s. The cause was uv's default 30 s timeout against a slow link. **Standing instruction for future sessions: use `UV_HTTP_TIMEOUT=180 uv sync` on a cold venv and `uv run --no-sync` thereafter.**

**Process notes for the next session.** The plan's code snippets repeatedly violate the repo's own ruff config (`line-length = 110`, `select = ["E","F","I","B","UP"]`) — this bit S0.T2 (two over-length lines), S1.T1 (an unannounced **B905** `zip()` without `strict=`) and S1.T2 (a 114-char literal). **Warn every future implementer to measure line lengths and run ruff before committing**, and to report each wrap with proof of behavioural equivalence. Also: no commit in this session carries a `Co-Authored-By` trailer — verified individually with `git show -s --format=%B` on each. One implementer reported that a harness reminder actively tried to inject one; the repo rule correctly took precedence.

**Stopped at:** S1.T2 done, reviewed, committed and pushed. **Next action: S2.T1** (MRWAClient), then S2.T2, then Gate A.

### 2026-09-22 — Planning session (Fable 5.1)
- Read `init_prompt.md`; profiled the provided CSV (189,865 rows, all WA); two research agents verified MRWA REST endpoints, OSM/Google feasibility; Fable re-verified MapServer root and layer 12 schema.
- Asked the user four questions (width gaps, row shape, circle rule, CSV role) — answers recorded in Decisions log.
- Wrote `orchestrator_plan.md`, this tracker, repo `CLAUDE.md`, `.gitignore`; created the vault hub `05-Projects/DBE/DBE.md` and a decision note; initial commit on `main`.
- Stopped: planning complete. Next: user starts an Opus session with the prompt in `CLAUDE.md` → "Kick-off".
