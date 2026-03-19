"""Tests for score.py — LLM scoring utilities."""

from score import (
    SYSTEM_PROMPT,
    build_isco_prompt,
    detect_occupation_format,
    parse_llm_response,
)

# --- parse_llm_response ---


def test_parse_llm_response_clean_json():
    raw = '{"exposure": 7, "rationale": "Test rationale"}'
    result = parse_llm_response(raw)
    assert result["exposure"] == 7
    assert result["rationale"] == "Test rationale"


def test_parse_llm_response_with_json_fences():
    raw = '```json\n{"exposure": 5, "rationale": "Moderate exposure."}\n```'
    result = parse_llm_response(raw)
    assert result["exposure"] == 5
    assert result["rationale"] == "Moderate exposure."


def test_parse_llm_response_with_bare_fences():
    raw = '```\n{"exposure": 3, "rationale": "Low exposure."}\n```'
    result = parse_llm_response(raw)
    assert result["exposure"] == 3


def test_parse_llm_response_with_whitespace():
    raw = '  \n  {"exposure": 9, "rationale": "Very high."}  \n  '
    result = parse_llm_response(raw)
    assert result["exposure"] == 9


# --- build_isco_prompt ---


def test_build_isco_prompt_basic():
    occ = {
        "title": "ICT Professionals",
        "isco_code": "25",
        "category_label": "Professionals",
        "slug": "ict-professionals",
    }
    prompt = build_isco_prompt(occ)
    assert "# ICT Professionals" in prompt
    assert "**ISCO-08 Code:** 25" in prompt
    assert "**Major Group:** Professionals" in prompt
    assert "Cyprus/EU labour market" in prompt


def test_build_isco_prompt_minimal():
    occ = {"title": "General Clerks", "slug": "general-clerks"}
    prompt = build_isco_prompt(occ)
    assert "# General Clerks" in prompt
    assert "ISCO-08 Code" not in prompt
    assert "Major Group" not in prompt


# --- detect_occupation_format ---


def test_detect_occupation_format_cyprus():
    occs = [{"title": "Managers", "isco_code": "1", "slug": "managers"}]
    assert detect_occupation_format(occs) == "cyprus"


def test_detect_occupation_format_bls():
    occs = [{"title": "Accountants", "slug": "accountants"}]
    assert detect_occupation_format(occs) == "bls"


def test_detect_occupation_format_empty():
    assert detect_occupation_format([]) == "bls"


# --- SYSTEM_PROMPT content ---


def test_system_prompt_contains_cyprus_context():
    assert "Cyprus" in SYSTEM_PROMPT
    assert "ISCO-08" in SYSTEM_PROMPT
    assert "EU" in SYSTEM_PROMPT


def test_system_prompt_contains_sector_references():
    assert "tourism" in SYSTEM_PROMPT.lower()
    assert "shipping" in SYSTEM_PROMPT.lower()
    assert "financial services" in SYSTEM_PROMPT.lower()


def test_system_prompt_contains_scoring_anchors():
    assert "agricultural labourer" in SYSTEM_PROMPT
    assert "ICT professional" in SYSTEM_PROMPT
    assert "general clerk" in SYSTEM_PROMPT
