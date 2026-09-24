from roadmapper import schema
from roadmapper.enrich import ENRICH_COLUMNS

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
