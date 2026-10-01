# KPI code examples (Python)

```python
import pandas as pd

df = pd.read_csv("data/customers_clean.csv")

# Customers
customers = df["CustomerID"].nunique()

# Revenue & tickets
revenue = df["PurchaseAmount"].dropna().sum()
avg_ticket = df["PurchaseAmount"].dropna().mean()
median_ticket = df["PurchaseAmount"].dropna().median()

# Rating (domain 1–5)
r = pd.to_numeric(df["Rating"], errors="coerce")
r = r.where(r.between(1, 5))
avg_rating = r.mean()

# Category revenue
by_cat = (
    df.groupby("ProductCategory")
      .agg(customers=("CustomerID", "count"),
           revenue=("PurchaseAmount", "sum"),
           avg_ticket=("PurchaseAmount", "mean"))
      .sort_values("revenue", ascending=False)
)

# Data quality rates
n = len(df)
invalid_date_pct = 100 * df["DateInvalid"].mean()
unknown_cat_pct = 100 * (df["ProductCategory"] == "Unknown").mean()
status = "ALERT" if invalid_date_pct >= 3 or unknown_cat_pct >= 20 else "OK"
```
