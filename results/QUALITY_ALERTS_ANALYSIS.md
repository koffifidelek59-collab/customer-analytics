# Data quality alerts — analysis

**Status:** `ALERT`  
**Generated:** 2026-10-01T17:44:00.411664+00:00

Data quality status is ALERT. 5 policy rule(s) breached (2 high, 3 medium).

## Metrics

| Metric | Value |
|--------|------:|
| rows | 2100 |
| invalid_dates_count | 118 |
| invalid_dates_pct | 5.62 |
| unknown_category_count | 565 |
| unknown_category_pct | 26.9 |
| missing_amount_pct | 4.62 |
| missing_age_pct | 76.43 |
| missing_rating_pct | 29.19 |
| duplicate_ids_removed | 50 |

## Breached rules

### [HIGH] Invalid purchase dates

118 rows (5.62%) have invalid dates.

**Recommendation:** Enforce ISO date validation at POS / ingestion; exclude flagged rows from trend KPIs.

### [HIGH] Unknown product category

565 rows (26.9%) are Unknown category.

**Recommendation:** Mandatory category at capture before merchandising or assortment decisions.

### [MEDIUM] Missing age after domain purge

76.43% of ages missing after removing values outside 1–100.

**Recommendation:** Block ages outside 1–100 at entry; re-collect for critical segments.

### [MEDIUM] Missing / invalid ratings

29.19% ratings missing after restricting to 1–5.

**Recommendation:** Constrain rating widget to 1–5; monitor completion rate.

### [MEDIUM] Duplicate CustomerIDs in source

50 duplicate CustomerIDs removed at ETL.

**Recommendation:** Enforce unique CustomerID in upstream system.

## Priority actions

1. Enforce ISO date validation at POS / ingestion; exclude flagged rows from trend KPIs.
2. Mandatory category at capture before merchandising or assortment decisions.

## KPI impact

- Trend KPIs must exclude DateInvalid rows.
- Category revenue share is biased while Unknown remains elevated.
- Age-band analysis is limited by missing age after domain purge.
