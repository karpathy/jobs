"""
Scrape Jobs and Skills Australia occupation profile pages (raw HTML).

Saves raw HTML to html/<slug>.html as the source of truth.
Run process.py afterwards to derive pages/<slug>.md.

Usage:
    uv run python scrape.py                      # scrape all
    uv run python scrape.py --start 0 --end 5    # scrape first 5
    uv run python scrape.py --force               # re-scrape ignoring cache

Caching: skips any occupation where html/<slug>.html already exists.
"""

import argparse
import json
import os
import time
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Main scraper
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Scrape JSA occupation profile pages")
    parser.add_argument("--start", type=int, default=0, help="Start index (inclusive)")
    parser.add_argument("--end", type=int, default=None, help="End index (exclusive)")
    parser.add_argument("--force", action="store_true", help="Re-scrape even if cached")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    args = parser.parse_args()

    # Load master list
    with open("occupations.json") as f:
        occupations = json.load(f)

    end = args.end if args.end is not None else len(occupations)
    subset = occupations[args.start:end]

    # Create output dirs
    os.makedirs("html", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("pages", exist_ok=True)

    # Figure out what needs scraping (cache based on html/ existence)
    to_scrape = []
    for i, occ in enumerate(subset, start=args.start):
        html_path = f"html/{occ['slug']}.html"
        if not args.force and os.path.exists(html_path):
            print(f"  [{i}] CACHED {occ['title']}")
            continue
        to_scrape.append((i, occ))

    if not to_scrape:
        print("Nothing to scrape — all cached.")
        return

    print(f"\nScraping {len(to_scrape)} occupations (non-headless Chromium)...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for idx, (i, occ) in enumerate(to_scrape):
            slug = occ["slug"]
            url = occ["url"]
            html_path = f"html/{slug}.html"

            print(f"  [{i}] {occ['title']}...", end=" ", flush=True)

            try:
                resp = page.goto(url, wait_until="networkidle", timeout=30000)
                if resp.status != 200:
                    print(f"HTTP {resp.status} — SKIPPED")
                    continue

                # Wait for dynamic content to load
                page.wait_for_timeout(2000)

                # Save raw HTML — this is the source of truth
                html = page.content()
                with open(html_path, "w") as f:
                    f.write(html)

                print(f"OK ({len(html):,} bytes)")

            except Exception as e:
                print(f"ERROR: {e}")

            # Be polite
            if idx < len(to_scrape) - 1:
                time.sleep(args.delay)

        browser.close()

    # Summary
    cached = len([f for f in os.listdir("html") if f.endswith(".html")])
    print(f"\nDone. {cached}/{len(occupations)} HTML files cached in html/")


if __name__ == "__main__":
    main()
