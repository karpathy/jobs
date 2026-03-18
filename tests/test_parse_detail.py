"""Tests for parse_detail.py — HTML to Markdown parsing."""

import os
import tempfile

from parse_detail import clean, parse_ooh_page


class TestClean:
    def test_basic(self):
        assert clean("  hello   world  ") == "hello world"

    def test_newlines(self):
        assert clean("a\n\nb") == "a b"


class TestParseOohPage:
    """Test HTML parsing with a minimal fixture."""

    MINIMAL_HTML = """\
    <html>
    <head><link rel="canonical" href="https://example.com/test"></head>
    <body>
    <h1>Test Occupation</h1>
    <table id="quickfacts">
      <tbody>
        <tr><th>2024 Median Pay</th><td>$50,000 per year</td></tr>
        <tr><th>Entry-Level Education</th><td>Bachelor's degree</td></tr>
      </tbody>
    </table>
    <div id="panes">
      <div id="tab-2">
        <article>
          <h2><span>What They Do</span></h2>
          <p>Test workers do test things.</p>
        </article>
      </div>
    </div>
    <p class="update">Last Modified: 2024-01-01</p>
    </body>
    </html>
    """

    def test_extracts_title(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.MINIMAL_HTML)
            f.flush()
            result = parse_ooh_page(f.name)
        os.unlink(f.name)
        assert "# Test Occupation" in result

    def test_extracts_quick_facts(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.MINIMAL_HTML)
            f.flush()
            result = parse_ooh_page(f.name)
        os.unlink(f.name)
        assert "## Quick Facts" in result
        assert "$50,000 per year" in result
        assert "Bachelor's degree" in result

    def test_extracts_section(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.MINIMAL_HTML)
            f.flush()
            result = parse_ooh_page(f.name)
        os.unlink(f.name)
        assert "## What They Do" in result
        assert "Test workers do test things." in result

    def test_extracts_source_url(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.MINIMAL_HTML)
            f.flush()
            result = parse_ooh_page(f.name)
        os.unlink(f.name)
        assert "https://example.com/test" in result

    def test_extracts_last_modified(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(self.MINIMAL_HTML)
            f.flush()
            result = parse_ooh_page(f.name)
        os.unlink(f.name)
        assert "Last Modified: 2024-01-01" in result
