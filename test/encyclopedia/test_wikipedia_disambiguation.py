"""Offline disambiguation cases and the history line on an encyclopedia entry."""

from pathlib import Path

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.pipeline.wikipedia_disambiguation import (
    disambiguation_page_html,
    educational_examples,
    resolve_disambiguation,
)


def test_educational_disambiguation_examples():
    for case in educational_examples():
        page = disambiguation_page_html(
            f"{case['term']} may refer to:",
            case["items"],
        )
        decision = resolve_disambiguation(
            case["term"],
            page,
            case["sentences"],
            leads=case["leads"],
        )
        assert decision.status == case["status"], (
            f"{case['name']} should be {case['status']}, got {decision.status}: {decision.history}"
        )
        if case["title"]:
            assert decision.chosen_title == case["title"], (
                f"{case['name']} should select {case['title']}, got {decision.chosen_title}"
            )
        assert decision.history.startswith("Disambiguation:"), (
            f"{case['name']} should record a short history"
        )


def test_disambiguation_history_is_written_on_the_entry(tmp_path: Path):
    encyclopedia = AmiEncyclopedia(title="Disambiguation examples")
    encyclopedia.entries.append({
        "term": "SST",
        "search_term": "SST",
        "page_title": "Sea surface temperature",
        "wikipedia_url": "https://en.wikipedia.org/wiki/Sea_surface_temperature",
        "description_html": "<p class=\"wpage_first_para\">Sea surface temperature is the water temperature close to the ocean's surface.</p>",
        "definition_html": "",
        "disambiguation_history": (
            "Disambiguation: acronym in the papers selected Sea surface temperature. "
            "Also considered: Supersonic transport."
        ),
        "wikidata_id": "",
        "figure_html": None,
        "wikipedia_page_retrieved": True,
        "first_paragraph_retrieved": True,
    })
    output = Path(tmp_path, "encyclopedia.html")
    encyclopedia.save_wiki_normalized_html(output)
    html = output.read_text(encoding="utf-8")
    assert "disambiguation-history" in html, "The entry should carry the history class"
    assert "acronym in the papers selected Sea surface temperature" in html, (
        "The entry should record why the page was chosen"
    )
