"""Re-render the QA plot for an existing `dbe extract` output directory.

`dbe extract` now writes qa_plot.png automatically (unless run with --no-plot); this
script exists to re-render one after the fact, e.g. after editing the styling in
`dbe/plot.py`.
"""

import argparse
from pathlib import Path

from dbe.plot import render_qa_plot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out-dir", type=Path, required=True, help="directory holding roads.csv and metadata.json"
    )
    args = ap.parse_args()
    out = render_qa_plot(
        args.out_dir / "roads.csv", args.out_dir / "metadata.json", args.out_dir / "qa_plot.png"
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
