"""
Build occupations.json by scraping the Jobs and Skills Australia occupations index.

Scrapes the JSA occupations listing page to extract all ANZSCO 4-digit
occupation groups with their titles, URLs, categories, and codes.

Usage:
    uv run python build_occupations.py
    uv run python build_occupations.py --level 6    # include 6-digit occupations too

Output: occupations.json
"""

import argparse
import json
import re
from playwright.sync_api import sync_playwright

JSA_BASE = "https://www.jobsandskills.gov.au"
OCCUPATIONS_URL = f"{JSA_BASE}/data/occupation-and-industry-profiles/occupations"

# ANZSCO major group categories (1-digit)
ANZSCO_MAJOR_GROUPS = {
    "1": "managers",
    "2": "professionals",
    "3": "technicians-and-trades-workers",
    "4": "community-and-personal-service-workers",
    "5": "clerical-and-administrative-workers",
    "6": "sales-workers",
    "7": "machinery-operators-and-drivers",
    "8": "labourers",
}


def slugify(title):
    """Convert a title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def get_category(anzsco_code):
    """Get the major group category from an ANZSCO code."""
    if anzsco_code and len(anzsco_code) >= 1:
        return ANZSCO_MAJOR_GROUPS.get(anzsco_code[0], "other")
    return "other"


def main():
    parser = argparse.ArgumentParser(description="Build occupations.json from JSA")
    parser.add_argument("--level", type=int, default=4, choices=[4, 6],
                        help="ANZSCO level: 4 (unit groups) or 6 (individual occupations)")
    args = parser.parse_args()

    print(f"Scraping JSA occupations index (ANZSCO {args.level}-digit level)...")

    occupations = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to the occupations listing
        page.goto(OCCUPATIONS_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # Look for occupation links
        # JSA URL pattern: /occupations/{ANZSCO}-{slug}
        links = page.query_selector_all("a")
        seen_codes = set()

        for link in links:
            href = link.get_attribute("href") or ""
            text = (link.inner_text() or "").strip()

            if not text or not href:
                continue

            # Match JSA occupation URL pattern
            # e.g., /occupations/2211-accountants or /occupations/221111-accountants-general
            match = re.search(r'/occupations/(\d{4,6})-(.+?)(?:\?|#|$)', href)
            if not match:
                continue

            code = match.group(1)
            url_slug = match.group(2)

            # Filter by level
            if args.level == 4 and len(code) != 4:
                continue
            if args.level == 6 and len(code) != 6:
                continue

            if code in seen_codes:
                continue
            seen_codes.add(code)

            # Build full URL
            if href.startswith("/"):
                full_url = JSA_BASE + href
            elif href.startswith("http"):
                full_url = href
            else:
                full_url = f"{OCCUPATIONS_URL}/{code}-{url_slug}"

            category = get_category(code)
            slug = f"{code}-{url_slug}"

            occupations.append({
                "title": text,
                "url": full_url,
                "category": category,
                "slug": slug,
                "anzsco_code": code,
            })

        # If the page has pagination or "load more", try scrolling
        prev_count = 0
        max_scrolls = 20
        for _ in range(max_scrolls):
            if len(occupations) == prev_count and prev_count > 0:
                break
            prev_count = len(occupations)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)

            # Re-scan for new links
            links = page.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href") or ""
                text = (link.inner_text() or "").strip()

                if not text or not href:
                    continue

                match = re.search(r'/occupations/(\d{4,6})-(.+?)(?:\?|#|$)', href)
                if not match:
                    continue

                code = match.group(1)
                url_slug = match.group(2)

                if args.level == 4 and len(code) != 4:
                    continue
                if args.level == 6 and len(code) != 6:
                    continue

                if code in seen_codes:
                    continue
                seen_codes.add(code)

                if href.startswith("/"):
                    full_url = JSA_BASE + href
                elif href.startswith("http"):
                    full_url = href
                else:
                    full_url = f"{OCCUPATIONS_URL}/{code}-{url_slug}"

                category = get_category(code)
                slug = f"{code}-{url_slug}"

                occupations.append({
                    "title": text,
                    "url": full_url,
                    "category": category,
                    "slug": slug,
                    "anzsco_code": code,
                })

        browser.close()

    # Sort by ANZSCO code
    occupations.sort(key=lambda x: x["anzsco_code"])

    # Write output
    with open("occupations.json", "w") as f:
        json.dump(occupations, f, indent=2)

    print(f"\nWrote {len(occupations)} occupations to occupations.json")

    # Summary by category
    by_cat = {}
    for occ in occupations:
        cat = occ["category"]
        by_cat[cat] = by_cat.get(cat, 0) + 1
    print("\nBy category:")
    for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
