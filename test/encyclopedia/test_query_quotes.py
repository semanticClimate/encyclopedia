"""Tests for the Europe PMC quote and bracket checker."""

import subprocess
import sys
from pathlib import Path

from encyclopedia.pipeline.query_quotes import (
    check_query_quotes,
    format_query_quote_report,
    join_query_lines,
    query_to_send,
)
from scripts.query_to_encyclopedia import parse_args


def _codes(query: str) -> set[str]:
    return {issue.code for issue in check_query_quotes(query).issues}


def test_eeflood_query_is_already_a_phrase():
    report = check_query_quotes('flood* AND "eastern England"')
    assert report.ok
    assert report.edited == 'flood* AND "eastern England"'
    assert report.shell_argument == '\'flood* AND "eastern England"\''
    readings = {piece.text: piece.reading for piece in report.pieces}
    assert readings["flood*"] == "wildcard; * matches any ending"
    assert readings['"eastern England"'] == "phrase; the words stay in this order"
    assert "look right" in format_query_quote_report(report)


def test_single_quotes_become_phrase_quotes():
    report = check_query_quotes("'amoc' AND 'european climate' AND 'adaptation'")
    assert report.ok
    assert report.normalized == "'amoc' AND 'european climate' AND 'adaptation'"
    assert report.edited == '"amoc" AND "european climate" AND "adaptation"'
    assert "single_quotes" in _codes(report.original)
    assert query_to_send(report, edit=False) == report.normalized
    assert query_to_send(report, edit=True) == report.edited


def test_shell_wrapper_and_outer_double_quotes_are_removed():
    wrapped = check_query_quotes('\'flood* AND "eastern England"\'')
    assert wrapped.edited == 'flood* AND "eastern England"'
    assert "shell_wrapper" in _codes(wrapped.original)

    doubled = check_query_quotes("\"'amoc' AND 'european climate' AND 'adaptation'\"")
    assert doubled.edited == '"amoc" AND "european climate" AND "adaptation"'


def test_license_example_uses_double_quotes_inside_parentheses():
    guide = "\"(LICENSE:'cc by' OR LICENSE:'cc-by') AND METHODS:'transcriptome assembly'\""
    report = check_query_quotes(guide)
    assert report.edited == (
        '(LICENSE:"cc by" OR LICENSE:"cc-by") AND METHODS:"transcriptome assembly"'
    )
    correct = '(LICENSE:"cc by" OR LICENSE:"cc-by") AND METHODS:"transcriptome assembly"'
    assert check_query_quotes(correct).edited == correct


def test_square_brackets_group_with_parentheses_and_dates_use_brackets():
    grouped = check_query_quotes('[flood OR floods] AND "eastern England"')
    assert grouped.edited == '(flood OR floods) AND "eastern England"'

    ranged = check_query_quotes("flood* AND FIRST_PDATE:(2020-01-01 TO 2024-12-31)")
    assert ranged.edited == "flood* AND FIRST_PDATE:[2020-01-01 TO 2024-12-31]"

    kept = check_query_quotes('flood* AND FIRST_PDATE:[2020-01-01 TO 2024-12-31]')
    assert kept.edited == kept.original
    assert "range_parentheses" not in _codes(kept.original)

    nested = check_query_quotes("(flood OR rain) AND (FIRST_PDATE:(2020 TO 2024))")
    assert nested.edited == "(flood OR rain) AND (FIRST_PDATE:[2020 TO 2024])"


def test_curly_quotes_apostrophes_and_operator_case():
    curly = check_query_quotes("flood* AND \u201ceastern England\u201d")
    assert curly.edited == 'flood* AND "eastern England"'
    assert "curly_quotes" in _codes(curly.original)

    phrase = check_query_quotes('"Europe\'s climate" AND flood')
    assert phrase.edited == '"Europe\'s climate" AND flood'
    assert phrase.ok

    name = check_query_quotes("flood's AND rain")
    assert name.ok
    assert name.edited == "flood's AND rain"

    cased = check_query_quotes('flood* and "eastern England"')
    assert cased.edited == 'flood* AND "eastern England"'


def test_unbalanced_quotes_and_brackets_are_errors():
    opened = check_query_quotes('"eastern England')
    assert not opened.ok
    assert "unclosed_double" in _codes(opened.original)
    assert opened.edited == opened.normalized

    mismatched = check_query_quotes("(flood OR floods]")
    assert "mismatched_closer" in _codes(mismatched.original)

    extra = check_query_quotes("flood)")
    assert "extra_closer" in _codes(extra.original)


def test_wildcard_inside_quotes_is_kept_as_written():
    report = check_query_quotes('"flood*"')
    assert report.edited == '"flood*"'
    assert "wildcard_in_quotes" in _codes(report.original)
    assert report.ok


def test_join_query_lines_drops_blank_lines():
    assert join_query_lines('flood*\nAND "eastern England"\n') == 'flood* AND "eastern England"'


def test_parse_args_accepts_the_quote_checker_flags():
    args = parse_args(["--check-query", "--edit-query", "--query", "flood", "--query-file", "-"])
    assert args.check_query
    assert args.edit_query
    assert args.query_file == Path("-")


def test_check_query_cli_prints_the_suggested_query_and_exits():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/query_to_encyclopedia.py",
            "--check-query",
            "--query",
            "'amoc' AND 'european climate'",
            "--limit",
            "50",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert '"amoc" AND "european climate"' in completed.stdout
    assert "-q " in completed.stdout
    assert "pygetpapers" in completed.stdout
