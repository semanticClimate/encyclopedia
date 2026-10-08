"""Tests for the query-to-encyclopedia pipeline helpers."""

import json
from pathlib import Path

import pytest

from encyclopedia.pipeline.query_to_encyclopedia import (
    apply_false_positive_filter,
    build_pygetpapers_command,
    commons_thumbnail_url,
    discover_paper_folders,
    is_boilerplate_sentence,
    links_from_wikipedia_page,
    load_terms_by_relevance,
    prepare_plain_texts,
    redirect_pointer,
    search_term_in_text,
    select_paper_examples,
    select_paper_folders,
    thumbnail_html,
    wikipedia_thumbnail_html,
    write_filtered_wordlist,
    xml_file_to_plain_text,
    _load_run_pygetpapers,
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


def test_pygetpapers_exposes_a_query_runner():
    command_runner = _load_run_pygetpapers()
    if command_runner is not None:
        assert callable(command_runner), "run_pygetpapers must be callable"
        return
    try:
        from pygetpapers import Pygetpapers
    except ImportError:
        pytest.skip("pygetpapers is not installed in this interpreter")
    assert callable(Pygetpapers().run_command), "Installed pygetpapers must provide run_command"


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
    quoted = build_pygetpapers_command(
        query='flood* AND "eastern England"',
        output_dir=Path.home() / "temp" / "eeflood" / "pygetpapers",
        limit=50,
    )
    assert "-q 'flood* AND \"eastern England\"'" in quoted, (
        "The Europe PMC query must be the -q value, with the phrase in double quotes"
    )


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


def test_xml_file_to_plain_text_skips_europe_pmc_error_json(tmp_path: Path):
    error_xml = Path(tmp_path, "fulltext.xml")
    error_xml.write_text(
        '{"status":500,"error":"Internal Server Error","path":"/fullTextXML"}',
        encoding="utf-8",
    )
    assert xml_file_to_plain_text(error_xml) == "", "Error JSON must not be treated as article text"

    paper_dir = Path(tmp_path, "PMC11438572")
    paper_dir.mkdir()
    Path(paper_dir, "eupmc_result.json").write_text('{"pmcid":"PMC11438572"}', encoding="utf-8")
    Path(paper_dir, "fulltext.xml").write_text(error_xml.read_text(encoding="utf-8"), encoding="utf-8")
    texts = prepare_plain_texts([paper_dir], Path(tmp_path, "texts"))
    assert texts == [], "A paper whose fulltext.xml is an error body should be skipped"


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
    assert terms == ["marine heatwave"], "Highest-frequency term should be kept within max_terms"
    assert load_terms_by_relevance(wordlist, max_terms=1) == ["marine heatwave"], (
        "Loading an existing wordlist should keep the most relevant term"
    )
    saved = wordlist.read_text(encoding="utf-8")
    assert "marine heatwave (4 times in 1 paper)" in saved, "Phrase should state frequency and papers"
    assert "rare token" not in saved, "Terms below min_count should be omitted"


def test_links_from_wikipedia_page_keep_article_wikidata_and_description_links():
    from lxml.html import fromstring
    from amilib.wikimedia import WikipediaPage

    page = WikipediaPage()
    page.html_elem = fromstring(
        "<html><head>"
        '<link rel="canonical" href="https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation"/>'
        "</head><body>"
        '<li id="t-wikibase"><a href="https://www.wikidata.org/wiki/Special:EntityPage/Q165415">'
        "<span>Wikidata item</span></a></li>"
        "<main><p>The Atlantic Meridional Overturning Circulation (AMOC) is a system of currents. "
        'It moves water. See <a href="/wiki/Climate_change">climate change</a>.</p></main>'
        "</body></html>"
    )
    links = links_from_wikipedia_page(page)
    assert links["wikipedia_url"] == (
        "https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation"
    ), "Entry should link to the Wikipedia article"
    assert links["wikidata_id"] == "Q165415", "Entry should link to the Wikidata item"
    assert "https://en.wikipedia.org/wiki/Climate_change" in links["description_html"], (
        "Links inside the description should be absolute"
    )


def test_wordlist_prefers_terms_found_in_more_papers_then_sorts_alphabetically(tmp_path: Path):
    first = Path(tmp_path, "PMC1_keywords.csv")
    second = Path(tmp_path, "PMC2_keywords.csv")
    first.write_text("keyword,count\nAMOC,2\nlocal jargon,50\n", encoding="utf-8")
    second.write_text("keyword,count\nAMOC,3\n", encoding="utf-8")
    wordlist = Path(tmp_path, "wordlist.csv")
    terms = write_filtered_wordlist(
        [first, second],
        wordlist,
        min_count=2,
        min_term_words=1,
        max_term_words=4,
        max_terms=1,
    )
    assert terms == ["AMOC"], "A term in two papers outranks a frequent term in one paper"
    saved = wordlist.read_text(encoding="utf-8")
    assert "AMOC (5 times in 2 papers)" in saved, "Phrase should sum frequency across papers"


def test_wordlist_merges_case_variants_and_keeps_sentence_context(tmp_path: Path):
    first = Path(tmp_path, "PMC1_keywords.csv")
    second = Path(tmp_path, "PMC2_keywords.csv")
    first.write_text(
        "keyword,count\nClimate change,4\nclimate change,6\nAMOC,2\namoc,1\n",
        encoding="utf-8",
    )
    second.write_text("keyword,count\nclimate change,3\n", encoding="utf-8")
    Path(tmp_path, "PMC1_contexts.jsonl").write_text(
        json.dumps({
            "keyword": "Climate change",
            "sentence": "Climate change alters European rainfall.",
            "start": 0,
            "end": 14,
            "source": "PMC1.txt",
        }) + "\n",
        encoding="utf-8",
    )
    wordlist = Path(tmp_path, "wordlist.csv")
    terms = write_filtered_wordlist(
        [first, second],
        wordlist,
        min_count=2,
        min_term_words=1,
        max_term_words=4,
        max_terms=10,
    )
    assert "climate change" in terms, "Case variants should be one lowercase phrase when that spelling is more frequent"
    assert "Climate change" not in terms, "The less frequent spelling should not be a separate term"
    assert "AMOC" in terms, "The acronym spelling should be kept when it is more frequent"
    assert "amoc" not in terms, "The lowercase acronym should be merged into AMOC"
    saved = wordlist.read_text(encoding="utf-8")
    assert "climate change (13 times in 2 papers)" in saved, (
        "Frequency should sum both spellings, and a paper with both spellings counts once"
    )
    contexts = Path(tmp_path, "wordlist_contexts.jsonl").read_text(encoding="utf-8")
    assert "Climate change alters European rainfall." in contexts, (
        "The sentence around the phrase should be kept for linking back to the paper"
    )
    assert '"keyword": "climate change"' in contexts, (
        "Context should use the same spelling as the wordlist"
    )


def test_search_term_in_text_ignores_case_and_keeps_the_sentence():
    text = (
        "Ignore climate. Climate change alters European rainfall. "
        "Later the climate changes again."
    )
    records = search_term_in_text(text, "climate change", "PMC1.txt")
    assert len(records) == 1, "climate changes is a different phrase from climate change"
    record = records[0]
    assert record["matched"] == "Climate change", "The spelling in the paper should be kept"
    assert record["sentence"] == "Climate change alters European rainfall.", (
        "The sentence around the term should be kept"
    )
    assert record["start"] == 0, "The term starts the sentence"
    assert text[record["source_start"]:record["source_end"]] == "Climate change", (
        "source_start and source_end should point at the term in the paper"
    )
    assert record["match_count"] == 1, "Only one whole-phrase match should be counted"


def test_search_term_in_text_shows_the_first_hits_in_the_paper():
    text = (
        "Centre for Climate Change Research. "
        "Much later, climate change alters rainfall."
    )
    records = search_term_in_text(
        text,
        "climate change",
        "PMC1.txt",
        per_document=1,
        in_document_order=True,
    )
    assert records[0]["matched"] == "Climate Change", (
        "The first hit in the paper should be shown, including an unexpected one"
    )
    assert records[0]["match_count"] == 2, "The paper total should still be reported"


def test_non_content_wikipedia_page_is_marked():
    from lxml.html import fromstring
    from amilib.wikimedia import WikipediaPage
    from encyclopedia.pipeline.query_to_encyclopedia import links_from_wikipedia_page

    page = WikipediaPage()
    page.html_elem = fromstring(
        "<html><head><title>AMOC - Wikipedia</title>"
        '<link rel="canonical" href="https://en.wikipedia.org/wiki/AMOC_(disambiguation)"/>'
        "</head><body><main><p>AMOC may refer to several different topics in climate science.</p>"
        "</main></body></html>"
    )
    links = links_from_wikipedia_page(page)
    assert links["page_title"] == "AMOC", "Entry title should be the Wikipedia page title"
    assert links["content_note"] == "No description: disambiguation page", (
        "A disambiguation page should be marked as having no description"
    )


def test_boilerplate_sentences_are_affiliations_and_references():
    affiliation = (
        "5 0000 0001 0726 5157 Oeschger Centre for Climate Change Research, "
        "University of Bern, Bern, Switzerland 3 grid."
    )
    reference = (
        "Clark PU Pisias NG Stocker TF Weaver AJ The role of the thermohaline "
        "circulation in abrupt climate change Nature 2002 415 863 869 10."
    )
    body = (
        "Reconstructions of the AMOC suggest that this tipping point may have "
        "previously been crossed multiple times since the Last Glacial Maximum."
    )
    assert is_boilerplate_sentence(affiliation)
    assert is_boilerplate_sentence(reference)
    assert not is_boilerplate_sentence(body)
    assert not is_boilerplate_sentence("In 2020 the AMOC weakened across the Atlantic.")


def test_false_positive_filter_keeps_body_terms_and_resolves_contexts(tmp_path: Path):
    wordlist = Path(tmp_path, "wordlist.csv")
    wordlist.write_text(
        "term,phrase,frequency,paper_count\n"
        "climate change,climate change (3 times in 1 papers),3,1\n"
        "AMOC,AMOC (10 times in 4 papers),10,4\n"
        "salinity,salinity (6 times in 3 papers),6,3\n",
        encoding="utf-8",
    )
    Path(tmp_path, "wordlist_contexts.jsonl").write_text(
        "\n".join([
            json.dumps({
                "keyword": "climate change",
                "sentence": (
                    "5 0000 0001 0726 5157 Oeschger Centre for Climate Change Research, "
                    "University of Bern 3 grid."
                ),
            }),
            json.dumps({
                "keyword": "AMOC",
                "sentence": "Reconstructions of the AMOC suggest a tipping point.",
            }),
            json.dumps({
                "keyword": "AMOC",
                "sentence": "Clark PU Weaver AJ Atlantic overturning Nature 2002 415 863 10.",
            }),
            json.dumps({
                "keyword": "salinity",
                "sentence": "Atlantic salinity increased in the same record.",
            }),
        ]) + "\n",
        encoding="utf-8",
    )
    filtered = apply_false_positive_filter(wordlist, max_terms=1)
    assert filtered.terms == ["AMOC"], "The most relevant body term should be kept"
    assert [term for term, _reason in filtered.rejected] == ["climate change"]
    assert filtered.contexts_by_term["amoc"] == [
        "Reconstructions of the AMOC suggest a tipping point."
    ]
    assert "Clark PU" not in Path(tmp_path, "wordlist_contexts.jsonl").read_text(encoding="utf-8")
    rejected = Path(tmp_path, "rejected_terms.csv").read_text(encoding="utf-8")
    assert "climate change" in rejected


def test_amoc25_encyclopedia_example_asks_for_25_papers_and_50_entries():
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "Examples" / "amoc25_encyclopedia.py"
    spec = importlib.util.spec_from_file_location("amoc25_encyclopedia_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.QUERY == "AMOC"
    assert module.PAPER_LIMIT == 25
    assert module.MAX_ENTRIES == 50
    assert module.AMOC_ROOT == Path.home() / "temp" / "amoc25"
    command = build_pygetpapers_command(module.QUERY, module.PYGETPAPERS_DIR, module.PAPER_LIMIT)
    assert "-q AMOC" in command
    assert "-k 25" in command


def test_amoc_encyclopedia_example_asks_for_100_papers_and_100_entries():
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "Examples" / "amoc_encyclopedia.py"
    spec = importlib.util.spec_from_file_location("amoc_encyclopedia_example", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.QUERY == "AMOC"
    assert module.PAPER_LIMIT == 100
    assert module.MAX_ENTRIES == 100
    assert module.AMOC_ROOT == Path.home() / "temp" / "amoc"
    command = build_pygetpapers_command(module.QUERY, module.PYGETPAPERS_DIR, module.PAPER_LIMIT)
    assert "-q AMOC" in command
    assert "-k 100" in command


def test_commons_thumbnail_url_uses_an_upload_wikimedia_thumb():
    parsed = (
        "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f2/Antarctica.svg/"
        "250px-Antarctica.svg.png?utm_source=en.wikipedia.org&utm_content=thumbnail"
    )
    thumb = commons_thumbnail_url(parsed)
    assert thumb == (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/"
        "Antarctica.svg/250px-Antarctica.svg.png"
    )
    too_small = thumb.replace("/250px-", "/220px-")
    assert commons_thumbnail_url(too_small).endswith("/250px-Antarctica.svg.png")
    original = "https://upload.wikimedia.org/wikipedia/commons/5/59/Arctic_Ocean_-_en.png"
    assert commons_thumbnail_url(original).endswith("/250px-Arctic_Ocean_-_en.png")
    html = thumbnail_html(original, "https://en.wikipedia.org/wiki/File:Arctic_Ocean_-_en.png", "Arctic")
    assert 'class="encyclopedia-thumbnail"' in html
    assert 'width="220"' in html
    assert "/250px-" in html
    assert "utm_source" not in html


def test_wikipedia_thumbnail_html_prefers_the_infobox_image():
    from lxml.html import fromstring

    class Page:
        html_elem = fromstring(
            "<html><body><table class='infobox'><tr><td>"
            "<a href='/wiki/File:AMOC.svg' class='mw-file-description'>"
            "<img alt='AMOC' src='//upload.wikimedia.org/wikipedia/commons/a/ab/AMOC.svg' width='220'>"
            "</a></td></tr></table></body></html>"
        )

    html = wikipedia_thumbnail_html(Page())
    assert "250px-AMOC.svg.png" in html
    assert 'href="https://en.wikipedia.org/wiki/File:AMOC.svg"' in html


def test_redirect_pointer_uses_the_wikipedia_redirect_banner():
    from lxml.html import fromstring

    class Page:
        html_elem = fromstring(
            "<html><head><title>Atlantic meridional overturning circulation - Wikipedia</title>"
            '<link rel="canonical" href="https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation"/>'
            "</head><body><div class='mw-redirectedfrom'>"
            "(Redirected from <a href='/w/index.php?title=AMOC&amp;redirect=no'>AMOC</a>)</div>"
            "</body></html>"
        )

    url, title = redirect_pointer(Page(), "AMOC")
    assert url == "https://en.wikipedia.org/w/index.php?title=AMOC&redirect=no"
    assert title == "AMOC"


def test_missing_articles_are_one_page_and_pointers_keep_their_source(tmp_path: Path):
    from encyclopedia.core.encyclopedia import AmiEncyclopedia

    encyclopedia = AmiEncyclopedia(title="AMOC")
    encyclopedia.entries = [
        {
            "term": "zebra missing",
            "search_term": "zebra missing",
            "content_note": "No description: no Wikipedia article",
            "description_html": '<p class="no-description">No description: no Wikipedia article</p>',
            "page_title": "zebra missing",
        },
        {
            "term": "AMOC",
            "search_term": "AMOC",
            "wikidata_id": "Q1",
            "wikidata_category": "ocean current",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation",
            "page_title": "Atlantic meridional overturning circulation",
            "description_html": "<p>The AMOC is an ocean current.</p>",
            "pointer_kind": "redirect",
            "pointer_url": "https://en.wikipedia.org/w/index.php?title=AMOC&redirect=no",
            "pointer_title": "AMOC",
            "figure_html": (
                '<a class="encyclopedia-thumbnail" href="https://en.wikipedia.org/wiki/File:AMOC.svg">'
                '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/AMOC.svg/220px-AMOC.svg.png"'
                ' alt="AMOC" width="220"></a>'
            ),
        },
        {
            "term": "alpha missing",
            "search_term": "alpha missing",
            "content_note": "No description: no Wikipedia article",
            "description_html": '<p class="no-description">No description: no Wikipedia article</p>',
            "page_title": "alpha missing",
        },
        {
            "term": "SST",
            "search_term": "SST",
            "wikidata_id": "Q2",
            "wikidata_category": "temperature",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Sea_surface_temperature",
            "page_title": "Sea surface temperature",
            "description_html": "<p>Sea surface temperature is measured.</p>",
            "pointer_kind": "disambiguation",
            "pointer_url": "https://en.wikipedia.org/wiki/SST",
            "pointer_title": "SST",
        },
    ]
    html = encyclopedia.create_wiki_normalized_html()
    assert html.index('term="AMOC"') < html.index('class="encyclopedia-entry missing-articles"')
    assert html.index('term="SST"') < html.index('class="encyclopedia-entry missing-articles"')
    assert html.count("No description: no Wikipedia article") == 1
    assert html.index(">alpha missing<") < html.index(">zebra missing<")
    assert "Redirected from " in html
    assert 'href="https://en.wikipedia.org/w/index.php?title=AMOC&amp;redirect=no"' in html
    assert "disambiguated from " in html
    assert 'href="https://en.wikipedia.org/wiki/SST"' in html
    assert 'class="encyclopedia-thumbnail"' in html
    assert 'width="220"' in html


def test_paper_examples_link_three_papers_and_can_reset(tmp_path: Path):
    from encyclopedia.core.encyclopedia import AmiEncyclopedia

    records = [
        {
            "sentence": "1 Author A grid. The AMOC project.",
            "source": "PMC1.txt",
            "start": 0,
            "end": 1,
            "matched": "1",
        },
        {
            "sentence": "The AMOC slowed.",
            "source": "PMC10089918.txt",
            "start": 4,
            "end": 8,
            "matched": "AMOC",
        },
        {
            "sentence": "Later the AMOC recovered.",
            "source": "PMC10089918.txt",
            "start": 10,
            "end": 14,
            "matched": "AMOC",
        },
        {
            "sentence": "A second paper measured AMOC.",
            "source": "PMC2.txt",
            "start": 24,
            "end": 28,
            "matched": "AMOC",
        },
        {
            "sentence": "A third paper modelled AMOC.",
            "source": "PMC3.txt",
            "start": 23,
            "end": 27,
            "matched": "AMOC",
        },
        {
            "sentence": "A fourth paper also found AMOC.",
            "source": "PMC4.txt",
            "start": 26,
            "end": 30,
            "matched": "AMOC",
        },
    ]
    examples = select_paper_examples(records, max_examples=3)
    assert [item["source"] for item in examples] == [
        "PMC10089918.txt",
        "PMC2.txt",
        "PMC3.txt",
    ]
    assert examples[0]["url"] == "https://europepmc.org/article/PMC/PMC10089918"

    contexts = Path(tmp_path, "wordlist_contexts.jsonl")
    contexts.write_text(
        "\n".join(json.dumps({"keyword": "AMOC", **record}) for record in records) + "\n",
        encoding="utf-8",
    )
    wordlist = Path(tmp_path, "wordlist.csv")
    wordlist.write_text(
        "term,phrase,frequency,paper_count\nAMOC,AMOC (4 times in 4 papers),4,4\n",
        encoding="utf-8",
    )
    filtered = apply_false_positive_filter(wordlist, max_terms=5, max_paper_examples=3)
    assert [item["source"] for item in filtered.paper_examples["amoc"]] == [
        "PMC10089918.txt",
        "PMC2.txt",
        "PMC3.txt",
    ]

    encyclopedia = AmiEncyclopedia(title="AMOC")
    encyclopedia.paper_example_limit = 3
    encyclopedia.entries = [
        {
            "term": "AMOC",
            "search_term": "AMOC",
            "wikidata_id": "Q1",
            "wikidata_category": "ocean current",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation",
            "page_title": "Atlantic meridional overturning circulation",
            "description_html": "<p>The AMOC is an ocean current.</p>",
            "paper_examples": examples,
        },
        {
            "term": "alpha missing",
            "search_term": "alpha missing",
            "content_note": "No description: no Wikipedia article",
            "description_html": '<p class="no-description">No description: no Wikipedia article</p>',
            "page_title": "alpha missing",
            "paper_examples": [examples[0]],
        },
    ]
    html = encyclopedia.create_wiki_normalized_html()
    assert 'href="https://europepmc.org/article/PMC/PMC10089918"' in html
    assert 'class="paper-hit">AMOC<' in html
    assert "PMC4" not in html
    assert 'id="example-limit"' in html
    assert 'max="3"' in html
    assert 'id="example-limit-reset"' in html
    assert ">Reset<" in html
    assert "data-example-limit" in html
    article = html[:html.index('class="encyclopedia-entry missing-articles"')]
    missing = html[html.index('class="missing-article-list"'):]
    assert "PMC10089918" in article
    assert "PMC2" in article
    assert "PMC10089918" in missing


def test_load_terms_by_relevance_sorts_by_count_then_limits(tmp_path: Path):
    wordlist = Path(tmp_path, "wordlist.csv")
    wordlist.write_text(
        "term,count\n"
        "adaptation,5\n"
        "AMOC,40\n"
        "european climate,12\n",
        encoding="utf-8",
    )
    terms = load_terms_by_relevance(wordlist, max_terms=2)
    assert terms == ["AMOC", "european climate"], "Selected terms should be alphabetical"
