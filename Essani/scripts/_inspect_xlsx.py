"""Quick inspection of the Excel files at project root to understand layout."""
import sys
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

files = [
    "odoo_corrigido.xlsx",
    "odoo_corrigido_remapped.xlsx",
    "ids in main.xlsx",
]

for f in files:
    p = ROOT / f
    if not p.exists():
        print(f"!! Missing: {f}")
        continue
    print(f"\n========== {f} ==========")
    try:
        xl = pd.ExcelFile(p)
        print("Sheets:", xl.sheet_names)
        for s in xl.sheet_names:
            df = pd.read_excel(p, sheet_name=s, nrows=5)
            print(f"\n-- Sheet [{s}] -- shape head:", df.shape, " columns:")
            for c in df.columns:
                print(f"   - {c!r}")
            print("first rows:")
            print(df.head(3).to_string(max_colwidth=40))
    except Exception as exc:
        print(f"error reading {f}: {exc}")
