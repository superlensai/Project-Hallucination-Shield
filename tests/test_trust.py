import pytest
from src.verifier.trust import TrustCalculator

def test_trust_calculator_base_score():
    metadata = {
        "info": {
            "author": "Test Author",
            "home_page": "https://github.com/test/repo",
            "summary": "A very long summary that should provide some points for documentation quality."
        }
    }
    score = TrustCalculator.calculate_score(metadata)
    # 10 (author) + 15 (github) + 8 (summary) = 33
    assert score == 33

def test_trust_calculator_missing_data():
    metadata = {"info": {}}
    score = TrustCalculator.calculate_score(metadata)
    assert score == 0

def test_trust_calculator_none_values():
    metadata = {
        "info": {
            "author": None,
            "home_page": None,
            "summary": None
        }
    }
    score = TrustCalculator.calculate_score(metadata)
    assert score == 0
