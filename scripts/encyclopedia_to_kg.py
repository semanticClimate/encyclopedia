#!/usr/bin/env python3
"""
Build a knowledge graph from an encyclopedia HTML file.

Each encyclopedia term becomes a node. Edges are added only for the link
options named with --link. Further options will be added to LINK_OPTIONS.

The option available now:

  description    the entry description links to another entry's Wikipedia page

The graph records how it was made: query, pygetpapers command, corpus, wordlist,
encyclopedia file, and which link options were used. Those values are read from
pipeline_summary.json next to the encyclopedia when that file exists.

Example:
  python scripts/encyclopedia_to_kg.py \\
      --encyclopedia ~/temp/eeflood/encyclopedia/eeflood_encyclopedia.html \\
      --query 'flood* AND "eastern England"' \\
      --output temp/eeflood_kg.graphml

  python Examples/eeflood_encyclopedia_to_kg.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from encyclopedia.utils.knowledge_graph.entry_graph import (
    LINK_OPTIONS,
    attach_creation_history,
    build_unweighted_entry_graph,
    entries_from_encyclopedia_html,
    load_creation_history,
    pipeline_summary_path,
)
from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a knowledge graph from an encyclopedia."
    )
    parser.add_argument(
        "--encyclopedia",
        type=Path,
        required=True,
        help="Encyclopedia HTML file",
    )
    parser.add_argument(
        "--link",
        action="append",
        choices=sorted(LINK_OPTIONS),
        default=None,
        help=(
            "Link to create. Repeat this option to add further kinds when they exist. "
            "description: an entry description links to another entry. "
            "Default: description."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="GraphML file to write. Default: <encyclopedia stem>_kg.graphml beside the input",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="pipeline_summary.json. Default: the summary beside the encyclopedia",
    )
    parser.add_argument("--query", default="", help="Europe PMC query, stored in the graph history")
    parser.add_argument(
        "--pygetpapers-command",
        default="",
        help="pygetpapers command that downloaded the corpus, stored in the graph history",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        help="Corpus directory, stored in the graph history",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    encyclopedia = args.encyclopedia.expanduser()
    if not encyclopedia.is_file():
        raise SystemExit(f"Encyclopedia file not found: {encyclopedia}")
    link_names = args.link or ["description"]
    unknown = [name for name in link_names if name not in LINK_OPTIONS]
    if unknown:
        known = ", ".join(sorted(LINK_OPTIONS))
        raise SystemExit(f"Unknown link option {unknown[0]!r}. Known options: {known}")
    relationships = [LINK_OPTIONS[name] for name in link_names]

    entries = entries_from_encyclopedia_html(encyclopedia)
    graph = build_unweighted_entry_graph(entries, links=relationships)
    summary = args.summary.expanduser() if args.summary else pipeline_summary_path(encyclopedia)
    history = load_creation_history(
        summary,
        query=args.query,
        pygetpapers_command=args.pygetpapers_command,
        corpus_dir=str(args.corpus.expanduser()) if args.corpus else "",
        encyclopedia_html=str(encyclopedia),
        links=",".join(link_names),
    )
    attach_creation_history(graph, history)
    output = args.output.expanduser() if args.output else encyclopedia.with_name(
        f"{encyclopedia.stem}_kg.graphml"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    GraphExporter().export_graphml(graph, output)

    print(f"Query: {history['query']}")
    print(f"Corpus: {history['corpus_dir']}")
    print(f"Encyclopedia: {history['encyclopedia_html']}")
    print(f"Entries: {graph.number_of_nodes()}")
    for name in link_names:
        relationship = LINK_OPTIONS[name]
        count = sum(
            1 for _source, _target, data in graph.edges(data=True)
            if data.get("relationship") == relationship
        )
        print(f"{name}: {count}")
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
