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
