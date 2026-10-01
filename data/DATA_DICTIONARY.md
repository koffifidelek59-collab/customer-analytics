# Data Dictionary — Customer Analytics (Task 9)

## customers_raw.csv
Source file as provided (messy types, duplicates, invalid domains).

## customers_clean.csv

| Column | Type | Description |
|--------|------|-------------|
| CustomerID | string | Unique customer key (deduplicated) |
| Name | string | Customer name |
| Age | float | Age in years; invalid values (-1, 200) set to missing |
| AgeBand | string | 0-18, 19-30, 31-45, 46-60, 61-75, 76+, Unknown |
| Gender | string | Male / Female / missing (standardized) |
| Email | string | Email address |
| Phone | string | Phone when present |
| PurchaseAmount | float | Purchase amount in currency units |
| PurchaseDate | string | Original date string |
| PurchaseDateParsed | date | Parsed date when valid |
| PurchaseYear | int | Year of purchase |
| PurchaseMonthName | string | Jan…Dec |
| PurchaseQuarter | int | 1–4 |
| ProductCategory | string | Clothing, Electronics, Books, Home, Toys, or Unknown |
| Rating | float | Satisfaction 1–5; values outside range invalidated |
| AmountMissing | bool | True if PurchaseAmount missing |
| DateInvalid | bool | True if date could not be parsed |

## Cleaning rules
1. Drop junk columns (Unnamed, trailing Gender duplicate).
2. Drop duplicate CustomerID (keep first).
3. Standardize Gender to Male/Female.
4. Age outside 1–100 → missing.
5. Rating outside 1–5 → missing.
6. Impossible dates flagged DateInvalid.
7. Missing ProductCategory → Unknown.
