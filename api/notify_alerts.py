#!/usr/bin/env python3
"""
Customer Analytics — Task 9
Alert notification dispatcher

Channels: console · webhook (Slack/Teams/generic) · email (SMTP) · file

Usage:
  python api/notify_alerts.py
  python api/notify_alerts.py --config api/notify_config.json --dry-run
  python api/notify_alerts.py --force   # notify even if status OK
"""

from __future__ import annotations

import argparse
import json
import os
import smtplib
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALERTS = ROOT / "results" / "quality_alerts.json"
DEFAULT_CONFIG = ROOT / "api" / "notify_config.json"
DEFAULT_LOG = ROOT / "results" / "notification_log.json"


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_message(alerts_doc: dict) -> dict:
    status = alerts_doc.get("status", "OK")
    summary = alerts_doc.get("summary", {})
    metrics = alerts_doc.get("metrics", {})
    items = alerts_doc.get("alerts", [])
    lines = [
        f"[Customer Analytics Task 9] Data quality: {status}",
        f"Time (UTC): {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
        f"Alerts: {summary.get('total_alerts', len(items))} "
        f"(high={summary.get('high', 0)}, medium={summary.get('medium', 0)})",
        "",
        "Key metrics:",
        f"  · rows={metrics.get('rows')}",
        f"  · invalid_dates={metrics.get('invalid_dates_pct')}%",
        f"  · unknown_category={metrics.get('unknown_category_pct')}%",
        f"  · missing_age={metrics.get('missing_age_pct')}%",
        f"  · missing_rating={metrics.get('missing_rating_pct')}%",
        "",
    ]
    if items:
        lines.append("Breaches:")
        for a in items:
            lines.append(f"  [{a.get('severity', '').upper()}] {a.get('title')}: {a.get('message')}")
            if a.get("recommendation"):
                lines.append(f"      → {a['recommendation']}")
    else:
        lines.append("No threshold breaches.")
    text = "\n".join(lines)
    return {
        "status": status,
        "title": f"Customer DQ {status}",
        "text": text,
        "alerts": items,
        "metrics": metrics,
    }


def notify_console(msg: dict, cfg: dict) -> dict:
    print(msg["text"])
    return {"channel": "console", "ok": True}


def notify_file(msg: dict, cfg: dict) -> dict:
    path = Path(cfg.get("path") or (ROOT / "results" / "last_alert_notification.txt"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(msg["text"] + "\n", encoding="utf-8")
    return {"channel": "file", "ok": True, "path": str(path)}


def notify_webhook(msg: dict, cfg: dict) -> dict:
    url = cfg.get("url") or os.environ.get("DQ_WEBHOOK_URL", "")
    if not url:
        return {"channel": "webhook", "ok": False, "error": "no webhook url (set config url or DQ_WEBHOOK_URL)"}
    # Slack-compatible payload; also works for many generic receivers
    payload = {
        "text": msg["text"],
        "status": msg["status"],
        "title": msg["title"],
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": msg["title"]}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"```{msg['text'][:2800]}```"}},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"channel": "webhook", "ok": True, "http_status": resp.status}
    except Exception as e:
        return {"channel": "webhook", "ok": False, "error": str(e)}


def notify_email(msg: dict, cfg: dict) -> dict:
    host = cfg.get("smtp_host") or os.environ.get("DQ_SMTP_HOST", "")
    port = int(cfg.get("smtp_port") or os.environ.get("DQ_SMTP_PORT", "587"))
    user = cfg.get("smtp_user") or os.environ.get("DQ_SMTP_USER", "")
    password = cfg.get("smtp_password") or os.environ.get("DQ_SMTP_PASSWORD", "")
    sender = cfg.get("from") or os.environ.get("DQ_SMTP_FROM", user)
    recipients = cfg.get("to") or []
    if isinstance(recipients, str):
        recipients = [recipients]
    if not host or not recipients:
        return {"channel": "email", "ok": False, "error": "smtp_host and to[] required (or env DQ_SMTP_*)"}
    mime = MIMEText(msg["text"], "plain", "utf-8")
    mime["Subject"] = msg["title"]
    mime["From"] = sender
    mime["To"] = ", ".join(recipients)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls(context=context)
            if user and password:
                server.login(user, password)
            server.sendmail(sender, recipients, mime.as_string())
        return {"channel": "email", "ok": True, "to": recipients}
    except Exception as e:
        return {"channel": "email", "ok": False, "error": str(e)}


CHANNELS = {
    "console": notify_console,
    "file": notify_file,
    "webhook": notify_webhook,
    "email": notify_email,
}


def dispatch(alerts_doc: dict, config: dict, dry_run: bool = False) -> dict:
    msg = build_message(alerts_doc)
    status = msg["status"]
    # Only notify on WARN/ALERT unless force / always
    min_level = (config.get("min_status") or "WARN").upper()
    order = {"OK": 0, "WARN": 1, "ALERT": 2}
    should = order.get(status, 0) >= order.get(min_level, 1)
    if config.get("always"):
        should = True
    results = []
    enabled = config.get("channels") or [{"type": "console"}, {"type": "file"}]
    for ch in enabled:
        if not ch.get("enabled", True):
            continue
        ctype = ch.get("type", "console")
        fn = CHANNELS.get(ctype)
        if not fn:
            results.append({"channel": ctype, "ok": False, "error": "unknown channel"})
            continue
        if dry_run or not should:
            results.append({"channel": ctype, "ok": True, "skipped": not should, "dry_run": dry_run})
            continue
        results.append(fn(msg, ch))
    log = {
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "should_notify": should,
        "dry_run": dry_run,
        "results": results,
        "preview": msg["text"][:500],
    }
    return log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Dispatch data-quality alert notifications")
    ap.add_argument("--alerts", type=Path, default=DEFAULT_ALERTS)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--log", type=Path, default=DEFAULT_LOG)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="notify even if below min_status")
    args = ap.parse_args(argv)

    alerts_doc = load_json(args.alerts, {"status": "OK", "alerts": [], "summary": {}, "metrics": {}})
    config = load_json(args.config, {
        "min_status": "WARN",
        "channels": [{"type": "console"}, {"type": "file", "path": str(ROOT / "results" / "last_alert_notification.txt")}],
    })
    if args.force:
        config["always"] = True

    log = dispatch(alerts_doc, config, dry_run=args.dry_run)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Notification log → {args.log}")
    failed = [r for r in log["results"] if not r.get("ok") and not r.get("skipped")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
