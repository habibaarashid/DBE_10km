from dbe.mrwa_client import normalise_properties
from tests.conftest import load_fixture

EXPECTED_17 = [
    "ROAD", "ROAD_NAME", "COMMON_USAGE_NAME", "START_SLK", "END_SLK", "CWY", "START_TRUE_DIST",
    "END_TRUE_DIST", "NETWORK_TYPE", "RA_NO", "RA_NAME", "LG_NO", "LG_NAME", "START_NODE_NO",
    "START_NODE_NAME", "END_NODE_NO", "END_NODE_NAME", "DATUM_NE_ID", "NM_BEGIN_MP", "NM_END_MP",
    "NETWORK_ELEMENT", "ROUTE_NE_ID", "OBJECTID", "GlobalID", "GEOLOCSTLength",
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
