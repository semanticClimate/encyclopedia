"""
TDD: Scope guardrail — refuse when retrieval empty or below threshold.
"""

import pytest

from encyclopedia.chatbot.guardrails import check_scope_refuse, REFUSAL_MESSAGE


class TestCheckScopeRefuse:
    """Contract: check_scope_refuse(result, min_score) -> (should_refuse, message)."""

    def test_empty_result_refuse(self):
        """Empty retrieval result -> should_refuse True, message is REFUSAL_MESSAGE."""
        should_refuse, msg = check_scope_refuse([], min_score=0.2)
        assert should_refuse is True, "Empty result must trigger refuse"
        assert msg == REFUSAL_MESSAGE, f"Refusal message must be REFUSAL_MESSAGE, got {msg}"

    def test_low_score_refuse(self):
        """Max score below min_score -> should_refuse True."""
        result = [({"text": "x", "term": "y"}, 0.1)]
        should_refuse, msg = check_scope_refuse(result, min_score=0.2)
        assert should_refuse is True, "Score 0.1 < 0.2 must trigger refuse"
        assert msg == REFUSAL_MESSAGE

    def test_above_threshold_do_not_refuse(self):
        """Max score >= min_score -> should_refuse False, message empty."""
        result = [({"text": "climate", "term": "climate change"}, 0.5)]
        should_refuse, msg = check_scope_refuse(result, min_score=0.2)
        assert should_refuse is False, "Score 0.5 >= 0.2 must not refuse"
        assert msg == ""

    def test_boundary_at_min_score(self):
        """Score exactly min_score -> do not refuse."""
        result = [({"text": "x", "term": "y"}, 0.2)]
        should_refuse, _ = check_scope_refuse(result, min_score=0.2)
        assert should_refuse is False, "Score equal to min_score must not refuse"

    def test_multiple_results_use_max_score(self):
        """When multiple chunks, max score is used for threshold."""
        result = [
            ({"text": "a", "term": "x"}, 0.1),
            ({"text": "climate change", "term": "climate"}, 0.9),
        ]
        should_refuse, _ = check_scope_refuse(result, min_score=0.2)
        assert should_refuse is False, "Max score 0.9 >= 0.2 must not refuse"
