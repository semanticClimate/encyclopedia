"""
Answer pipeline: question → retrieve → guardrail → prompt → LLM → response.
"""

from typing import Dict, Any, Callable


def answer_question(
    question: str,
    retriever,
    min_score: float = 0.2,
    prompt_builder: Callable = None,
    llm_generate: Callable[[str], str] = None,
) -> Dict[str, Any]:
    """
    Run the full pipeline: retrieval, scope guardrail, prompt build, LLM.

    Args:
        question: User question.
        retriever: Object with .search(query, k) returning list of (chunk, score).
        min_score: Minimum max score to allow answer (else refuse).
        prompt_builder: (chunks, question, system_prompt) -> str. Default: build_prompt.
        llm_generate: prompt -> answer string. If None, returns placeholder.

    Returns:
        dict with answer (str), refused (bool), citations (list of chunk dicts if not refused).
    """
    from encyclopedia.chatbot.guardrails import check_scope_refuse
    from encyclopedia.chatbot.prompt import build_prompt

    if prompt_builder is None:
        prompt_builder = build_prompt

    retrieval_result = retriever.search(question, k=5)
    should_refuse, refusal_msg = check_scope_refuse(retrieval_result, min_score=min_score)

    if should_refuse:
        return {
            "answer": refusal_msg,
            "refused": True,
            "citations": [],
        }

    chunks = [c for c, _ in retrieval_result]
    prompt = prompt_builder(chunks, question, system_prompt="Answer only from the excerpts above. Cite the section (term) when possible.")

    if llm_generate is not None:
        answer = llm_generate(prompt)
    else:
        answer = "(No LLM configured; implement llm_generate for production.)"

    return {
        "answer": answer,
        "refused": False,
        "citations": chunks,
    }
