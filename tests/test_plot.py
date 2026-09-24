import json

from matplotlib.colors import to_hex

from roadmapper.plot import OTHER_STYLE, STYLES, _build_figure, _dash_for, render_qa_plot

ROADS_CSV = """NETWORK_TYPE,GEOMETRY_WKT
Local Road,"LINESTRING (115.89 -32.00, 115.891 -32.001)"
State Road,"LINESTRING (115.90 -32.01, 115.901 -32.011)"
Main Roads Controlled Path,"LINESTRING (115.88 -31.99, 115.881 -31.991)"
Miscellaneous Road,"LINESTRING (115.87 -31.98, 115.871 -31.981)"
Proposed Road,"LINESTRING (115.86 -31.97, 115.861 -31.971)"
Crossover,"LINESTRING (115.85 -31.96, 115.851 -31.961)"
"""

METADATA = {
    "centre_lat": -32.0018629,
    "centre_lon": 115.8924599,
    "radius_km": 2.4,
    "extracted_at_utc": "2026-09-22T00:00:00+00:00",
    "segments_intersecting": 6,
}


def _write_inputs(tmp_path):
    roads_csv = tmp_path / "roads.csv"
    roads_csv.write_text(ROADS_CSV)
    metadata_json = tmp_path / "metadata.json"
    metadata_json.write_text(json.dumps(METADATA))
    return roads_csv, metadata_json


def test_render_qa_plot_writes_a_real_png(tmp_path):
    roads_csv, metadata_json = _write_inputs(tmp_path)
    out_png = tmp_path / "qa_plot.png"
    result = render_qa_plot(roads_csv, metadata_json, out_png)
    assert result == out_png
    assert out_png.exists()
    data = out_png.read_bytes()
    assert len(data) > 1024, "PNG suspiciously small for a rendered plot"
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_palette_hex_values_are_pinned():
    """The colours were validated with a colour-blindness checker; pin them against silent drift."""
    assert STYLES["Local Road"][0] == "#2a78d6"
    assert STYLES["Miscellaneous Road"][0] == "#e87ba4"
    assert STYLES["State Road"][0] == "#4a3aa7"
    assert STYLES["Main Roads Controlled Path"][0] == "#008300"


def test_proposed_road_and_crossover_have_different_dashes():
    """A previous version gave both the same dash pattern, making their legend entries identical."""
    proposed = _dash_for("Proposed Road")
    crossover = _dash_for("Crossover")
    assert proposed != crossover


def test_line_widths_are_pinned():
    """Widths were chosen deliberately (State thickest, Local hairline); pin against drift."""
    assert STYLES["Local Road"][1] == 0.35
    assert STYLES["Miscellaneous Road"][1] == 0.9
    assert STYLES["State Road"][1] == 1.4
    assert STYLES["Main Roads Controlled Path"][1] == 0.9


def test_other_style_colour_is_pinned():
    assert OTHER_STYLE[0] == "#6b6a66"


def _collections_by_hex_colour(fig):
    """Map each LineCollection actually added to the axes to the hex colour it was drawn with.

    Reads the real Figure/axes, not the STYLES constants, so a bug that fails to pass zorder
    (or anything else) through to the LineCollection constructor is caught by inspecting the
    object matplotlib actually drew.
    """
    ax = fig.axes[0]
    by_colour = {}
    for lc in ax.collections:
        colour = to_hex(lc.get_color()[0])
        by_colour[colour] = lc
    return by_colour


def test_draw_order_controlled_path_above_state_above_local(tmp_path):
    """Controlled Paths run alongside the freeways; a thick State line on top would bury them."""
    roads_csv, metadata_json = _write_inputs(tmp_path)
    fig = _build_figure(roads_csv, metadata_json)
    by_colour = _collections_by_hex_colour(fig)

    local = by_colour[STYLES["Local Road"][0]]
    misc = by_colour[STYLES["Miscellaneous Road"][0]]
    state = by_colour[STYLES["State Road"][0]]
    controlled_path = by_colour[STYLES["Main Roads Controlled Path"][0]]

    assert controlled_path.get_zorder() > state.get_zorder() > local.get_zorder()

    # Pinned on the actual LineCollections drawn, not just the STYLES constants: a mutant that
    # drops `linewidths=lw` from the LineCollection call would leave every test above green
    # while silently reverting every road type to matplotlib's default width.
    assert local.get_linewidth()[0] == STYLES["Local Road"][1] == 0.35
    assert misc.get_linewidth()[0] == STYLES["Miscellaneous Road"][1] == 0.9
    assert state.get_linewidth()[0] == STYLES["State Road"][1] == 1.4
    assert controlled_path.get_linewidth()[0] == STYLES["Main Roads Controlled Path"][1] == 0.9


def test_multilinestring_both_parts_are_drawn(tmp_path):
    """A MULTILINESTRING road must contribute every part to its LineCollection, not just one."""
    roads_csv = tmp_path / "roads.csv"
    roads_csv.write_text(
        "NETWORK_TYPE,GEOMETRY_WKT\n"
        'Local Road,"MULTILINESTRING '
        '((115.89 -32.00, 115.891 -32.001), (115.90 -32.01, 115.901 -32.011))"\n'
    )
    metadata_json = tmp_path / "metadata.json"
    metadata_json.write_text(json.dumps(METADATA))

    fig = _build_figure(roads_csv, metadata_json)
    [lc] = fig.axes[0].collections
    assert len(lc.get_segments()) == 2
