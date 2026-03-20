"""Tests for make_prompt.py — prompt generation utilities."""

from make_prompt import detect_format, fmt_jobs, fmt_pay, load_records_bls, load_records_cyprus


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


class TestDetectFormat:
    def test_cyprus_by_isco(self):
        assert detect_format(["title", "isco_code", "slug"]) == "cyprus"

    def test_cyprus_by_pay_field(self):
        assert detect_format(["title", "median_pay_annual_eur", "slug"]) == "cyprus"

    def test_bls(self):
        assert detect_format(["title", "median_pay_annual", "slug"]) == "bls"

    def test_empty(self):
        assert detect_format([]) == "bls"


class TestLoadRecordsCyprus:
    def test_basic(self):
        occs = [{"title": "Managers", "slug": "managers", "category": "managers"}]
        csv_rows = {
            "managers": {
                "category": "managers",
                "median_pay_annual_eur": "45000",
                "employment_thousands": "12.5",
                "entry_education": "Bachelor's degree or higher",
            }
        }
        scores = {"managers": {"exposure": 6, "rationale": "High exposure."}}
        records = load_records_cyprus(occs, csv_rows, scores)
        assert len(records) == 1
        assert records[0]["pay"] == 45000
        assert records[0]["jobs"] == 12500
        assert records[0]["exposure"] == 6


class TestLoadRecordsBls:
    def test_basic(self):
        occs = [{"title": "Accountants", "slug": "accountants", "category": "business"}]
        csv_rows = {
            "accountants": {
                "category": "business",
                "median_pay_annual": "80000",
                "num_jobs_2024": "1400000",
                "outlook_pct": "4",
                "outlook_desc": "Average",
                "entry_education": "Bachelor's degree",
            }
        }
        scores = {"accountants": {"exposure": 7, "rationale": "Knowledge work."}}
        records = load_records_bls(occs, csv_rows, scores)
        assert len(records) == 1
        assert records[0]["pay"] == 80000
        assert records[0]["jobs"] == 1400000
        assert records[0]["outlook_pct"] == 4
