# ETL Pipeline — Customer Analytics (Task 9)

## Stages

1. **Extract** — load raw CSV, drop junk columns  
2. **Transform** — dedupe, gender, age 1–100, rating 1–5, dates, Unknown category, age bands  
3. **Load** — write `data/customers_clean.csv`  
4. **Quality** — policy thresholds → `results/quality_alerts.json` + analysis markdown  

## Run

```bash
python etl/run_etl.py
python etl/run_etl.py --source data/customers_raw.csv --out data/customers_clean.csv
echo $?   # 0=OK · 1=WARN · 2=ALERT · 3=error
```
