# Alert notifications — configuration

## Channels

| Channel | Enable | Config |
|---------|--------|--------|
| **console** | default on | prints message |
| **file** | default on | `results/last_alert_notification.txt` |
| **webhook** | off | Slack/Teams URL or `DQ_WEBHOOK_URL` |
| **email** | off | SMTP or `DQ_SMTP_*` env vars |

## Policy

- `min_status`: `WARN` → notify on WARN and ALERT only  
- Set `"always": true` or pass `--force` to notify on OK too  

## Run

```bash
python api/run_quality_alerts.py
python api/notify_alerts.py
python api/notify_alerts.py --dry-run
python api/notify_alerts.py --config api/notify_config.json
```

## Slack example

1. Create Incoming Webhook in Slack  
2. Put URL in `notify_config.json` → channels webhook `url`  
3. Set `"enabled": true`  
4. `python api/notify_alerts.py`
