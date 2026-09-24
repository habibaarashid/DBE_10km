import json
from pathlib import Path

import pytest
import requests

import dbe.mrwa_client
from dbe.mrwa_client import (
    LAYER_ROAD_NETWORK,
    MRWAClient,
    MRWAError,
    MRWATransientError,
    normalise_properties,
)

ENV = (115.88, -32.01, 115.90, -31.99)


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """Serves a scripted list of responses; records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.methods = []

    def _next(self, method, url, payload):
        self.methods.append(method)
        self.calls.append((url, payload))
        if not self.responses:
            raise AssertionError("no scripted response left")
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def get(self, url, params=None, timeout=None, headers=None):
        return self._next("GET", url, params)

    def post(self, url, data=None, timeout=None, headers=None):
        return self._next("POST", url, data)


def _feat(oid):
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[115.89, -32.0], [115.891, -32.0]],
        },
        "properties": {"OBJECTID": oid, "ROAD": "H001"},
    }


def _page(oids, exceeded=None):
    body = {"type": "FeatureCollection", "features": [_feat(o) for o in oids]}
    if exceeded is not None:
        body["exceededTransferLimit"] = exceeded
    return FakeResponse(body)


def test_pages_until_short_page():
    session = FakeSession([_page(range(3), exceeded=True), _page(range(3, 5))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    feats = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert [f["properties"]["OBJECTID"] for f in feats] == [0, 1, 2, 3, 4]
    assert len(session.calls) == 2
    url, params = session.calls[1]
    assert url.endswith("/17/query")
    assert params["resultOffset"] == 3 and params["resultRecordCount"] == 3
    assert params["f"] == "geojson" and params["outSR"] == 4326 and params["inSR"] == 4326
    assert params["geometryType"] == "esriGeometryEnvelope"
    assert params["geometry"] == "115.88,-32.01,115.9,-31.99"
    assert params["orderByFields"] == "OBJECTID ASC"
    assert session.methods == ["POST", "POST"]


def test_single_short_page_stops_immediately():
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    assert len(client.query_envelope(LAYER_ROAD_NETWORK, ENV)) == 2
    assert len(session.calls) == 1


def test_retries_transient_then_succeeds():
    session = FakeSession([FakeResponse({}, status=503), requests.ConnectionError("boom"), _page(range(1))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=5)
    assert len(client.query_envelope(LAYER_ROAD_NETWORK, ENV)) == 1
    assert len(session.calls) == 3


def test_gives_up_after_max_retries():
    session = FakeSession([FakeResponse({}, status=503)] * 3)
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=3)
    with pytest.raises(MRWATransientError):
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)


def test_arcgis_error_body_raises_without_retry():
    session = FakeSession([FakeResponse({"error": {"code": 400, "message": "Invalid parameter"}})])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, max_retries=5)
    with pytest.raises(MRWAError) as exc:
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert "Invalid parameter" in str(exc.value)
    assert len(session.calls) == 1


def test_cache_hit_skips_network(tmp_path):
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, cache_dir=tmp_path)
    first = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert len(list(tmp_path.glob("*.json"))) == 1
    client2 = MRWAClient(session=FakeSession([]), page_size=3, sleep_s=0, cache_dir=tmp_path)
    second = client2.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert first == second


def test_paged_query_caches_each_page_separately(tmp_path):
    session = FakeSession([_page(range(3), exceeded=True), _page(range(3, 5))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, cache_dir=tmp_path)
    feats = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert [f["properties"]["OBJECTID"] for f in feats] == [0, 1, 2, 3, 4]
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_layer_metadata_uses_get_pjson():
    session = FakeSession([FakeResponse({"name": "Road Network", "fields": []})])
    client = MRWAClient(session=session, sleep_s=0)
    meta = client.layer_metadata(17)
    assert meta["name"] == "Road Network"
    url, params = session.calls[0]
    assert url.endswith("/17") and params == {"f": "pjson"}
    assert session.methods == ["GET"]


def test_normalise_properties_renames_length_field():
    props = {"OBJECTID": 1, "GEOLOC.STLength()": 0.0003}
    out = normalise_properties(props)
    assert out == {"OBJECTID": 1, "GEOLOCSTLength": 0.0003}
    assert "GEOLOC.STLength()" in props  # original untouched
    assert normalise_properties({"GEOLOCSTLength": 1.0}) == {"GEOLOCSTLength": 1.0}


def test_exceeded_flag_under_properties_continues_paging():
    short_but_more = FakeResponse(
        {
            "type": "FeatureCollection",
            "features": [_feat(o) for o in range(3)],
            "properties": {"exceededTransferLimit": True},
        }
    )
    session = FakeSession([short_but_more, _page(range(3, 5))])
    client = MRWAClient(session=session, page_size=5, sleep_s=0)
    feats = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert [f["properties"]["OBJECTID"] for f in feats] == [0, 1, 2, 3, 4]
    assert len(session.calls) == 2
    assert session.calls[1][1]["resultOffset"] == 3


def test_empty_page_terminates_even_with_exceeded_flag_set():
    session = FakeSession([_page(range(3), exceeded=True), _page([], exceeded=True)])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    feats = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert [f["properties"]["OBJECTID"] for f in feats] == [0, 1, 2]
    assert len(session.calls) == 2


def test_max_pages_guard_raises_mrwa_error(monkeypatch):
    monkeypatch.setattr(dbe.mrwa_client, "MAX_PAGES", 2)
    session = FakeSession([_page(range(3), exceeded=True), _page(range(3, 6), exceeded=True)])
    client = MRWAClient(session=session, page_size=3, sleep_s=0)
    with pytest.raises(MRWAError) as exc:
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert "exceeded" in str(exc.value) and "pages" in str(exc.value)
    assert not isinstance(exc.value, MRWATransientError)


def test_corrupt_cache_entry_is_discarded_and_refetched(tmp_path):
    """A truncated cache file must not be permanently fatal.

    Before this guard the JSONDecodeError escaped `_request` entirely and the network was never
    attempted, so one interrupted write poisoned that page for every later run.
    """
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, cache_dir=tmp_path)
    first = client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    entry = next(iter(tmp_path.glob("*.json")))
    entry.write_text('{"type": "FeatureColl')  # truncated mid-write

    session2 = FakeSession([_page(range(2))])
    client2 = MRWAClient(session=session2, page_size=3, sleep_s=0, cache_dir=tmp_path)
    second = client2.query_envelope(LAYER_ROAD_NETWORK, ENV)
    assert second == first
    assert len(session2.calls) == 1, "the network must be retried, not skipped"
    assert json.loads(entry.read_text())  # the entry was rewritten and is valid again


def test_a_crashed_cache_write_never_leaves_a_truncated_entry(tmp_path, monkeypatch):
    """The cache must be crash-safe, not merely tidy.

    An earlier version of this test only checked that no `.tmp` file was left behind, which is
    trivially true when the non-atomic code never creates one — it passed with the fix reverted.
    This simulates the real hazard instead: a write that dies half-way through. Under the atomic
    write the wreckage lands on the temp file and anything under the real name stays valid; under
    a direct write the cache entry itself is left truncated and poisons every later run.
    """
    session = FakeSession([_page(range(2))])
    client = MRWAClient(session=session, page_size=3, sleep_s=0, cache_dir=tmp_path)
    real_write = Path.write_text

    def crashing_write(self, data, *args, **kwargs):
        real_write(self, data[: len(data) // 2])
        raise OSError("simulated interruption")

    monkeypatch.setattr(Path, "write_text", crashing_write)
    with pytest.raises(OSError):
        client.query_envelope(LAYER_ROAD_NETWORK, ENV)
    for leftover in tmp_path.glob("*.json"):
        json.loads(leftover.read_text())
