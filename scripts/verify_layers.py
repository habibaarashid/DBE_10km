"""Fetch layer metadata for the four MRWA layers and print a schema summary. Network required."""

import json
import sys
from pathlib import Path

import requests

BASE = "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
LAYERS = {
    17: "Road Network",
    12: "Pavement and Surfacing State",
    16: "Road Hierarchy",
    8: "Legal Speed Limit",
}
OUT = Path("tests/fixtures")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for layer_id, expected_name in LAYERS.items():
        r = requests.get(
            f"{BASE}/{layer_id}",
            params={"f": "pjson"},
            timeout=60,
            headers={"User-Agent": "DBE/0.1 schema check"},
        )
        r.raise_for_status()
        meta = r.json()
        (OUT / f"layer{layer_id}_metadata.json").write_text(json.dumps(meta, indent=2))
        fields = [f["name"] for f in meta.get("fields", [])]
        adv = meta.get("advancedQueryCapabilities", {})
        wkid = meta.get("extent", {}).get("spatialReference", {}).get("wkid")
        print(f"\n== layer {layer_id}: {meta.get('name')} (expected '{expected_name}')")
        print(
            f"   geometryType={meta.get('geometryType')} wkid={wkid}"
            f" maxRecordCount={meta.get('maxRecordCount')}"
        )
        print(
            f"   supportsPagination={adv.get('supportsPagination')}"
            f" supportsOrderBy={adv.get('supportsOrderBy')}"
            f" supportsStatistics={adv.get('supportsStatistics')}"
        )
        print(f"   fields ({len(fields)}): {', '.join(fields)}")
        if meta.get("name") != expected_name:
            print("   !! NAME MISMATCH", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
