"""Metre-accurate local geometry via an azimuthal-equidistant projection centred on the query point."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import shapely
from pyproj import CRS, Transformer
from shapely.geometry import LineString, MultiLineString, Point, Polygon, shape
from shapely.ops import transform as _shp_transform

WGS84 = CRS.from_epsg(4326)


class LocalProjection:
    """Azimuthal equidistant projection centred on (lat, lon); units are metres, centre is (0, 0)."""

    def __init__(self, lat: float, lon: float) -> None:
        self.lat = float(lat)
        self.lon = float(lon)
        proj4 = f"+proj=aeqd +lat_0={self.lat} +lon_0={self.lon} +datum=WGS84 +units=m +no_defs"
        self.crs = CRS.from_proj4(proj4)
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
    """Metrics of one segment against the query circle.

    `circle_local` must be `LocalProjection.circle(radius_m)`: a buffer of the origin, so its
    radius is read back exactly from its bounds (buffer vertices sit on the axes). Inclusion is
    decided by the exact distance to the centre, not by intersecting the polygon: the polygon is
    a 256-gon *inscribed* in the true circle, 0.753 m short of it at 10 km, and the first review
    of the 10 km run found two streets sitting in that band (9,999.9 m from the centre) that the
    polygon test excluded. `INSIDE_FRACTION` still uses the polygon, so it can under-count up to
    ~0.75 m of length per boundary crossing at 10 km (worst observed 0.043 on the reference run),
    and a segment included only inside that band reports 0.0.
    """
    radius_m = float(circle_local.bounds[2])
    local = proj.to_local(geom_wgs84)
    length = float(local.length)
    inter = local.intersection(circle_local)
    inside_len = 0.0 if inter.is_empty else float(inter.length)
    dist = float(local.distance(Point(0.0, 0.0)))
    parts = _parts(geom_wgs84)
    first = parts[0].coords[0]
    last = parts[-1].coords[-1]
    return SegmentMetrics(
        intersects=dist <= radius_m,
        length_m=length,
        inside_fraction=(inside_len / length) if length > 0 else 0.0,
        dist_to_centre_m=dist,
        start_lat=float(first[1]),
        start_lon=float(first[0]),
        end_lat=float(last[1]),
        end_lon=float(last[0]),
        vertex_count=sum(len(p.coords) for p in parts),
        wkt=shapely.to_wkt(geom_wgs84, rounding_precision=7),
    )
