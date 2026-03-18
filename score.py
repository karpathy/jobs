"""
Score each occupation's AI exposure using an LLM via OpenRouter.

Supports two input modes:
  1. Markdown descriptions from pages/<slug>.md (legacy BLS pipeline)
  2. ISCO-08 occupation titles from occupations_cy.json (Cyprus pipeline)

Results are cached incrementally to scores.json so the script can be
resumed if interrupted.

Usage:
    uv run python score.py                                    # auto-detect input
    uv run python score.py --occupations occupations_cy.json  # Cyprus occupations
    uv run python score.py --model google/gemini-3-flash-preview
    uv run python score.py --start 0 --end 10                 # test on first 10
"""

import argparse
import json
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "google/gemini-3-flash-preview"
OUTPUT_FILE = "scores.json"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """\
You are an expert labour market analyst evaluating how exposed different \
occupations are to AI. You will be given an occupation description based on \
the ISCO-08 international classification, in the context of the Cyprus and \
EU labour market.

Rate the occupation's overall **AI Exposure** on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation? Consider both \
direct effects (AI automating tasks currently done by humans) and indirect \
effects (AI making each worker so productive that fewer are needed).

A key signal is whether the job's work product is fundamentally digital. If \
the job can be done entirely from a home office on a computer — writing, \
coding, analysing, communicating — then AI exposure is inherently high (7+), \
because AI capabilities in digital domains are advancing rapidly. Even if \
today's AI can't handle every aspect of such a job, the trajectory is steep \
and the ceiling is very high. Conversely, jobs requiring physical presence, \
manual skill, or real-time human interaction in the physical world have a \
natural barrier to AI exposure.

Consider the Cyprus/EU context where relevant:
- Tourism and hospitality are major employers in Cyprus
- Financial services and shipping are key sectors
- The EU Digital Decade targets drive digital skills demand
- Public sector employment is proportionally larger than in the US
- Construction and real estate are significant economic drivers

Use these anchors to calibrate your score:

- **0–1: Minimal exposure.** The work is almost entirely physical, hands-on, \
or requires real-time human presence in unpredictable environments. AI has \
essentially no impact on daily work. \
Examples: agricultural labourer, construction labourer, commercial diver.

- **2–3: Low exposure.** Mostly physical or interpersonal work. AI might help \
with minor peripheral tasks (scheduling, paperwork) but doesn't touch the \
core job. \
Examples: electrician, plumber, firefighter, building trades worker.

- **4–5: Moderate exposure.** A mix of physical/interpersonal work and \
knowledge work. AI can meaningfully assist with the information-processing \
parts but a substantial share of the job still requires human presence. \
Examples: health associate professional, police officer, personal care worker.

- **6–7: High exposure.** Predominantly knowledge work with some need for \
human judgment, relationships, or physical presence. AI tools are already \
useful and workers using AI may be substantially more productive. \
Examples: teaching professional, manager, business administration professional.

- **8–9: Very high exposure.** The job is almost entirely done on a computer. \
All core tasks — writing, coding, analysing, designing, communicating — are \
in domains where AI is rapidly improving. The occupation faces major \
restructuring. \
Examples: ICT professional, legal professional, business/admin associate \
professional.

- **10: Maximum exposure.** Routine information processing, fully digital, \
with no physical component. AI can already do most of it today. \
Examples: general clerk, numerical recording clerk, data entry operator.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors>"
}\
"""


def parse_llm_response(content):
    """Parse LLM response, stripping markdown fences if present.

    Args:
        content: Raw text content from LLM response.

    Returns:
        Parsed dict with 'exposure' and 'rationale' keys.
    """
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def score_occupation(client, text, model):
    """Send one occupation to the LLM and parse the structured response."""
    response = client.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return parse_llm_response(content)


def build_isco_prompt(occ):
    """Build a scoring prompt from an ISCO-08 occupation entry.

    When no detailed markdown description is available, constructs a
    prompt from the occupation metadata (title, ISCO code, category).

    Args:
        occ: Dict with title, isco_code, category_label, etc.

    Returns:
        String prompt for LLM scoring.
    """
    lines = [f"# {occ['title']}"]
    lines.append("")

    if occ.get("isco_code"):
        lines.append(f"**ISCO-08 Code:** {occ['isco_code']}")
    if occ.get("category_label"):
        lines.append(f"**Major Group:** {occ['category_label']}")
    lines.append("")
    lines.append(
        f'This is the ISCO-08 sub-major group "{occ["title"]}". '
        "Score this occupation group's AI exposure based on the typical "
        "duties and work environment of workers in this category within "
        "the Cyprus/EU labour market."
    )

    return "\n".join(lines)


def detect_occupation_format(occupations):
    """Detect whether occupation list is BLS or Cyprus format."""
    if occupations and "isco_code" in occupations[0]:
        return "cyprus"
    return "bls"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--occupations", default=None, help="Occupations JSON file (auto-detects)")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--force", action="store_true", help="Re-score even if already cached")
    args = parser.parse_args()

    # Auto-detect occupations file
    occ_path = args.occupations
    if occ_path is None:
        if os.path.exists("occupations_cy.json"):
            occ_path = "occupations_cy.json"
        elif os.path.exists("occupations.json"):
            occ_path = "occupations.json"
        else:
            print("Error: no occupations JSON found.")
            return

    with open(occ_path) as f:
        occupations = json.load(f)

    fmt = detect_occupation_format(occupations)
    print(f"Using {occ_path} ({fmt} format)")

    subset = occupations[args.start : args.end]

    # Load existing scores
    scores = {}
    if os.path.exists(OUTPUT_FILE) and not args.force:
        with open(OUTPUT_FILE) as f:
            for entry in json.load(f):
                scores[entry["slug"]] = entry

    print(f"Scoring {len(subset)} occupations with {args.model}")
    print(f"Already cached: {len(scores)}")

    errors = []
    client = httpx.Client()

    for i, occ in enumerate(subset):
        slug = occ["slug"]

        if slug in scores:
            continue

        # Build prompt text: prefer markdown file, fall back to ISCO prompt
        md_path = f"pages/{slug}.md"
        if os.path.exists(md_path):
            with open(md_path) as f:
                text = f.read()
        elif fmt == "cyprus":
            text = build_isco_prompt(occ)
        else:
            print(f"  [{i + 1}] SKIP {slug} (no markdown)")
            continue

        print(f"  [{i + 1}/{len(subset)}] {occ['title']}...", end=" ", flush=True)

        try:
            result = score_occupation(client, text, args.model)
            scores[slug] = {
                "slug": slug,
                "title": occ["title"],
                **result,
            }
            print(f"exposure={result['exposure']}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(slug)

        # Save after each one (incremental checkpoint)
        with open(OUTPUT_FILE, "w") as f:
            json.dump(list(scores.values()), f, indent=2)

        if i < len(subset) - 1:
            time.sleep(args.delay)

    client.close()

    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")
    if errors:
        print(f"Errors: {errors}")

    # Summary stats
    vals = [s for s in scores.values() if "exposure" in s]
    if vals:
        avg = sum(s["exposure"] for s in vals) / len(vals)
        by_score = {}
        for s in vals:
            bucket = s["exposure"]
            by_score[bucket] = by_score.get(bucket, 0) + 1
        print(f"\nAverage exposure across {len(vals)} occupations: {avg:.1f}")
        print("Distribution:")
        for k in sorted(by_score):
            print(f"  {k}: {'█' * by_score[k]} ({by_score[k]})")


if __name__ == "__main__":
    main()
