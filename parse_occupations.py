"""
Parse occupation index page to extract all occupations.

Currently parses BLS OOH A-Z index. Will be replaced with parsers for
HRDA occupation listings and Eurostat ISCO-08 codes for Cyprus.
"""

import json

from bs4 import BeautifulSoup

with open("occupational_outlook_handbook.html") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# The occupation listings are inside <div class="a-z-list">
az_list = soup.find("div", class_="a-z-list")

# Each <li> contains either:
# 1. A direct link: <a href="url">Occupation Name</a>
# 2. An alias: <a href="url">Alias</a>, see: <a href="url">Canonical Name</a>
#
# We want the unique canonical occupations (deduplicated by URL).

occupations = {}  # url -> canonical name
aliases = []  # list of (alias_name, canonical_name, url)

for li in az_list.find_all("li"):
    links = li.find_all("a")
    text = li.get_text()

    if ", see:" in text or ", see " in text:
        # This is an alias entry — the second link is the canonical one
        if len(links) >= 2:
            alias_name = links[0].get_text(strip=True)
            canonical_name = links[1].get_text(strip=True)
            url = links[1]["href"]
            aliases.append((alias_name, canonical_name, url))
            # Still register the canonical occupation
            if url not in occupations:
                occupations[url] = canonical_name
    else:
        # Direct entry
        if links:
            name = links[0].get_text(strip=True)
            url = links[0]["href"]
            if url not in occupations:
                occupations[url] = name

# Sort by name
sorted_occupations = sorted(occupations.items(), key=lambda x: x[1].lower())

print(f"Total unique occupations: {len(sorted_occupations)}")
print(f"Total aliases (redirects): {len(aliases)}")
print()
print("--- First 20 occupations ---")
for url, name in sorted_occupations[:20]:
    print(f"  {name}")
    print(f"    {url}")
print("...")
print()
print("--- Last 10 occupations ---")
for url, name in sorted_occupations[-10:]:
    print(f"  {name}")
    print(f"    {url}")

# Save to JSON for further analysis
output = []
for url, name in sorted_occupations:
    output.append({"title": name, "url": url})

with open("occupations.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved {len(output)} occupations to occupations.json")
