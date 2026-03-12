"""
FastAPI app for the climate encyclopedia chatbot: POST /ask, GET /health, GET / (UI).

Pipeline is initialized at startup (corpus, vector retriever, optional LLM).
Requires: pip install fastapi uvicorn; chatbot deps: sentence-transformers, chromadb.
"""

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Project root (encyclopedia/chatbot/app.py -> parent.parent.parent)
ROOT = Path(__file__).resolve().parent.parent.parent


def _find_encyclopedia_path() -> Optional[Path]:
    """First available: env, aggregated JSON, fixture cache, root files, or None."""
    from encyclopedia.utils.resources import Resources

    env_path = os.environ.get("CHATBOT_ENCYCLOPEDIA")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p
    json_path = Path(Resources.TEMP_DIR, "chatbot", "climate_encyclopedia_entries.json")
    if json_path.exists():
        return json_path
    cache_dir = Path(ROOT, "test", "encyclopedia", "fixtures", "cache")
    if cache_dir.exists():
        for p in sorted(cache_dir.glob("encyclopedia_*.html")):
            return p
    for name in ["encyclopedia_output.html", "my_encyclopedia.html", "demo_encyclopedia.html"]:
        p = Path(ROOT, name)
        if p.exists():
            return p
    return None


def _make_llm_generator() -> Optional[Callable[[str], str]]:
    """Return llm_generate callable from env: Ollama, then OpenAI, else None."""
    ollama_model = os.environ.get("OLLAMA_MODEL")
    if ollama_model:
        try:
            from encyclopedia.chatbot.llm import make_ollama_generator
            return make_ollama_generator(model=ollama_model)
        except Exception:
            return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            from encyclopedia.chatbot.llm import make_openai_generator
            return make_openai_generator(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=api_key,
            )
        except Exception:
            return None
    return None


def _build_pipeline() -> Dict[str, Any]:
    """
    Load corpus, build chunks, vector retriever, and optional LLM.
    Returns dict with retriever, llm_generate, and optional error message.
    """
    try:
        from encyclopedia.chatbot.corpus import load_entries_from_encyclopedia, entries_to_sections
        from encyclopedia.chatbot.chunker import chunk_sections
        from encyclopedia.chatbot.retrieval import VectorRetriever
        from encyclopedia.utils.resources import Resources
    except ImportError as e:
        return {"retriever": None, "llm_generate": None, "error": f"Chatbot deps missing: {e}"}

    enc_path = _find_encyclopedia_path()
    if enc_path is None:
        from encyclopedia.core.encyclopedia import AmiEncyclopedia
        enc = AmiEncyclopedia(title="API")
        enc.entries = [
            {"term": "climate change", "description_html": "<p>Long-term shifts in temperatures and weather patterns.</p>", "wikidata_id": "Q7942"},
            {"term": "greenhouse gas", "description_html": "<p>Gases that trap heat in the atmosphere.</p>", "wikidata_id": "Q131784"},
        ]
        entries = list(enc.entries)
    else:
        entries = load_entries_from_encyclopedia(enc_path)

    if not entries:
        return {"retriever": None, "llm_generate": None, "error": "No corpus loaded."}

    sections = entries_to_sections(entries)
    chunks = chunk_sections(sections)
    persist_dir = str(Path(Resources.get_temp_dir("chatbot", "api"), "chroma"))
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    retriever = VectorRetriever(
        chunks,
        persist_directory=persist_dir,
        collection_name="climate_chatbot_api",
    )
    llm_generate = _make_llm_generator()
    return {"retriever": retriever, "llm_generate": llm_generate, "error": None}


def create_app():
    """Create FastAPI app with pipeline state and routes."""
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import HTMLResponse, JSONResponse
        from pydantic import BaseModel
    except ImportError as e:
        raise ImportError(
            "FastAPI and pydantic are required for the chatbot API. "
            "Install with: pip install fastapi uvicorn"
        ) from e

    app = FastAPI(title="Climate Encyclopedia Chatbot", version="0.1.0")
    pipeline = _build_pipeline()
    app.state.retriever = pipeline["retriever"]
    app.state.llm_generate = pipeline["llm_generate"]
    app.state.pipeline_error = pipeline.get("error")

    class AskRequest(BaseModel):
        question: str

    class AskResponse(BaseModel):
        answer: str
        refused: bool
        citations: List[Dict[str, Any]]

    @app.get("/health")
    def health():
        """Liveness check."""
        if app.state.pipeline_error:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": app.state.pipeline_error},
            )
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest):
        """Run the RAG pipeline and return answer, refused flag, and citations."""
        if app.state.retriever is None:
            raise HTTPException(status_code=503, detail=app.state.pipeline_error or "Pipeline not loaded.")
        from encyclopedia.chatbot.pipeline import answer_question

        result = answer_question(
            req.question.strip() or "What is climate change?",
            app.state.retriever,
            min_score=0.2,
            llm_generate=app.state.llm_generate,
        )
        return AskResponse(
            answer=result.get("answer", ""),
            refused=result.get("refused", False),
            citations=result.get("citations", []),
        )

    @app.get("/", response_class=HTMLResponse)
    def ui():
        """Simple HTML UI: input question, display answer and citations."""
        html = _UI_HTML
        return HTMLResponse(html)

    return app


_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Climate Encyclopedia Chatbot</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
    h1 { font-size: 1.25rem; }
    label { display: block; margin-bottom: 0.25rem; font-weight: 500; }
    input[type="text"] { width: 100%; padding: 0.5rem; font-size: 1rem; box-sizing: border-box; }
    button { margin-top: 0.5rem; padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer; }
    #answer { margin-top: 1rem; padding: 1rem; background: #f5f5f5; border-radius: 6px; white-space: pre-wrap; }
    #citations { margin-top: 0.5rem; font-size: 0.9rem; color: #555; }
    .refused { color: #c00; }
    .loading { color: #666; }
  </style>
</head>
<body>
  <h1>Climate Encyclopedia Chatbot</h1>
  <p>Ask a question about climate change. Answers are grounded in the encyclopedia only.</p>
  <form id="form">
    <label for="question">Question</label>
    <input type="text" id="question" name="question" placeholder="e.g. What is climate change?" autocomplete="off">
    <button type="submit" id="submit">Ask</button>
  </form>
  <div id="answer" class="loading" aria-live="polite"></div>
  <div id="citations"></div>
  <script>
    const form = document.getElementById('form');
    const question = document.getElementById('question');
    const answerEl = document.getElementById('answer');
    const citationsEl = document.getElementById('citations');
    const submitBtn = document.getElementById('submit');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const q = (question.value || '').trim();
      if (!q) return;
      submitBtn.disabled = true;
      answerEl.textContent = 'Loading…';
      answerEl.className = 'loading';
      citationsEl.textContent = '';
      try {
        const res = await fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: q })
        });
        const data = await res.json();
        answerEl.textContent = data.answer || '(No answer)';
        answerEl.className = data.refused ? 'refused' : '';
        if (data.citations && data.citations.length > 0) {
          citationsEl.innerHTML = 'Citations: ' + data.citations.map(c => (c.term || c.section_label || '') + (c.text ? ': ' + c.text.slice(0, 80) + '…' : '')).join(' | ');
        } else {
          citationsEl.textContent = '';
        }
      } catch (err) {
        answerEl.textContent = 'Error: ' + err.message;
        answerEl.className = 'refused';
      }
      submitBtn.disabled = false;
    });
  </script>
</body>
</html>
"""
