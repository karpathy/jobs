"""Tests for make_csv.py — CSV extraction utilities."""

from make_csv import clean, parse_number, parse_outlook, parse_pay


class TestClean:
    def test_collapses_whitespace(self):
        assert clean("  hello   world  ") == "hello world"

    def test_strips_newlines(self):
        assert clean("line1\n  line2\n") == "line1 line2"

    def test_empty_string(self):
        assert clean("") == ""

    def test_tabs_and_mixed(self):
        assert clean("\t hello \t world \n") == "hello world"


class TestParsePay:
    def test_annual_and_hourly(self):
        assert parse_pay("$62,350 per year $29.98 per hour") == ("62350", "29.98")

    def test_annual_only(self):
        assert parse_pay("$45,000 per year") == ("45000", "")

    def test_hourly_only(self):
        assert parse_pay("$23.33 per hour") == ("", "23.33")

    def test_no_amounts(self):
        assert parse_pay("varies") == ("", "")

    def test_large_salary(self):
        assert parse_pay("$130,000 per year $62.50 per hour") == ("130000", "62.50")


class TestParseOutlook:
    def test_with_description(self):
        assert parse_outlook("9% (Much faster than average)") == ("9", "Much faster than average")

    def test_negative(self):
        assert parse_outlook("-3% (Decline)") == ("-3", "Decline")

    def test_no_description(self):
        assert parse_outlook("4%") == ("4", "")

    def test_text_only(self):
        assert parse_outlook("Little or no change") == ("", "Little or no change")


class TestParseNumber:
    def test_with_commas(self):
        assert parse_number("1,234,567") == "1234567"

    def test_negative(self):
        assert parse_number("-500") == "-500"

    def test_plain(self):
        assert parse_number("42") == "42"
