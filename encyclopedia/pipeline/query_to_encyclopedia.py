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
import csv
import json
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from lxml import etree

from encyclopedia.ipcc.phase1_wordlist import (
    choose_surface_form,
    collect_keyword_csvs,
    phrase_key,
)
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
    query: str = ""
    pygetpapers_command: str = ""


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


def _load_run_pygetpapers():
    """Return the command-string runner from a current pygetpapers checkout."""
    try:
        from pygetpapers import run_pygetpapers
    except ImportError:
        try:
            from pygetpapers.pygetpapers import run_pygetpapers
        except ImportError:
            return None
    return run_pygetpapers


def run_pygetpapers_query(
    query: str,
    output_dir: Path,
    limit: int,
    download_pdf: bool = False,
) -> Dict[str, object]:
    """Run pygetpapers and return its result dictionary.

    Current checkouts export run_pygetpapers(command_string). The installed
    package on some machines only exposes Pygetpapers.run_command.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_pygetpapers_command(
        query=query,
        output_dir=output_dir,
        limit=limit,
        download_xml=True,
        download_pdf=download_pdf,
    )
    run_pygetpapers = _load_run_pygetpapers()
    if run_pygetpapers is not None:
        result = run_pygetpapers(command)
        if isinstance(result, dict):
            result["query"] = query
            result["pygetpapers_command"] = command
        return result

    try:
        from pygetpapers import Pygetpapers
    except ImportError as exc:
        raise ImportError(
            "pygetpapers is required to download papers. "
            "Install it with: pip install pygetpapers "
            "or pip install -e ../pygetpapers"
        ) from exc

    Pygetpapers().run_command(
        output=str(output_dir),
        query=query,
        xml=True,
        pdf=download_pdf,
        limit=limit,
        api=EUROPE_PMC_API,
    )
    return {
        "success": True,
        "output_directory": str(output_dir),
        "query": query,
        "pygetpapers_command": command,
    }


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


def _markup_to_plain_text(raw: str) -> str:
    """Strip tags from markup when the XML parser cannot build a tree."""
    plain = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    plain = re.sub(r"(?is)<[^>]+>", " ", plain)
    plain = plain.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", plain).strip()


def xml_file_to_plain_text(xml_path: Path) -> str:
    """Extract visible text from a JATS or HTML fulltext file.

    Europe PMC sometimes saves an error JSON body under fulltext.xml. Those
    files have no document root and are skipped.
    """
    raw = Path(xml_path).read_text(encoding="utf-8", errors="ignore").lstrip()
    if not raw.startswith("<"):
        return ""

    parser = etree.XMLParser(recover=True, huge_tree=True)
    try:
        tree = etree.parse(str(xml_path), parser)
        if tree.getroot() is None:
            return _markup_to_plain_text(raw)
        for element in tree.xpath("//script|//style"):
            parent = element.getparent()
            if parent is not None:
                parent.remove(element)
        texts = tree.xpath("//text()")
        plain = " ".join(part.strip() for part in texts if part and str(part).strip())
    except (etree.XMLSyntaxError, AssertionError, OSError):
        plain = _markup_to_plain_text(raw)
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
        plain = xml_file_to_plain_text(source)
        if not plain:
            continue
        text_path = Path(text_dir, f"{folder.name}.txt")
        text_path.write_text(plain, encoding="utf-8")
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


def _phrase_with_counts(term: str, frequency: int, paper_count: int) -> str:
    """Phrase text that states how often the term was found, and in how many papers."""
    paper_word = "paper" if paper_count == 1 else "papers"
    return f"{term} ({frequency} times in {paper_count} {paper_word})"


def aggregate_term_stats(keyword_csv_paths: Sequence[Path]) -> Dict[str, Dict[str, int]]:
    """Sum frequency per term and count how many papers contain it.

    Each keyword CSV is one paper. Repeated rows in the same file add to
    frequency but count as one paper.
    """
    grouped: Dict[str, Dict[str, object]] = {}
    for csv_path in keyword_csv_paths:
        per_paper: Dict[str, Dict[str, object]] = {}
        for term, count in _read_keyword_counts(csv_path):
            key = phrase_key(term)
            bucket = per_paper.setdefault(key, {"frequency": 0, "forms": {}})
            bucket["frequency"] = int(bucket["frequency"]) + count
            forms = bucket["forms"]
            assert isinstance(forms, dict)
            forms[term] = forms.get(term, 0) + count
        for key, bucket in per_paper.items():
            record = grouped.setdefault(key, {"frequency": 0, "paper_count": 0, "forms": {}})
            record["frequency"] = int(record["frequency"]) + int(bucket["frequency"])
            record["paper_count"] = int(record["paper_count"]) + 1
            forms = record["forms"]
            assert isinstance(forms, dict)
            paper_forms = bucket["forms"]
            assert isinstance(paper_forms, dict)
            for form, count in paper_forms.items():
                forms[form] = forms.get(form, 0) + count
    stats: Dict[str, Dict[str, int]] = {}
    for record in grouped.values():
        forms = record["forms"]
        assert isinstance(forms, dict)
        term = choose_surface_form(forms)
        stats[term] = {
            "frequency": int(record["frequency"]),
            "paper_count": int(record["paper_count"]),
        }
    return stats


def _read_keyword_counts(csv_path: Path) -> List[tuple]:
    """Read term,count pairs from one txt2phrases CSV."""
    from encyclopedia.ipcc.phase1_wordlist import _read_keyword_csv

    return _read_keyword_csv(csv_path)


def _term_rows_from_wordlist(wordlist_csv: Path) -> List[tuple]:
    """Read term, frequency, paper_count rows from a wordlist CSV."""
    rows: List[tuple] = []
    with open(wordlist_csv, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            term = (row.get("term") or "").strip()
            if not term:
                continue
            frequency = _int_field(row, "frequency", "count")
            if "paper_count" in row and str(row.get("paper_count") or "").strip():
                paper_count = _int_field(row, "paper_count")
            else:
                paper_count = 1
            rows.append((term, frequency, paper_count))
    return rows


def _int_field(row: Dict[str, str], *names: str) -> int:
    for name in names:
        if name not in row:
            continue
        try:
            return int(float(row.get(name) or 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _by_relevance(item: tuple) -> tuple:
    """More papers first, then higher frequency, then alphabetical."""
    term, frequency, paper_count = item
    return (-paper_count, -frequency, term.lower())


def select_terms_by_relevance(rows: Sequence[tuple], max_terms: int) -> List[str]:
    """Choose terms by paper coverage and frequency, then sort them alphabetically."""
    ranked = sorted(rows, key=_by_relevance)
    chosen = _limit_ranked_terms(ranked, max_terms)
    chosen.sort(key=lambda item: item[0].lower())
    return [term for term, _frequency, _paper_count in chosen]


def write_filtered_wordlist(
    keyword_csv_paths: Sequence[Path],
    wordlist_csv: Path,
    min_count: int,
    min_term_words: int,
    max_term_words: int,
    max_terms: int,
    text_dir: Optional[Path] = None,
) -> List[str]:
    """Write the selected wordlist with frequency and paper count.

    Relevance is how many papers contain the phrase, then how often it occurs.
    The written list, and the returned terms, are alphabetical.
    """
    stats = aggregate_term_stats(keyword_csv_paths)
    rows = []
    for term, record in stats.items():
        frequency = record["frequency"]
        paper_count = record["paper_count"]
        if frequency < min_count:
            continue
        token_count = len(term.split())
        if token_count < min_term_words or token_count > max_term_words:
            continue
        rows.append((term, frequency, paper_count))

    selected_terms = select_terms_by_relevance(rows, max_terms)
    selected = {term for term in selected_terms}
    written_rows = [row for row in rows if row[0] in selected]
    written_rows.sort(key=lambda item: item[0].lower())

    wordlist_csv = Path(wordlist_csv)
    wordlist_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(wordlist_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["term", "phrase", "frequency", "paper_count"],
        )
        writer.writeheader()
        for term, frequency, paper_count in written_rows:
            writer.writerow({
                "term": term,
                "phrase": _phrase_with_counts(term, frequency, paper_count),
                "frequency": frequency,
                "paper_count": paper_count,
            })
    _write_selected_contexts(
        keyword_csv_paths,
        wordlist_csv,
        selected_terms,
        text_dir=text_dir,
    )
    return selected_terms


def _context_path_for_keyword_csv(csv_path: Path) -> Path:
    """Sidecar written beside a keyword CSV during extraction."""
    name = csv_path.name
    if name.endswith("_keywords.csv"):
        return csv_path.with_name(name[: -len("_keywords.csv")] + "_contexts.jsonl")
    return csv_path.with_name(f"{csv_path.stem}_contexts.jsonl")


_MAX_SENTENCE_CHARS = 400
_CONTEXT_WINDOW = 120
_CONTEXTS_PER_PAPER = 5


def _term_pattern(term: str) -> Optional[re.Pattern]:
    """Case-insensitive whole-phrase pattern."""
    parts = [re.escape(part) for part in term.split() if part]
    if not parts:
        return None
    return re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)


def _snap_to_word(text: str, left: int, right: int) -> tuple:
    """Move a character window out to the nearest spaces so it does not cut a word."""
    if left > 0 and not text[left - 1].isspace():
        previous = text.rfind(" ", 0, left)
        if previous != -1:
            left = previous + 1
    if right < len(text) and not text[right - 1].isspace():
        following = text.find(" ", right)
        if following != -1:
            right = following
    return left, right


def _immediate_context(text: str, match_start: int, match_end: int) -> tuple:
    """Sentence around a match, or a short window when the sentence is very long.

    The third value is True when the snippet is a whole sentence.
    """
    left = 0
    for index in range(match_start - 1, -1, -1):
        if text[index] in ".!?\n":
            left = index + 1
            break
    right = len(text)
    for index in range(match_end, len(text)):
        if text[index] in ".!?\n":
            right = index + 1
            break
    whole_sentence = right - left <= _MAX_SENTENCE_CHARS
    if not whole_sentence:
        left = max(0, match_start - _CONTEXT_WINDOW)
        right = min(len(text), match_end + _CONTEXT_WINDOW)
        left, right = _snap_to_word(text, left, right)
    raw = text[left:right]
    leading = len(raw) - len(raw.lstrip())
    sentence = raw.strip()
    start = match_start - left - leading
    end = match_end - left - leading
    return sentence, max(0, start), min(len(sentence), end), whole_sentence


def search_term_in_text(
    text: str,
    term: str,
    source: str,
    per_document: int = _CONTEXTS_PER_PAPER,
    in_document_order: bool = False,
) -> List[dict]:
    """Find a term in one paper, ignoring case, and keep the surrounding sentence.

    in_document_order keeps the earliest hits. That is the view used when
    checking unexpected matches. The default keeps complete sentences first.
    """
    pattern = _term_pattern(term)
    if pattern is None or not text:
        return []
    matches = list(pattern.finditer(text))
    ranked = []
    for match in matches:
        sentence, start, end, whole_sentence = _immediate_context(
            text, match.start(), match.end()
        )
        ranked.append((0 if whole_sentence else 1, match.start(), {
            "keyword": term,
            "matched": match.group(0),
            "sentence": sentence,
            "start": start,
            "end": end,
            "source": source,
            "source_start": match.start(),
            "source_end": match.end(),
            "match_count": len(matches),
        }))
    if in_document_order:
        ranked.sort(key=lambda item: item[1])
    else:
        ranked.sort(key=lambda item: (item[0], item[1]))
    return [record for _rank, _start, record in ranked[:per_document]]


def search_texts_for_terms(
    text_files: Sequence[Path],
    terms: Sequence[str],
    per_document: int = _CONTEXTS_PER_PAPER,
) -> List[dict]:
    """Re-search each plain-text paper for the encyclopedia terms."""
    records: List[dict] = []
    for text_path in text_files:
        text = Path(text_path).read_text(encoding="utf-8")
        source = Path(text_path).name
        for term in terms:
            records.extend(search_term_in_text(text, term, source, per_document))
    return records


def _write_selected_contexts(
    keyword_csv_paths: Sequence[Path],
    wordlist_csv: Path,
    selected_terms: Sequence[str],
    text_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Save the sentence around each selected term.

    When the paper text is available, the term is searched again in that text.
    Otherwise contexts saved beside the keyword CSVs are copied. The keyword
    spelling matches the wordlist, so a later tool can open the sentence in
    the source paper.
    """
    output = Path(wordlist_csv).with_name(f"{Path(wordlist_csv).stem}_contexts.jsonl")
    if text_dir is not None:
        text_files = sorted(Path(text_dir).glob("*.txt"))
        if text_files:
            kept = search_texts_for_terms(text_files, selected_terms)
            if not kept:
                return None
            _write_context_jsonl(output, kept)
            return output
    surface_by_key = {phrase_key(term): term for term in selected_terms}
    kept = []
    for csv_path in keyword_csv_paths:
        context_path = _context_path_for_keyword_csv(Path(csv_path))
        if not context_path.is_file():
            continue
        for line in context_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            key = phrase_key(str(record.get("keyword") or ""))
            if key not in surface_by_key:
                continue
            record["keyword"] = surface_by_key[key]
            kept.append(record)
    if not kept:
        return None
    _write_context_jsonl(output, kept)
    return output


def _write_context_jsonl(output: Path, records: Sequence[dict]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


_ORCID = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dXx]\b")
_GRID = re.compile(r"\bgrid\.", re.IGNORECASE)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
_INITIALS = re.compile(r"\b[A-Z]{1,3}\b")
_YEAR_THEN_PAGES = re.compile(r"\b(?:19|20)\d{2}\b(?:\s+\d+){2,}")
_DOI = re.compile(r"\b10\.\d{4,9}/\S+")
_AFFILIATION_PREFIX = re.compile(r"^\d+\s+\d{4}\s+\d{4}\b")
FALSE_POSITIVE_REASON = "only affiliation or reference hits"


def is_boilerplate_sentence(sentence: str) -> bool:
    """True for an affiliation line or a reference line, which are false-positive hits."""
    text = " ".join(str(sentence or "").split())
    if not text:
        return True
    if _ORCID.search(text) or _GRID.search(text) or _EMAIL.search(text):
        return True
    if _AFFILIATION_PREFIX.search(text):
        return True
    initials = len(_INITIALS.findall(text))
    if text.endswith("10.") and _YEAR.search(text) and initials >= 2:
        return True
    if initials >= 3 and _YEAR_THEN_PAGES.search(text):
        return True
    if _DOI.search(text) and _YEAR.search(text) and initials >= 2:
        return True
    return False


def split_boilerplate_terms(
    rows: Sequence[tuple],
    sentences_by_term: Dict[str, Sequence[str]],
) -> tuple:
    """Keep terms that occur in a body sentence.

    sentences_by_term is keyed by phrase_key. A term with saved sentences is a
    false positive when every sentence is an affiliation or a reference. A term
    with no saved sentences stays, because there is no hit to reject.
    """
    kept: List[tuple] = []
    rejected: List[tuple] = []
    for row in rows:
        term = row[0]
        sentences = list(sentences_by_term.get(phrase_key(term), []))
        if sentences and all(is_boilerplate_sentence(sentence) for sentence in sentences):
            rejected.append((term, FALSE_POSITIVE_REASON))
        else:
            kept.append(row)
    return kept, rejected


@dataclass(frozen=True)
class FalsePositiveFilterResult:
    """Terms kept for the encyclopedia, and the terms removed as false positives."""

    terms: List[str]
    contexts_by_term: Dict[str, List[str]]
    rejected: List[tuple]


def apply_false_positive_filter(
    wordlist_csv: Path,
    max_terms: int,
    contexts_jsonl: Optional[Path] = None,
    rejected_csv: Optional[Path] = None,
) -> FalsePositiveFilterResult:
    """Drop affiliation-only and reference-only terms, then keep the most relevant.

    Rewrites the wordlist to the kept terms. Rewrites the context file to the
    body sentences for those terms. Writes the rejected terms beside the wordlist.
    """
    from encyclopedia.pipeline.wikipedia_disambiguation import load_context_sentences

    wordlist_csv = Path(wordlist_csv)
    context_path = Path(contexts_jsonl) if contexts_jsonl else wordlist_csv.with_name(
        f"{wordlist_csv.stem}_contexts.jsonl"
    )
    rejected_path = Path(rejected_csv) if rejected_csv else wordlist_csv.with_name("rejected_terms.csv")
    rows = _term_rows_from_wordlist(wordlist_csv)
    sentences = load_context_sentences(context_path) if context_path.is_file() else {}
    kept_rows, rejected = split_boilerplate_terms(rows, sentences)
    terms = select_terms_by_relevance(kept_rows, max_terms)
    chosen = set(terms)
    final_rows = [row for row in kept_rows if row[0] in chosen]
    _write_wordlist_rows(wordlist_csv, final_rows)
    _write_rejected_terms(rejected_path, rejected)
    records = _content_context_records(context_path, terms)
    if context_path.is_file() or records:
        _write_context_jsonl(context_path, records)
    contexts = load_context_sentences(context_path) if context_path.is_file() else {}
    return FalsePositiveFilterResult(terms, contexts, rejected)


def _write_wordlist_rows(wordlist_csv: Path, rows: Sequence[tuple]) -> None:
    written = sorted(rows, key=lambda item: item[0].lower())
    wordlist_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(wordlist_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["term", "phrase", "frequency", "paper_count"],
        )
        writer.writeheader()
        for term, frequency, paper_count in written:
            writer.writerow({
                "term": term,
                "phrase": _phrase_with_counts(term, frequency, paper_count),
                "frequency": frequency,
                "paper_count": paper_count,
            })


def _write_rejected_terms(rejected_csv: Path, rejected: Sequence[tuple]) -> None:
    rejected_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(rejected_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["term", "reason"])
        writer.writeheader()
        for term, reason in sorted(rejected, key=lambda item: item[0].lower()):
            writer.writerow({"term": term, "reason": reason})


def _content_context_records(context_path: Path, terms: Sequence[str]) -> List[dict]:
    keys = {phrase_key(term) for term in terms}
    if not context_path.is_file() or not keys:
        return []
    records = []
    for line in context_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        keyword = str(record.get("keyword") or "")
        sentence = str(record.get("sentence") or "")
        if phrase_key(keyword) not in keys or is_boilerplate_sentence(sentence):
            continue
        records.append(record)
    return records


def load_terms_by_relevance(wordlist_csv: Path, max_terms: int) -> List[str]:
    """Select terms by paper count and frequency, returned alphabetically.

    A wordlist that only has a count column treats each row as one paper.
    max_terms of 0 keeps every term.
    """
    rows = _term_rows_from_wordlist(Path(wordlist_csv))
    return select_terms_by_relevance(rows, max_terms)


def _limit_ranked_terms(items: Sequence[tuple], max_terms: int) -> Sequence[tuple]:
    """Keep the first max_terms rows of a list already sorted by relevance."""
    if max_terms > 0:
        return list(items)[:max_terms]
    return list(items)


WIKIPEDIA_ORIGIN = "https://en.wikipedia.org"
WIKIDATA_ORIGIN = "https://www.wikidata.org/wiki/"


def _absolutize_wikipedia_html(html: str) -> str:
    """Turn Wikipedia-relative links into absolute URLs."""
    if not html:
        return html
    html = html.replace('href="/wiki/', f'href="{WIKIPEDIA_ORIGIN}/wiki/')
    html = html.replace("href='/wiki/", f"href='{WIKIPEDIA_ORIGIN}/wiki/")
    html = html.replace('href="/w/', f'href="{WIKIPEDIA_ORIGIN}/w/')
    html = html.replace('src="//', 'src="https://')
    html = html.replace('href="//', 'href="https://')
    return html


def _canonical_wikipedia_url(wikipedia_page) -> str:
    """Article URL from the page, not the search URL used to find it."""
    html_elem = getattr(wikipedia_page, "html_elem", None)
    if html_elem is not None:
        links = html_elem.xpath("//link[@rel='canonical']/@href")
        if links and links[0]:
            return str(links[0])
    return str(getattr(wikipedia_page, "search_url", "") or "")


def _wikipedia_page_title(wikipedia_page) -> str:
    """Visible title of the Wikipedia page."""
    html_elem = getattr(wikipedia_page, "html_elem", None)
    if html_elem is not None:
        titles = html_elem.xpath("//title/text()")
        if titles:
            title = str(titles[0]).strip()
            for suffix in (" - Wikipedia", " — Wikipedia"):
                if title.endswith(suffix):
                    title = title[: -len(suffix)].strip()
            if title:
                return title
    url = _canonical_wikipedia_url(wikipedia_page)
    if "/wiki/" in url:
        from urllib.parse import unquote
        return unquote(url.split("/wiki/")[-1].replace("_", " "))
    return ""


def _non_content_note(wikipedia_page) -> str:
    """Explain a Wikipedia page that is not an article description."""
    url = _canonical_wikipedia_url(wikipedia_page).lower()
    if "index.php?search=" in url or "/special:search" in url:
        return "No description: no Wikipedia article"
    if "(disambiguation)" in url:
        return "No description: disambiguation page"
    html_elem = getattr(wikipedia_page, "html_elem", None)
    if html_elem is None:
        return ""
    if html_elem.xpath("//body[contains(@class,'mw-disambig')]"):
        return "No description: disambiguation page"
    leads = html_elem.xpath("//main//p[1]//text()")
    lead = " ".join(str(part) for part in leads).lower()
    if "may refer to" in lead:
        return "No description: disambiguation page"
    return ""


def _wikidata_id_from_page(wikipedia_page) -> str:
    """Q or P id linked from the Wikipedia page."""
    try:
        href = wikipedia_page.get_wikidata_item() or ""
    except Exception:
        href = ""
    match = re.search(r"\b([QP]\d+)\b", str(href))
    return match.group(1) if match else ""


def links_from_wikipedia_page(wikipedia_page) -> Dict[str, object]:
    """Definition, description, image, Wikipedia URL, and Wikidata id from one page."""
    from encyclopedia.cli.versioned_editor import (
        _extract_images_from_wikipedia_page,
        _fix_image_urls,
        _get_first_paragraph_html_from_wikipedia_page,
    )

    # Paragraph extraction removes navigation, including the Wikidata link.
    wikipedia_url = _canonical_wikipedia_url(wikipedia_page)
    page_title = _wikipedia_page_title(wikipedia_page)
    wikidata_id = _wikidata_id_from_page(wikipedia_page)
    content_note = _non_content_note(wikipedia_page)
    definition_html, description_html = _get_first_paragraph_html_from_wikipedia_page(
        wikipedia_page
    )
    figure = None
    image_link = ""
    images = _extract_images_from_wikipedia_page(wikipedia_page, verbose=False)
    if images:
        figure = images[0]
        _fix_image_urls(figure)
        if getattr(figure, "tag", None) == "a":
            image_link = figure.get("href") or ""
        elif hasattr(figure, "xpath"):
            anchors = figure.xpath(".//a[@href]")
            if anchors:
                image_link = anchors[0].get("href") or ""
    return {
        "wikipedia_url": wikipedia_url,
        "page_title": page_title,
        "wikidata_id": wikidata_id,
        "content_note": content_note,
        "definition_html": _absolutize_wikipedia_html(definition_html or ""),
        "description_html": _absolutize_wikipedia_html(description_html or ""),
        "figure_html": figure,
        "image_link": image_link,
    }


def _new_entry(term: str) -> Dict[str, object]:
    return {
        "term": term,
        "search_term": term,
        "page_title": term,
        "wikipedia_url": "",
        "content_note": "",
        "wikidata_id": "",
        "wikidata_category": "",
        "definition_html": "",
        "description_html": "",
        "figure_html": None,
        "image_link": "",
        "wikipedia_page_retrieved": False,
        "first_paragraph_retrieved": False,
        "disambiguation_history": "",
    }


def _apply_wikipedia_page(entry: Dict[str, object], wikipedia_page, encyclopedia) -> None:
    """Copy Wikipedia text and the entry links from one downloaded page."""
    extracted = links_from_wikipedia_page(wikipedia_page)
    entry["wikipedia_page_retrieved"] = True
    entry["wikipedia_url"] = extracted["wikipedia_url"]
    entry["page_title"] = extracted["page_title"] or entry["term"]
    entry["wikidata_id"] = extracted["wikidata_id"]
    entry["figure_html"] = extracted["figure_html"]
    entry["image_link"] = extracted["image_link"]
    note = extracted["content_note"]
    if note:
        entry["content_note"] = note
        entry["definition_html"] = ""
        entry["description_html"] = f'<p class="no-description">{note}</p>'
        entry["first_paragraph_retrieved"] = False
        if "no Wikipedia article" in note:
            entry["page_title"] = entry["term"]
    elif not extracted["description_html"]:
        note = "No description: Wikipedia page has no content paragraph"
        entry["content_note"] = note
        entry["description_html"] = f'<p class="no-description">{note}</p>'
        entry["first_paragraph_retrieved"] = False
    else:
        entry["definition_html"] = extracted["definition_html"]
        entry["description_html"] = extracted["description_html"]
        entry["first_paragraph_retrieved"] = True
    if extracted["wikidata_id"]:
        entry["wikidata_category"] = encyclopedia._get_wikidata_category(
            str(extracted["wikidata_id"])
        )


def create_encyclopedia_from_terms(
    terms: Sequence[str],
    title: str,
    encyclopedia_html: Path,
    add_wikipedia: bool = True,
    contexts_by_term: Optional[Dict[str, List[str]]] = None,
):
    """Create encyclopedia entries directly from terms.

    Each term is one entry. Wikipedia is downloaded once and supplies the
    definition, description, image, article link, and Wikidata link.
    """
    from amilib.wikimedia import WikipediaPage
    from encyclopedia.core.encyclopedia import AmiEncyclopedia

    encyclopedia = AmiEncyclopedia(title=title)
    total = len(terms)
    for index, term in enumerate(terms, start=1):
        print(f"Encyclopedia {index}/{total}: {term}", flush=True)
        entry = _new_entry(term)
        if add_wikipedia:
            try:
                wikipedia_page = WikipediaPage.lookup_wikipedia_page_for_term(term)
            except Exception as exc:
                wikipedia_page = None
                print(f"  Wikipedia: lookup failed ({exc})", flush=True)
            if wikipedia_page is None:
                print("  Wikipedia: not found", flush=True)
            else:
                _apply_wikipedia_page(entry, wikipedia_page, encyclopedia)
                _resolve_disambiguation_entry(
                    entry,
                    term,
                    wikipedia_page,
                    encyclopedia,
                    contexts_by_term,
                )
                print(f"  Wikipedia: {entry['wikipedia_url'] or 'no article url'}", flush=True)
                print(f"  Wikidata: {entry['wikidata_id'] or 'not found'}", flush=True)
                if entry["disambiguation_history"]:
                    print(f"  {entry['disambiguation_history']}", flush=True)
                elif entry["content_note"]:
                    print(f"  {entry['content_note']}", flush=True)
        encyclopedia.entries.append(entry)

    html_path = Path(encyclopedia_html)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    encyclopedia.save_wiki_normalized_html(html_path)
    return encyclopedia


def _resolve_disambiguation_entry(
    entry: Dict[str, object],
    term: str,
    wikipedia_page,
    encyclopedia,
    contexts_by_term: Optional[Dict[str, List[str]]],
) -> None:
    """Replace a disambiguation page with the lead that matches the papers."""
    note = str(entry.get("content_note") or "")
    if "disambiguation" not in note:
        return
    from amilib.wikimedia import WikipediaPage
    from encyclopedia.pipeline.wikipedia_disambiguation import resolve_disambiguation

    sentences = []
    if contexts_by_term:
        sentences = list(contexts_by_term.get(phrase_key(term), []))
    html_elem = getattr(wikipedia_page, "html_elem", None)
    decision = resolve_disambiguation(term, html_elem, sentences)
    if decision.status == "resolved" and decision.chosen_title:
        try:
            chosen_page = WikipediaPage.lookup_wikipedia_page_for_term(decision.chosen_title)
        except Exception as exc:
            chosen_page = None
            print(f"  Disambiguation page failed ({exc})", flush=True)
        if chosen_page is not None:
            _apply_wikipedia_page(entry, chosen_page, encyclopedia)
    entry["disambiguation_history"] = decision.history


def build_encyclopedia_from_terms(
    terms: Sequence[str],
    title: str,
    encyclopedia_html: Path,
    add_wikipedia: bool = True,
    contexts_by_term: Optional[Dict[str, List[str]]] = None,
):
    """Create and save an encyclopedia from an ordered term list."""
    return create_encyclopedia_from_terms(
        terms,
        title,
        encyclopedia_html,
        add_wikipedia=add_wikipedia,
        contexts_by_term=contexts_by_term,
    )


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

    pygetpapers_command = ""
    if query.strip():
        pygetpapers_command = build_pygetpapers_command(
            query=query,
            output_dir=Path(work_dir, "pygetpapers") if pygetpapers_dir is None else Path(pygetpapers_dir),
            limit=limit,
            download_xml=True,
            download_pdf=download_pdf,
        )
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
        pygetpapers_command = str(download_result.get("pygetpapers_command") or pygetpapers_command)
    else:
        pygetpapers_dir = Path(pygetpapers_dir)
        if not pygetpapers_dir.is_dir():
            raise FileNotFoundError(f"pygetpapers directory not found: {pygetpapers_dir}")

    paper_count = len(discover_paper_folders(pygetpapers_dir))
    corpus_path: Optional[Path] = None
    review_json: Optional[Path] = Path(review_table) if review_table else None
    if stop_after == STOP_AFTER_DOWNLOAD:
        return _finish(
            work_dir, pygetpapers_dir, None, None, None, None, paper_count, 0, stop_after,
            query, pygetpapers_command,
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
            paper_count, 0, stop_after, query, pygetpapers_command,
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
        text_dir=Path(work_dir, "texts"),
    )
    if stop_after == STOP_AFTER_WORDLIST:
        return _finish(
            work_dir, pygetpapers_dir, corpus_path, review_json, wordlist_csv, None,
            len(folders), len(terms), stop_after, query, pygetpapers_command,
        )

    html_path = Path(encyclopedia_html) if encyclopedia_html else Path(work_dir, "encyclopedia.html")
    encyclopedia_title = title or query or pygetpapers_dir.name
    context_path = wordlist_csv.with_name(f"{wordlist_csv.stem}_contexts.jsonl")
    contexts = None
    if context_path.is_file():
        from encyclopedia.pipeline.wikipedia_disambiguation import load_context_sentences

        contexts = load_context_sentences(context_path)
    build_encyclopedia_from_terms(
        terms,
        encyclopedia_title,
        html_path,
        add_wikipedia=add_wikipedia,
        contexts_by_term=contexts,
    )
    return _finish(
        work_dir, pygetpapers_dir, corpus_path, review_json, wordlist_csv, html_path,
        len(folders), len(terms), stop_after, query, pygetpapers_command,
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
    query: str = "",
    pygetpapers_command: str = "",
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
        query=query,
        pygetpapers_command=pygetpapers_command,
    )
    summary = {
        "query": query,
        "pygetpapers_command": pygetpapers_command,
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
