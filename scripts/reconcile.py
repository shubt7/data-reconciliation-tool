"""Reconcile an order-system extract against a billing report.

Usage (from the project root):
    python3 scripts/reconcile.py data/source_system.csv data/billing_report.csv

Rules applied before comparing:
  * Keys (invoice_id) are trimmed and upper-cased, so " inv-00001" matches "INV-00001".
  * Dates are read as ISO (2025-01-31) or day/month/year (31/01/2025) and written as ISO.
  * Amounts match when they differ by no more than the tolerance (default 0.01).

Results are written to output/ and a summary is printed.
"""
import argparse
import os
from datetime import datetime

import pandas as pd

KEY = "invoice_id"
COMPARE_COLS = ["customer", "invoice_date", "amount"]


def parse_date(value):
    if pd.isna(value):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return f"UNPARSEABLE:{value}"


def load(path):
    df = pd.read_csv(path, dtype=str)
    df[KEY] = df[KEY].str.strip().str.upper()
    df["invoice_date"] = df["invoice_date"].map(parse_date)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").round(2)
    df["customer"] = df["customer"].str.strip()
    return df


def reconcile(source_path, billing_path, tolerance=0.01):
    src = load(source_path)
    bill = load(billing_path)

    src_dupes = src[src.duplicated(KEY, keep=False)]
    bill_dupes = bill[bill.duplicated(KEY, keep=False)]

    # Compare one row per invoice; duplicates are reported separately
    src_u = src.drop_duplicates(KEY, keep="first")
    bill_u = bill.drop_duplicates(KEY, keep="first")

    merged = src_u.merge(bill_u, on=KEY, how="outer", suffixes=("_src", "_bill"), indicator=True)

    missing_in_billing = merged[merged["_merge"] == "left_only"][[KEY] + [c + "_src" for c in COMPARE_COLS]]
    missing_in_source = merged[merged["_merge"] == "right_only"][[KEY] + [c + "_bill" for c in COMPARE_COLS]]

    both = merged[merged["_merge"] == "both"].copy()
    both["amount_diff"] = (both["amount_bill"] - both["amount_src"]).round(2)
    amount_mismatch = both[both["amount_diff"].abs() > tolerance]
    amount_mismatch = amount_mismatch[[KEY, "customer_src", "amount_src", "amount_bill", "amount_diff"]]

    date_mismatch = both[both["invoice_date_src"] != both["invoice_date_bill"]]
    date_mismatch = date_mismatch[[KEY, "invoice_date_src", "invoice_date_bill"]]

    matched = both[both["amount_diff"].abs() <= tolerance]

    summary = {
        "source_rows": len(src),
        "billing_rows": len(bill),
        "matched_invoices": len(matched),
        "missing_in_billing": len(missing_in_billing),
        "missing_in_source": len(missing_in_source),
        "amount_mismatches": len(amount_mismatch),
        "date_mismatches": len(date_mismatch),
        "duplicate_rows_in_billing": len(bill_dupes),
        "duplicate_rows_in_source": len(src_dupes),
        "unparseable_dates": int(
            src["invoice_date"].str.startswith("UNPARSEABLE").sum()
            + bill["invoice_date"].str.startswith("UNPARSEABLE").sum()
        ),
        "value_in_source": round(src["amount"].sum(), 2),
        "value_in_billing": round(bill["amount"].sum(), 2),
        "net_value_difference": round(bill["amount"].sum() - src["amount"].sum(), 2),
    }

    results = {
        "missing_in_billing": missing_in_billing,
        "missing_in_source": missing_in_source,
        "amount_mismatches": amount_mismatch,
        "date_mismatches": date_mismatch,
        "duplicates_in_billing": bill_dupes,
    }
    return summary, results


def write_outputs(summary, results, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)
    pd.DataFrame([summary]).T.rename(columns={0: "value"}).to_csv(os.path.join(out_dir, "summary.csv"))
    for name, frame in results.items():
        frame.to_csv(os.path.join(out_dir, f"{name}.csv"), index=False)

    s = summary
    lines = [
        "# Reconciliation summary",
        "",
        f"Rows: order system {s['source_rows']:,}, billing report {s['billing_rows']:,}",
        "",
        "| Check | Count |",
        "|---|---:|",
        f"| Matched invoices | {s['matched_invoices']:,} |",
        f"| Missing in billing (never billed) | {s['missing_in_billing']:,} |",
        f"| Missing in order system (billed, no order) | {s['missing_in_source']:,} |",
        f"| Amount mismatches | {s['amount_mismatches']:,} |",
        f"| Date mismatches | {s['date_mismatches']:,} |",
        f"| Rows involved in duplicate invoice IDs (billing) | {s['duplicate_rows_in_billing']:,} |",
        f"| Unparseable dates | {s['unparseable_dates']:,} |",
        "",
        f"Value in order system: ${s['value_in_source']:,.2f}",
        f"Value in billing report: ${s['value_in_billing']:,.2f}",
        f"Net difference (billing minus orders): {'-' if s['net_value_difference'] < 0 else ''}${abs(s['net_value_difference']):,.2f}",
    ]
    with open(os.path.join(out_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source")
    parser.add_argument("billing")
    parser.add_argument("--tolerance", type=float, default=0.01)
    args = parser.parse_args()

    summary, results = reconcile(args.source, args.billing, args.tolerance)
    write_outputs(summary, results)
    print(open("output/summary.md", encoding="utf-8").read())
