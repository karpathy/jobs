"""Parse a Jobs and Skills Australia occupation profile page into a clean Markdown document."""

import sys
import re
from bs4 import BeautifulSoup

def clean(text):
    """Clean up whitespace from extracted text."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_jsa_page(html_path):
    """Parse a JSA occupation profile page into Markdown."""
    with open(html_path, "r") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    md = []

    # --- Title ---
    h1 = soup.find("h1")
    title = clean(h1.get_text()) if h1 else "Unknown Occupation"
    md.append(f"# {title}")
    md.append("")

    # --- Source URL ---
    canonical = soup.find("link", rel="canonical")
    if canonical and canonical.get("href"):
        md.append(f"**Source:** {canonical['href']}")
        md.append("")

    # --- Quick stats / Key facts ---
    # JSA pages typically have key stats in structured sections
    # Look for common stat containers
    for section in soup.find_all(["div", "section"]):
        heading = section.find(["h2", "h3"])
        if not heading:
            continue
        heading_text = clean(heading.get_text()).lower()

        # Skip navigation and irrelevant sections
        if any(skip in heading_text for skip in ["menu", "footer", "navigation", "breadcrumb"]):
            continue

        section_title = clean(heading.get_text())
        if not section_title:
            continue

        # Extract content from the section
        content_parts = []

        # Get all paragraphs
        for p in section.find_all("p", recursive=False):
            text = clean(p.get_text())
            if text and len(text) > 5:
                content_parts.append(text)

        # Get all list items
        for ul in section.find_all("ul", recursive=False):
            for li in ul.find_all("li"):
                text = clean(li.get_text())
                if text:
                    content_parts.append(f"- {text}")

        # Get all definition lists (common in JSA for stats)
        for dl in section.find_all("dl", recursive=False):
            dts = dl.find_all("dt")
            dds = dl.find_all("dd")
            for dt, dd in zip(dts, dds):
                label = clean(dt.get_text())
                value = clean(dd.get_text())
                if label and value:
                    content_parts.append(f"- **{label}:** {value}")

        # Get tables
        for table in section.find_all("table", recursive=False):
            rows = table.find_all("tr")
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
                    # Header row
                    content_parts.append("| " + " | ".join(table_data[0]) + " |")
                    content_parts.append("| " + " | ".join(["---"] * max_cols) + " |")
                    for row_data in table_data[1:]:
                        content_parts.append("| " + " | ".join(row_data) + " |")

        if content_parts:
            md.append(f"## {section_title}")
            md.append("")
            md.extend(content_parts)
            md.append("")

    # --- Fallback: extract all meaningful text if sections yielded little ---
    if len(md) < 5:
        # Extract key stat values from common patterns
        for elem in soup.find_all(["span", "div", "p"]):
            text = clean(elem.get_text())
            # Look for earnings patterns (e.g., "$1,889 per week")
            if re.search(r'\$[\d,]+\s*per\s*week', text):
                md.append(f"- {text}")
            # Look for employment numbers
            elif re.search(r'[\d,]+\s*(employed|workers|people)', text, re.I):
                md.append(f"- {text}")
            # Look for growth percentages
            elif re.search(r'[\d.]+%\s*(growth|decline|change)', text, re.I):
                md.append(f"- {text}")
        md.append("")

    # --- Last Modified ---
    update_elem = soup.find(string=re.compile(r'last updated|modified|published', re.I))
    if update_elem:
        md.append("---")
        md.append(f"*{clean(update_elem)}*")
        md.append("")

    return "\n".join(md)


# Keep backward compatibility alias
parse_ooh_page = parse_jsa_page


if __name__ == "__main__":
    html_path = sys.argv[1] if len(sys.argv) > 1 else "electrician.html"
    result = parse_jsa_page(html_path)

    # Write output
    out_path = html_path.replace(".html", ".md")
    with open(out_path, "w") as f:
        f.write(result)
    print(f"Written to {out_path}")
    print()
    print(result)
