"""
Build data/actuals.csv from the BlueRidge dashboard Excel template.

Run this whenever a fresh Excel template lands in data/. It normalizes the
schema so the Streamlit app can load it directly with pandas.read_csv.

Transformations:
- Header row is at Excel row 3 (index 2)
- Date column "Monthly (use 1st of month)" is renamed to "Date" and shifted
  to month-end (matching how the Streamlit app expects monthly rows)
- Win Rate and Utilization are stored as decimals (0.42); converted to
  percentages (42.0) to match the app's format
- Blank cells stay as NaN; the app treats NaN as "no data" rather than 0
- Division names are stripped
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).parent
DEFAULT_INPUT = DATA_DIR / "BlueRidge_Dashboard_Template-2026-03-18.xlsx"
DEFAULT_OUTPUT = DATA_DIR / "actuals.csv"

COLUMN_MAP = {
    "Monthly (use 1st of month)": "Date",
}
PERCENT_COLS = ["Win Rate", "Utilization"]


def build(input_path: Path, output_path: Path) -> pd.DataFrame:
    df = pd.read_excel(input_path, sheet_name="Data Entry", header=2, engine="openpyxl")
    df = df.rename(columns=COLUMN_MAP)

    df = df.dropna(subset=["Date", "Division"])
    df["Division"] = df["Division"].astype(str).str.strip()
    df["Date"] = pd.to_datetime(df["Date"]) + pd.offsets.MonthEnd(0)

    for col in PERCENT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce") * 100.0

    for col in df.columns:
        if col not in ("Date", "Division"):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_values(["Date", "Division"]).reset_index(drop=True)
    df.to_csv(output_path, index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()

    df = build(args.input, args.output)
    print(f"Wrote {args.output} ({len(df)} rows)")
    print(f"Divisions: {sorted(df['Division'].unique().tolist())}")
    print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")


if __name__ == "__main__":
    main()
