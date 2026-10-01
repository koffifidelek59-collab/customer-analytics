#!/usr/bin/env python3
"""Analyze data-quality alerts from clean dataset or existing JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from etl.run_etl import run_quality_alerts, transform, extract  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Analyze customer data quality alerts")
    ap.add_argument("--clean", type=Path, default=ROOT / "data" / "customers_clean.csv")
    ap.add_argument("--raw", type=Path, default=ROOT / "data" / "customers_raw.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "quality_alerts.json")
    args = ap.parse_args(argv)

    if args.clean.exists():
        df = pd.read_csv(args.clean)
        audit = {"duplicate_ids_removed": 0, "invalid_dates": int(df["DateInvalid"].sum()) if "DateInvalid" in df.columns else 0}
    else:
        raw = extract(args.raw)
        df, audit = transform(raw)

    result = run_quality_alerts(df, audit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Status: {result['status']}")
    print(result["analysis"]["headline"])
    print("\nAlerts:")
    for a in result["alerts"]:
        print(f"  [{a['severity'].upper()}] {a['title']}: {a['message']}")
    print("\nPriority actions:")
    for i, act in enumerate(result["analysis"]["priority_actions"], 1):
        print(f"  {i}. {act}")

    return 2 if result["status"] == "ALERT" else (1 if result["status"] == "WARN" else 0)


if __name__ == "__main__":
    sys.exit(main())
