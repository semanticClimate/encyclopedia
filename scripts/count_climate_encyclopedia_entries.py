#!/usr/bin/env python3
"""
Find climate-related encyclopedia HTML files under <root>/encyclopedia,
aggregate entries, and report deduplicated count.

Climate encyclopedias: fixture caches (small/medium/large), any file with
'climate' in path or title, and Example/temp encyclopedias that contain climate terms.

Usage: python scripts/count_climate_encyclopedia_entries.py
       (run from repo root with pythonpath or pip install -e .)
"""
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

from encyclopedia.core.encyclopedia import AmiEncyclopedia


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


def main():
    root = ROOT
    # Known climate-related encyclopedia sources (avoid loading dozens of test outputs)
    sources = []
    # 1) Fixture caches (small, medium, large = climate-inclusive)
    cache_dir = root / "test" / "encyclopedia" / "fixtures" / "cache"
    if cache_dir.exists():
        for p in sorted(cache_dir.glob("encyclopedia_*.html")):
            sources.append(p)
    # 2) Temp copies and explicitly climate-named
    temp_dir = root / "temp"
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
            p = temp_dir / name
            if p.exists():
                sources.append(p)
    # 3) Root and Examples
    for name in ["encyclopedia_output.html", "my_encyclopedia.html", "demo_encyclopedia.html"]:
        p = root / name
        if p.exists():
            sources.append(p)
    for name in ["knowledge_graph_encyclopedia.html", "simple_encyclopedia_example.html"]:
        p = root / "Examples" / name
        if p.exists():
            sources.append(p)

    # Load and collect entries (skip duplicates by path so we don't double-count same file)
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

    # Deduplicate by canonical key
    by_key = {}
    for e in all_entries:
        k = canonical_key(e)
        if k and k not in by_key:
            by_key[k] = e

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
    print(f"Entries after deduplication (by wikidata_id / wikipedia_url / term): {len(by_key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
