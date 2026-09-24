import math

import pytest
from shapely.geometry import LineString, MultiLineString, Point

from roadmapper.geometry import LocalProjection, geojson_to_line, iter_vertices, segment_metrics

CURTIN = (-32.0018629, 115.8924599)


def test_centre_maps_to_origin():
    proj = LocalProjection(*CURTIN)
    p = proj.to_local(Point(CURTIN[1], CURTIN[0]))  # shapely is (x=lon, y=lat)
    assert abs(p.x) < 1e-6 and abs(p.y) < 1e-6


def test_roundtrip_wgs84():
    proj = LocalProjection(*CURTIN)
    line = LineString([(115.88, -32.0), (115.9, -32.01)])
    back = proj.to_wgs84(proj.to_local(line))
    for (x0, y0), (x1, y1) in zip(line.coords, back.coords, strict=True):
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


def _proj_and_circle(radius_m=1000.0):
    proj = LocalProjection(*CURTIN)
    return proj, proj.circle(radius_m)


def _offset_line(proj, dx0, dy0, dx1, dy1):
    """Build a WGS84 line from local-metre offsets around the centre."""
    return proj.to_wgs84(LineString([(dx0, dy0), (dx1, dy1)]))


def test_geojson_to_line_accepts_line_and_multiline():
    ls = geojson_to_line({"type": "LineString", "coordinates": [[115.89, -32.0], [115.9, -32.0]]})
    assert ls.geom_type == "LineString"
    ml_coords = [[[115.89, -32.0], [115.9, -32.0]], [[115.9, -32.0], [115.91, -32.01]]]
    ml = geojson_to_line({"type": "MultiLineString", "coordinates": ml_coords})
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


def test_wkt_rounds_coordinates_to_seven_decimal_places():
    # Input has more decimal places than the WKT rounding_precision, so the rendered
    # WKT differs at precision 2 (rounds more coarsely) and at precision 12 (keeps
    # them all) from the expected precision-7 output below. This pins the parameter
    # itself, unlike a coordinate such as 115.89 whose trailing zeros render
    # identically at every precision.
    proj, circle = _proj_and_circle()
    line = LineString([(115.89245991234, -32.00186291234), (115.9, -32.0)])
    m = segment_metrics(line, proj, circle)
    assert m.wkt == "LINESTRING (115.8924599 -32.0018629, 115.9 -32)"


def test_multiline_start_is_first_part_end_is_last_part():
    proj, circle = _proj_and_circle()
    ml = MultiLineString([[(115.89, -32.0), (115.895, -32.0)], [(115.9, -32.0), (115.91, -32.01)]])
    m = segment_metrics(ml, proj, circle)
    assert (m.start_lon, m.start_lat) == (115.89, -32.0)
    assert (m.end_lon, m.end_lat) == (115.91, -32.01)
    assert m.vertex_count == 4
    assert m.wkt.startswith("MULTILINESTRING")


def test_circle_bounds_give_back_the_radius_exactly():
    proj, circle = _proj_and_circle(10_000.0)
    assert circle.bounds[2] == 10_000.0  # segment_metrics reads the radius from here


def test_segment_in_the_polygon_sagitta_band_is_included_by_exact_distance():
    """The 256-gon is inscribed: mid-chord it sits 0.753 m inside the true 10 km circle. Two real
    streets lay in that band in the 10 km run and were dropped, so inclusion must use the circle."""
    proj, circle = _proj_and_circle(10_000.0)
    theta = math.pi / 256  # mid-chord azimuth, where the polygon is furthest inside the circle
    # 0.05 m either side of the circle; the two real streets were 0.088 m inside it
    for factor, expected in ((0.999995, True), (1.000005, False)):
        r = 10_000.0 * factor
        cx, cy = r * math.cos(theta), r * math.sin(theta)
        tx, ty = -math.sin(theta) * 5.0, math.cos(theta) * 5.0  # short tangential segment
        line = _offset_line(proj, cx - tx, cy - ty, cx + tx, cy + ty)
        m = segment_metrics(line, proj, circle)
        assert m.intersects is expected, (factor, m.dist_to_centre_m)
        assert not circle.intersects(proj.to_local(line))  # the polygon test rejects both
        if expected:
            assert m.inside_fraction == 0.0  # included inside the band: nothing overlaps the polygon
