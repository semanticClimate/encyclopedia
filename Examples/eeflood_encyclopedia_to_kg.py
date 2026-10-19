#!/usr/bin/env python3
"""
Build a knowledge graph from the eastern England flood encyclopedia.

The papers, corpus, and encyclopedia are already at ~/temp/eeflood. This
example does not download papers or call Wikipedia. It writes GraphML whose
graph-level history records the query, the pygetpapers command, the corpus,
and the encyclopedia.

    python Examples/eeflood_encyclopedia_to_kg.py

The saved pipeline summary for this run has the corpus paths. It was written
before the summary stored the query, so this example supplies the query and
the pygetpapers command.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.encyclopedia_to_kg import main


QUERY = 'flood* AND "eastern England"'
PYGETPAPERS_COMMAND = (
    "pygetpapers -q 'flood* AND \"eastern England\"' -k 50 "
    "-o ~/temp/eeflood/pygetpapers --api europe_pmc -x"
)
ENCYCLOPEDIA_HTML = Path.home() / "temp" / "eeflood" / "encyclopedia" / "eeflood_encyclopedia.html"
OUTPUT = Path(ROOT, "temp", "eeflood_kg.graphml")


def build_eeflood_graph() -> None:
    main([
        "--encyclopedia",
        str(ENCYCLOPEDIA_HTML),
        "--link",
        "description",
        "--query",
        QUERY,
        "--pygetpapers-command",
        PYGETPAPERS_COMMAND,
        "--output",
        str(OUTPUT),
    ])


if __name__ == "__main__":
    build_eeflood_graph()
