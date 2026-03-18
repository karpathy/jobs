"""Tests for make_prompt.py — prompt generation utilities."""

from make_prompt import fmt_jobs, fmt_pay


class TestFmtPay:
    def test_none(self):
        assert fmt_pay(None) == "?"

    def test_normal(self):
        assert fmt_pay(50000) == "€50,000"

    def test_large(self):
        assert fmt_pay(130000) == "€130,000"


class TestFmtJobs:
    def test_none(self):
        assert fmt_jobs(None) == "?"

    def test_millions(self):
        assert fmt_jobs(1_500_000) == "1.5M"

    def test_thousands(self):
        assert fmt_jobs(50_000) == "50K"

    def test_small(self):
        assert fmt_jobs(500) == "500"

    def test_exact_million(self):
        assert fmt_jobs(1_000_000) == "1.0M"

    def test_exact_thousand(self):
        assert fmt_jobs(1_000) == "1K"
