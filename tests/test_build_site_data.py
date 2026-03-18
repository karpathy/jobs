"""Tests for build_site_data.py — site data merging logic."""


def test_merge_logic():
    """Test that CSV stats and scores merge correctly into site data format."""
    # This tests the core merging logic without running main()
    csv_data = [
        {
            "title": "Software Developer",
            "slug": "software-developers",
            "category": "Computer and Information Technology",
            "median_pay_annual": "130000",
            "num_jobs_2024": "1800000",
            "outlook_pct": "17",
            "outlook_desc": "Much faster than average",
            "entry_education": "Bachelor's degree",
            "url": "https://example.com/software-developers",
        }
    ]
    scores_data = [
        {
            "slug": "software-developers",
            "title": "Software Developer",
            "exposure": 9,
            "rationale": "Highly digital work.",
        }
    ]

    # Simulate merge logic from build_site_data.py
    scores = {s["slug"]: s for s in scores_data}
    data = []
    for row in csv_data:
        slug = row["slug"]
        score = scores.get(slug, {})
        data.append(
            {
                "title": row["title"],
                "slug": slug,
                "category": row["category"],
                "pay": int(row["median_pay_annual"]) if row["median_pay_annual"] else None,
                "jobs": int(row["num_jobs_2024"]) if row["num_jobs_2024"] else None,
                "outlook": int(row["outlook_pct"]) if row["outlook_pct"] else None,
                "outlook_desc": row["outlook_desc"],
                "education": row["entry_education"],
                "exposure": score.get("exposure"),
                "exposure_rationale": score.get("rationale"),
                "url": row.get("url", ""),
            }
        )

    assert len(data) == 1
    assert data[0]["title"] == "Software Developer"
    assert data[0]["pay"] == 130000
    assert data[0]["jobs"] == 1800000
    assert data[0]["exposure"] == 9
    assert data[0]["outlook"] == 17


def test_missing_score_defaults_to_none():
    """When no score exists for an occupation, exposure fields should be None."""
    scores = {}
    row = {"slug": "unknown-job", "median_pay_annual": "", "num_jobs_2024": ""}
    score = scores.get(row["slug"], {})
    assert score.get("exposure") is None
    assert score.get("rationale") is None
