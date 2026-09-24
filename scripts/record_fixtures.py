"""Record GeoJSON fixtures for a ~2.5 km box around Curtin's Design building. Network required.

Radius escalated from the plan's default 1500 m to 2500 m per task S0.T3 Step 2's documented
contingency: layer 12 (Pavement and Surfacing State) returns 0 features at 1500 m (confirmed live via
returnCountOnly, not just an empty page) but 113 features at 2500 m. Fixture filenames use the
`curtin2500` suffix to match; see tests/fixtures/README.md for the exact envelope recorded.
"""
import json
import math
import time
from pathlib import Path

import requests

BASE = "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
LAT, LON, RADIUS_M = -32.0018629, 115.8924599, 2500.0
LAYERS = [17, 12, 16, 8]
OUT = Path("tests/fixtures")
PAGE = 2000

dlat = RADIUS_M / 111_320.0
dlon = RADIUS_M / (111_320.0 * math.cos(math.radians(LAT)))
ENVELOPE = (LON - dlon, LAT - dlat, LON + dlon, LAT + dlat)


def fetch_all(layer_id: int) -> list[dict]:
    feats: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": "1=1",
            "geometry": ",".join(f"{v:.7f}" for v in ENVELOPE),
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*", "returnGeometry": "true", "outSR": 4326,
            "f": "geojson", "orderByFields": "OBJECTID ASC",
            "resultOffset": offset, "resultRecordCount": PAGE,
        }
        r = requests.post(f"{BASE}/{layer_id}/query", data=params, timeout=120,
                          headers={"User-Agent": "RoadMapper/0.1 fixture recorder"})
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"])
        page = data.get("features", [])
        feats.extend(page)
        print(f"layer {layer_id}: offset {offset} -> {len(page)} features")
        if len(page) < PAGE:
            return feats
        offset += len(page)
        time.sleep(0.3)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for layer_id in LAYERS:
        feats = fetch_all(layer_id)
        path = OUT / f"layer{layer_id}_curtin2500.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        print(f"wrote {path} ({path.stat().st_size / 1e6:.2f} MB, {len(feats)} features)")
    print("ENVELOPE =", ENVELOPE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
