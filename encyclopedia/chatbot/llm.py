"""
LLM backends for the chatbot pipeline: Ollama (local) and OpenAI-compatible API.

Provides callables (prompt: str) -> str for use with answer_question(..., llm_generate=...).
Uses requests only; no openai package required.
"""

from typing import Callable, Optional

try:
    import requests
except ImportError:
    requests = None


def _check_requests():
    if requests is None:
        raise ImportError("requests is required for LLM backends. pip install requests")


def ollama_generate(
    prompt: str,
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> str:
    """
    Send prompt to local Ollama and return the generated text.

    Args:
        prompt: Full prompt string (system + context + question).
        model: Ollama model name (e.g. llama3.2:3b, phi3:mini).
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds.

    Returns:
        Generated text from the model.

    Raises:
        ImportError: If requests is not installed.
        requests.RequestException: On network or API errors.
        ValueError: If response does not contain expected content.
    """
    _check_requests()
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if "response" not in data:
        raise ValueError(f"Ollama response missing 'response': {list(data.keys())}")
    return (data.get("response") or "").strip()


def make_ollama_generator(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> Callable[[str], str]:
    """
    Return a callable (prompt -> str) that uses Ollama.

    Usage:
        llm_generate = make_ollama_generator(model="llama3.2:3b")
        answer_question("What is climate change?", retriever, llm_generate=llm_generate)
    """
    def _generate(prompt: str) -> str:
        return ollama_generate(prompt, model=model, base_url=base_url, timeout=timeout)
    return _generate


def openai_compatible_generate(
    prompt: str,
    model: str,
    api_key: str,
    base_url: Optional[str] = None,
    timeout: int = 60,
) -> str:
    """
    Send prompt to an OpenAI-compatible chat API (e.g. OpenAI, Mistral, local server).

    Uses POST /v1/chat/completions with a single user message.

    Args:
        prompt: Full prompt string (sent as one user message).
        model: Model name (e.g. gpt-4o-mini, mistral-small).
        api_key: API key for Authorization header.
        base_url: API base URL (e.g. https://api.openai.com/v1). If None, uses OpenAI.
        timeout: Request timeout in seconds.

    Returns:
        Generated text (choices[0].message.content).

    Raises:
        ImportError: If requests is not installed.
        requests.RequestException: On network or API errors.
        ValueError: If response does not contain expected content.
    """
    _check_requests()
    url = (base_url or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise ValueError(f"API response has no choices: {data}")
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if content is None:
        raise ValueError(f"API response message missing content: {msg}")
    return (content or "").strip()


def make_openai_generator(
    model: str,
    api_key: str,
    base_url: Optional[str] = None,
    timeout: int = 60,
) -> Callable[[str], str]:
    """
    Return a callable (prompt -> str) that uses an OpenAI-compatible API.

    Usage:
        llm_generate = make_openai_generator(
            model="gpt-4o-mini",
            api_key=os.environ["OPENAI_API_KEY"],
        )
        answer_question("What is climate change?", retriever, llm_generate=llm_generate)
    """
    def _generate(prompt: str) -> str:
        return openai_compatible_generate(
            prompt, model=model, api_key=api_key, base_url=base_url, timeout=timeout
        )
    return _generate
