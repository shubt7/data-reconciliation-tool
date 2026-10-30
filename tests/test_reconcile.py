"""Tests for the reconciliation rules. Run with:  python3 -m pytest tests/"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from reconcile import parse_date, reconcile  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(ROOT, "data", "source_system.csv")
BILL = os.path.join(ROOT, "data", "billing_report.csv")


def test_parse_date_accepts_iso_and_day_first():
    assert parse_date("2025-01-31") == "2025-01-31"
    assert parse_date("31/01/2025") == "2025-01-31"


def test_parse_date_flags_bad_values():
    assert parse_date("31-31-2025").startswith("UNPARSEABLE")


def test_sample_data_reconciles_to_planted_errors():
    summary, _ = reconcile(SRC, BILL)
    assert summary["missing_in_billing"] == 15
    assert summary["missing_in_source"] == 5
    assert summary["amount_mismatches"] == 25
    assert summary["date_mismatches"] == 0
    assert summary["unparseable_dates"] == 0
