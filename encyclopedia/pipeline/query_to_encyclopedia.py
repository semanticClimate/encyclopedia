"""
Query literature with pygetpapers, review it in semantic_corpus, and build an encyclopedia.

Stages:
1. Download Europe PMC papers with pygetpapers (PMC*/eupmc_result.json layout).
2. Ingest that directory into a BAGIT corpus and write a review table.
3. Extract keyphrases from included papers (or every downloaded paper).
4. Build a Wikipedia-enriched encyclopedia from the wordlist.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from lxml import etree

from encyclopedia.ipcc.phase1_wordlist import aggregate_keyword_counts, collect_keyword_csvs
from encyclopedia.utils.resources import Resources


PYGETPAPERS_COMMAND = "pygetpapers"
EUROPE_PMC_API = "europe_pmc"
EUPMC_RESULT_JSON = "eupmc_result.json"
FULLTEXT_XML = "fulltext.xml"
FULLTEXT_HTML = "fulltext.html"
PMC_PREFIX = "PMC"
PAPER_ID_PREFIX = "europe_pmc_"
REVIEW_STATUS_INCLUDE = "include"
STOP_AFTER_DOWNLOAD = "download"
STOP_AFTER_REVIEW = "review"
STOP_AFTER_WORDLIST = "wordlist"
STOP_AFTER_ENCYCLOPEDIA = "encyclopedia"
STOP_AFTER_VALUES = (
    STOP_AFTER_DOWNLOAD,
    STOP_AFTER_REVIEW,
    STOP_AFTER_WORDLIST,
    STOP_AFTER_ENCYCLOPEDIA,
)


@dataclass(frozen=True)
class QueryToEncyclopediaResult:
    """Paths and counts produced by one pipeline run."""

    pygetpapers_dir: Path
    corpus_dir: Optional[Path]
    review_json: Optional[Path]
    wordlist_csv: Optional[Path]
    encyclopedia_html: Optional[Path]
    paper_count: int
    term_count: int
    stop_after: str


def build_pygetpapers_command(
    query: str,
    output_dir: Path,
    limit: int,
    download_xml: bool = True,
    download_pdf: bool = False,
) -> str:
    """Build a pygetpapers command string for Europe PMC."""
    if not query.strip():
        raise ValueError("query must be a non-empty string")
    if limit < 1:
        raise ValueError(f"limit must be at least 1, got {limit}")

    parts = [
        PYGETPAPERS_COMMAND,
        "-q",
        query,
        "-k",
        str(limit),
        "-o",
        str(output_dir),
        "--api",
        EUROPE_PMC_API,
    ]
    if download_xml:
        parts.append("-x")
    if download_pdf:
        parts.append("-p")
    return " ".join(shlex.quote(part) for part in parts)


def run_pygetpapers_query(
    query: str,
    output_dir: Path,
    limit: int,
    download_pdf: bool = False,
) -> Dict[str, object]:
    """Run pygetpapers and return its result dictionary."""
    try:
        from pygetpapers import run_pygetpapers
    except ImportError as exc:
        raise ImportError(
            "pygetpapers is required to download papers. "
            "Install the sibling repo with: pip install -e ../pygetpapers"
        ) from exc

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_pygetpapers_command(
        query=query,
        output_dir=output_dir,
        limit=limit,
        download_xml=True,
        download_pdf=download_pdf,
    )
    return run_pygetpapers(command)


def discover_paper_folders(pygetpapers_dir: Path) -> List[Path]:
    """Return PMC folders that contain eupmc_result.json."""
    pygetpapers_dir = Path(pygetpapers_dir)
    if not pygetpapers_dir.is_dir():
        return []
    folders: List[Path] = []
    for child in pygetpapers_dir.iterdir():
        if not child.is_dir() or not child.name.startswith(PMC_PREFIX):
            continue
        if Path(child, EUPMC_RESULT_JSON).is_file():
            folders.append(child)
    return sorted(folders)


def pmcid_from_review_row(row: Dict[str, object]) -> str:
    """Read a PMC id from a semantic_corpus review row."""
    pmcid = str(row.get("pmcid") or "").strip()
    if pmcid:
        return pmcid
    paper_id = str(row.get("paper_id") or "").strip()
    if paper_id.startswith(PAPER_ID_PREFIX):
        return paper_id[len(PAPER_ID_PREFIX):]
    return paper_id


def included_pmcids(review_table_path: Path) -> List[str]:
    """Return PMC ids whose review_status is include."""
    review_table_path = Path(review_table_path)
    rows = json.loads(review_table_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Review table must be a JSON list: {review_table_path}")
    pmcids: List[str] = []
    for row in rows:
        if row.get("review_status") != REVIEW_STATUS_INCLUDE:
            continue
        pmcid = pmcid_from_review_row(row)
        if pmcid:
            pmcids.append(pmcid)
    return pmcids


def select_paper_folders(
    pygetpapers_dir: Path,
    review_table_path: Optional[Path] = None,
    use_all_papers: bool = False,
) -> List[Path]:
    """Choose paper folders for keyphrase extraction.

    Without a review table, or when use_all_papers is true, every downloaded
    paper is used. With a review table, only rows marked include are used.
    """
    folders = discover_paper_folders(pygetpapers_dir)
    if use_all_papers or review_table_path is None:
        return folders

    wanted = set(included_pmcids(Path(review_table_path)))
    if not wanted:
        raise ValueError(
            "Review table has no papers marked include. "
            "Edit review_status, or pass use_all_papers=True."
        )
    return [folder for folder in folders if folder.name in wanted]


def xml_file_to_plain_text(xml_path: Path) -> str:
    """Extract visible text from a JATS or HTML fulltext file."""
    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        tree = etree.parse(str(xml_path), parser)
        for element in tree.xpath("//script|//style"):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
        texts = tree.xpath("//text()")
        plain = " ".join(part.strip() for part in texts if part and str(part).strip())
    except etree.XMLSyntaxError:
        raw = Path(xml_path).read_text(encoding="utf-8", errors="ignore")
        plain = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
        plain = re.sub(r"(?is)<[^>]+>", " ", plain)
    plain = plain.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", plain).strip()


def prepare_plain_texts(paper_folders: Sequence[Path], text_dir: Path) -> List[Path]:
    """Write one .txt file per paper from fulltext.xml or fulltext.html."""
    text_dir = Path(text_dir)
    text_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for folder in paper_folders:
        source = Path(folder, FULLTEXT_XML)
        if not source.is_file():
            source = Path(folder, FULLTEXT_HTML)
        if not source.is_file():
            continue
        text_path = Path(text_dir, f"{folder.name}.txt")
        text_path.write_text(xml_file_to_plain_text(source), encoding="utf-8")
        written.append(text_path)
    return written


def extract_keyword_csvs(
    text_files: Sequence[Path],
    keyword_dir: Path,
    top_n: int,
) -> List[Path]:
    """Run txt2phrases on prepared text files and return keyword CSV paths."""
    try:
        from txt2phrases import KeywordExtraction
    except ImportError:
        try:
            from txt2phrases.keyword import KeywordExtraction
        except ImportError as exc:
            raise ImportError(
                "txt2phrases is required to build the wordlist. "
                "Install with: pip install txt2phrases"
            ) from exc

    keyword_dir = Path(keyword_dir)
    keyword_dir.mkdir(parents=True, exist_ok=True)
    for text_file in text_files:
        extractor = KeywordExtraction(
            input_path=str(text_file),
            output_folder=str(keyword_dir),
            top_n=top_n,
        )
        extractor.extract()
    return collect_keyword_csvs(keyword_dir)


def write_filtered_wordlist(
    keyword_csv_paths: Sequence[Path],
    wordlist_csv: Path,
    min_count: int,
    min_term_words: int,
    max_term_words: int,
    max_terms: int,
) -> List[str]:
    """Aggregate keyword CSVs and write a term,count wordlist."""
    counts = aggregate_keyword_counts(keyword_csv_paths)
    items = []
    for term, count in counts.items():
        if count < min_count:
            continue
        token_count = len(term.split())
        if token_count < min_term_words or token_count > max_term_words:
            continue
        items.append((term, count))
    items.sort(key=lambda item: (-item[1], item[0].lower()))
    if max_terms > 0:
        items = items[:max_terms]

    wordlist_csv = Path(wordlist_csv)
    wordlist_csv.parent.mkdir(parents=True, exist_ok=True)
    lines = ["term,count"]
    for term, count in items:
        escaped = term.replace('"', '""')
        if "," in term or '"' in term:
            lines.append(f'"{escaped}",{count}')
        else:
            lines.append(f"{term},{count}")
    wordlist_csv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return [term for term, _count in items]


def ingest_downloaded_papers(
    pygetpapers_dir: Path,
    corpus_dir: Path,
) -> Dict[str, Path]:
    """Ingest a pygetpapers directory and export semantic_corpus review tables."""
    try:
        from semantic_corpus.corpus_review.workflow import ingest_and_review_pygetpapers
    except ImportError as exc:
        raise ImportError(
            "semantic_corpus is required to ingest and review papers. "
            "Install the sibling repo with: pip install -e ../semantic_corpus"
        ) from exc

    return ingest_and_review_pygetpapers(
        Path(pygetpapers_dir),
        Path(corpus_dir),
        query_run_path=None,
    )


def _slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text.strip()).strip("_").lower()
    return slug[:60] or "query"


def run_query_to_encyclopedia(
    *,
    query: str = "",
    pygetpapers_dir: Optional[Path] = None,
    work_dir: Optional[Path] = None,
    corpus_dir: Optional[Path] = None,
    limit: int = 10,
    download_pdf: bool = False,
    review_table: Optional[Path] = None,
    use_all_papers: bool = False,
    top_n: int = 50,
    max_terms: int = 30,
    min_count: int = 2,
    min_term_words: int = 1,
    max_term_words: int = 6,
    title: str = "",
    encyclopedia_html: Optional[Path] = None,
    add_wikipedia: bool = True,
    stop_after: str = STOP_AFTER_ENCYCLOPEDIA,
    skip_ingest: bool = False,
) -> QueryToEncyclopediaResult:
    """Run the query-to-encyclopedia pipeline up to stop_after."""
    if stop_after not in STOP_AFTER_VALUES:
        raise ValueError(
            f"stop_after must be one of {STOP_AFTER_VALUES}, got {stop_after!r}"
        )
    if pygetpapers_dir is None and not query.strip():
        raise ValueError("Provide query or pygetpapers_dir")

    if work_dir is None:
        work_dir = Resources.get_temp_dir("query_to_encyclopedia", _slug(query or "existing"))
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    if pygetpapers_dir is None:
        pygetpapers_dir = Path(work_dir, "pygetpapers")
        download_result = run_pygetpapers_query(
            query=query,
            output_dir=pygetpapers_dir,
            limit=limit,
            download_pdf=download_pdf,
        )
        if not download_result.get("success"):
            detail = download_result.get("error") or download_result.get("stderr") or download_result
            raise RuntimeError(f"pygetpapers failed: {detail}")
    else:
        pygetpapers_dir = Path(pygetpapers_dir)
        if not pygetpapers_dir.is_dir():
            raise FileNotFoundError(f"pygetpapers directory not found: {pygetpapers_dir}")

    paper_count = len(discover_paper_folders(pygetpapers_dir))
    corpus_path: Optional[Path] = None
    review_json: Optional[Path] = Path(review_table) if review_table else None
    if stop_after == STOP_AFTER_DOWNLOAD:
        return _finish(
            work_dir, pygetpapers_dir, None, None, None, None, paper_count, 0, stop_after
        )

    corpus_path = Path(corpus_dir) if corpus_dir else Path(work_dir, "corpus")
    if skip_ingest:
        if review_json is None or not review_json.is_file():
            raise FileNotFoundError(
                "skip_ingest requires an existing review table JSON"
            )
    else:
        review_paths = ingest_downloaded_papers(pygetpapers_dir, corpus_path)
        if review_json is None:
            review_json = Path(review_paths["json"])
    if stop_after == STOP_AFTER_REVIEW:
        return _finish(
            work_dir, pygetpapers_dir, corpus_path, review_json, None, None,
            paper_count, 0, stop_after,
        )

    table_for_filter = Path(review_table) if review_table else None
    folders = select_paper_folders(
        pygetpapers_dir,
        review_table_path=table_for_filter,
        use_all_papers=use_all_papers or table_for_filter is None,
    )
    text_files = prepare_plain_texts(folders, Path(work_dir, "texts"))
    if not text_files:
        raise FileNotFoundError(
            f"No fulltext.xml or fulltext.html files in {len(folders)} selected papers"
        )
    keyword_csvs = extract_keyword_csvs(text_files, Path(work_dir, "keywords"), top_n=top_n)
    wordlist_csv = Path(work_dir, "wordlist.csv")
    terms = write_filtered_wordlist(
        keyword_csvs,
        wordlist_csv,
        min_count=min_count,
        min_term_words=min_term_words,
        max_term_words=max_term_words,
        max_terms=max_terms,
    )
    if stop_after == STOP_AFTER_WORDLIST:
        return _finish(
            work_dir, pygetpapers_dir, corpus_path, review_json, wordlist_csv, None,
            len(folders), len(terms), stop_after,
        )

    from Examples.create_encyclopedia_from_wordlist import (
        create_encyclopedia_from_wordlist,
        save_encyclopedia,
    )

    html_path = Path(encyclopedia_html) if encyclopedia_html else Path(work_dir, "encyclopedia.html")
    encyclopedia_title = title or query or pygetpapers_dir.name
    encyclopedia = create_encyclopedia_from_wordlist(
        terms=terms,
        title=encyclopedia_title,
        add_wikipedia=add_wikipedia,
        add_images=False,
        validate=False,
        verbose=False,
    )
    save_encyclopedia(encyclopedia, html_path)
    return _finish(
        work_dir, pygetpapers_dir, corpus_path, review_json, wordlist_csv, html_path,
        len(folders), len(terms), stop_after,
    )


def _finish(
    work_dir: Path,
    pygetpapers_dir: Path,
    corpus_dir: Optional[Path],
    review_json: Optional[Path],
    wordlist_csv: Optional[Path],
    encyclopedia_html: Optional[Path],
    paper_count: int,
    term_count: int,
    stop_after: str,
) -> QueryToEncyclopediaResult:
    result = QueryToEncyclopediaResult(
        pygetpapers_dir=pygetpapers_dir,
        corpus_dir=corpus_dir,
        review_json=review_json,
        wordlist_csv=wordlist_csv,
        encyclopedia_html=encyclopedia_html,
        paper_count=paper_count,
        term_count=term_count,
        stop_after=stop_after,
    )
    summary = {
        "pygetpapers_dir": str(pygetpapers_dir),
        "corpus_dir": str(corpus_dir) if corpus_dir else "",
        "review_json": str(review_json) if review_json else "",
        "wordlist_csv": str(wordlist_csv) if wordlist_csv else "",
        "encyclopedia_html": str(encyclopedia_html) if encyclopedia_html else "",
        "paper_count": paper_count,
        "term_count": term_count,
        "stop_after": stop_after,
    }
    Path(work_dir, "pipeline_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    return result
