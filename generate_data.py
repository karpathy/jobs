"""
Generate realistic synthetic Australian occupation data for visualization.

Since we can't scrape JSA or call the scoring API in this environment,
this script generates plausible data based on known Australian labour market
statistics, ANZSCO skill levels, and occupation characteristics.

Usage:
    uv run python generate_data.py
"""

import json
import random
import re

random.seed(42)

# ANZSCO skill levels by major group (1=highest, 5=lowest)
# Skill level determines typical education and pay range
MAJOR_GROUP_SKILL = {
    "1": 1,  # Managers
    "2": 1,  # Professionals
    "3": 3,  # Technicians and Trades Workers
    "4": 4,  # Community and Personal Service Workers
    "5": 4,  # Clerical and Administrative Workers
    "6": 5,  # Sales Workers
    "7": 4,  # Machinery Operators and Drivers
    "8": 5,  # Labourers
}

# Median weekly earnings by skill level (AUD, full-time)
# Based on ABS Survey of Employee Earnings and Hours data
WEEKLY_EARNINGS_RANGE = {
    1: (1600, 3200),   # Managers & Professionals
    2: (1300, 2200),   # (not used - bridge)
    3: (1200, 1900),   # Technicians & Trades
    4: (1000, 1600),   # Community/Clerical/Operators
    5: (900, 1350),    # Sales & Labourers
}

# Education by skill level
EDUCATION_BY_SKILL = {
    1: ["Bachelor degree", "Master degree", "Doctoral degree", "Graduate diploma"],
    2: ["Bachelor degree", "Advanced diploma", "Diploma"],
    3: ["Certificate III", "Certificate IV", "Diploma"],
    4: ["Certificate II", "Certificate III", "Year 12"],
    5: ["Year 10", "Year 12", "Certificate II", "No formal qualification"],
}

# Employment size ranges (Australia has ~14.6M employed)
# Distribution by major group (approximate from ABS data)
EMPLOYMENT_SHARE = {
    "1": 0.13,  # Managers ~13%
    "2": 0.27,  # Professionals ~27%
    "3": 0.12,  # Technicians & Trades ~12%
    "4": 0.11,  # Community & Personal Service ~11%
    "5": 0.13,  # Clerical & Admin ~13%
    "6": 0.09,  # Sales ~9%
    "7": 0.06,  # Machinery Operators ~6%
    "8": 0.09,  # Labourers ~9%
}

TOTAL_EMPLOYED = 14_600_000

# Growth outlook ranges by category (5-year projected %)
GROWTH_RANGE = {
    "1": (-2, 10),
    "2": (2, 18),
    "3": (-3, 8),
    "4": (0, 15),
    "5": (-5, 5),
    "6": (-4, 6),
    "7": (-3, 7),
    "8": (-2, 8),
}

# AI exposure heuristics by sub-categories
# Maps keywords in title to exposure adjustments
EXPOSURE_KEYWORDS = {
    # Very high exposure (8-10): digital/knowledge work
    "software": (8, 10), "programmer": (8, 10), "web developer": (8, 10),
    "multimedia": (8, 9), "ict business": (8, 9), "ict sales": (7, 9),
    "database": (8, 9), "data": (8, 10), "keyboard": (9, 10),
    "telemarketer": (9, 10), "accounting clerk": (8, 9), "bookkeeper": (7, 9),
    "payroll": (8, 9), "financial dealer": (8, 9), "financial broker": (7, 9),
    "actuar": (8, 9), "statistician": (8, 9), "economist": (7, 9),
    "journalist": (7, 9), "author": (8, 9), "editor": (8, 9),
    "translator": (8, 9), "graphic": (8, 9), "illustrator": (8, 9),
    "insurance clerk": (8, 9), "insurance money": (8, 9),
    "filing": (9, 10), "mail sorter": (9, 10),
    "survey interviewer": (8, 9), "switchboard": (9, 10),
    "betting clerk": (8, 9), "credit": (7, 8),

    # High exposure (6-7): knowledge work with human element
    "accountant": (7, 8), "auditor": (7, 8), "solicitor": (7, 8),
    "barrister": (6, 7), "management": (6, 7), "policy": (6, 8),
    "marketing": (7, 8), "public relation": (6, 8), "advertising": (7, 8),
    "human resource professional": (6, 8), "human resource manager": (6, 7),
    "librarian": (7, 8), "archivist": (7, 8), "curator": (5, 7),
    "teacher": (5, 7), "lecturer": (6, 7), "tutor": (6, 7),
    "education adviser": (6, 7), "training": (6, 7),
    "finance manager": (6, 7), "corporate": (6, 7),
    "general manager": (5, 7), "chief executive": (5, 7),
    "school principal": (5, 6), "office manager": (6, 7),
    "practice manager": (6, 7), "secretary": (7, 8),
    "personal assistant": (7, 8), "receptionist": (6, 8),
    "general clerk": (7, 8), "bank worker": (7, 8),
    "interior designer": (7, 8), "fashion": (6, 8),
    "urban": (6, 7), "land economist": (6, 8), "valuer": (6, 7),
    "intelligence": (7, 8), "conveyancer": (7, 8), "legal clerk": (7, 8),
    "debt collector": (6, 7), "human resource clerk": (7, 8),
    "inspector": (5, 6), "insurance investigator": (6, 7),
    "library assistant": (6, 7), "contract": (6, 7), "project administrator": (6, 7),
    "call or contact centre": (7, 8), "real estate": (5, 7),
    "insurance agent": (6, 7), "sales representative": (5, 7),
    "ict trainer": (6, 7), "technical sales": (6, 7),
    "retail buyer": (5, 6), "ticket": (7, 8),
    "conference": (6, 7), "event": (6, 7),
    "transport service manager": (5, 6),
    "supply and distribution": (5, 6), "purchasing": (6, 7),
    "transport and despatch": (6, 7),

    # Moderate exposure (4-5): mixed physical/knowledge
    "registered nurse": (4, 5), "nurse manager": (5, 6),
    "nurse educator": (5, 7), "midwife": (3, 4),
    "pharmacist": (5, 6), "dentist": (4, 5), "dental practitioner": (4, 5),
    "physiotherapist": (3, 5), "occupational therapist": (4, 5),
    "psychologist": (5, 6), "social worker": (5, 6), "counsellor": (4, 6),
    "dietitian": (5, 6), "optometrist": (4, 5),
    "chiropractor": (3, 4), "podiatrist": (3, 5),
    "medical imaging": (5, 6), "medical laboratory": (5, 7),
    "environmental scientist": (5, 7), "chemist": (5, 7),
    "life scientist": (5, 7), "geologist": (4, 6),
    "agricultural scientist": (4, 6), "veterinarian": (3, 5),
    "architect": (6, 7), "civil engineering professional": (5, 6),
    "electrical engineer": (5, 7), "electronics engineer": (6, 7),
    "mechanical engineer": (5, 7), "industrial": (5, 7),
    "chemical engineer": (5, 7), "mining engineer": (4, 6),
    "other engineering": (5, 7), "surveyor": (5, 6), "cartographer": (5, 7),
    "air transport": (3, 5), "marine transport": (3, 5),
    "construction manager": (4, 5), "engineering manager": (5, 6),
    "production manager": (5, 6), "manufacturer": (4, 6),
    "ict manager": (6, 7), "research and development": (6, 7),
    "retail manager": (4, 6), "health and welfare": (5, 6),
    "child care centre manager": (4, 5),
    "other education manager": (5, 6),
    "import": (5, 6), "wholesale": (5, 6),
    "police": (3, 5), "prison officer": (3, 4),
    "amusement": (4, 5), "sports centre": (4, 5),
    "minister of religion": (3, 5),
    "welfare recreation": (4, 5),
    "sales manager": (5, 7),
    "advertising manager": (6, 7),
    "enrolled nurse": (3, 5),
    "medical technician": (4, 6),
    "dental hygienist": (3, 5),
    "ambulance": (3, 4), "paramedic": (3, 4),
    "science technician": (4, 6),
    "ict support technician": (5, 7),
    "telecommunications technical": (5, 6),

    # Moderate exposure: some trades with digital components
    "architectural technician": (5, 6), "building technician": (5, 6),
    "civil engineering draftsperson": (6, 7), "electrical engineering draftsperson": (6, 7),
    "electronic engineering draftsperson": (6, 7), "mechanical engineering draftsperson": (6, 7),
    "other building and engineering technician": (4, 6),
    "ict support": (5, 7), "telecommunications": (4, 6),
    "printing trades": (5, 7),

    # Low exposure (2-3): physical/trades work
    "electrician": (2, 3), "plumber": (2, 3),
    "carpenter": (1, 3), "bricklayer": (1, 3), "stonemason": (1, 3),
    "motor mechanic": (2, 3), "automotive": (2, 3),
    "metal fitter": (2, 3), "machinist": (2, 3),
    "welder": (1, 3), "structural steel": (1, 3), "sheetmetal": (1, 3),
    "painting trades": (1, 2), "floor finisher": (1, 2),
    "glazier": (1, 2), "plasterer": (1, 2), "roof tiler": (1, 2),
    "wall and floor tiler": (1, 2), "plumber": (2, 3),
    "airconditioning": (2, 3), "refrigeration": (2, 3),
    "electrical distribution": (2, 3), "electronics trades": (3, 4),
    "chef": (2, 3), "cook": (1, 3), "baker": (1, 3), "pastrycook": (1, 3),
    "butcher": (1, 2), "smallgoods": (1, 2),
    "hairdresser": (2, 3), "beauty therapist": (2, 3),
    "animal attendant": (1, 3), "shearer": (0, 1),
    "florist": (2, 3), "gardener": (1, 2), "greenkeeper": (1, 2),
    "cabinetmaker": (2, 3), "wood machinist": (2, 3),
    "boat builder": (1, 3), "shipwright": (1, 3),
    "jeweller": (2, 4), "sign writer": (3, 5),
    "performing arts technician": (2, 4),
    "gallery library museum technician": (3, 5),
    "chemical gas petroleum": (2, 4), "plant operator": (2, 3),
    "aircraft maintenance": (2, 4), "precision metal": (2, 3),
    "toolmaker": (2, 3), "patternmaker": (2, 3),
    "metal casting": (1, 2), "forging": (1, 2),
    "canvas": (1, 3), "leather": (1, 3),
    "driving instructor": (2, 3),
    "funeral worker": (2, 4),
    "massage therapist": (2, 3),
    "diversional therapist": (3, 5),
    "indigenous health": (3, 4),
    "welfare support": (4, 5),
    "child carer": (2, 3), "education aide": (3, 4),
    "aged and disabled carer": (2, 3), "dental assistant": (2, 3),
    "nursing support": (2, 3), "personal care worker": (2, 3),
    "special care": (2, 4),
    "security officer": (2, 3), "security guard": (2, 3),
    "fire and emergency": (1, 3), "defence force": (2, 4),
    "fitness instructor": (2, 3), "outdoor adventure": (1, 2),
    "sports coach": (2, 4), "sportsperson": (1, 3),
    "gallery museum tour guide": (3, 4),
    "personal care consultant": (3, 4),
    "tourism and travel": (5, 6), "travel attendant": (3, 4),
    "other personal service": (2, 4),

    # Low exposure: hospitality
    "bar attendant": (1, 2), "barista": (1, 2),
    "cafe worker": (1, 2), "gaming worker": (2, 4),
    "hotel service": (3, 4), "waiter": (1, 2),
    "other hospitality": (1, 3),
    "cafe and restaurant manager": (3, 5),
    "caravan park": (3, 4), "hotel and motel manager": (3, 5),
    "licensed club": (3, 5),

    # Low exposure: sales floor
    "sales assistant": (3, 5), "checkout operator": (4, 6),
    "cashier": (4, 6), "pharmacy sales": (3, 4),
    "retail supervisor": (3, 5), "ict sales assistant": (4, 6),
    "motor vehicle": (3, 4), "model": (1, 3), "demonstrator": (2, 4),

    # Minimal exposure (0-1): heavy physical/outdoor
    "truck driver": (1, 2), "bus driver": (1, 2), "coach driver": (1, 2),
    "train driver": (1, 3), "tram driver": (1, 3),
    "delivery driver": (1, 2), "automobile driver": (1, 2),
    "forklift": (1, 2), "crane": (1, 2), "hoist": (1, 2),
    "earthmoving": (0, 2), "agricultural.*plant operator": (0, 2),
    "other mobile plant": (1, 2), "other stationary plant": (1, 2),
    "storeperson": (2, 3), "machine operator": (1, 3),
    "spraypainter": (1, 2), "sewing machinist": (2, 3),
    "paper and wood processing": (1, 2),
    "photographic developer": (3, 5),
    "clay concrete glass": (1, 2), "plastics and rubber production": (1, 2),

    # Minimal: labourers
    "cleaner": (0, 2), "laundry worker": (0, 2), "car detailer": (0, 1),
    "building and plumbing labourer": (0, 1), "concreter": (0, 1),
    "fencer": (0, 1), "insulation": (0, 1), "paving": (0, 1),
    "railway track": (0, 1), "structural steel construction": (0, 2),
    "other construction": (0, 2), "mining labourer": (0, 2),
    "food and drink factory": (0, 2), "meat boner": (0, 1),
    "meat.*process": (0, 1), "metal engineering process": (1, 2),
    "plastics and rubber factory": (1, 2), "product assembler": (1, 2),
    "product quality": (2, 4), "other factory process": (1, 2),
    "farm.*worker": (0, 1), "garden.*labourer": (0, 1), "nursery": (0, 1),
    "forestry.*logging": (0, 1), "fast food cook": (0, 2),
    "food trades assistant": (0, 1), "kitchenhand": (0, 1),
    "freight handler": (0, 1), "shelf filler": (0, 1),
    "caretaker": (1, 2), "deck and fishing": (0, 1), "handyperson": (0, 2),
    "motor vehicle parts.*fitter": (1, 2), "printing assistant": (1, 2),
    "recycling": (0, 1), "rubbish collector": (0, 1),
    "vending machine": (1, 2), "other miscellaneous labourer": (0, 2),
    "other miscellaneous technician": (2, 4),
    "other miscellaneous clerical": (5, 7),

    # Farmers
    "aquaculture farmer": (2, 3), "crop farmer": (2, 3),
    "livestock farmer": (2, 3), "mixed crop": (2, 3),

    # Arts - mixed
    "actor": (2, 4), "dancer": (1, 3), "entertainer": (2, 4),
    "music professional": (3, 5), "photographer": (4, 6),
    "visual arts": (3, 5), "crafts professional": (3, 5),
    "artistic director": (5, 7), "media producer": (5, 7), "presenter": (4, 6),
    "film.*director": (4, 6), "television": (4, 6), "radio": (4, 6),
    "stage director": (3, 5),

    # Medical specialists
    "generalist medical practitioner": (4, 5), "anaesthetist": (3, 4),
    "specialist physician": (4, 5), "psychiatrist": (4, 5),
    "surgeon": (2, 4), "other medical practitioner": (4, 5),
    "audiologist": (4, 5), "speech pathologist": (4, 5),
    "complementary health": (2, 4),
    "occupational.*environmental health": (5, 6),
    "other health diagnostic": (4, 6),
    "social professional": (5, 6),

    # Commissioned officers
    "commissioned officer": (3, 5),
    "senior non-commissioned": (3, 4),
    "other specialist manager": (5, 6),
    "other hospitality retail": (4, 5),

    # Sales
    "auctioneer": (3, 5), "stock and station agent": (3, 5),
    "other sales assistant": (3, 5), "other sales support": (3, 5),
}


def get_exposure(title):
    """Get AI exposure score based on occupation title keywords."""
    title_lower = title.lower()
    best_match = None
    best_match_len = 0

    for keyword, (lo, hi) in EXPOSURE_KEYWORDS.items():
        if re.search(keyword, title_lower):
            if len(keyword) > best_match_len:
                best_match = (lo, hi)
                best_match_len = len(keyword)

    if best_match:
        lo, hi = best_match
        return random.randint(lo, hi)

    # Default based on major group
    major = title_lower[0] if title_lower[0].isdigit() else "5"
    defaults = {"1": (5, 7), "2": (5, 8), "3": (2, 4), "4": (2, 4),
                "5": (6, 8), "6": (3, 6), "7": (1, 3), "8": (0, 2)}
    lo, hi = defaults.get(major, (3, 6))
    return random.randint(lo, hi)


def get_exposure_rationale(title, exposure):
    """Generate a brief rationale based on exposure level."""
    title_lower = title.lower()

    if exposure >= 8:
        reasons = [
            f"{title} involves predominantly digital work that AI can increasingly perform. Core tasks like data processing, analysis, and documentation are in domains where AI is advancing rapidly.",
            f"The work of {title} is largely computer-based. AI tools are already capable of handling significant portions of these tasks, from automated processing to intelligent analysis.",
            f"{title} work is almost entirely digital, involving tasks like data entry, analysis, and written communication that AI systems can increasingly automate.",
        ]
    elif exposure >= 6:
        reasons = [
            f"{title} combines knowledge work with human judgment. While AI can assist with analysis and documentation, interpersonal skills and contextual decision-making remain important.",
            f"Much of {title} work involves information processing where AI can boost productivity significantly, though human oversight and relationship management are still needed.",
            f"{title} involves substantial knowledge work that AI tools are beginning to reshape, but professional judgment, stakeholder relationships, and complex decision-making provide some insulation.",
        ]
    elif exposure >= 4:
        reasons = [
            f"{title} involves a mix of hands-on and analytical work. AI can assist with the information-processing components, but physical presence and human interaction remain central.",
            f"While AI may assist {title} with administrative tasks, diagnostics, or planning, the core work requires physical presence, manual skill, or direct human interaction.",
            f"{title} has moderate AI exposure: technology can augment decision-making and streamline processes, but the fundamentally human and physical aspects of the role limit full automation.",
        ]
    elif exposure >= 2:
        reasons = [
            f"{title} is primarily hands-on work requiring physical presence and manual skill. AI has minimal direct impact on core tasks, though it may help with peripheral administrative work.",
            f"The core work of {title} requires physical dexterity, real-world problem solving, and on-site presence that AI cannot replicate. Only minor administrative tasks may be affected.",
            f"{title} involves predominantly physical or interpersonal work. AI tools may assist with scheduling or documentation, but the essential skills are manual and practical.",
        ]
    else:
        reasons = [
            f"{title} is almost entirely physical labour in real-world environments. AI has essentially no impact on the core work, which requires manual effort and physical presence.",
            f"The work of {title} is fundamentally physical and hands-on, performed in unpredictable real-world settings. Current AI capabilities have negligible impact on these tasks.",
            f"{title} requires physical presence, manual labour, and real-time adaptation to physical environments — areas where AI has minimal practical application.",
        ]

    return random.choice(reasons)


def get_growth_desc(pct):
    """Classify growth percentage into description."""
    if pct < -2:
        return "Declining"
    elif pct < 0:
        return "Slight decline"
    elif pct < 3:
        return "Slow growth"
    elif pct < 7:
        return "Moderate growth"
    elif pct < 12:
        return "Strong growth"
    else:
        return "Very strong growth"


def main():
    with open("occupations.json") as f:
        occupations = json.load(f)

    # Count occupations per major group for employment distribution
    by_major = {}
    for occ in occupations:
        major = occ["anzsco_code"][0]
        by_major.setdefault(major, []).append(occ)

    data = []
    for occ in occupations:
        code = occ["anzsco_code"]
        major = code[0]
        title = occ["title"]
        skill_level = MAJOR_GROUP_SKILL[major]

        # Weekly earnings
        lo, hi = WEEKLY_EARNINGS_RANGE[skill_level]
        # Add some variation within skill level
        weekly = random.randint(lo, hi)
        annual = weekly * 52

        # Employment
        major_share = EMPLOYMENT_SHARE.get(major, 0.05)
        n_in_group = len(by_major.get(major, []))
        avg_per_occ = (TOTAL_EMPLOYED * major_share) / max(n_in_group, 1)
        # Log-normal-ish distribution: some occupations are much larger
        employment = max(500, int(avg_per_occ * random.lognormvariate(0, 0.7)))

        # Education
        edu_options = EDUCATION_BY_SKILL[skill_level]
        education = random.choice(edu_options)

        # Growth outlook
        growth_lo, growth_hi = GROWTH_RANGE[major]
        outlook = round(random.uniform(growth_lo, growth_hi), 0)
        outlook = int(outlook)
        outlook_desc = get_growth_desc(outlook)

        # AI exposure
        exposure = get_exposure(title)
        rationale = get_exposure_rationale(title, exposure)

        data.append({
            "title": title,
            "slug": occ["slug"],
            "category": occ["category"],
            "pay": annual,
            "jobs": employment,
            "outlook": outlook,
            "outlook_desc": outlook_desc,
            "education": education,
            "exposure": exposure,
            "exposure_rationale": rationale,
            "url": occ["url"],
        })

    # Write site/data.json
    import os
    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w") as f:
        json.dump(data, f)

    # Also write scores.json and occupations.csv for pipeline compatibility
    scores = []
    for d in data:
        scores.append({
            "slug": d["slug"],
            "title": d["title"],
            "exposure": d["exposure"],
            "rationale": d["exposure_rationale"],
        })
    with open("scores.json", "w") as f:
        json.dump(scores, f, indent=2)

    # Summary
    total_jobs = sum(d["jobs"] for d in data)
    total_wages = sum(d["jobs"] * d["pay"] for d in data)
    exposures = [d["exposure"] for d in data]
    w_avg = sum(d["exposure"] * d["jobs"] for d in data) / total_jobs

    print(f"Generated data for {len(data)} occupations")
    print(f"Total employment: {total_jobs:,} ({total_jobs/1e6:.1f}M)")
    print(f"Total annual wages: A${total_wages/1e9:.0f}B")
    print(f"Job-weighted avg AI exposure: {w_avg:.1f}/10")
    print(f"Exposure distribution:")
    for i in range(11):
        count = sum(1 for d in data if d["exposure"] == i)
        jobs = sum(d["jobs"] for d in data if d["exposure"] == i)
        if count:
            print(f"  {i}: {'█' * count} ({count} occs, {jobs/1e6:.1f}M jobs)")


if __name__ == "__main__":
    main()
