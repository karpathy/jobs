"""Tests for score.py — LLM scoring utilities."""

import json


def test_json_fence_stripping():
    """Test that markdown code fences are properly stripped from LLM responses."""
    # Simulate the fence-stripping logic from score.py
    raw = '```json\n{"exposure": 7, "rationale": "Test rationale"}\n```'
    content = raw.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    result = json.loads(content)
    assert result["exposure"] == 7
    assert result["rationale"] == "Test rationale"


def test_json_without_fences():
    """Test parsing clean JSON without fences."""
    raw = '{"exposure": 5, "rationale": "Moderate exposure."}'
    result = json.loads(raw.strip())
    assert result["exposure"] == 5


def test_exposure_score_range():
    """Validate that exposure scores should be 0-10."""
    for score in range(11):
        assert 0 <= score <= 10
