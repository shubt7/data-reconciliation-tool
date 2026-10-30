# Data Reconciliation Tool

A Python tool that compares an order-system extract with a billing report and shows exactly where they disagree, so finance and operations teams can investigate and fix the gaps.

**All data in this project is synthetic.** `scripts/generate_sales_data.py` creates two files with deliberate errors so the tool has something to find.

## Business problem

Finance needs to know whether every order was billed correctly. Reconciling by hand in Excel is slow and error-prone, and small differences (a missing invoice, a double-posted row, a $3 rounding error) are easy to miss.

## What it checks

| Check | What it means |
|---|---|
| Missing in billing | Orders that were never invoiced |
| Missing in order system | Invoices that have no matching order |
| Amount mismatches | Same invoice, different amount |
| Date mismatches | Same invoice, different date |
| Duplicate invoice IDs | Invoices posted more than once |

The full matching rules are in `docs/reconciliation_rules.md`.

## Sample result

Running the tool on the sample data:

| Check | Count |
|---|---:|
| Matched invoices | 1,160 |
| Missing in billing | 15 |
| Missing in order system | 5 |
| Amount mismatches | 25 |
| Date mismatches | 0 |
| Rows involved in duplicate invoice IDs | 16 |

The billing report totals $23,048.79 less than the order system. The tool breaks that gap into its causes:

| Cause | Amount |
|---|---:|
| 15 orders never billed | -$41,726.91 |
| 8 invoices posted twice (extra copies) | +$15,152.83 |
| 25 amount differences | +$1,319.54 |
| 5 invoices billed with no matching order | +$2,205.75 |
| **Net difference** | **-$23,048.79** |

Breaking the total down this way is what turns one number into a list of fixes for each team.

Each check writes a CSV to `output/`, so an analyst can filter the exact invoices and send them to the team that owns the fix.

## How to run

Requires Python 3.9+ with pandas.

```bash
pip install pandas pytest
python3 scripts/generate_sales_data.py                  # optional: rebuild the sample files
python3 scripts/reconcile.py data/source_system.csv data/billing_report.csv
python3 -m pytest -q tests/
```

To check your own files, pass them in the same order: order system first, billing report second. The column names must match `invoice_id, customer, invoice_date, amount`.

## Project structure

```
data/      sample source_system.csv and billing_report.csv
scripts/   generate_sample_data.py, reconcile.py
output/    summary.md and one CSV per check
tests/     tests for date parsing and the expected sample results
docs/      reconciliation_rules.md
```

## What I'd do next

- Add a tolerance by customer or currency.
- Add a Power BI or Excel view of the exception files.
- Add a root-cause tag to each exception, such as "duplicate posting" or "pricing change".
