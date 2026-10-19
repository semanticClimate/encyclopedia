"""Entry–entry graph with the unweighted links.

Nodes are encyclopedia terms. An edge is either:

- links_to: E1's description links to E2's Wikipedia page
- shares_paper: E1 and E2 both reference the same paper

Text similarity and numeric weights are left out.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set
from urllib.parse import parse_qs, unquote, urlparse

import networkx as nx
from lxml.html import fromstring, tostring

_ARTICLE_HOST = "wikipedia.org"
_NON_ARTICLE_NAMESPACES = {
    "File",
    "Special",
    "Category",
    "Help",
    "Wikipedia",
    "Template",
    "Portal",
    "Talk",
    "User",
    "MediaWiki",
    "Draft",
    "Module",
}
_COLLECTOR_TERM = "No Wikipedia article"
_PMC_ID = re.compile(r"PMC(\d+)", re.IGNORECASE)

LINKS_TO = "links_to"
SHARES_PAPER = "shares_paper"

# Graph-level record of how the encyclopedia, and then the graph, was made.
HISTORY_FIELDS = (
    "query",
    "pygetpapers_command",
    "pygetpapers_dir",
    "corpus_dir",
    "review_json",
    "wordlist_csv",
    "encyclopedia_html",
    "paper_count",
    "term_count",
    "stop_after",
    "links",
)

# Names the encyclopedia-to-graph script can be given. Further kinds are added here.
LINK_OPTIONS = {
    "description": LINKS_TO,
}


def wikipedia_page_key(url: str) -> str:
    """Language host plus article title, or empty when url is not an article."""
    raw = str(url or "").strip()
    if not raw or raw.startswith("#"):
        return ""
    if raw.startswith("/wiki/") or raw.startswith("/w/"):
        raw = "https://en.wikipedia.org" + raw
    elif raw.startswith("wiki/"):
        raw = "https://en.wikipedia.org/" + raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower().split(":")[0]
    if _ARTICLE_HOST not in host:
        return ""
    title = ""
    path = unquote(parsed.path or "")
    if path.startswith("/wiki/"):
        title = path[len("/wiki/"):]
    elif path.rstrip("/").endswith("/index.php"):
        title = unquote((parse_qs(parsed.query).get("title") or [""])[0])
    title = title.split("#", 1)[0].strip().strip("/")
    if not title:
        return ""
    namespace = title.split(":", 1)[0]
    if ":" in title and namespace in _NON_ARTICLE_NAMESPACES:
        return ""
    title = title.replace(" ", "_")
    return f"{host}/wiki/{title}"


def paper_id(value: str) -> str:
    """PMC id from a Europe PMC url or a paper filename."""
    match = _PMC_ID.search(str(value or ""))
    if not match:
        return ""
    return "PMC" + match.group(1)


def papers_of(entry: dict) -> Set[str]:
    """Papers referenced on one entry."""
    found: Set[str] = set()
    for example in entry.get("paper_examples") or []:
        if isinstance(example, str):
            identifier = paper_id(example)
        else:
            identifier = paper_id(str(example.get("url") or "")) or paper_id(
                str(example.get("source") or "")
            )
        if identifier:
            found.add(identifier)
    return found


def description_page_keys(description_html: str) -> List[str]:
    """Wikipedia articles linked from a description, in document order."""
    html = str(description_html or "").strip()
    if not html:
        return []
    try:
        root = fromstring(html)
    except Exception:
        return []
    keys: List[str] = []
    for anchor in root.xpath(".//a[@href]"):
        key = wikipedia_page_key(anchor.get("href") or "")
        if key:
            keys.append(key)
    return keys


def pipeline_summary_path(encyclopedia_html: Path) -> Optional[Path]:
    """pipeline_summary.json beside the encyclopedia, or one directory above it."""
    for parent in list(Path(encyclopedia_html).parents)[:4]:
        candidate = parent / "pipeline_summary.json"
        if candidate.is_file():
            return candidate
    return None


def load_creation_history(summary_path: Optional[Path] = None, **overrides) -> Dict[str, str]:
    """History fields from a pipeline summary, with later values filling gaps.

    An empty override does not erase a value already stored in the summary.
    """
    raw: Dict = {}
    if summary_path and Path(summary_path).is_file():
        raw = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    history = {field: raw.get(field, "") for field in HISTORY_FIELDS}
    for key, value in overrides.items():
        if key in HISTORY_FIELDS and value is not None and str(value) != "":
            history[key] = value
    return {
        field: "" if history.get(field) is None else str(history.get(field))
        for field in HISTORY_FIELDS
    }


def attach_creation_history(graph: nx.Graph, history: Dict[str, str]) -> None:
    """Store creation history as graph-level GraphML attributes."""
    for field in HISTORY_FIELDS:
        graph.graph[f"history_{field}"] = str(history.get(field, "") or "")


def entries_from_encyclopedia_html(html_path) -> List[dict]:
    """Read encyclopedia entries from an HTML file.

    page(E) is the entry's own Wikipedia link. Description links are kept in
    the description HTML. Paper links on the entry are kept for later options.
    """
    root = fromstring(Path(html_path).read_bytes())
    entries = []
    for div in root.xpath(".//div[@role='ami_entry']"):
        description = div.xpath(".//p[contains(@class,'wpage_first_para')]")
        own_page = div.xpath("./a[contains(@class,'wikipedia-link')]")
        papers = []
        for anchor in div.xpath(".//a[contains(@class,'paper-link')]"):
            papers.append({
                "url": anchor.get("href") or "",
                "source": (anchor.text_content() or "").strip(),
            })
        entries.append({
            "term": div.get("term") or "",
            "wikipedia_url": own_page[0].get("href") if own_page else "",
            "description_html": tostring(description[0], encoding="unicode") if description else "",
            "wikidata_id": div.get("wikidataID") or div.get("wikidataid") or "",
            "paper_examples": papers,
        })
    return entries


def build_unweighted_entry_graph(
    entries: Sequence[dict],
    links: Iterable[str] | None = None,
) -> nx.MultiDiGraph:
    """Build an entry graph using the requested link kinds.

    links uses the relationship ids, such as links_to. When omitted, both
    links_to and shares_paper are created. shares_paper is stored once, from
    the earlier term to the later term.
    """
    selected = {LINKS_TO, SHARES_PAPER} if links is None else set(links)
    graph = nx.MultiDiGraph()
    page_to_term: Dict[str, str] = {}
    papers_by_term: Dict[str, Set[str]] = {}

    for entry in _entry_nodes(entries):
        term = str(entry.get("term") or "").strip()
        page = wikipedia_page_key(str(entry.get("wikipedia_url") or ""))
        papers = papers_of(entry)
        graph.add_node(
            term,
            term=term,
            wikipedia_url=str(entry.get("wikipedia_url") or ""),
            wikidata_id=str(entry.get("wikidata_id") or ""),
            papers=sorted(papers),
        )
        if page and page not in page_to_term:
            page_to_term[page] = term
        papers_by_term[term] = papers

    if LINKS_TO in selected:
        for entry in _entry_nodes(entries):
            source = str(entry.get("term") or "").strip()
            linked_pages = set(description_page_keys(str(entry.get("description_html") or "")))
            for page in linked_pages:
                target = page_to_term.get(page, "")
                if target and target != source:
                    graph.add_edge(source, target, relationship=LINKS_TO)

    if SHARES_PAPER in selected:
        terms = list(papers_by_term)
        for index, left in enumerate(terms):
            for right in terms[index + 1:]:
                shared = papers_by_term[left] & papers_by_term[right]
                if not shared:
                    continue
                earlier, later = sorted((left, right), key=str.casefold)
                graph.add_edge(
                    earlier,
                    later,
                    relationship=SHARES_PAPER,
                    shared_papers=sorted(shared),
                )
    return graph


def _entry_nodes(entries: Iterable[dict]) -> List[dict]:
    chosen: List[dict] = []
    seen = set()
    for entry in entries:
        term = str(entry.get("term") or "").strip()
        if not term or term == _COLLECTOR_TERM or term.casefold() in seen:
            continue
        seen.add(term.casefold())
        chosen.append(entry)
    return chosen
