"""Unweighted entry–entry links: description links and shared papers."""

from pathlib import Path

from encyclopedia.utils.knowledge_graph.entry_graph import (
    LINKS_TO,
    SHARES_PAPER,
    build_unweighted_entry_graph,
)


def _paper(pmc: str) -> dict:
    return {
        "source": f"{pmc}.txt",
        "url": f"https://europepmc.org/article/PMC/{pmc}",
    }


def _edges(graph, relationship):
    return [
        (source, target, data)
        for source, target, data in graph.edges(data=True)
        if data.get("relationship") == relationship
    ]


def test_description_link_option_omits_shared_papers():
    entries = [
        {
            "term": "AMOC",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation",
            "description_html": '<p>See <a href="/wiki/Sea_surface_temperature">SST</a>.</p>',
            "paper_examples": [_paper("PMC1")],
        },
        {
            "term": "SST",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Sea_surface_temperature",
            "description_html": "<p>Measured.</p>",
            "paper_examples": [_paper("PMC1")],
        },
    ]
    graph = build_unweighted_entry_graph(entries, links=[LINKS_TO])
    assert [data["relationship"] for _s, _t, data in graph.edges(data=True)] == [LINKS_TO]


def test_encyclopedia_script_writes_description_links(tmp_path: Path):
    import subprocess
    import sys

    html = tmp_path / "mini_encyclopedia.html"
    html.write_text(
        """<html><body>
        <div role="ami_encyclopedia" title="Mini">
          <div role="ami_entry" term="AMOC" wikidataID="Q1">
            <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation">AMOC</a>
            <p class="wpage_first_para">See <a href="/wiki/Sea_surface_temperature">SST</a>.</p>
          </div>
          <div role="ami_entry" term="SST" wikidataID="Q2">
            <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Sea_surface_temperature">SST</a>
            <p class="wpage_first_para">Measured at the surface.</p>
          </div>
        </div>
        </body></html>""",
        encoding="utf-8",
    )
    output = tmp_path / "mini.graphml"
    script = Path(__file__).resolve().parents[2] / "scripts" / "encyclopedia_to_kg.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--encyclopedia", str(html), "--link", "description", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert output.is_file()
    graphml = output.read_text(encoding="utf-8")
    assert 'source="AMOC" target="SST"' in graphml
    assert ">links_to<" in graphml
    assert "shares_paper" not in graphml
    assert "description: 1" in completed.stdout


def test_graph_history_records_query_corpus_and_encyclopedia(tmp_path: Path):
    import subprocess
    import sys

    html = tmp_path / "encyclopedia" / "mini_encyclopedia.html"
    html.parent.mkdir()
    html.write_text(
        """<html><body>
        <div role="ami_encyclopedia" title="Mini">
          <div role="ami_entry" term="AMOC" wikidataID="Q1">
            <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation">AMOC</a>
            <p class="wpage_first_para">See <a href="/wiki/Sea_surface_temperature">SST</a>.</p>
          </div>
          <div role="ami_entry" term="SST" wikidataID="Q2">
            <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Sea_surface_temperature">SST</a>
            <p class="wpage_first_para">Measured at the surface.</p>
          </div>
        </div>
        </body></html>""",
        encoding="utf-8",
    )
    summary = tmp_path / "pipeline_summary.json"
    summary.write_text(
        '{"query": "", "corpus_dir": "/data/corpus", "pygetpapers_dir": "/data/pygetpapers",'
        ' "paper_count": 50, "encyclopedia_html": ""}\n',
        encoding="utf-8",
    )
    output = tmp_path / "mini.graphml"
    script = Path(__file__).resolve().parents[2] / "scripts" / "encyclopedia_to_kg.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--encyclopedia",
            str(html),
            "--summary",
            str(summary),
            "--query",
            'flood* AND "eastern England"',
            "--pygetpapers-command",
            "pygetpapers -q 'flood* AND \"eastern England\"' -k 50",
            "--output",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    graphml = output.read_text(encoding="utf-8")
    assert 'attr.name="history_query"' in graphml
    assert "flood* AND" in graphml
    assert "/data/corpus" in graphml
    assert 'attr.name="history_links"' in graphml
    assert ">description<" in graphml
    assert str(html) in graphml or "mini_encyclopedia.html" in graphml


def test_unweighted_links_follow_pages_and_shared_papers():
    entries = [
        {
            "term": "AMOC",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation",
            "wikidata_id": "Q1",
            "description_html": (
                "<p>The AMOC is related to "
                '<a href="/wiki/Sea_surface_temperature">sea surface temperature</a> '
                "and to itself "
                '<a href="https://en.wikipedia.org/wiki/Atlantic_meridional_overturning_circulation">'
                "AMOC</a> and a "
                '<a href="/wiki/File:AMOC.svg">file</a>.</p>'
            ),
            "paper_examples": [_paper("PMC10089918"), _paper("PMC2")],
        },
        {
            "term": "SST",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Sea_surface_temperature?redirect=no",
            "wikidata_id": "Q2",
            "description_html": "<p>Sea surface temperature is measured.</p>",
            "paper_examples": [_paper("PMC10089918"), _paper("PMC3")],
        },
        {
            "term": "AMOC collapse",
            "wikipedia_url": "",
            "description_html": "",
            "paper_examples": [_paper("PMC2")],
        },
        {
            "term": "Brazil",
            "wikipedia_url": "https://en.wikipedia.org/wiki/Brazil",
            "description_html": (
                '<p>See <a href="https://en.wikipedia.org/wiki/Greenhouse_gas">greenhouse gas</a>.</p>'
            ),
            "paper_examples": [_paper("PMC9")],
        },
        {
            "term": "No Wikipedia article",
            "wikipedia_url": "",
            "description_html": "",
            "paper_examples": [_paper("PMC10089918")],
        },
    ]

    graph = build_unweighted_entry_graph(entries)

    assert set(graph.nodes) == {"AMOC", "SST", "AMOC collapse", "Brazil"}
    assert graph.nodes["AMOC"]["wikidata_id"] == "Q1"
    assert graph.nodes["AMOC"]["papers"] == ["PMC10089918", "PMC2"]

    links = _edges(graph, LINKS_TO)
    assert [(source, target) for source, target, _data in links] == [("AMOC", "SST")]
    shares = _edges(graph, SHARES_PAPER)
    assert sorted((source, target, data["shared_papers"]) for source, target, data in shares) == [
        ("AMOC", "AMOC collapse", ["PMC2"]),
        ("AMOC", "SST", ["PMC10089918"]),
    ]
    for _source, _target, data in graph.edges(data=True):
        assert "weight" not in data
