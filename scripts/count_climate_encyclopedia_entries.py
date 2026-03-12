#!/usr/bin/env python3
"""
Find climate-related encyclopedia HTML files under <root>/encyclopedia,
aggregate entries, and report deduplicated count.

Optionally exports the deduplicated entries to a single JSON file for chatbot
indexing (see CLIMATE_CHATBOT_DESIGN.md).

Climate encyclopedias: fixture caches (small/medium/large), any file with
'climate' in path or title, and Example/temp encyclopedias that contain climate terms.

Usage: python scripts/count_climate_encyclopedia_entries.py [--export]
       (run from repo root with pythonpath or pip install -e .)
       --export  write deduplicated entries to temp/chatbot/climate_encyclopedia_entries.json
"""
import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def canonical_key(entry: dict) -> str:
    """Stable key for deduplication: prefer wikidata_id, then wikipedia_url, else normalized term."""
    wid = entry.get("wikidata_id")
    if wid and str(wid).strip():
        s = str(wid).strip()
        if "wikidata.org" in s:
            for part in s.split("/"):
                if part.startswith("Q") and len(part) > 1 and part[1:].isdigit():
                    return f"q:{part}"
        return f"q:{s}"
    url = entry.get("wikipedia_url")
    if url and "/wiki/" in str(url):
        title = str(url).split("/wiki/")[-1].split("#")[0].split("?")[0].strip()
        if title:
            return f"w:{title.lower().replace(' ', '_')}"
    term = (entry.get("term") or entry.get("search_term") or "").strip()
    if term:
        return f"t:{term.lower().replace(' ', '_')}"
    return None  # skip entries with no key


def _entry_to_json_serializable(entry: dict) -> dict:
    """Return a copy of the entry with only JSON-serializable values."""
    out = {}
    for k, v in entry.items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, (list, dict)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def get_aggregated_entries(root: Path = None):
    """
    Load all climate-related encyclopedia sources, deduplicate by canonical key,
    and return the list of unique entries plus source metadata.

    Returns:
        tuple: (deduplicated_entries: list[dict], loaded: list[tuple])
    """
    if root is None:
        root = ROOT
    sources = []
    cache_dir = Path(root, "test", "encyclopedia", "fixtures", "cache")
    if cache_dir.exists():
        for p in sorted(cache_dir.glob("encyclopedia_*.html")):
            sources.append(p)
    temp_dir = Path(root, "temp")
    if temp_dir.exists():
        for name in [
            "climate_encyclopedia.html",
            "test/encyclopedia/GeneratedWithImages/climate_encyclopedia_with_images.html",
            "test/encyclopedia/TestKnowledgeGraphBuilder/climate_encyclopedia.html",
            "test/encyclopedia/fixtures/small_test_encyclopedia.html",
            "test/encyclopedia/fixtures/medium_test_encyclopedia.html",
            "test/encyclopedia/fixtures/large_test_encyclopedia.html",
            "example_encyclopedia.html",
        ]:
            p = Path(temp_dir, name)
            if p.exists():
                sources.append(p)
    for name in ["encyclopedia_output.html", "my_encyclopedia.html", "demo_encyclopedia.html"]:
        p = Path(root, name)
        if p.exists():
            sources.append(p)
    for name in ["knowledge_graph_encyclopedia.html", "simple_encyclopedia_example.html"]:
        p = Path(root, "Examples", name)
        if p.exists():
            sources.append(p)

    seen_paths = set()
    all_entries = []
    loaded = []

    for path in sources:
        path = path.resolve()
        if path in seen_paths:
            continue
        seen_paths.add(path)
        try:
            enc = AmiEncyclopedia()
            enc.create_from_html_file(path)
            entries = list(enc.entries) if enc.entries else []
            if not entries:
                continue
            rel = path.relative_to(root) if root in path.parents else path.name
            loaded.append((str(rel), len(entries), enc.title or ""))
            for e in entries:
                all_entries.append(e)
        except Exception:
            continue

    by_key = {}
    for e in all_entries:
        k = canonical_key(e)
        if k and k not in by_key:
            by_key[k] = e

    deduplicated = list(by_key.values())
    return deduplicated, loaded


def export_aggregated_to_json(output_path: Path, entries: list) -> Path:
    """
    Write aggregated entries to a JSON file for chatbot indexing.

    Args:
        output_path: Path to write (e.g. temp/chatbot/climate_encyclopedia_entries.json).
        entries: List of entry dicts from get_aggregated_entries().

    Returns:
        Path that was written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serializable = [_entry_to_json_serializable(e) for e in entries]
    payload = {"entries": serializable, "count": len(serializable)}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Aggregate climate encyclopedia entries and optionally export to JSON.")
    parser.add_argument("--export", action="store_true", help="Export deduplicated entries to temp/chatbot/climate_encyclopedia_entries.json")
    args = parser.parse_args()

    root = ROOT
    deduplicated, loaded = get_aggregated_entries(root)

    # Report
    print("Climate-related encyclopedias in <root>/encyclopedia:\n")
    total_raw = 0
    for rel, n, title in loaded:
        total_raw += n
        print(f"  {rel}")
        print(f"    entries: {n}  title: {title or '(none)'}")
    print("---")
    print(f"Sources loaded: {len(loaded)}")
    print(f"Total entries (sum): {total_raw}")
    print(f"Entries after deduplication (by wikidata_id / wikipedia_url / term): {len(deduplicated)}")

    if args.export:
        output_path = Path(Resources.TEMP_DIR, "chatbot", "climate_encyclopedia_entries.json")
        export_aggregated_to_json(output_path, deduplicated)
        print(f"Exported to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
