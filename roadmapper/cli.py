"""Command-line interface: `roadmapper extract …` and `roadmapper to-xlsx …`."""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

from roadmapper import __version__, schema
from roadmapper.export import csv_to_xlsx, write_csv, write_json
from roadmapper.extract import NoRoadsFound, extract
from roadmapper.mrwa_client import MRWAClient, MRWAError  # MRWAClient is monkeypatched in tests

log = logging.getLogger("roadmapper")

ROADS_CSV = "roads.csv"
VERTICES_CSV = "roads_vertices.csv"
METADATA_JSON = "metadata.json"
ROADS_XLSX = "roads.xlsx"
QA_PLOT_PNG = "qa_plot.png"


def _positive(value: str) -> float:
    f = float(value)
    if not math.isfinite(f) or f <= 0:
        raise argparse.ArgumentTypeError("must be a finite number > 0")
    return f


def _latitude(value: str) -> float:
    f = float(value)
    if not math.isfinite(f) or not -90.0 <= f <= 90.0:
        raise argparse.ArgumentTypeError(
            f"{value} is not a latitude (-90 to 90); did you pass --lat and --lon in the wrong order?"
        )
    return f


def _longitude(value: str) -> float:
    f = float(value)
    if not math.isfinite(f) or not -180.0 <= f <= 180.0:
        raise argparse.ArgumentTypeError(
            f"{value} is not a longitude (-180 to 180); did you pass --lat and --lon in the wrong order?"
        )
    return f


def _remove_stale(path: Path) -> None:
    """Remove a leftover artifact from a previous run into the same --out.

    An artifact present in --out must belong to the run that just finished. When this run
    skips regenerating `path` (--no-plot / --no-xlsx), a file left over from an earlier run
    would silently disagree with the CSVs sitting next to it while looking current. Both
    qa_plot.png and roads.xlsx are fully regenerable from the CSVs, so removing a stale copy
    loses nothing. Only acts when the file exists; never logs otherwise.

    Best-effort, like the plot itself: this is housekeeping, and a failure to tidy up must not
    turn a successful extraction into an exit-1 failure after the CSVs are already written. But
    it must not be silent either — a stale file that could not be removed is exactly the
    misleading artifact this function exists to prevent, so the warning names it.
    """
    if not path.exists():
        return
    try:
        path.unlink()
    except OSError as exc:
        log.warning("could not remove stale %s from a previous run (%s); it does NOT describe "
                    "this run — delete it by hand", path, exc)
        return
    log.info("removed stale %s from a previous run (skipped this run)", path.name)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="roadmapper", description="Roads inside a circle, from Main Roads WA open data."
    )
    p.add_argument("--version", action="version", version=f"roadmapper {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    ex = sub.add_parser(
        "extract", help="query MRWA, write roads.csv / roads_vertices.csv / metadata.json (+ roads.xlsx)"
    )
    ex.add_argument("--lat", type=_latitude, required=True, help="centre latitude, e.g. -32.0018629")
    ex.add_argument("--lon", type=_longitude, required=True, help="centre longitude, e.g. 115.8924599")
    ex.add_argument("--radius-km", type=_positive, required=True, help="radius in kilometres, e.g. 10")
    ex.add_argument("--out", type=Path, default=Path("output/run"), help="output directory")
    ex.add_argument("--cache-dir", type=Path, default=None, help="raw API cache (default: <out>/cache)")
    ex.add_argument("--no-xlsx", action="store_true", help="skip the XLSX conversion")
    ex.add_argument("--no-plot", action="store_true", help="skip the QA plot (qa_plot.png)")
    ex.add_argument("--osm", action="store_true",
                    help="NOT IMPLEMENTED - OpenStreetMap enrichment was measured and skipped; "
                         "passing this flag is an error (see docs/task_docs/orchestrator_plan.md)")
    ex.add_argument("-v", "--verbose", action="store_true")
    ex.set_defaults(func=run_extract)

    tx = sub.add_parser(
        "to-xlsx", help="convert an existing roads.csv + roads_vertices.csv (+ metadata.json) to XLSX"
    )
    tx.add_argument("--roads", type=Path, required=True)
    tx.add_argument("--vertices", type=Path, required=True)
    tx.add_argument("--metadata", type=Path, required=True)
    tx.add_argument("--out", type=Path, required=True)
    tx.add_argument("-v", "--verbose", action="store_true")
    tx.set_defaults(func=run_to_xlsx)
    return p


def run_extract(args: argparse.Namespace) -> dict:
    if args.osm:
        raise ValueError(
            "--osm is not implemented. OpenStreetMap enrichment was skipped deliberately: in the "
            "reference 10 km circle only 0.97% of OSM ways carried a width tag, and OSM's ODbL licence "
            "would attach share-alike terms to your output. Re-run without --osm."
        )
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    cache_dir = args.cache_dir or (out / "cache")
    client = MRWAClient(cache_dir=cache_dir)
    result = extract(args.lat, args.lon, args.radius_km, source=client, with_osm=args.osm)
    roads_csv = write_csv(result.roads, schema.OUTPUT_COLUMNS, out / ROADS_CSV)
    vertices_csv = write_csv(result.vertices, schema.VERTEX_COLUMNS, out / VERTICES_CSV)
    metadata_json = write_json(result.metadata, out / METADATA_JSON)
    report = {
        "roads_csv": str(roads_csv),
        "vertices_csv": str(vertices_csv),
        "metadata_json": str(metadata_json),
        "segments": len(result.roads),
        "vertices": len(result.vertices),
    }
    if not args.no_plot:
        plot_png = out / QA_PLOT_PNG
        try:
            from roadmapper.plot import render_qa_plot

            render_qa_plot(roads_csv, metadata_json, plot_png)
            report["plot"] = str(plot_png)
            log.info("wrote %s", plot_png)
        except Exception as exc:  # best-effort: the CSVs are the deliverable, the plot is an aid
            # A stale PNG from an earlier run into the same --out, or a truncated one from a
            # savefig that died partway, must not be left behind: it would no longer be a
            # rendering of what this run just wrote.
            try:
                plot_png.unlink(missing_ok=True)
            except OSError as unlink_exc:
                log.warning("could not remove stale/partial %s: %s", plot_png, unlink_exc)
            report["plot"] = None
            report["plot_error"] = f"{type(exc).__name__}: {exc}"
            log.warning("QA plot not written (%s: %s); the CSVs are unaffected", type(exc).__name__, exc)
    else:
        _remove_stale(out / QA_PLOT_PNG)
    if not args.no_xlsx:
        xlsx_report = csv_to_xlsx(roads_csv, vertices_csv, metadata_json, out / ROADS_XLSX)
        report["xlsx"] = str(out / ROADS_XLSX)
        report["xlsx_sheets"] = xlsx_report["sheets"]
    else:
        _remove_stale(out / ROADS_XLSX)
    log.info("done: %s segments, %s vertices -> %s", len(result.roads), len(result.vertices), out)
    return report


def run_to_xlsx(args: argparse.Namespace) -> dict:
    report = csv_to_xlsx(args.roads, args.vertices, args.metadata, args.out)
    log.info("wrote %s (%s)", args.out, ", ".join(report["sheets"]))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on usage errors, 0 on --help/--version
        return int(exc.code or 0)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    # matplotlib logs every font it scores at DEBUG — thousands of lines that would bury the
    # extraction's own output under -v. Its warnings and errors still come through.
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    try:
        args.func(args)
        return 0
    except NoRoadsFound as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except MRWAError as exc:
        print(f"error: MRWA service problem: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
