#!/usr/bin/env python3
"""Export Customer DQ + KPI metrics as Prometheus text format (for Grafana)."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collect() -> str:
    lines = [
        "# HELP customer_dq_status Data quality status (0=OK,1=WARN,2=ALERT)",
        "# TYPE customer_dq_status gauge",
    ]
    qa = {}
    p = ROOT / "results" / "quality_alerts.json"
    if p.exists():
        qa = json.loads(p.read_text(encoding="utf-8"))
    status_map = {"OK": 0, "WARN": 1, "ALERT": 2}
    st = status_map.get(qa.get("status", "OK"), 0)
    lines.append(f'customer_dq_status{{project="task9"}} {st}')
    metrics = qa.get("metrics") or {}
    mapping = {
        "rows": "customer_rows",
        "invalid_dates_pct": "customer_invalid_dates_pct",
        "unknown_category_pct": "customer_unknown_category_pct",
        "missing_age_pct": "customer_missing_age_pct",
        "missing_rating_pct": "customer_missing_rating_pct",
        "missing_amount_pct": "customer_missing_amount_pct",
        "duplicate_ids_removed": "customer_duplicates_removed",
    }
    for src, name in mapping.items():
        if src in metrics:
            lines.append(f"# TYPE {name} gauge")
            lines.append(f'{name}{{project="task9"}} {metrics[src]}')
    # KPIs if present
    kpis_path = ROOT / "results" / "kpis.csv"
    if kpis_path.exists():
        try:
            import csv
            with kpis_path.open() as f:
                rows = list(csv.DictReader(f))
            for row in rows:
                key = (row.get("metric") or row.get("kpi") or "").strip().lower().replace(" ", "_")
                val = row.get("value") or row.get("Value")
                if key and val is not None:
                    try:
                        float(val)
                        lines.append(f"# TYPE customer_kpi_{key} gauge")
                        lines.append(f'customer_kpi_{key}{{project="task9"}} {val}')
                    except ValueError:
                        pass
        except Exception:
            pass
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9108)
    ap.add_argument("--once", action="store_true", help="print metrics and exit")
    args = ap.parse_args()
    body = collect()
    if args.once:
        print(body)
        return
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in ("/metrics", "/"):
                self.send_response(404); self.end_headers(); return
            data = collect().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def log_message(self, *a):
            pass
    print(f"Prometheus metrics on http://127.0.0.1:{args.port}/metrics")
    HTTPServer(("0.0.0.0", args.port), H).serve_forever()


if __name__ == "__main__":
    main()
