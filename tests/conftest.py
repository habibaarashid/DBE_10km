import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
CURTIN = dict(lat=-32.0018629, lon=115.8924599, radius_km=2.4)


def load_fixture(layer_id: int) -> list[dict]:
    path = FIXTURES / f"layer{layer_id}_curtin2500.geojson"
    return json.loads(path.read_text())["features"]


class FixtureSource:
    """Duck-typed stand-in for MRWAClient that serves recorded features."""

    def __init__(self, layers: dict[int, list[dict]]):
        self.layers = layers
        self.calls: list[tuple[int, tuple]] = []

    def query_envelope(self, layer_id: int, envelope, out_fields: str = "*") -> list[dict]:
        self.calls.append((layer_id, tuple(envelope)))
        return list(self.layers.get(layer_id, []))


@pytest.fixture(scope="session")
def fixture_source() -> FixtureSource:
    return FixtureSource({lid: load_fixture(lid) for lid in (17, 12, 16, 8)})


@pytest.fixture(autouse=True)
def _reset_fixture_source_calls(request):
    """Clear FixtureSource.calls before each test.

    `fixture_source` is session-scoped for speed, so without this its `.calls` log would
    accumulate across tests and `calls[0]` would refer to some earlier test's first call.
    """
    if "fixture_source" in request.fixturenames:
        request.getfixturevalue("fixture_source").calls.clear()


@pytest.fixture
def curtin_2400() -> dict:
    return dict(CURTIN)
