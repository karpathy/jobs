"""
Score each occupation's AI exposure, advantage, or growth using an LLM via OpenRouter.

Reads Markdown descriptions from pages/, sends each to an LLM with a scoring
rubric, and collects structured scores. Results are cached incrementally to
a per-metric JSON file so the script can be resumed if interrupted.

Usage:
    uv run python score.py                        # default: exposure
    uv run python score.py --metric advantage
    uv run python score.py --metric growth
    uv run python score.py --model google/gemini-3-flash-preview
    uv run python score.py --start 0 --end 10     # test on first 10
"""

import argparse
import json
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "google/gemini-3-flash-preview"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Metric configs ────────────────────────────────────────────────────────

EXPOSURE_PROMPT = """\
You are an expert analyst evaluating how exposed different occupations are to \
AI. You will be given a detailed description of an occupation from the Bureau \
of Labor Statistics.

Rate the occupation's overall **AI Exposure** on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation? Consider both \
direct effects (AI automating tasks currently done by humans) and indirect \
effects (AI making each worker so productive that fewer are needed).

A key signal is whether the job's work product is fundamentally digital. If \
the job can be done entirely from a home office on a computer — writing, \
coding, analyzing, communicating — then AI exposure is inherently high (7+), \
because AI capabilities in digital domains are advancing rapidly. Even if \
today's AI can't handle every aspect of such a job, the trajectory is steep \
and the ceiling is very high. Conversely, jobs requiring physical presence, \
manual skill, or real-time human interaction in the physical world have a \
natural barrier to AI exposure.

Use these anchors to calibrate your score:

- **0–1: Minimal exposure.** The work is almost entirely physical, hands-on, \
or requires real-time human presence in unpredictable environments. AI has \
essentially no impact on daily work. \
Examples: roofer, landscaper, commercial diver.

- **2–3: Low exposure.** Mostly physical or interpersonal work. AI might help \
with minor peripheral tasks (scheduling, paperwork) but doesn't touch the \
core job. \
Examples: electrician, plumber, firefighter, dental hygienist.

- **4–5: Moderate exposure.** A mix of physical/interpersonal work and \
knowledge work. AI can meaningfully assist with the information-processing \
parts but a substantial share of the job still requires human presence. \
Examples: registered nurse, police officer, veterinarian.

- **6–7: High exposure.** Predominantly knowledge work with some need for \
human judgment, relationships, or physical presence. AI tools are already \
useful and workers using AI may be substantially more productive. \
Examples: teacher, manager, accountant, journalist.

- **8–9: Very high exposure.** The job is almost entirely done on a computer. \
All core tasks — writing, coding, analyzing, designing, communicating — are \
in domains where AI is rapidly improving. The occupation faces major \
restructuring. \
Examples: software developer, graphic designer, translator, data analyst, \
paralegal, copywriter.

- **10: Maximum exposure.** Routine information processing, fully digital, \
with no physical component. AI can already do most of it today. \
Examples: data entry clerk, telemarketer.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors>"
}\
"""

ADVANTAGE_PROMPT = """\
You are an expert analyst evaluating how much workers in different occupations \
can benefit from adopting AI tools. You will be given a detailed description \
of an occupation from the Bureau of Labor Statistics.

Rate the occupation's **AI Advantage** on a scale from 0 to 10.

AI Advantage measures: how much can a worker in this occupation amplify their \
productivity and competitive edge by adopting AI tools? Consider:
- Can AI automate repetitive parts of their work, freeing time for higher-value tasks?
- Does using AI tools create a meaningful gap between adopters and non-adopters?
- How much faster/better can the core work product become with AI assistance?

Use these anchors to calibrate your score:

- **0–1: Minimal.** Work is physical/manual, AI tools barely relevant. \
Examples: roofer, landscaper.

- **2–3: Low.** Mostly hands-on; AI helps with paperwork but not core work. \
Examples: electrician, firefighter.

- **4–5: Moderate.** Mix of physical and knowledge work; AI assists the desk portions. \
Examples: nurse, veterinarian.

- **6–7: High.** Mostly knowledge work; AI tools already boost productivity significantly. \
Examples: teacher, accountant.

- **8–9: Very high.** Almost entirely digital; AI copilots transform every core task. \
Examples: software developer, graphic designer.

- **10: Maximum.** AI can handle nearly all tasks; early adopters are dramatically more productive. \
Examples: data entry clerk.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "advantage": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors>"
}\
"""

GROWTH_PROMPT = """\
You are an expert analyst evaluating how AI will affect demand for different \
occupations. You will be given a detailed description of an occupation from \
the Bureau of Labor Statistics.

Rate the occupation's **AI Growth** on a scale from 0 to 10.

AI Growth measures: how much will AI expand demand, create new sub-roles, or \
grow the market for this occupation? Consider:
- Will AI make this service cheaper/faster, unlocking latent demand?
- Does AI create new problem domains that need this occupation?
- Will productivity gains lead to more hiring (elastic demand) or less (inelastic)?
- Are there regulatory, trust, or social factors that sustain or grow demand?

Use these anchors to calibrate your score:

- **0–1: Shrinking.** AI directly replaces demand; fewer workers needed. \
Examples: data entry clerk, telemarketer.

- **2–3: Flat.** AI doesn't meaningfully change demand. \
Examples: roofer, bus driver.

- **4–5: Stable+.** New AI-adjacent demand roughly offsets automation. \
Examples: accountant, paralegal.

- **6–7: Growing.** AI creates meaningful new demand or accessibility. \
Examples: nurse, teacher, trades.

- **8–9: Strongly growing.** AI opens major new markets or sub-specialties. \
Examples: cybersecurity analyst, data engineer.

- **10: Explosive.** Entirely new demand driven by AI. \
Examples: AI/ML engineer, prompt engineer.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "growth": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors>"
}\
"""

METRIC_CONFIG = {
    "exposure": {
        "prompt": EXPOSURE_PROMPT,
        "output_file": "scores.json",
        "score_key": "exposure",
    },
    "advantage": {
        "prompt": ADVANTAGE_PROMPT,
        "output_file": "scores_advantage.json",
        "score_key": "advantage",
    },
    "growth": {
        "prompt": GROWTH_PROMPT,
        "output_file": "scores_growth.json",
        "score_key": "growth",
    },
}


def score_occupation(client, text, model, system_prompt):
    """Send one occupation to the LLM and parse the structured response."""
    response = client.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]  # remove first line
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--metric", default="exposure",
                        choices=["exposure", "advantage", "growth"],
                        help="Which metric to score (default: exposure)")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--force", action="store_true",
                        help="Re-score even if already cached")
    args = parser.parse_args()

    cfg = METRIC_CONFIG[args.metric]
    output_file = cfg["output_file"]
    score_key = cfg["score_key"]
    system_prompt = cfg["prompt"]

    with open("occupations.json") as f:
        occupations = json.load(f)

    subset = occupations[args.start:args.end]

    # Load existing scores
    scores = {}
    if os.path.exists(output_file) and not args.force:
        with open(output_file) as f:
            for entry in json.load(f):
                scores[entry["slug"]] = entry

    print(f"Scoring {len(subset)} occupations for '{args.metric}' with {args.model}")
    print(f"Output: {output_file}")
    print(f"Already cached: {len(scores)}")

    errors = []
    client = httpx.Client()

    for i, occ in enumerate(subset):
        slug = occ["slug"]

        if slug in scores:
            continue

        md_path = f"pages/{slug}.md"
        if not os.path.exists(md_path):
            print(f"  [{i+1}] SKIP {slug} (no markdown)")
            continue

        with open(md_path) as f:
            text = f.read()

        print(f"  [{i+1}/{len(subset)}] {occ['title']}...", end=" ", flush=True)

        try:
            result = score_occupation(client, text, args.model, system_prompt)
            scores[slug] = {
                "slug": slug,
                "title": occ["title"],
                **result,
            }
            print(f"{score_key}={result[score_key]}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(slug)

        # Save after each one (incremental checkpoint)
        with open(output_file, "w") as f:
            json.dump(list(scores.values()), f, indent=2)

        if i < len(subset) - 1:
            time.sleep(args.delay)

    client.close()

    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")
    if errors:
        print(f"Errors: {errors}")

    # Summary stats
    vals = [s for s in scores.values() if score_key in s]
    if vals:
        avg = sum(s[score_key] for s in vals) / len(vals)
        by_score = {}
        for s in vals:
            bucket = s[score_key]
            by_score[bucket] = by_score.get(bucket, 0) + 1
        print(f"\nAverage {score_key} across {len(vals)} occupations: {avg:.1f}")
        print("Distribution:")
        for k in sorted(by_score):
            print(f"  {k}: {'█' * by_score[k]} ({by_score[k]})")


if __name__ == "__main__":
    main()
