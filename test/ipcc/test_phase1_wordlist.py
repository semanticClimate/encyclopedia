from pathlib import Path
import json

from encyclopedia.ipcc.phase1_wordlist import build_phase1_outputs
from scripts.ipcc_phase1_wordlist import _html_to_text
from test.resources import Resources


def test_build_phase1_outputs_creates_csv_and_report(tmp_path):
    keyword_csv = Path(tmp_path, "sample_keywords.csv")
    keyword_csv.write_text(
        "keyword,count\n"
        "climate change,10\n"
        "ipcc,5\n"
        "adaptation strategy,2\n"
        "oneoff token,1\n"
        ",1\n",
        encoding="utf-8",
    )

    result = build_phase1_outputs(
        keyword_csv_paths=[keyword_csv],
        source_files=[keyword_csv],
        main_subject="ipcc",
        output_subdir="phase1_wordlist_test",
        min_count=2,
        min_term_words=1,
        max_term_words=3,
    )

    assert result.raw_wordlist_csv.exists(), "raw_wordlist.csv must be created"
    assert result.extraction_report_json.exists(), "extraction_report.json must be created"
    assert (
        str(result.output_dir).startswith(str(Path(Resources.TEMP_DIR, "ipcc")))
    ), "phase 1 output directory must be under temp/<main_subject>/"

    csv_text = result.raw_wordlist_csv.read_text(encoding="utf-8")
    assert "manual_delete" in csv_text, "Expected manual_delete column in CSV"
    assert ",No" in csv_text, "manual_delete default should be No"
    assert "climate change,10" in csv_text, "Expected term count for climate change"
    assert "ipcc,5" in csv_text, "Expected term count for ipcc"
    assert "oneoff token,1" not in csv_text, "count=1 terms should be truncated"

    report = json.loads(result.extraction_report_json.read_text(encoding="utf-8"))
    assert report["stage"] == "phase_1_wordlist", "Report must identify phase 1 stage"
    assert report["main_subject"] == "ipcc", "Report must contain main_subject"
    assert report["min_count"] == 2, "Report must record min_count threshold"


def test_html_to_text_removes_tags_and_scripts():
    html = (
        "<html><head><style>.x{color:red;}</style></head>"
        "<body><h1>Introduction</h1><script>alert('x')</script><p>IPCC SYR text.</p></body></html>"
    )
    text = _html_to_text(html)
    assert "Introduction" in text, "Heading text should be retained"
    assert "IPCC SYR text." in text, "Paragraph text should be retained"
    assert "alert" not in text, "Script contents should be removed"
