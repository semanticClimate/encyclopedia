"""
Guardrails: scope check — refuse when retrieval is empty or low confidence.
"""

from typing import List, Tuple

REFUSAL_MESSAGE = (
    "I can only answer from the climate encyclopedia; I don't have information on that."
)


def check_scope_refuse(
    retrieval_result: List[Tuple[dict, float]],
    min_score: float = 0.2,
) -> Tuple[bool, str]:
    """
    Decide whether to refuse (no answer from corpus).

    Args:
        retrieval_result: List of (chunk, score) from retriever.search().
        min_score: Minimum max score to allow an answer.

    Returns:
        (should_refuse, message). When should_refuse is True, message is REFUSAL_MESSAGE.
    """
    if not retrieval_result:
        return True, REFUSAL_MESSAGE
    max_score = max(s for _, s in retrieval_result)
    if max_score < min_score:
        return True, REFUSAL_MESSAGE
    return False, ""
