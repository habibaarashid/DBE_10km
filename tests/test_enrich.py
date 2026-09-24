import pytest

from roadmapper.enrich import ENRICH_COLUMNS, EnrichIndex, enrich_segment

EXPECTED_COLUMNS = [
    "ROAD_HIERARCHY", "SPEED_LIMIT", "TOTAL_PAVE_WIDTH_M", "TOTAL_SEAL_WIDTH_M", "TRAFFICABLE_SURF_WIDTH_M",
    "NO_OF_LANES", "SEALED_SHOULDER_L_M", "SEALED_SHOULDER_R_M", "KERB_L", "KERB_R", "WIDTH_M",
    "WIDTH_SOURCE",
]


def _f(**props):
    return {"type": "Feature", "geometry": None, "properties": props}


def _index():
    pavement = [
        _f(ROAD="H001", CWY="Left", START_SLK=0.0, END_SLK=1.0, TOTAL_PAVE_WIDTH=12.0, TOTAL_SEAL_WIDTH=10.0,
           TRAFFICABLE_SURF_WIDTH=9.0, NO_OF_LANES=3, SEALED_SHOULDER_L=0.5, SEALED_SHOULDER_R=1.0,
           KERB_L="Y", KERB_R="N"),
        _f(ROAD="H001", CWY="Left", START_SLK=1.0, END_SLK=3.0, TOTAL_PAVE_WIDTH=8.0, TOTAL_SEAL_WIDTH=7.0,
           TRAFFICABLE_SURF_WIDTH=7.0, NO_OF_LANES=2, SEALED_SHOULDER_L=0.0, SEALED_SHOULDER_R=0.0,
           KERB_L="N", KERB_R="N"),
    ]
    hierarchy = [
        _f(ROAD="H001", CWY="Single", START_SLK=0.0, END_SLK=5.0, ROAD_HIERARCHY="Primary Distributor"),
        _f(ROAD="1010001", CWY="Single", START_SLK=0.0, END_SLK=5.0, ROAD_HIERARCHY="Access Road"),
    ]
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
    # These five columns previously had their key asserted but never their value, so dropping a
    # mapping or swapping left for right passed the whole suite. See the S3.T2 review.
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

    The output must still carry all twelve keys in order — a later task builds CSV rows straight
    from these keys, so a missing one would shift every subsequent column in the file.
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
    idx = EnrichIndex.from_features(
        fixture_source.layers[12], fixture_source.layers[16], fixture_source.layers[8])
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
