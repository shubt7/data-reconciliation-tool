# Reconciliation rules

These rules define what counts as a match between the order system and the billing report.

| Rule | Definition | Why |
|---|---|---|
| Key | `invoice_id`, trimmed and upper-cased | Stops formatting differences from being counted as errors |
| Date format | ISO (`YYYY-MM-DD`) or day/month/year (`DD/MM/YYYY`), stored as ISO | The billing report uses a different date format |
| Amount tolerance | Difference of $0.01 or less is a match | Allows for rounding |
| Missing in billing | In the order system, not in billing | Orders that were never invoiced (revenue leakage) |
| Missing in order system | In billing, not in the order system | Invoices with no source order (possible over-billing or a data-feed gap) |
| Amount mismatch | Both systems have the invoice, but amounts differ by more than tolerance | Pricing, tax or keying errors |
| Date mismatch | Both systems have the invoice, but dates differ | Posting-period issues |
| Duplicate invoice ID | The same invoice ID appears more than once in a system | Double posting; the first row is used for matching and the rest are reported |

## Acceptance criteria

- Every invoice in either file appears in exactly one result category.
- The counts in `summary.md` add up to the total invoices in each file.
- Running the script twice on the same files gives identical output.
- Unparseable dates are reported, not silently dropped.
