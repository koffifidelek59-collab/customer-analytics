#!/usr/bin/env python3
"""
Customer Analytics — Task 9
ETL Pipeline (Extract → Transform → Load)
Author: KOUAME Koffi Fidèle · Senior Data Analyst

Usage:
  python etl/run_etl.py
  python etl/run_etl.py --source data/customers_raw.csv --out data/customers_clean.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "customers_raw.csv"
DEFAULT_OUT = ROOT / "data" / "customers_clean.csv"
DEFAULT_AUDIT = ROOT / "results" / "etl_audit.json"
DEFAULT_QUALITY = ROOT / "results" / "quality_alerts.json"

AGE_MIN, AGE_MAX = 1, 100
RATING_MIN, RATING_MAX = 1, 5


def extract(path: Path) -> pd.DataFrame:
    """Extract: load raw extract and drop pure junk columns."""
    if not path.exists():
        # fallback: try common names
        alt = ROOT / "data" / "Customers_Fakedata.csv"
        if alt.exists():
            path = alt
        else:
            raise FileNotFoundError(f"Source not found: {path}")
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    # drop unnamed / empty columns
    drop_cols = [c for c in df.columns if str(c).startswith("Unnamed") or str(c).strip() == ""]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Transform: cleaning rules + derived fields. Returns clean df + audit dict."""
    audit = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "rows_in": int(len(df)),
        "rules": [],
    }
    out = df.copy()

    # Standard column names (tolerant)
    rename = {}
    for c in out.columns:
        cl = c.strip().lower().replace(" ", "")
        if cl in {"customerid", "customer_id", "id"}:
            rename[c] = "CustomerID"
        elif cl in {"name", "customername"}:
            rename[c] = "Name"
        elif cl in {"email", "e-mail"}:
            rename[c] = "Email"
        elif cl == "age":
            rename[c] = "Age"
        elif cl == "gender":
            rename[c] = "Gender"
        elif cl in {"productcategory", "category", "product"}:
            rename[c] = "ProductCategory"
        elif cl in {"purchaseamount", "amount", "price"}:
            rename[c] = "PurchaseAmount"
        elif cl in {"purchasedate", "date"}:
            rename[c] = "PurchaseDate"
        elif cl == "rating":
            rename[c] = "Rating"
    out = out.rename(columns=rename)

    # Collapse duplicate column names (keep first)
    if out.columns.duplicated().any():
        out = out.loc[:, ~out.columns.duplicated()].copy()

    # Duplicates on CustomerID
    before = len(out)
    if "CustomerID" in out.columns:
        out = out.drop_duplicates(subset=["CustomerID"], keep="first")
    dupes = before - len(out)
    audit["rules"].append({"rule": "drop_duplicate_customer_id", "removed": int(dupes)})
    audit["duplicate_ids_removed"] = int(dupes)

    # Gender standardize
    if "Gender" in out.columns:
        gser = out["Gender"]
        if isinstance(gser, pd.DataFrame):
            gser = gser.iloc[:, 0]
        g = gser.astype(str).str.strip().str.lower()
        mapped = g.map({
            "m": "Male", "male": "Male", "man": "Male",
            "f": "Female", "female": "Female", "woman": "Female",
        })
        out["Gender"] = mapped
        audit["rules"].append({"rule": "standardize_gender", "known": int(mapped.notna().sum())})

    # Age domain
    if "Age" in out.columns:
        age = pd.to_numeric(out["Age"], errors="coerce")
        invalid_age = int(((age < AGE_MIN) | (age > AGE_MAX)).sum())
        age = age.where(age.between(AGE_MIN, AGE_MAX))
        out["Age"] = age
        audit["rules"].append({"rule": "age_domain_1_100", "invalidated": invalid_age})
        audit["invalid_ages"] = invalid_age

    # Rating domain
    if "Rating" in out.columns:
        r = pd.to_numeric(out["Rating"], errors="coerce")
        invalid_r = int(((r < RATING_MIN) | (r > RATING_MAX)).sum())
        r = r.where(r.between(RATING_MIN, RATING_MAX))
        out["Rating"] = r
        audit["rules"].append({"rule": "rating_domain_1_5", "invalidated": invalid_r})
        audit["invalid_ratings"] = invalid_r

    # Amount
    if "PurchaseAmount" in out.columns:
        amt = pd.to_numeric(out["PurchaseAmount"], errors="coerce")
        out["PurchaseAmount"] = amt
        out["AmountMissing"] = amt.isna()
        audit["missing_amount"] = int(amt.isna().sum())

    # Dates
    if "PurchaseDate" in out.columns:
        raw = out["PurchaseDate"]
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=False)
        # flag impossible / unparsed
        out["DateInvalid"] = parsed.isna() & raw.notna()
        # also mark clearly absurd years if parsed
        if parsed.notna().any():
            bad_year = parsed.dt.year.lt(1990) | parsed.dt.year.gt(2035)
            out.loc[bad_year.fillna(False), "DateInvalid"] = True
            parsed = parsed.where(~bad_year)
        out["PurchaseMonth"] = parsed.dt.month
        out["PurchaseMonthName"] = parsed.dt.month.map({
            1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
            7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
        }, na_action="ignore")
        # string date only for valid
        out["PurchaseDate"] = parsed.dt.strftime("%Y-%m-%d")
        out.loc[out["DateInvalid"], "PurchaseDate"] = pd.NA
        out.loc[out["DateInvalid"], "PurchaseMonth"] = pd.NA
        out.loc[out["DateInvalid"], "PurchaseMonthName"] = pd.NA
        audit["invalid_dates"] = int(out["DateInvalid"].sum())
        audit["rules"].append({"rule": "date_parse_and_flag", "invalid_dates": audit["invalid_dates"]})

    # Category
    if "ProductCategory" in out.columns:
        cat = out["ProductCategory"]
        cat = cat.where(cat.notna(), other=pd.NA)
        cat = cat.astype("string").str.strip()
        cat = cat.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NaN": pd.NA, "<NA>": pd.NA})
        out["ProductCategory"] = cat.fillna("Unknown")
        audit["unknown_category"] = int((out["ProductCategory"] == "Unknown").sum())
        audit["rules"].append({"rule": "category_unknown_fill", "unknown": audit["unknown_category"]})

    # Age band
    if "Age" in out.columns:
        bins = [0, 18, 30, 45, 60, 75, 200]
        labels = ["0-18", "19-30", "31-45", "46-60", "61-75", "76+"]
        band = pd.cut(out["Age"], bins=bins, labels=labels, right=True)
        out["AgeBand"] = band.astype(object).where(band.notna(), "Unknown")
        out["AgeBand"] = out["AgeBand"].astype(str)
        out.loc[out["Age"].isna(), "AgeBand"] = "Unknown"

    audit["rows_out"] = int(len(out))
    audit["finished_at"] = datetime.now(timezone.utc).isoformat()
    return out, audit


def load(df: pd.DataFrame, path: Path) -> None:
    """Load: write clean dataset."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def run_quality_alerts(df: pd.DataFrame, audit: dict) -> dict:
    """Analyze data-quality alerts against policy thresholds."""
    n = max(len(df), 1)
    invalid_dates = int(df["DateInvalid"].sum()) if "DateInvalid" in df.columns else int(audit.get("invalid_dates", 0))
    unknown_cat = int((df["ProductCategory"] == "Unknown").sum()) if "ProductCategory" in df.columns else 0
    missing_amt = int(df["PurchaseAmount"].isna().sum()) if "PurchaseAmount" in df.columns else 0
    missing_age = int(df["Age"].isna().sum()) if "Age" in df.columns else 0
    missing_rating = int(df["Rating"].isna().sum()) if "Rating" in df.columns else 0

    metrics = {
        "rows": int(len(df)),
        "invalid_dates_count": invalid_dates,
        "invalid_dates_pct": round(100 * invalid_dates / n, 2),
        "unknown_category_count": unknown_cat,
        "unknown_category_pct": round(100 * unknown_cat / n, 2),
        "missing_amount_pct": round(100 * missing_amt / n, 2),
        "missing_age_pct": round(100 * missing_age / n, 2),
        "missing_rating_pct": round(100 * missing_rating / n, 2),
        "duplicate_ids_removed": int(audit.get("duplicate_ids_removed", 0)),
    }

    # Policy thresholds
    rules = [
        {
            "id": "invalid_dates",
            "title": "Invalid purchase dates",
            "severity": "high",
            "threshold_pct": 3.0,
            "value_pct": metrics["invalid_dates_pct"],
            "breached": metrics["invalid_dates_pct"] >= 3.0,
            "message": f"{metrics['invalid_dates_count']} rows ({metrics['invalid_dates_pct']}%) have invalid dates.",
            "recommendation": "Enforce ISO date validation at POS / ingestion; exclude flagged rows from trend KPIs.",
        },
        {
            "id": "unknown_category",
            "title": "Unknown product category",
            "severity": "high",
            "threshold_pct": 20.0,
            "value_pct": metrics["unknown_category_pct"],
            "breached": metrics["unknown_category_pct"] >= 20.0,
            "message": f"{metrics['unknown_category_count']} rows ({metrics['unknown_category_pct']}%) are Unknown category.",
            "recommendation": "Mandatory category at capture before merchandising or assortment decisions.",
        },
        {
            "id": "missing_age",
            "title": "Missing age after domain purge",
            "severity": "medium",
            "threshold_pct": 30.0,
            "value_pct": metrics["missing_age_pct"],
            "breached": metrics["missing_age_pct"] >= 30.0,
            "message": f"{metrics['missing_age_pct']}% of ages missing after removing values outside 1–100.",
            "recommendation": "Block ages outside 1–100 at entry; re-collect for critical segments.",
        },
        {
            "id": "missing_rating",
            "title": "Missing / invalid ratings",
            "severity": "medium",
            "threshold_pct": 25.0,
            "value_pct": metrics["missing_rating_pct"],
            "breached": metrics["missing_rating_pct"] >= 25.0,
            "message": f"{metrics['missing_rating_pct']}% ratings missing after restricting to 1–5.",
            "recommendation": "Constrain rating widget to 1–5; monitor completion rate.",
        },
        {
            "id": "missing_amount",
            "title": "Missing purchase amount",
            "severity": "high",
            "threshold_pct": 5.0,
            "value_pct": metrics["missing_amount_pct"],
            "breached": metrics["missing_amount_pct"] >= 5.0,
            "message": f"{metrics['missing_amount_pct']}% of amounts are missing.",
            "recommendation": "Amount required for closed transactions.",
        },
        {
            "id": "duplicates",
            "title": "Duplicate CustomerIDs in source",
            "severity": "medium",
            "threshold_count": 1,
            "value_count": metrics["duplicate_ids_removed"],
            "breached": metrics["duplicate_ids_removed"] >= 1,
            "message": f"{metrics['duplicate_ids_removed']} duplicate CustomerIDs removed at ETL.",
            "recommendation": "Enforce unique CustomerID in upstream system.",
        },
    ]

    alerts = []
    for r in rules:
        if r.get("breached"):
            alerts.append({
                "id": r["id"],
                "title": r["title"],
                "severity": r["severity"],
                "message": r["message"],
                "recommendation": r["recommendation"],
                "threshold": {k: r[k] for k in r if k.startswith("threshold")},
                "value": {k: r[k] for k in r if k.startswith("value")},
            })

    high = sum(1 for a in alerts if a["severity"] == "high")
    med = sum(1 for a in alerts if a["severity"] == "medium")
    if high > 0:
        status = "ALERT"
    elif med > 0:
        status = "WARN"
    else:
        status = "OK"

    result = {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_alerts": len(alerts),
            "high": high,
            "medium": med,
            "low": 0,
        },
        "metrics": metrics,
        "policy_rules": rules,
        "alerts": alerts,
        "analysis": {
            "headline": (
                f"Data quality status is {status}. "
                f"{len(alerts)} policy rule(s) breached "
                f"({high} high, {med} medium)."
            ),
            "priority_actions": [a["recommendation"] for a in alerts if a["severity"] == "high"][:5]
            or [a["recommendation"] for a in alerts][:3],
            "kpi_impact": [
                "Trend KPIs must exclude DateInvalid rows.",
                "Category revenue share is biased while Unknown remains elevated.",
                "Age-band analysis is limited by missing age after domain purge.",
            ],
        },
    }
    return result


def run(source: Path, out: Path, audit_path: Path, quality_path: Path) -> int:
    print("=== Customer Analytics ETL ===")
    print(f"Extract: {source}")
    raw = extract(source)
    print(f"  rows_in={len(raw)}")

    clean, audit = transform(raw)
    print(f"Transform: rows_out={len(clean)} · duplicates_removed={audit.get('duplicate_ids_removed', 0)}")

    load(clean, out)
    print(f"Load: {out}")

    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"Audit: {audit_path}")

    quality = run_quality_alerts(clean, audit)
    quality_path.write_text(json.dumps(quality, indent=2), encoding="utf-8")
    print(f"Quality: {quality_path} · status={quality['status']} · alerts={quality['summary']['total_alerts']}")

    # Human-readable analysis
    analysis_md = ROOT / "results" / "QUALITY_ALERTS_ANALYSIS.md"
    lines = [
        "# Data quality alerts — analysis",
        "",
        f"**Status:** `{quality['status']}`  ",
        f"**Generated:** {quality['generated_at']}",
        "",
        quality["analysis"]["headline"],
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|--------|------:|",
    ]
    for k, v in quality["metrics"].items():
        lines.append(f"| {k} | {v} |")
    lines += ["", "## Breached rules", ""]
    if not quality["alerts"]:
        lines.append("No threshold breaches.")
    for a in quality["alerts"]:
        lines += [
            f"### [{a['severity'].upper()}] {a['title']}",
            "",
            a["message"],
            "",
            f"**Recommendation:** {a['recommendation']}",
            "",
        ]
    lines += ["## Priority actions", ""]
    for i, act in enumerate(quality["analysis"]["priority_actions"], 1):
        lines.append(f"{i}. {act}")
    lines += ["", "## KPI impact", ""]
    for x in quality["analysis"]["kpi_impact"]:
        lines.append(f"- {x}")
    analysis_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Analysis: {analysis_md}")

    # exit code for CI
    return 2 if quality["status"] == "ALERT" else (1 if quality["status"] == "WARN" else 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Customer Analytics ETL + quality alerts")
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    ap.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    args = ap.parse_args(argv)
    try:
        code = run(args.source, args.out, args.audit, args.quality)
    except Exception as e:
        print(f"ETL failed: {e}", file=sys.stderr)
        return 3
    return code


if __name__ == "__main__":
    sys.exit(main())
