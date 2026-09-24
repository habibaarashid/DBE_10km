"""Writers: CSV (source of truth), metadata JSON, and CSV → XLSX conversion."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from roadmapper import schema

log = logging.getLogger(__name__)

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_CELL_CHARS = 32_767
_TRUNCATE_AT = 32_700
_TRUNCATE_MARK = "…TRUNCATED"


def write_csv(rows: list[dict[str, Any]], columns: list[str], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: ("" if row.get(c) is None else row.get(c)) for c in columns})
    return path


def write_json(obj: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    return path


def _read_csv(path: Path) -> pd.DataFrame:
    """Read a produced CSV back without pandas reinterpreting its contents.

    `keep_default_na=False, na_values=[""]` is LOAD-BEARING, not incidental. With pandas'
    defaults, the literal text "nan" (and "NA", "null", "None", "N/A" …) is coerced to a missing
    value, so a road genuinely named or labelled with one of those strings would silently become
    blank in the XLSX while the CSV still showed it. Only an empty cell means absent here.
    Do not "simplify" these kwargs away — see the S3.T1 fix review, MINOR-3.
    """
    dtype = {c: str for c in schema.ID_COLUMNS}
    # float_precision="round_trip" parses each number exactly as float(<csv text>); the default fast
    # parser is off by ~1e-14 on tens of thousands of cells. The XLSX writer still serialises to 16
    # significant digits, so workbook cells agree with the CSV to ~1e-14 relative, not bit-exactly.
    return pd.read_csv(
        path,
        dtype=dtype,
        keep_default_na=False,
        na_values=[""],
        encoding="utf-8",
        float_precision="round_trip",
    )


def _require_header(path: Path, expected: list[str], label: str) -> None:
    """Refuse a CSV whose header is not the schema's: to-xlsx must never mislabel a sheet."""
    with Path(path).open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh), [])
    if header != expected:
        raise ValueError(
            f"{label} {path} does not have the expected columns (starts {header[:3]}, expected "
            f"{expected[:3]}); are --roads and --vertices swapped?"
        )


def _truncate_long_cells(df: pd.DataFrame) -> int:
    count = 0
    for col in df.columns:
        if not (pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object):
            # pandas 3 uses a dedicated `str` dtype, so `!= object` alone would skip every text column
            continue
        lengths = df[col].astype(str).str.len()
        mask = lengths > EXCEL_MAX_CELL_CHARS
        if mask.any():
            count += int(mask.sum())
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.slice(0, _TRUNCATE_AT) + _TRUNCATE_MARK
    return count


def csv_to_xlsx(
    roads_csv: Path, vertices_csv: Path, metadata_json: Path, xlsx_path: Path, max_rows: int = EXCEL_MAX_ROWS
) -> dict[str, Any]:
    _require_header(roads_csv, schema.OUTPUT_COLUMNS, "roads CSV")
    _require_header(vertices_csv, schema.VERTEX_COLUMNS, "vertices CSV")
    if not Path(metadata_json).exists():
        raise ValueError(f"metadata file not found: {metadata_json}")
    roads = _read_csv(Path(roads_csv))
    vertices = _read_csv(Path(vertices_csv))
    metadata = json.loads(Path(metadata_json).read_text(encoding="utf-8"))
    truncated = _truncate_long_cells(roads)
    chunk = max(1, max_rows - 1)  # header occupies one row
    sheets: list[str] = []
    xlsx_path = Path(xlsx_path)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as xw:
        roads.to_excel(xw, sheet_name="roads", index=False)
        sheets.append("roads")
        for i, start in enumerate(range(0, max(len(vertices), 1), chunk)):
            name = "vertices" if i == 0 else f"vertices_{i + 1}"
            vertices.iloc[start : start + chunk].to_excel(xw, sheet_name=name, index=False)
            sheets.append(name)
        meta_rows = [(k, json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in metadata.items()]
        pd.DataFrame(meta_rows, columns=["key", "value"]).to_excel(xw, sheet_name="metadata", index=False)
        sheets.append("metadata")
    if truncated:
        log.warning(
            "%s cell(s) exceeded Excel's %s-char limit and were truncated in the XLSX (CSV is complete)",
            truncated,
            EXCEL_MAX_CELL_CHARS,
        )
    return {
        "sheets": sheets,
        "roads_rows": int(len(roads)),
        "vertices_rows": int(len(vertices)),
        "truncated_cells": truncated,
    }
