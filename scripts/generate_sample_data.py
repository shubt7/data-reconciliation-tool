"""Create two synthetic extracts that should match, with deliberate errors.

source_system.csv  = orders as recorded in the order system
billing_report.csv = the same orders as they arrive in the billing report

Errors are planted on purpose so the reconciliation has something to find:
missing rows, duplicate rows, amount differences, and formatting differences.
"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
N = 1200

ids = [f"INV-{i:05d}" for i in range(1, N + 1)]
customers = rng.choice(["Acme Corp", "Northwind", "Globex", "Initech", "Umbrella Ltd"], N)
dates = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, N), unit="D")
amounts = np.round(rng.uniform(50, 5000, N), 2)

source = pd.DataFrame({
    "invoice_id": ids,
    "customer": customers,
    "invoice_date": dates.strftime("%Y-%m-%d"),
    "amount": amounts,
})

billing = source.copy()

# 1. Invoices missing from billing (never billed)
billing = billing.drop(index=rng.choice(N, 15, replace=False))

# 2. Duplicated rows in billing (double-posted)
dups = billing.sample(8, random_state=1)
billing = pd.concat([billing, dups], ignore_index=True)

# 3. Amount differences (rounding, tax applied twice, keying errors)
idx = billing.sample(25, random_state=2).index
billing.loc[idx, "amount"] = (billing.loc[idx, "amount"] * rng.choice([1.08, 0.97, 1.0005], 25)).round(2)

# 4. Invoices only in billing (not in the order system)
extra = pd.DataFrame({
    "invoice_id": [f"INV-{i:05d}" for i in range(N + 1, N + 6)],
    "customer": ["Globex"] * 5,
    "invoice_date": ["2025-06-01"] * 5,
    "amount": [120.00, 980.50, 45.25, 300.00, 760.00],
})
billing = pd.concat([billing, extra], ignore_index=True)

# 5. Formatting differences that should NOT count as errors
billing["invoice_id"] = billing["invoice_id"].str.lower().str.replace("inv-", "INV-", regex=False)
billing["invoice_id"] = billing["invoice_id"].str.replace("INV-", " INV-", regex=False).str.strip()
billing["invoice_date"] = pd.to_datetime(billing["invoice_date"]).dt.strftime("%d/%m/%Y")

source.to_csv("data/source_system.csv", index=False)
billing.to_csv("data/billing_report.csv", index=False)
print(f"source rows: {len(source)}, billing rows: {len(billing)}")
