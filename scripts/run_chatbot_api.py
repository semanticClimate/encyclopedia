#!/usr/bin/env python3
"""
Run the climate encyclopedia chatbot FastAPI app (POST /ask, GET /health, GET / UI).

Usage (from repo root):
  python scripts/run_chatbot_api.py
  # or: uvicorn encyclopedia.chatbot.app:create_app --factory --host 0.0.0.0 --port 8000

Optional env: CHATBOT_ENCYCLOPEDIA, OLLAMA_MODEL, OPENAI_API_KEY, OPENAI_MODEL (see CLIMATE_CHATBOT_DESIGN.md).

Requires: pip install fastapi uvicorn
Chatbot index: pip install sentence-transformers chromadb (or use small in-memory fallback).
"""

import sys
from pathlib import Path

# Ensure project root on path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    try:
        from encyclopedia.chatbot.app import create_app
        import uvicorn
    except ImportError as e:
        print("Install FastAPI and uvicorn: pip install fastapi uvicorn", file=sys.stderr)
        raise SystemExit(1) from e

    app = create_app()
    host = "0.0.0.0"
    port = 8000
    print(f"Climate Chatbot API: http://{host}:{port}/")
    print("  GET  /       — UI")
    print("  POST /ask    — {\"question\": \"...\"}")
    print("  GET  /health — liveness")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
