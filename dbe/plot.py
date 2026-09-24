"""Render roads.csv as a PNG for reviewers.

Segments are coloured by NETWORK_TYPE with the query circle drawn in black. Called by
`dbe extract` (best-effort, after the CSVs and metadata.json are written) and by
`scripts/qa_plot.py` for re-rendering an existing output directory.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.figure import Figure
from shapely import wkt

from dbe.geometry import LocalProjection

# Colours are the validated default palette of the dataviz skill, checked with its validator in
# `--pairs all` mode. On a map any road type can sit beside any other, so every pair must stay
# distinguishable, not just neighbours in the legend. Result for these four: worst colour-blind
# separation 13.0 (magenta vs blue, target >= 8), worst normal-vision separation 16.3 (violet vs
# blue, floor 15).
#
# The previous palette failed: its grey for Miscellaneous roads read as colourless and scored 11.6
# against the Local blue, below the floor even for full colour vision. The best contrast-only
# alternative (blue, green, violet, red) was rejected because its weakest pair was red vs green at
# 7.2 — the classic colour-blind confusion, and exactly the pair that would sit side by side if
# state highways were red and the paths running beside them green.
#
# Draw order and line weight are part of the fix, not decoration. Types were previously drawn
# alphabetically, which put State Roads last and on top of the Controlled Paths that parallel them,
# burying the path. Now the paths draw last. Every type but State was also drawn at the same hairline
# as the 19,741 local streets, so the two small categories vanished into the grid.
#
#   type                          colour     width  zorder  role
STYLES = {
    "Local Road": ("#2a78d6", 0.35, 1),  # blue: the dense background grid, thinnest
    "Miscellaneous Road": ("#e87ba4", 0.9, 2),  # magenta: campus, carpark and industrial roads
    "State Road": ("#4a3aa7", 1.4, 3),  # violet: the arterial skeleton, thickest
    "Main Roads Controlled Path": ("#008300", 0.9, 4),  # green: drawn last so it shows beside State
}
# Proposed Road and Crossover are rare (34 and 3 records statewide; none in the Curtin run). A fifth
# and sixth hue would exceed what the palette validates on all pairs, so they share one neutral and
# are told apart by line pattern instead: from the four hues above by being patterned at all, and
# from each other by a different pattern. (A first version gave both the same dash, which made their
# two legend entries identical — the exact problem this palette exists to fix.) Any other unexpected
# type falls back to the same neutral with a dash-dot pattern.
OTHER_STYLE = ("#6b6a66", 0.9, 5)
OTHER_DASHES = {
    "Proposed Road": (0, (4, 2)),  # dashed
    "Crossover": (0, (1, 1.5)),  # dotted
}
OTHER_DASH_FALLBACK = (0, (4, 1.5, 1, 1.5))  # dash-dot
LEGEND_ORDER = ["State Road", "Local Road", "Main Roads Controlled Path", "Miscellaneous Road"]


def _dash_for(ntype: str):
    """Solid for the four validated hues; a distinct pattern for each rare neutral type."""
    if ntype in STYLES:
        return "solid"
    return OTHER_DASHES.get(ntype, OTHER_DASH_FALLBACK)


def _build_figure(roads_csv: Path, metadata_json: Path) -> Figure:
    """Build the QA Figure from `roads_csv` + `metadata_json` (read from disk).

    Factored out of `render_qa_plot` so tests can inspect the drawn Figure itself — e.g. the
    actual zorder/geometry of each `LineCollection` added to the axes — rather than only the
    STYLES constants that are supposed to produce it.
    """
    roads_csv = Path(roads_csv)
    metadata_json = Path(metadata_json)

    roads = pd.read_csv(
        roads_csv,
        usecols=["NETWORK_TYPE", "GEOMETRY_WKT"],
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    meta = json.loads(metadata_json.read_text())

    fig = Figure(figsize=(10, 10), dpi=150)
    ax = fig.subplots()
    counts = roads["NETWORK_TYPE"].value_counts()
    for ntype, group in roads.groupby("NETWORK_TYPE"):
        colour, lw, z = STYLES.get(ntype, OTHER_STYLE)
        dash = _dash_for(ntype)
        segments = []
        for w in group["GEOMETRY_WKT"]:
            geom = wkt.loads(w)
            parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
            for part in parts:
                segments.append(list(part.coords))
        # Round caps match the original solid_capstyle="round" only for solid lines; on a dashed
        # LineCollection a round cap grows each dash by ~1 linewidth and shrinks each gap to match
        # (dash-collection capstyle is not split into solid/dash the way Line2D's is), which would
        # visually collapse the short dash/dot patterns that tell Proposed Road and Crossover apart.
        capstyle = "round" if dash == "solid" else "butt"
        lc = LineCollection(
            segments, colors=colour, linewidths=lw, linestyles=dash, zorder=z, capstyle=capstyle
        )
        ax.add_collection(lc)
    # Legend in a fixed, meaningful order rather than groupby's alphabetical one. Types absent from
    # this run are omitted, so the legend never advertises a colour the map does not use.
    for ntype in LEGEND_ORDER + sorted(set(counts.index) - set(LEGEND_ORDER)):
        if ntype not in counts:
            continue
        colour, _, _ = STYLES.get(ntype, OTHER_STYLE)
        ax.plot([], [], color=colour, linewidth=2.5, linestyle=_dash_for(ntype),
                label=f"{ntype} ({counts[ntype]:,})")
    proj = LocalProjection(meta["centre_lat"], meta["centre_lon"])
    ring = proj.to_wgs84(proj.circle(meta["radius_km"] * 1000.0)).exterior
    ax.plot(*ring.xy, color="black", linewidth=1.2, linestyle="--", label=f"{meta['radius_km']} km radius")
    ax.plot(meta["centre_lon"], meta["centre_lat"], marker="+", color="black", markersize=12)
    ax.set_aspect(1.0 / math.cos(math.radians(meta["centre_lat"])))
    ax.autoscale_view()
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(
        f"DBE — {meta['segments_intersecting']} segments, extracted {meta['extracted_at_utc']}"
    )
    ax.legend(loc="lower left", fontsize=8, frameon=True)
    fig.tight_layout()
    return fig


def render_qa_plot(roads_csv: Path, metadata_json: Path, out_png: Path) -> Path:
    """Render `roads_csv` + `metadata_json` (read from disk) to a QA PNG at `out_png`."""
    out_png = Path(out_png)
    fig = _build_figure(roads_csv, metadata_json)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    return out_png
