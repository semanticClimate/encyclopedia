"""Choose a Wikipedia page from a disambiguation page using paper sentences.

The gloss on the disambiguation page is often only a few words. A shortlist of
candidates is ranked with that gloss, then the lead paragraph of each
shortlisted page is compared with the sentences saved from the papers.
Comparison uses scikit-learn TF-IDF, which is already a project dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

from lxml.html import fromstring
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from encyclopedia.ipcc.phase1_wordlist import phrase_key


SHORTLIST_SIZE = 5
SCORE_MARGIN = 1.5
MINIMUM_SCORE = 0.12
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "encyclopedia/1.0 (disambiguation; research)"
_LEADING_WORDS = {"the", "a", "an", "of", "and", "for", "in", "on"}


@dataclass
class DisambiguationCandidate:
    """One link on a disambiguation page."""

    title: str
    gloss: str
    href: str


@dataclass
class DisambiguationDecision:
    """Result of comparing disambiguation targets with paper sentences."""

    status: str
    history: str
    chosen_title: str = ""
    titles: List[str] = field(default_factory=list)


def load_context_sentences(contexts_jsonl: Path) -> Dict[str, List[str]]:
    """Group saved paper sentences by case-insensitive term."""
    grouped: Dict[str, List[str]] = {}
    path = Path(contexts_jsonl)
    if not path.is_file():
        return grouped
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        term = str(record.get("keyword") or "").strip()
        sentence = str(record.get("sentence") or "").strip()
        if not term or not sentence:
            continue
        grouped.setdefault(phrase_key(term), []).append(sentence)
    return grouped


def disambiguation_page_html(intro: str, items: Sequence[tuple]) -> str:
    """Build a small disambiguation page for tests and the educational example.

    Each item is (title, gloss).
    """
    lines = []
    for title, gloss in items:
        slug = title.replace(" ", "_")
        lines.append(
            f'<li><a href="/wiki/{slug}" title="{title}">{title}</a>, {gloss}</li>'
        )
    body = "".join(lines)
    return (
        "<html><body><main>"
        f"<p>{intro}</p><ul>{body}</ul>"
        "</main></body></html>"
    )


def parse_disambiguation_candidates(html_elem) -> List[DisambiguationCandidate]:
    """Read article links and their glosses from a disambiguation page."""
    if isinstance(html_elem, str):
        html_elem = fromstring(html_elem)
    candidates: List[DisambiguationCandidate] = []
    seen = set()
    for item in html_elem.xpath("//li[.//a[contains(@href, '/wiki/')]]"):
        link = item.xpath(".//a[contains(@href, '/wiki/')]")[0]
        href = link.get("href") or ""
        slug = href.split("/wiki/")[-1].split("#")[0]
        if ":" in slug or slug.lower().endswith("(disambiguation)"):
            continue
        title = " ".join((link.get("title") or link.text_content() or "").split())
        if not title:
            continue
        key = phrase_key(title)
        if key in seen:
            continue
        seen.add(key)
        gloss = " ".join(item.text_content().split())
        candidates.append(DisambiguationCandidate(title=title, gloss=gloss, href=href))
        if len(candidates) >= 30:
            break
    return candidates


def acronym_expansion(term: str, sentences: Sequence[str]) -> str:
    """Return a definition written next to the term in the papers, if one exists."""
    term_pattern = re.escape(term.strip())
    before = re.compile(
        rf"([A-Za-z][A-Za-z\s\-]{{2,80}}?)\s*\(\s*{term_pattern}\s*\)",
        re.IGNORECASE,
    )
    after = re.compile(
        rf"{term_pattern}\s*\(\s*([A-Za-z][A-Za-z\s\-]{{2,80}}?)\s*\)",
        re.IGNORECASE,
    )
    for sentence in sentences:
        match = before.search(sentence) or after.search(sentence)
        if match is None:
            continue
        expansion = _clean_expansion(match.group(1))
        if len(expansion.split()) >= 2:
            return expansion
    return ""


def _clean_expansion(text: str) -> str:
    words = text.strip(" .,:;").split()
    while words and words[0].lower() in _LEADING_WORDS:
        words.pop(0)
    return " ".join(words)


def title_matches_expansion(expansion: str, title: str) -> bool:
    """True when the paper's expansion names this Wikipedia title."""
    expansion_tokens = phrase_key(expansion).split()
    title_tokens = phrase_key(title).split()
    if not expansion_tokens or not title_tokens:
        return False
    if expansion_tokens == title_tokens:
        return True
    return len(expansion_tokens) >= 2 and all(token in title_tokens for token in expansion_tokens)


def text_similarities(query: str, documents: Sequence[str]) -> List[float]:
    """TF-IDF cosine of one query against each document."""
    if not query.strip() or not documents:
        return [0.0] * len(documents)
    corpus = [query] + [document or "" for document in documents]
    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2)).fit_transform(corpus)
    except ValueError:
        return [0.0] * len(documents)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
    return [float(score) for score in scores]


def fetch_wikipedia_leads(titles: Sequence[str]) -> Dict[str, str]:
    """Download the lead paragraph of each title from the MediaWiki API."""
    import requests

    requested = [title for title in titles if title]
    if not requested:
        return {}
    response = requests.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
            "titles": "|".join(requested),
        },
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json().get("query") or {}
    leads = {}
    for page in (payload.get("pages") or {}).values():
        title = str(page.get("title") or "")
        extract = str(page.get("extract") or "").strip()
        if title and extract:
            leads[phrase_key(title)] = extract
    for redirect in payload.get("redirects") or []:
        source = phrase_key(str(redirect.get("from") or ""))
        target = phrase_key(str(redirect.get("to") or ""))
        if source and target and target in leads:
            leads[source] = leads[target]
    return leads


def resolve_disambiguation(
    term: str,
    html_elem,
    sentences: Sequence[str],
    leads: Optional[Mapping[str, str]] = None,
) -> DisambiguationDecision:
    """Pick one disambiguation target, or keep a very small set when scores are close.

    Pass leads to supply lead paragraphs without calling Wikipedia. When leads
    is omitted, the shortlisted leads are downloaded.
    """
    candidates = parse_disambiguation_candidates(html_elem)
    if not candidates:
        return DisambiguationDecision(
            status="unresolved",
            history="Disambiguation: unresolved. The page listed no article links.",
        )

    expansion = acronym_expansion(term, sentences)
    if expansion:
        matched = [
            candidate for candidate in candidates
            if title_matches_expansion(expansion, candidate.title)
        ]
        if len(matched) == 1:
            title = matched[0].title
            others = _other_titles(candidates, [title])
            return DisambiguationDecision(
                status="resolved",
                chosen_title=title,
                titles=[title],
                history=_history("acronym in the papers selected", title, others),
            )

    query = " ".join(sentences)
    gloss_scores = text_similarities(
        query,
        [f"{candidate.title}. {candidate.gloss}" for candidate in candidates],
    )
    ranked = sorted(zip(candidates, gloss_scores), key=lambda item: item[1], reverse=True)
    shortlist = [candidate for candidate, _score in ranked[:SHORTLIST_SIZE]]
    lead_text = _leads_for_shortlist(shortlist, leads)
    documents = [
        lead_text.get(phrase_key(candidate.title)) or f"{candidate.title}. {candidate.gloss}"
        for candidate in shortlist
    ]
    scores = text_similarities(query, documents)
    ordered = sorted(zip(shortlist, scores), key=lambda item: item[1], reverse=True)
    return _decision_from_scores(ordered, candidates)


def _leads_for_shortlist(
    shortlist: Sequence[DisambiguationCandidate],
    leads: Optional[Mapping[str, str]],
) -> Dict[str, str]:
    if leads is not None:
        return {phrase_key(title): text for title, text in leads.items()}
    try:
        return fetch_wikipedia_leads([candidate.title for candidate in shortlist])
    except Exception:
        return {}


def _decision_from_scores(ordered, candidates) -> DisambiguationDecision:
    if not ordered:
        return DisambiguationDecision(
            status="unresolved",
            history="Disambiguation: unresolved. No candidate could be scored.",
        )
    best, best_score = ordered[0]
    second_score = ordered[1][1] if len(ordered) > 1 else 0.0
    titles = [candidate.title for candidate, _score in ordered]
    if best_score < MINIMUM_SCORE:
        return DisambiguationDecision(
            status="unresolved",
            titles=titles[:3],
            history=_unresolved_history(titles[:3]),
        )
    clearly_ahead = best_score >= second_score * SCORE_MARGIN
    if clearly_ahead:
        others = _other_titles(candidates, [best.title])
        return DisambiguationDecision(
            status="resolved",
            chosen_title=best.title,
            titles=[best.title],
            history=_history("lead paragraphs matched", best.title, others),
        )
    close = [candidate.title for candidate, score in ordered[:2] if score >= MINIMUM_SCORE]
    if len(close) == 2:
        return DisambiguationDecision(
            status="choice",
            titles=close,
            history=f"Disambiguation: two close pages kept, {close[0]} and {close[1]}.",
        )
    return DisambiguationDecision(
        status="unresolved",
        titles=titles[:3],
        history=_unresolved_history(titles[:3]),
    )


def _other_titles(candidates, chosen: Sequence[str]) -> List[str]:
    chosen_keys = {phrase_key(title) for title in chosen}
    return [
        candidate.title for candidate in candidates
        if phrase_key(candidate.title) not in chosen_keys
    ][:2]


def _history(reason: str, title: str, others: Sequence[str]) -> str:
    text = f"Disambiguation: {reason} {title}."
    if others:
        text += " Also considered: " + "; ".join(others) + "."
    return text


def _unresolved_history(titles: Sequence[str]) -> str:
    if not titles:
        return "Disambiguation: unresolved."
    return "Disambiguation: unresolved. Top pages: " + "; ".join(titles) + "."


def educational_examples() -> List[dict]:
    """Offline cases used by the example script and the tests."""
    return [
        {
            "name": "Acronym defined in the paper",
            "term": "SST",
            "sentences": [
                "The sea surface temperature (SST) anomaly was positive across the North Atlantic."
            ],
            "items": [
                ("Sea surface temperature", "ocean temperature"),
                ("Supersonic transport", "aircraft"),
                ("Secondary school teacher", "occupation"),
            ],
            "leads": {},
            "status": "resolved",
            "title": "Sea surface temperature",
        },
        {
            "name": "Lead paragraph selects the scientific sense",
            "term": "mercury",
            "sentences": [
                "Mercury concentrations in the sediment core increased during the industrial period.",
                "The marine sediment recorded mercury deposition from the atmosphere.",
            ],
            "items": [
                ("Mercury (planet)", "closest planet to the Sun"),
                ("Mercury (element)", "chemical element"),
            ],
            "leads": {
                "Mercury (planet)": (
                    "Mercury is the smallest planet in the Solar System and the nearest to the Sun. "
                    "It is a rocky planet with no atmosphere relevant to ocean sediment."
                ),
                "Mercury (element)": (
                    "Mercury is a chemical element. Mercury concentrations in marine sediment "
                    "record atmospheric deposition during the industrial period."
                ),
            },
            "status": "resolved",
            "title": "Mercury (element)",
        },
        {
            "name": "Climate sense of an acronym",
            "term": "AMV",
            "sentences": [
                "The AMV index describes multidecadal variability of Atlantic sea surface temperature."
            ],
            "items": [
                ("Atlantic multidecadal variability", "climate pattern"),
                ("Anime music video", "fan video"),
            ],
            "leads": {
                "Atlantic multidecadal variability": (
                    "Atlantic multidecadal variability is a climate pattern of sea surface "
                    "temperature in the North Atlantic over multiple decades."
                ),
                "Anime music video": (
                    "An anime music video is a fan-made video that edits animated footage to music."
                ),
            },
            "status": "resolved",
            "title": "Atlantic multidecadal variability",
        },
        {
            "name": "Two leads stay too close to choose",
            "term": "Atlantic index",
            "sentences": [
                "The survey measured Atlantic temperature and Atlantic salinity."
            ],
            "items": [
                ("Atlantic temperature index", "a northern ocean record"),
                ("Atlantic salinity index", "a southern ocean record"),
            ],
            "leads": {
                "Atlantic temperature index": (
                    "This page describes Atlantic temperature and Atlantic salinity "
                    "in the northern record."
                ),
                "Atlantic salinity index": (
                    "This page describes Atlantic temperature and Atlantic salinity "
                    "in the southern record."
                ),
            },
            "status": "choice",
            "title": "",
        },
        {
            "name": "No paper context matches a page",
            "term": "proxy",
            "sentences": ["The value was recorded in the supplement."],
            "items": [
                ("Proxy (climate)", "a stand-in used in elections"),
                ("Proxy server", "a computer network service"),
            ],
            "leads": {
                "Proxy (climate)": "A proxy vote is cast by someone else at a meeting or election.",
                "Proxy server": "A proxy server relays network traffic between a client and another server.",
            },
            "status": "unresolved",
            "title": "",
        },
    ]
