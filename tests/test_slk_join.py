import pytest

from dbe.slk_join import (
    SlkSpan,
    cwy_compatible,
    dominant_value,
    index_by_road,
    overlap_len,
    overlapping,
    span_from_properties,
    weighted_mean,
)


def _span(road, cwy, s, e, **attrs):
    return SlkSpan(road, cwy, s, e, attrs)


def test_overlap_len_basic_cases():
    assert overlap_len(0, 1, 0.5, 2) == pytest.approx(0.5)
    assert overlap_len(0.5, 2, 0, 1) == pytest.approx(0.5)
    assert overlap_len(0, 1, 1, 2) == 0.0
    assert overlap_len(0, 1, 2, 3) == 0.0
    assert overlap_len(1, 0, 0.25, 0.75) == pytest.approx(0.5)  # reversed input tolerated


def test_cwy_compatible():
    assert cwy_compatible("Left", "Left")
    assert cwy_compatible("Left", "Single") and cwy_compatible("Single", "Right")
    assert not cwy_compatible("Left", "Right")


def test_span_from_properties_handles_missing_and_bad_values():
    assert span_from_properties({"ROAD": "H001", "START_SLK": "0", "END_SLK": 0.3}) == _span(
        "H001", "Single", 0.0, 0.3
    )
    assert span_from_properties({"ROAD": "H001", "CWY": "", "START_SLK": 0, "END_SLK": 1}).cwy == "Single"
    assert span_from_properties({"ROAD": "H001", "START_SLK": None, "END_SLK": 1}) is None
    assert span_from_properties({"START_SLK": 0, "END_SLK": 1}) is None
    assert span_from_properties({"ROAD": "H001", "START_SLK": "abc", "END_SLK": 1}) is None


def test_overlapping_prefers_exact_cwy_over_single():
    sources = index_by_road([
        _span("H001", "Single", 0, 10, w=5.0),
        _span("H001", "Left", 0, 10, w=7.0),
        _span("H002", "Left", 0, 10, w=9.0),
    ])
    target = _span("H001", "Left", 2, 4)
    matched = overlapping(target, sources)
    assert [s.attrs["w"] for s, _ in matched] == [7.0]
    target_right = _span("H001", "Right", 2, 4)
    assert [s.attrs["w"] for s, _ in overlapping(target_right, sources)] == [5.0]  # only the Single fallback


def test_overlapping_zero_length_target_matches_containing_span():
    sources = index_by_road([_span("H001", "Single", 0, 1, w=1.0), _span("H001", "Single", 1, 2, w=2.0)])
    matched = overlapping(_span("H001", "Single", 1.5, 1.5), sources)
    assert [(s.attrs["w"], ov) for s, ov in matched] == [(2.0, 1.0)]


def test_dominant_value_picks_largest_overlap_and_skips_nulls():
    sources = index_by_road([
        _span("H001", "Single", 0, 0.4, h="Access Road"),
        _span("H001", "Single", 0.4, 2.0, h="Distributor"),
        _span("H001", "Single", 0, 2.0, h=None),
    ])
    assert dominant_value(_span("H001", "Single", 0.0, 1.0), sources, "h") == "Distributor"
    assert dominant_value(_span("H999", "Single", 0.0, 1.0), sources, "h") is None


def test_weighted_mean_uses_overlap_weights():
    sources = index_by_road([
        _span("H001", "Single", 0, 1, w=10.0),
        _span("H001", "Single", 1, 4, w=20.0),
        _span("H001", "Single", 0, 4, w="not a number"),
    ])
    # target 0..2 overlaps 1 km of w=10 and 1 km of w=20 -> 15
    assert weighted_mean(_span("H001", "Single", 0, 2), sources, "w") == pytest.approx(15.0)
    # target 0..4 -> (10*1 + 20*3)/4 = 17.5
    assert weighted_mean(_span("H001", "Single", 0, 4), sources, "w") == pytest.approx(17.5)
    assert weighted_mean(_span("H001", "Single", 5, 6), sources, "w") is None


def test_span_from_properties_rejects_non_finite_slk():
    for bad in (float("nan"), float("inf"), float("-inf"), "NaN", "inf", "-Infinity"):
        assert span_from_properties({"ROAD": "H001", "START_SLK": bad, "END_SLK": 1.0}) is None
        assert span_from_properties({"ROAD": "H001", "START_SLK": 0.0, "END_SLK": bad}) is None


def test_non_finite_source_span_cannot_hijack_the_join():
    """A NaN span scores FULL-target overlap, so it outranks every genuine span.

    `overlap_len` uses max/min, which fall through on NaN: `overlap_len(0, 9, nan, nan)` returns
    9.0, the largest weight any span can score — the hazard, asserted directly below. The single
    defence is `span_from_properties`, which refuses to build such a span, so one never reaches
    the index. Nothing downstream would stop it: a NaN span with finite attributes wins every
    comparison and reports 6.72 m and 1 lane instead of 10.44 m and 4.
    """
    good = [
        _span("H001", "Single", 0.0, 5.0, TOTAL_SEAL_WIDTH=10.0, NO_OF_LANES=4),
        _span("H001", "Single", 5.0, 9.0, TOTAL_SEAL_WIDTH=11.0, NO_OF_LANES=4),
    ]
    target = _span("H001", "Single", 0.0, 9.0)

    # The defence: the factory refuses to admit a non-finite span.
    corrupt_props = {"ROAD": "H001", "CWY": "Single", "START_SLK": float("nan"),
                     "END_SLK": float("nan"), "TOTAL_SEAL_WIDTH": 3.0, "NO_OF_LANES": 1}
    assert span_from_properties(corrupt_props) is None, "a non-finite span must never enter the index"

    # The hazard it prevents: a NaN span scores the maximum possible overlap weight.
    hijacker = _span("H001", "Single", float("nan"), float("nan"), TOTAL_SEAL_WIDTH=3.0, NO_OF_LANES=1)
    assert overlap_len(0.0, 9.0, hijacker.start_slk, hijacker.end_slk) == pytest.approx(9.0)
    sources = index_by_road(good)
    assert weighted_mean(target, sources, "TOTAL_SEAL_WIDTH") == pytest.approx(10.444444, rel=1e-5)
    assert dominant_value(target, sources, "NO_OF_LANES") == 4


def test_non_finite_attribute_value_is_skipped_not_averaged():
    """Both non-finite guards are load-bearing and each is pinned in this suite.

    `_present` rejects a float NaN. It cannot reject the *string* "nan", which is a perfectly
    ordinary non-empty string — only the `math.isfinite` check inside `weighted_mean`'s loop
    stops that one. Without it a single corrupt span poisons the whole segment's mean, not just
    its own term, which would put a wrong width in the output.
    """
    sources = index_by_road([
        _span("H001", "Single", 0.0, 1.0, w=8.0),
        _span("H001", "Single", 1.0, 2.0, w=float("nan")),
        _span("H001", "Single", 2.0, 3.0, w="nan"),
    ])
    result = weighted_mean(_span("H001", "Single", 0.0, 3.0), sources, "w")
    assert result == pytest.approx(8.0), "a NaN attribute must be skipped, never propagated"


def test_zero_is_data_not_absence():
    """A zero shoulder width or zero lane count is a real measurement and must survive.

    `_present` uses `value != ""` rather than a truthiness test precisely so that 0 is kept;
    mutating it to `bool(value)` previously survived the whole suite.
    """
    sources = index_by_road([_span("H001", "Single", 0.0, 1.0, shoulder=0.0, lanes=0, flag=False)])
    target = _span("H001", "Single", 0.0, 1.0)
    assert dominant_value(target, sources, "shoulder") == 0.0
    assert dominant_value(target, sources, "lanes") == 0
    assert dominant_value(target, sources, "flag") is False
    assert weighted_mean(target, sources, "shoulder") == 0.0
    blank = index_by_road([_span("H002", "Single", 0.0, 1.0, shoulder="", other=None)])
    assert dominant_value(_span("H002", "Single", 0.0, 1.0), blank, "shoulder") is None
    assert dominant_value(_span("H002", "Single", 0.0, 1.0), blank, "other") is None


def test_non_finite_attribute_never_reaches_dominant_value():
    """`dominant_value` feeds NO_OF_LANES, KERB_L/R, ROAD_HIERARCHY and SPEED_LIMIT.

    A NaN here would be written to the CSV as the literal "nan" — a bogus lane count rather
    than a blank. Strings and legitimate zeros must still come through untouched.
    """
    nan, inf = float("nan"), float("inf")
    sources = index_by_road([
        _span("H001", "Single", 0.0, 1.0, lanes=nan, big=inf, kerb="Yes", zero=0),
    ])
    target = _span("H001", "Single", 0.0, 1.0)
    assert dominant_value(target, sources, "lanes") is None
    assert dominant_value(target, sources, "big") is None
    assert dominant_value(target, sources, "kerb") == "Yes"
    assert dominant_value(target, sources, "zero") == 0


def test_non_finite_span_does_not_mask_a_good_one():
    """The good value must win, not merely survive — a NaN must not shadow a real reading."""
    sources = index_by_road([
        _span("H001", "Single", 0.0, 2.0, lanes=float("nan")),
        _span("H001", "Single", 0.0, 1.0, lanes=2),
    ])
    assert dominant_value(_span("H001", "Single", 0.0, 2.0), sources, "lanes") == 2
