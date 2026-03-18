"""
Parse an occupation detail page into a clean Markdown document.

Currently parses BLS OOH HTML format. Will be extended to handle
Cyprus-specific data sources (HRDA, Eurostat) in future iterations.
"""

import re
import sys

from bs4 import BeautifulSoup


def clean(text):
    """Clean up whitespace from extracted text."""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_ooh_page(html_path):
    with open(html_path) as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    md = []

    # --- Title ---
    h1 = soup.find("h1")
    title = clean(h1.get_text()) if h1 else "Unknown Occupation"
    md.append(f"# {title}")
    md.append("")

    # --- Source URL ---
    canonical = soup.find("link", rel="canonical")
    if canonical:
        md.append(f"**Source:** {canonical['href']}")
        md.append("")

    # --- Quick Facts ---
    qf_table = soup.find("table", id="quickfacts")
    if qf_table:
        md.append("## Quick Facts")
        md.append("")
        md.append("| Field | Value |")
        md.append("|-------|-------|")
        for row in qf_table.find("tbody").find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                field = clean(th.get_text())
                value = clean(td.get_text())
                md.append(f"| {field} | {value} |")
        md.append("")

    # --- Tab sections ---
    panes = soup.find("div", id="panes")
    if not panes:
        return "\n".join(md)

    tab_ids = ["tab-1", "tab-2", "tab-3", "tab-4", "tab-5", "tab-6", "tab-7", "tab-8", "tab-9"]
    # Skip tab-1 (Summary, already covered by quick facts) and tab-7 (State & Area Data, just links)

    for tab_id in tab_ids:
        tab_div = panes.find("div", id=tab_id)
        if not tab_div:
            continue

        article = tab_div.find("article")
        if not article:
            # tab-8 (Similar Occupations) doesn't have an article wrapper
            article = tab_div

        h2 = article.find("h2")
        if not h2:
            continue
        section_title = clean(h2.find("span").get_text()) if h2.find("span") else clean(h2.get_text())

        # Skip tabs we don't need
        if tab_id in (
            "tab-1",  # Summary (redundant with Quick Facts)
            "tab-7",  # State & Area Data (just links)
            "tab-8",  # Similar Occupations
            "tab-9",
        ):  # Contacts for More Information
            continue

        md.append(f"## {section_title}")
        md.append("")

        # --- Generic tab: extract paragraphs, headers, lists, tables ---
        # Process the pay chart if present
        chart_div = article.find("div", class_="ooh-chart")
        if chart_div:
            # Extract the bar chart data
            chart_subtitle = chart_div.find("p")
            dts = chart_div.find("dl")
            if dts:
                items = []
                dt_list = dts.find_all("dt")
                dd_list = dts.find_all("dd")
                for dt, dd in zip(dt_list, dd_list, strict=False):
                    label = clean(dt.get_text())
                    # find the value span
                    val_spans = dd.find_all("span")
                    for s in val_spans:
                        val_text = clean(s.get_text())
                        if val_text and (val_text.startswith("$") or val_text.endswith("%")):
                            items.append((label, val_text))
                            break
                if items:
                    subtitle = clean(chart_subtitle.get_text()) if chart_subtitle else ""
                    if subtitle:
                        md.append(f"*{subtitle}*")
                        md.append("")
                    for label, val in items:
                        md.append(f"- **{label}**: {val}")
                    md.append("")

        # Now process remaining content (skip chart divs)
        for elem in article.children:
            if hasattr(elem, "name"):
                if elem.name == "h2":
                    continue  # already printed
                if elem.name == "div" and elem.get("class") and "ooh-chart" in elem.get("class", []):
                    continue  # already handled
                if elem.name == "div" and elem.get("class") and "ooh_right_img" in elem.get("class", []):
                    continue  # skip images
                if elem.name == "h3":
                    md.append(f"### {clean(elem.get_text())}")
                    md.append("")
                elif elem.name == "p":
                    text = clean(elem.get_text())
                    if text:
                        md.append(text)
                        md.append("")
                elif elem.name == "ul":
                    for li in elem.find_all("li"):
                        md.append(f"- {clean(li.get_text())}")
                    md.append("")
                elif elem.name == "table":
                    # Skip the outlook-table (handled separately below)
                    if elem.get("id") == "outlook-table":
                        continue
                    # Parse generic table (employer breakdown, pay by industry, etc.)
                    rows = elem.find_all("tr")
                    if rows:
                        table_data = []
                        for row in rows:
                            cells = row.find_all(["td", "th"])
                            row_data = [clean(c.get_text()) for c in cells]
                            if row_data and any(row_data):
                                table_data.append(row_data)
                        if table_data:
                            max_cols = max(len(r) for r in table_data)
                            for r in table_data:
                                while len(r) < max_cols:
                                    r.append("")
                            # Render as simple rows (no header row for these tables)
                            md.append("| " + " | ".join(["---"] * max_cols) + " |")
                            for row_data in table_data:
                                md.append("| " + " | ".join(row_data) + " |")
                            md.append("")

        # Employment projections table (in Job Outlook tab)
        if tab_id == "tab-6":
            outlook_table = article.find("table", id="outlook-table")
            if outlook_table:
                md.append("### Employment Projections")
                md.append("")
                tbody = outlook_table.find("tbody")
                if tbody:
                    for row in tbody.find_all("tr"):
                        cells = row.find_all(["td", "th"])
                        values = [clean(c.get_text()) for c in cells]
                        if values:
                            # Format: Title, SOC, Employment 2024, Projected 2034, % change, numeric change
                            labels = [
                                "Occupational Title",
                                "SOC Code",
                                "Employment 2024",
                                "Projected Employment 2034",
                                "Change % 2024-34",
                                "Change Numeric 2024-34",
                            ]
                            for label, val in zip(labels, values, strict=False):
                                if val and val != "Get data":
                                    md.append(f"- **{label}:** {val}")
                            md.append("")

    # --- Last Modified ---
    update_p = soup.find("p", class_="update")
    if update_p:
        md.append("---")
        md.append(f"*{clean(update_p.get_text())}*")
        md.append("")

    return "\n".join(md)


if __name__ == "__main__":
    html_path = sys.argv[1] if len(sys.argv) > 1 else "electrician.html"
    result = parse_ooh_page(html_path)

    # Write output
    out_path = html_path.replace(".html", ".md")
    with open(out_path, "w") as f:
        f.write(result)
    print(f"Written to {out_path}")
    print()
    print(result)
