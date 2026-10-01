# Alert thresholds — analysis

**Overall status:** `ALERT`  
**Rules:** 6 · **Breached:** 5 (2 high, 3 medium)

## Threshold table

| Rule | Current | Threshold | Severity | Breached | Rationale |
|------|--------:|----------:|----------|----------|-----------|
| Invalid purchase dates (%) | 5.62 | >= 3.0 | high | YES | Trend KPIs (monthly revenue/volume) become unreliable above ~3% bad dates. |
| Unknown product category (%) | 26.9 | >= 20.0 | high | YES | Category mix and revenue share mislead merchandising when Unknown exceeds one-fi… |
| Missing purchase amount (%) | 4.62 | >= 5.0 | high | no | Revenue KPIs understate performance if amounts are missing. |
| Missing age after domain purge (%) | 76.43 | >= 30.0 | medium | YES | Age-band analysis and demographic targeting need sufficient coverage. |
| Missing / invalid ratings (%) | 29.19 | >= 25.0 | medium | YES | Experience KPIs need representative rating coverage. |
| Duplicate CustomerIDs removed (count) | 50 | >= 1 | medium | YES | Duplicate IDs inflate customer counts and distort per-customer metrics. |

## Distance to threshold (headroom)

| Rule | Distance | % over threshold |
|------|--------:|-----------------:|
| invalid_dates | 2.62 | 87.3 |
| unknown_category | 6.9 | 34.5 |
| missing_amount | -0.38 | 0 |
| missing_age | 46.43 | 154.8 |
| missing_rating | 4.19 | 16.8 |
| duplicates | 49 | 4900.0 |

## Recommendations

1. Keep invalid_dates threshold at 3% — material for trend integrity.
2. Tighten unknown_category target to 15% as a stretch goal once POS controls land.
3. missing_amount sits near 5% — monitor weekly to avoid silent revenue undercount.
4. Age and rating thresholds remain medium until source widgets are constrained.
5. Wire the same threshold table into Airflow sensors for automated gatekeeping.

## How thresholds feed the pipeline

1. ETL computes metrics on the clean table.
2. Quality module compares each metric to this policy table.
3. Status rollup: any **high** breach → `ALERT` (exit 2); else any medium → `WARN` (exit 1).
4. Airflow DAG fails the quality task on exit code 2 so downstream publish is blocked.

