#!/usr/bin/env python3
"""
Show how a disambiguation page is resolved from paper sentences.

The cases are offline. Each one parses a small disambiguation page, compares
the candidate lead paragraphs with the paper sentences using scikit-learn
TF-IDF, and prints the one-line history that would be stored on the
encyclopedia entry.

    python Examples/disambiguate_wikipedia_terms.py

Date: October 5, 2026 (system date)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.pipeline.wikipedia_disambiguation import (
    disambiguation_page_html,
    educational_examples,
    resolve_disambiguation,
)


def main() -> None:
    for case in educational_examples():
        page = disambiguation_page_html(
            f"{case['term']} may refer to:",
            case["items"],
        )
        decision = resolve_disambiguation(
            case["term"],
            page,
            case["sentences"],
            leads=case["leads"],
        )
        print(case["name"])
        print(f"  term: {case['term']}")
        print(f"  paper: {case['sentences'][0]}")
        print(f"  {decision.history}")
        print()


if __name__ == "__main__":
    main()
