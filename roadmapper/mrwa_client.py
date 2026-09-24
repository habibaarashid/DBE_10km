"""Thin client for the Main Roads WA ArcGIS REST MapServer (open data, anonymous)."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger(__name__)

BASE_URL = (
    "https://gisservices.mainroads.wa.gov.au/arcgis/rest/services/OpenData/RoadAssets_DataPortal/MapServer"
)
LAYER_ROAD_NETWORK = 17
LAYER_PAVEMENT = 12
LAYER_HIERARCHY = 16
LAYER_SPEED = 8
PAGE_SIZE = 2000
USER_AGENT = "RoadMapper/0.1 (research tool; https://github.com/habibaarashid)"
TRANSIENT_STATUS = {429, 500, 502, 503, 504}
LENGTH_FIELD_ALIASES = ("GEOLOC.STLength()", "Shape__Length", "SHAPE.STLength()")
MAX_PAGES = 10_000

Envelope = tuple[float, float, float, float]


class MRWAError(RuntimeError):
    """Non-retryable error (bad request, schema problem, or retries exhausted)."""


class MRWATransientError(MRWAError):
    """Raised once a transient failure has exhausted its retries."""


def normalise_properties(props: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with the server's length field renamed to the CSV's GEOLOCSTLength."""
    out = dict(props)
    for alias in LENGTH_FIELD_ALIASES:
        if alias in out:
            out["GEOLOCSTLength"] = out.pop(alias)
            break
    return out


class MRWAClient:
    def __init__(
        self,
        session: Any | None = None,
        base_url: str = BASE_URL,
        page_size: int = PAGE_SIZE,
        cache_dir: Path | None = None,
        sleep_s: float = 0.2,
        max_retries: int = 5,
        timeout_s: float = 90.0,
    ) -> None:
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")
        self.page_size = int(page_size)
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.sleep_s = sleep_s
        self.max_retries = int(max_retries)
        self.timeout_s = timeout_s
        self._headers = {"User-Agent": USER_AGENT}

    # -- public -------------------------------------------------------------------------------

    def layer_metadata(self, layer_id: int) -> dict[str, Any]:
        return self._request("GET", f"{self.base_url}/{layer_id}", {"f": "pjson"})

    def query_envelope(
        self, layer_id: int, envelope: Envelope, out_fields: str = "*"
    ) -> list[dict[str, Any]]:
        xmin, ymin, xmax, ymax = envelope
        base = {
            "where": "1=1",
            "geometry": f"{xmin},{ymin},{xmax},{ymax}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": out_fields,
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
            "orderByFields": "OBJECTID ASC",
            "resultRecordCount": self.page_size,
        }
        url = f"{self.base_url}/{layer_id}/query"
        features: list[dict[str, Any]] = []
        offset = 0
        for page in range(MAX_PAGES):
            data = self._request("POST", url, {**base, "resultOffset": offset})
            page_feats = data.get("features", []) or []
            features.extend(page_feats)
            exceeded = bool(
                data.get("exceededTransferLimit") or data.get("properties", {}).get("exceededTransferLimit")
            )
            log.info(
                "layer %s page %s: %s features (offset %s, exceeded=%s)",
                layer_id,
                page,
                len(page_feats),
                offset,
                exceeded,
            )
            if not page_feats or (len(page_feats) < self.page_size and not exceeded):
                break
            offset += len(page_feats)
            if self.sleep_s:
                time.sleep(self.sleep_s)
        else:
            raise MRWAError(f"layer {layer_id}: exceeded {MAX_PAGES} pages; paging is not terminating")
        return features

    # -- internals ----------------------------------------------------------------------------

    def _request(self, method: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
        cache_path = self._cache_path(method, url, params)
        if cache_path is not None and cache_path.exists():
            try:
                return json.loads(cache_path.read_text())
            except (ValueError, OSError) as exc:
                log.warning("discarding unreadable cache entry %s (%s); refetching", cache_path.name, exc)
                cache_path.unlink(missing_ok=True)
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, params=params, timeout=self.timeout_s, headers=self._headers)
                else:
                    resp = self.session.post(url, data=params, timeout=self.timeout_s, headers=self._headers)
                if resp.status_code in TRANSIENT_STATUS:
                    raise MRWATransientError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "error" in data:
                    raise MRWAError(f"ArcGIS error from {url}: {data['error']}")
                if cache_path is not None:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = cache_path.with_suffix(".json.tmp")
                    tmp.write_text(json.dumps(data))
                    tmp.replace(cache_path)
                return data
            except MRWATransientError as exc:
                last_exc = exc
            except (requests.RequestException, ValueError) as exc:  # ValueError covers bad JSON
                last_exc = exc
            wait = min(2**attempt, 16)
            log.warning(
                "%s %s failed (%s); retry %s/%s in %ss",
                method,
                url,
                last_exc,
                attempt + 1,
                self.max_retries,
                wait,
            )
            if self.sleep_s:
                time.sleep(wait)
        raise MRWATransientError(f"giving up on {url} after {self.max_retries} attempts: {last_exc}")

    def _cache_path(self, method: str, url: str, params: dict[str, Any]) -> Path | None:
        if self.cache_dir is None:
            return None
        key_src = json.dumps([method, url, sorted((k, str(v)) for k, v in params.items())])
        key = hashlib.sha1(key_src.encode()).hexdigest()[:20]
        return self.cache_dir / f"{key}.json"
