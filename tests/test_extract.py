import copy

import pytest

from roadmapper import schema
from roadmapper.extract import ExtractResult, NoRoadsFound, extract
from roadmapper.geometry import LocalProjection
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


def test_empty_coordinates_geometry_is_skipped_not_crashed(fixture_source, curtin_2400):
    feats = copy.deepcopy(fixture_source.layers[17])
    feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": []},
                  "properties": {"OBJECTID": -2, "ROAD": "X", "CWY": "Single"}})
    src = FixtureSource({**fixture_source.layers, 17: feats})
    res = extract(source=src, **curtin_2400)
    assert res.metadata["skipped_no_geometry"] == 1


def test_all_four_layers_receive_the_same_correct_envelope(fixture_source, curtin_2400):
    extract(source=fixture_source, **curtin_2400)
    proj = LocalProjection(curtin_2400["lat"], curtin_2400["lon"])
    expected = proj.envelope_wgs84(curtin_2400["radius_km"] * 1000.0)
    assert [layer for layer, _ in fixture_source.calls] == [17, 12, 16, 8]
    for _, env in fixture_source.calls:
        assert env == pytest.approx(expected)


def test_malformed_geometry_shapes_are_skipped_not_crashed(fixture_source, curtin_2400):
    """Four shapes that each abort the run if unguarded.

    The earlier guard tested only that `coordinates` was truthy, which these all satisfy. They
    raise from shapely or GEOS instead, which is why the conversion is wrapped rather than the
    shapes enumerated.
    """
    bad = [
        {"type": "LineString", "coordinates": [[115.89, -32.0]]},
        {"type": "MultiLineString", "coordinates": [[]]},
        {"type": "MultiLineString", "coordinates": [[[115.89, -32.0]]]},
        {"type": "Point", "coordinates": [115.89, -32.0]},
    ]
    feats = copy.deepcopy(fixture_source.layers[17])
    for i, geom in enumerate(bad):
        feats.append({"type": "Feature", "geometry": geom,
                      "properties": {"OBJECTID": -100 - i, "ROAD": "X", "CWY": "Single"}})
    src = FixtureSource({**fixture_source.layers, 17: feats})
    res = extract(source=src, **curtin_2400)
    assert res.metadata["skipped_bad_geometry"] == 4
    assert res.metadata["skipped_no_geometry"] == 0
    assert len(res.roads) == 1262


def test_duplicate_enrichment_spans_are_not_double_weighted(fixture_source, curtin_2400):
    """A span repeated by live paging must not be counted twice in the width average.

    Layer 17 has always been de-duplicated; layers 12/16/8 were not, so a duplicate skewed the
    overlap-weighted mean. The live 10 km run returned 135/376/111 duplicates on those layers.
    """
    baseline = extract(source=fixture_source, **curtin_2400)
    doubled = copy.deepcopy(fixture_source.layers[12]) * 2
    src = FixtureSource({**fixture_source.layers, 12: doubled})
    res = extract(source=src, **curtin_2400)
    assert res.metadata["enrich_duplicates_dropped"] == len(fixture_source.layers[12])
    base_w = {r["OBJECTID"]: r["WIDTH_M"] for r in baseline.roads}
    assert all(r["WIDTH_M"] == base_w[r["OBJECTID"]] for r in res.roads), (
        "duplicated pavement spans must not change any width"
    )


def test_a_geometryless_twin_does_not_suppress_the_real_feature(fixture_source, curtin_2400):
    """A malformed copy arriving first must not consume the OBJECTID.

    Previously `seen.add` ran before the geometry guard, so the good feature that followed was
    discarded as a duplicate and the row count silently dropped by one.
    """
    feats = copy.deepcopy(fixture_source.layers[17])
    real = feats[0]
    twin = {"type": "Feature", "geometry": None, "properties": dict(real["properties"])}
    src = FixtureSource({**fixture_source.layers, 17: [twin, *feats]})
    res = extract(source=src, **curtin_2400)
    assert res.metadata["skipped_no_geometry"] == 1
    assert len(res.roads) == 1262, "the real feature must still be emitted"
    assert any(r["OBJECTID"] == real["properties"]["OBJECTID"] for r in res.roads)


def test_metadata_never_claims_osm_ran(fixture_source, curtin_2400):
    """`osm_enabled` must be False even when the parameter is passed directly.

    The CLI now refuses the flag, but `extract()` is importable, and a metadata file claiming OSM
    ran when it did not is worse than one that says nothing.
    """
    res = extract(source=fixture_source, with_osm=True, **curtin_2400)
    assert res.metadata["osm_enabled"] is False
    assert res.metadata["osm_attribution"] is None
    assert all(r["OSM_WAY_ID"] is None for r in res.roads)
