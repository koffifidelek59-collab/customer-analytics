# Data quality alerts

## Policy thresholds

| Rule | Threshold | Severity |
|------|-----------|----------|
| Invalid dates | ≥ 3% | high |
| Unknown category | ≥ 20% | high |
| Missing amount | ≥ 5% | high |
| Missing age | ≥ 30% | medium |
| Missing rating | ≥ 25% | medium |
| Duplicate IDs removed | ≥ 1 | medium |

## Run

```bash
python etl/run_etl.py              # full ETL + alerts
python api/run_quality_alerts.py   # analyze alerts only
```

Exit codes: `0` OK · `1` WARN · `2` ALERT
