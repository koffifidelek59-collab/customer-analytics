"""
Automated Data Quality Alerts
Evaluates cleaning residual risk against configurable thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CLEAN_CSV = DATA / "customers_clean.csv"
SUMMARY_JSON = DATA / "analysis_summary.json"
ALERTS_OUT = DATA / "quality_alerts.json"

# Default thresholds (tune for production)
DEFAULT_THRESHOLDS = {
    "missing_gender_pct": 15.0,       # warn above %
    "missing_age_pct": 40.0,          # high after invalid age purge
    "missing_amount_pct": 5.0,
    "missing_rating_pct": 25.0,
    "invalid_date_pct": 3.0,
    "unknown_category_pct": 20.0,
    "duplicate_ids": 0,               # any residual dups after clean
    "avg_rating_low": 2.5,            # business quality signal
}


@dataclass
class Alert:
    id: str
    severity: str  # critical | high | medium | low | info
    title: str
    metric: str
    value: float
    threshold: float
    message: str
    recommendation: str
    fired_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _pct(num: int, den: int) -> float:
    if den <= 0:
        return 0.0
    return round(100.0 * num / den, 2)


def load_frame(path: Optional[Path] = None) -> pd.DataFrame:
    p = path or CLEAN_CSV
    if not p.exists():
        raise FileNotFoundError(f"Missing dataset: {p}")
    return pd.read_csv(p)


def compute_quality_metrics(df: pd.DataFrame, summary: Optional[dict] = None) -> Dict[str, Any]:
    n = len(df)
    summary = summary or {}
    audit = summary.get("audit") or {}

    gender_missing = int(df["Gender"].isna().sum()) if "Gender" in df.columns else 0
    age_missing = int(df["Age"].isna().sum()) if "Age" in df.columns else 0
    amount_missing = int(df["AmountMissing"].sum()) if "AmountMissing" in df.columns else int(df["PurchaseAmount"].isna().sum()) if "PurchaseAmount" in df.columns else 0
    rating_missing = int(df["Rating"].isna().sum()) if "Rating" in df.columns else 0
    date_invalid = int(df["DateInvalid"].sum()) if "DateInvalid" in df.columns else 0
    unknown_cat = int((df["ProductCategory"] == "Unknown").sum()) if "ProductCategory" in df.columns else 0
    dup_ids = int(df["CustomerID"].duplicated().sum()) if "CustomerID" in df.columns else 0

    rats = pd.to_numeric(df["Rating"], errors="coerce").dropna() if "Rating" in df.columns else pd.Series(dtype=float)
    avg_rating = float(rats.mean()) if len(rats) else None

    return {
        "rows": n,
        "missing_gender_pct": _pct(gender_missing, n),
        "missing_age_pct": _pct(age_missing, n),
        "missing_amount_pct": _pct(amount_missing, n),
        "missing_rating_pct": _pct(rating_missing, n),
        "invalid_date_pct": _pct(date_invalid, n),
        "unknown_category_pct": _pct(unknown_cat, n),
        "unknown_category_count": unknown_cat,
        "duplicate_ids": dup_ids,
        "avg_rating": avg_rating,
        "invalid_dates_count": date_invalid,
        "amount_missing_count": amount_missing,
        "duplicates_removed_at_clean": audit.get("duplicate_ids"),
        "invalid_ages_cleared_at_clean": audit.get("invalid_ages_cleared"),
        "invalid_ratings_cleared_at_clean": audit.get("invalid_ratings_cleared"),
    }


def evaluate_alerts(
    metrics: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Alert]:
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    alerts: List[Alert] = []
    now = datetime.now(timezone.utc).isoformat()

    def fire(aid, sev, title, metric, value, threshold, message, rec):
        alerts.append(Alert(
            id=aid, severity=sev, title=title, metric=metric,
            value=float(value) if value is not None else 0.0,
            threshold=float(threshold), message=message, recommendation=rec, fired_at=now,
        ))

    # Residual duplicates (should be 0 after clean)
    if metrics["duplicate_ids"] > th["duplicate_ids"]:
        fire(
            "DQ-DUP-001", "critical", "Residual duplicate CustomerIDs",
            "duplicate_ids", metrics["duplicate_ids"], th["duplicate_ids"],
            f"{metrics['duplicate_ids']} duplicate CustomerID(s) still present after cleaning.",
            "Re-run deduplication and block ingest of duplicate keys at source.",
        )

    if metrics["invalid_date_pct"] >= th["invalid_date_pct"]:
        sev = "high" if metrics["invalid_date_pct"] >= th["invalid_date_pct"] * 1.5 else "medium"
        fire(
            "DQ-DATE-001", sev, "Invalid purchase dates above threshold",
            "invalid_date_pct", metrics["invalid_date_pct"], th["invalid_date_pct"],
            f"{metrics['invalid_date_pct']}% of rows have invalid dates ({metrics['invalid_dates_count']} rows).",
            "Enforce calendar validation at capture; exclude flagged rows from trend KPIs.",
        )

    if metrics["missing_amount_pct"] >= th["missing_amount_pct"]:
        sev = "high" if metrics["missing_amount_pct"] >= 10 else "medium"
        fire(
            "DQ-AMT-001", sev, "Missing purchase amounts",
            "missing_amount_pct", metrics["missing_amount_pct"], th["missing_amount_pct"],
            f"{metrics['missing_amount_pct']}% of rows lack PurchaseAmount ({metrics['amount_missing_count']} rows).",
            "Make amount mandatory at checkout; reconcile POS failures daily.",
        )

    if metrics["unknown_category_pct"] >= th["unknown_category_pct"]:
        sev = "high" if metrics["unknown_category_pct"] >= 30 else "medium"
        fire(
            "DQ-CAT-001", sev, "Unknown product category too high",
            "unknown_category_pct", metrics["unknown_category_pct"], th["unknown_category_pct"],
            f"{metrics['unknown_category_pct']}% of purchases are category Unknown ({metrics['unknown_category_count']} rows).",
            "Improve POS category capture; map legacy codes to the five core categories.",
        )

    if metrics["missing_gender_pct"] >= th["missing_gender_pct"]:
        fire(
            "DQ-GEN-001", "medium", "Missing gender above threshold",
            "missing_gender_pct", metrics["missing_gender_pct"], th["missing_gender_pct"],
            f"{metrics['missing_gender_pct']}% of customers have no standardized gender.",
            "Optional field with controlled values (Male/Female) or explicit Prefer-not-to-say.",
        )

    if metrics["missing_age_pct"] >= th["missing_age_pct"]:
        fire(
            "DQ-AGE-001", "medium", "Age completeness low",
            "missing_age_pct", metrics["missing_age_pct"], th["missing_age_pct"],
            f"{metrics['missing_age_pct']}% of rows have missing age (includes purged invalid ages).",
            "Validate age at entry (1–100); review source systems emitting -1 or 200.",
        )

    if metrics["missing_rating_pct"] >= th["missing_rating_pct"]:
        fire(
            "DQ-RATE-001", "low", "Rating sparsity high",
            "missing_rating_pct", metrics["missing_rating_pct"], th["missing_rating_pct"],
            f"{metrics['missing_rating_pct']}% of rows have no valid rating (1–5).",
            "Prompt post-purchase rating; reject out-of-scale values (e.g. 10) at API.",
        )

    if metrics.get("avg_rating") is not None and metrics["avg_rating"] < th["avg_rating_low"]:
        fire(
            "BQ-RATE-001", "medium", "Average rating below service threshold",
            "avg_rating", metrics["avg_rating"], th["avg_rating_low"],
            f"Mean rating is {metrics['avg_rating']:.2f} (below {th['avg_rating_low']}).",
            "Trigger service-recovery for ratings 1–2; review top low-score categories.",
        )

    # Info: successful clean stats
    if metrics.get("duplicates_removed_at_clean"):
        fire(
            "DQ-INFO-001", "info", "Duplicates removed during cleaning",
            "duplicates_removed_at_clean", metrics["duplicates_removed_at_clean"], 0,
            f"{metrics['duplicates_removed_at_clean']} duplicate IDs were removed in the clean pipeline.",
            "Keep unique constraint on CustomerID in the warehouse.",
        )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    alerts.sort(key=lambda a: (severity_order.get(a.severity, 9), a.id))
    return alerts


def run_quality_alerts(
    csv_path: Optional[Path] = None,
    thresholds: Optional[Dict[str, float]] = None,
    write: bool = True,
) -> Dict[str, Any]:
    df = load_frame(csv_path)
    summary = {}
    if SUMMARY_JSON.exists():
        summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    metrics = compute_quality_metrics(df, summary)
    alerts = evaluate_alerts(metrics, thresholds)
    actionable = [a for a in alerts if a.severity in ("critical", "high", "medium", "low")]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ALERT" if any(a.severity in ("critical", "high") for a in alerts) else (
            "WARN" if any(a.severity == "medium" for a in alerts) else "OK"
        ),
        "summary": {
            "total_alerts": len(alerts),
            "critical": sum(1 for a in alerts if a.severity == "critical"),
            "high": sum(1 for a in alerts if a.severity == "high"),
            "medium": sum(1 for a in alerts if a.severity == "medium"),
            "low": sum(1 for a in alerts if a.severity == "low"),
            "info": sum(1 for a in alerts if a.severity == "info"),
        },
        "metrics": metrics,
        "thresholds": {**DEFAULT_THRESHOLDS, **(thresholds or {})},
        "alerts": [a.to_dict() for a in alerts],
        "actionable_alerts": [a.to_dict() for a in actionable],
    }
    if write:
        ALERTS_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    result = run_quality_alerts()
    print(f"Status: {result['status']}")
    print(f"Alerts: {result['summary']}")
    for a in result["alerts"]:
        if a["severity"] != "info":
            print(f"  [{a['severity'].upper()}] {a['id']}: {a['title']} ({a['value']} vs {a['threshold']})")


def alerts_as_prometheus_lines(payload: Optional[Dict[str, Any]] = None) -> str:
    """Export quality status as Prometheus text format (for /metrics scrape)."""
    payload = payload or run_quality_alerts(write=False)
    metrics = payload.get("metrics") or {}
    summary = payload.get("summary") or {}
    status = payload.get("status") or "OK"
    status_num = {"OK": 0, "WARN": 1, "ALERT": 2}.get(status, -1)
    lines = [
        "# HELP customer_dq_status Data quality rollup (0=OK,1=WARN,2=ALERT)",
        "# TYPE customer_dq_status gauge",
        f"customer_dq_status {status_num}",
        "# HELP customer_dq_alerts_total Alerts by severity",
        "# TYPE customer_dq_alerts_total gauge",
    ]
    for sev in ("critical", "high", "medium", "low", "info"):
        lines.append(f'customer_dq_alerts_total{{severity="{sev}"}} {summary.get(sev, 0)}')
    lines += [
        "# HELP customer_dq_invalid_date_pct Percent invalid purchase dates",
        "# TYPE customer_dq_invalid_date_pct gauge",
        f"customer_dq_invalid_date_pct {metrics.get('invalid_date_pct', 0)}",
        "# HELP customer_dq_unknown_category_pct Percent Unknown product category",
        "# TYPE customer_dq_unknown_category_pct gauge",
        f"customer_dq_unknown_category_pct {metrics.get('unknown_category_pct', 0)}",
        "# HELP customer_dq_missing_amount_pct Percent missing purchase amount",
        "# TYPE customer_dq_missing_amount_pct gauge",
        f"customer_dq_missing_amount_pct {metrics.get('missing_amount_pct', 0)}",
        "# HELP customer_dq_missing_age_pct Percent missing age",
        "# TYPE customer_dq_missing_age_pct gauge",
        f"customer_dq_missing_age_pct {metrics.get('missing_age_pct', 0)}",
        "# HELP customer_dq_missing_rating_pct Percent missing rating",
        "# TYPE customer_dq_missing_rating_pct gauge",
        f"customer_dq_missing_rating_pct {metrics.get('missing_rating_pct', 0)}",
    ]
    return "\n".join(lines) + "\n"


def send_webhook(payload: Dict[str, Any], url: str) -> Dict[str, Any]:
    """POST actionable alerts to a webhook (Slack/Teams/custom)."""
    import urllib.request
    body = json.dumps({
        "text": f"Customer+ DQ status: {payload.get('status')}",
        "status": payload.get("status"),
        "summary": payload.get("summary"),
        "alerts": payload.get("actionable_alerts") or [
            a for a in payload.get("alerts", []) if a.get("severity") != "info"
        ],
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return {"ok": True, "http_status": resp.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}
