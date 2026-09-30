"""Tests for the query-to-encyclopedia pipeline helpers."""

import json
from pathlib import Path

import pytest

from encyclopedia.pipeline.query_to_encyclopedia import (
    build_pygetpapers_command,
    discover_paper_folders,
    prepare_plain_texts,
    select_paper_folders,
    write_filtered_wordlist,
    xml_file_to_plain_text,
)


def _write_paper(folder: Path, body: str) -> None:
    folder.mkdir(parents=True)
    Path(folder, "eupmc_result.json").write_text(
        json.dumps({"title": folder.name, "pmcid": folder.name, "abstractText": body}),
        encoding="utf-8",
    )
    Path(folder, "fulltext.xml").write_text(
        f"<article><body><p>{body}</p><script>ignore me</script></body></article>",
        encoding="utf-8",
    )


def test_build_pygetpapers_command_quotes_query_and_sets_europe_pmc():
    command = build_pygetpapers_command(
        query='("marine heatwave") AND current',
        output_dir=Path("temp", "queries", "heat"),
        limit=10,
        download_xml=True,
        download_pdf=False,
    )
    assert command.startswith("pygetpapers "), "Command must invoke pygetpapers"
    assert "-k 10" in command, "Limit must be passed as -k"
    assert "--api europe_pmc" in command, "Query must target Europe PMC"
    assert " -x" in command, "XML download must be requested"
    assert " -p" not in command, "PDF download is off unless requested"


def test_select_paper_folders_keeps_included_pmcids(tmp_path: Path):
    download_dir = Path(tmp_path, "pygetpapers")
    _write_paper(Path(download_dir, "PMC111"), "marine heatwave text")
    _write_paper(Path(download_dir, "PMC222"), "unrelated glacier text")
    review_path = Path(tmp_path, "review_table.json")
    review_path.write_text(
        json.dumps(
            [
                {"paper_id": "europe_pmc_PMC111", "pmcid": "PMC111", "review_status": "include"},
                {"paper_id": "europe_pmc_PMC222", "pmcid": "PMC222", "review_status": "exclude"},
            ]
        ),
        encoding="utf-8",
    )

    selected = select_paper_folders(download_dir, review_table_path=review_path)
    names = [folder.name for folder in selected]
    assert names == ["PMC111"], "Only the included PMC folder should be selected"
    assert len(discover_paper_folders(download_dir)) == 2, "Both downloaded folders should be discovered"


def test_select_paper_folders_requires_an_include_when_filtering(tmp_path: Path):
    download_dir = Path(tmp_path, "pygetpapers")
    _write_paper(Path(download_dir, "PMC111"), "marine heatwave text")
    review_path = Path(tmp_path, "review_table.json")
    review_path.write_text(
        json.dumps([{"paper_id": "europe_pmc_PMC111", "pmcid": "PMC111", "review_status": "review"}]),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="include"):
        select_paper_folders(download_dir, review_table_path=review_path)


def test_prepare_plain_texts_reads_fulltext_xml(tmp_path: Path):
    download_dir = Path(tmp_path, "pygetpapers")
    _write_paper(Path(download_dir, "PMC111"), "Ocean current and marine heatwave.")
    texts = prepare_plain_texts(discover_paper_folders(download_dir), Path(tmp_path, "texts"))
    assert len(texts) == 1, "One plain-text file should be written"
    plain = texts[0].read_text(encoding="utf-8")
    assert "marine heatwave" in plain, "Paragraph text should be kept"
    assert "ignore me" not in plain, "Script text should be dropped"
    assert "marine heatwave" in xml_file_to_plain_text(Path(download_dir, "PMC111", "fulltext.xml"))


def test_write_filtered_wordlist_applies_count_and_max_terms(tmp_path: Path):
    keyword_csv = Path(tmp_path, "PMC111_keywords.csv")
    keyword_csv.write_text(
        "keyword,count\n"
        "marine heatwave,4\n"
        "ocean current,2\n"
        "rare token,1\n",
        encoding="utf-8",
    )
    wordlist = Path(tmp_path, "wordlist.csv")
    terms = write_filtered_wordlist(
        [keyword_csv],
        wordlist,
        min_count=2,
        min_term_words=1,
        max_term_words=4,
        max_terms=1,
    )
    assert terms == ["marine heatwave"], "Highest-count term should be kept within max_terms"
    saved = wordlist.read_text(encoding="utf-8")
    assert "marine heatwave,4" in saved, "Wordlist CSV should record the kept term"
    assert "rare token" not in saved, "Terms below min_count should be omitted"
