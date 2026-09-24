import pytest

from dbe.geometry import LocalProjection
from dbe.mrwa_client import LAYER_ROAD_NETWORK, MRWAClient

pytestmark = pytest.mark.network


def test_live_small_envelope_returns_roads():
    proj = LocalProjection(-32.0018629, 115.8924599)
    env = proj.envelope_wgs84(300.0)
    feats = MRWAClient(sleep_s=0).query_envelope(LAYER_ROAD_NETWORK, env)
    assert len(feats) >= 1
    assert feats[0]["geometry"]["type"] in ("LineString", "MultiLineString")
    assert "ROAD" in feats[0]["properties"]
