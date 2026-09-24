"""Validation-only comparison against the user's provided statewide CSV. Skips when inputs are absent."""

import csv
from collections import Counter
from pathlib import Path

import pytest

from roadmapper import schema

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
    # Measured 1.0000 on 2026-09-23, with new_since_export = 0. It cannot be pinned to exactly 1.0:
    # roads Main Roads adds after the user's export legitimately will not appear in it. But 0.95 was
    # a placeholder, not a measurement — it would stay green while ~1,077 of 21,558 ids (5%) were
    # corrupted, which is precisely the failure mode the handoff lists as fixed elsewhere (Gate C,
    # finding I-1). 0.99 still allows ~1% genuine drift while catching corruption above ~215 ids.
    assert ratio >= 0.99, (
        f"only {ratio:.4f} of extracted ids exist in the provided export; "
        f"{len(extracted - provided)} are new or corrupted"
    )


def test_no_row_comes_from_outside_the_metropolitan_region():
    """Blank is not the same as wrong.

    Two rows of 21,643 in the live 10 km output ("Graham Farmer Fwy PSP", a Main Roads Controlled
    Path) carry an empty RA_NAME, RA_NO, LG_NO and LG_NAME — a gap in the source data that the
    2.5 km fixtures never exposed. The check that matters is that no OTHER region appears, which
    would mean the circle or the envelope had leaked.
    """
    with EXTRACTED.open(newline="", encoding="utf-8") as fh:
        regions = Counter(row["RA_NAME"] for row in csv.DictReader(fh))
    foreign = {name: n for name, n in regions.items() if name not in ("Metropolitan", "")}
    assert foreign == {}, f"rows from outside the Metropolitan region: {foreign}"
    assert regions["Metropolitan"] > 0
    print(f"\nregions: {dict(regions)}")
