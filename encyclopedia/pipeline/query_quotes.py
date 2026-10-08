"""
Check and edit the quotes, parentheses, and square brackets in a Europe PMC query.

Europe PMC keeps a phrase in order only inside double quotes. Parentheses group
AND, OR, and NOT. Square brackets mark a range, such as a date. The shell then
wraps the whole query in another pair of quotes when it builds the pygetpapers
-q argument. This module separates those layers and can rewrite the common mix-ups.

A later natural-language parser can turn a plain sentence into a query string
and pass that string here. This module does not read plain English.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


_CURLY_QUOTES = {
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u00ab": '"',
    "\u00bb": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
}
_OPERATORS = {"AND", "OR", "NOT"}
_DATE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
_OPERATOR_WORD = re.compile(r"(?<![A-Za-z])(?:AND|OR|NOT|and|or|not)(?![A-Za-z])")


@dataclass(frozen=True)
class QueryQuoteIssue:
    """One finding from the quote checker."""

    code: str
    message: str
    severity: str


@dataclass(frozen=True)
class QueryPiece:
    """One readable piece of a query."""

    text: str
    role: str
    reading: str


@dataclass(frozen=True)
class QueryQuoteReport:
    """Original query, mechanical cleanup, and the suggested edit."""

    original: str
    normalized: str
    edited: str
    issues: Tuple[QueryQuoteIssue, ...]
    pieces: Tuple[QueryPiece, ...]

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def suggested(self) -> str:
        return self.edited

    @property
    def shell_argument(self) -> str:
        return shlex.quote(self.suggested) if self.suggested else ""


@dataclass
class _Token:
    kind: str
    text: str
    start: int
    end: int
    close: int = -1
    match: int = -1
    proximity: str = ""


def join_query_lines(text: str) -> str:
    """Join a query that was wrapped across lines. Blank lines are dropped."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return " ".join(line.strip() for line in lines if line.strip())


def read_query_text(query: str = "", query_file: Optional[Path] = None) -> str:
    """Return the query from --query or from a file. '-' reads standard input."""
    if query_file is not None and query.strip():
        raise ValueError("Pass the query with --query or --query-file, not both")
    if query_file is None:
        return query
    if str(query_file) == "-":
        import sys

        return join_query_lines(sys.stdin.read())
    return join_query_lines(Path(query_file).read_text(encoding="utf-8"))


def check_query_quotes(query: str) -> QueryQuoteReport:
    """Check a Europe PMC query and build an edited form for newcomers."""
    original = "" if query is None else str(query)
    if not original.strip():
        issue = QueryQuoteIssue("empty_query", "The query is empty.", "error")
        return QueryQuoteReport(original, "", "", (issue,), ())

    normalized, mechanical = _normalize(original.strip())
    tokens, structural = _scan(normalized)
    issues: List[QueryQuoteIssue] = list(mechanical)
    issues.extend(structural)

    if any(issue.severity == "error" for issue in issues):
        return QueryQuoteReport(
            original.strip(),
            normalized,
            normalized,
            tuple(issues),
            tuple(_pieces(tokens)),
        )

    edited, edit_issues, note_issues = _edit(normalized, tokens)
    issues.extend(edit_issues)
    if edited == normalized:
        display_tokens = tokens
    else:
        display_tokens, rescan_issues = _scan(edited)
        issues.extend(issue for issue in rescan_issues if issue.severity == "error")
    issues.extend(_notes(display_tokens))
    issues.extend(note_issues)
    return QueryQuoteReport(
        original.strip(),
        normalized,
        edited,
        tuple(issues),
        tuple(_pieces(display_tokens)),
    )


def query_to_send(report: QueryQuoteReport, *, edit: bool) -> str:
    """Query string to give pygetpapers. edit=True uses the suggested form."""
    if not report.ok:
        raise ValueError("query quotes or brackets are not balanced")
    return report.edited if edit else report.normalized


def format_query_quote_report(report: QueryQuoteReport, *, command: str = "") -> str:
    """Plain-text explanation of a query for a newcomer."""
    lines: List[str] = []
    if report.original != report.suggested:
        lines.append("Input")
        lines.append(f"  {report.original}")
        lines.append("")
    lines.append("Suggested query")
    lines.append(f"  {report.suggested}")
    lines.append("")
    lines.append("In a shell command that query is the -q value:")
    if report.shell_argument:
        lines.append(f"  -q {report.shell_argument}")
    lines.append("")
    lines.append("Reading")
    width = min(48, max((len(piece.text) for piece in report.pieces), default=0))
    for piece in report.pieces:
        lines.append(f"  {piece.text.ljust(width)}  {piece.reading}")
    if report.issues:
        lines.append("")
        lines.append("Notes")
        for issue in report.issues:
            lines.append(f"  - {issue.message}")
    else:
        lines.append("")
        lines.append("Quotes, parentheses, and square brackets look right.")
    if command:
        lines.append("")
        lines.append("Command")
        lines.append(f"  {command}")
    if not report.ok:
        lines.append("")
        lines.append("The query still needs a fix before Europe PMC can use it.")
    return "\n".join(lines)


def _normalize(text: str) -> Tuple[str, List[QueryQuoteIssue]]:
    issues: List[QueryQuoteIssue] = []
    current = text
    if any(mark in current for mark in _CURLY_QUOTES):
        current = "".join(_CURLY_QUOTES.get(char, char) for char in current)
        issues.append(
            QueryQuoteIssue(
                "curly_quotes",
                "Curly quotes were changed to straight quotes.",
                "edit",
            )
        )
    if '\\"' in current or "\\'" in current:
        current = current.replace('\\"', '"').replace("\\'", "'")
        issues.append(
            QueryQuoteIssue(
                "escaped_quotes",
                "Backslashes in front of quotes were removed.",
                "edit",
            )
        )
    peeled_layers = 0
    for _ in range(2):
        peeled = _peel_wrapper(current)
        if peeled is None:
            break
        current = peeled
        peeled_layers += 1
    if peeled_layers:
        issues.append(
            QueryQuoteIssue(
                "shell_wrapper",
                "A pair of quotes wrapped the whole query, so that pair was removed.",
                "edit",
            )
        )
    return current, issues


def _peel_wrapper(text: str) -> Optional[str]:
    if len(text) < 2 or text[0] not in "'\"" or text[-1] != text[0]:
        return None
    close = _find_double_close(text, 0) if text[0] == '"' else _find_single_close(text, 0)
    if close != len(text) - 1:
        return None
    inner = text[1:-1].strip()
    if _contains_query_structure(inner):
        return inner
    return None


def _contains_query_structure(text: str) -> bool:
    """True when text looks like a whole query rather than one phrase."""
    if any(char in text for char in "()[]\""):
        return True
    if _OPERATOR_WORD.search(text):
        return True
    return any(
        text[index] == "'" and _is_single_open(text, index) for index in range(len(text))
    )


def _scan(text: str) -> Tuple[List[_Token], List[QueryQuoteIssue]]:
    tokens: List[_Token] = []
    issues: List[QueryQuoteIssue] = []
    stack: List[int] = []
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char == '"':
            token, i, unclosed = _read_phrase(text, i, '"')
            tokens.append(token)
            if unclosed:
                issues.append(
                    QueryQuoteIssue(
                        "unclosed_double",
                        "A double quote is still open at the end of the query.",
                        "error",
                    )
                )
            elif token.text == "":
                issues.append(
                    QueryQuoteIssue("empty_quotes", "A pair of quotes has nothing inside.", "error")
                )
            continue
        if char == "'" and _is_single_open(text, i):
            token, i, unclosed = _read_phrase(text, i, "'")
            tokens.append(token)
            if unclosed:
                issues.append(
                    QueryQuoteIssue(
                        "unclosed_single",
                        "A single quote is still open at the end of the query.",
                        "error",
                    )
                )
            elif '"' in token.text:
                issues.append(
                    QueryQuoteIssue(
                        "quote_inside_quote",
                        "A single-quoted span contains a double quote.",
                        "error",
                    )
                )
            elif token.text == "":
                issues.append(
                    QueryQuoteIssue("empty_quotes", "A pair of quotes has nothing inside.", "error")
                )
            continue
        if char in "([":
            tokens.append(_Token("open", char, i, i + 1))
            stack.append(len(tokens) - 1)
            i += 1
            continue
        if char in ")]":
            token = _Token("close", char, i, i + 1)
            tokens.append(token)
            if not stack:
                issues.append(
                    QueryQuoteIssue(
                        "extra_closer",
                        f"A closing {char} has no matching opener.",
                        "error",
                    )
                )
            else:
                open_index = stack.pop()
                opener = tokens[open_index]
                expected = ")" if opener.text == "(" else "]"
                opener.match = len(tokens) - 1
                token.match = open_index
                if expected != char:
                    issues.append(
                        QueryQuoteIssue(
                            "mismatched_closer",
                            f"A {opener.text} is closed by {char}.",
                            "error",
                        )
                    )
            i += 1
            continue
        if char == ":":
            tokens.append(_Token("colon", ":", i, i + 1))
            i += 1
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in "\"()[]:":
            if text[j] == "'" and _is_single_open(text, j):
                break
            j += 1
        word = text[i:j]
        kind = "operator" if word.upper() in _OPERATORS else "word"
        tokens.append(_Token(kind, word, i, j))
        i = j
    for open_index in stack:
        opener = tokens[open_index].text
        code = "unclosed_paren" if opener == "(" else "unclosed_bracket"
        name = "parenthesis" if opener == "(" else "square bracket"
        issues.append(
            QueryQuoteIssue(code, f"A {name} is still open at the end of the query.", "error")
        )
    return tokens, issues


def _read_phrase(text: str, start: int, quote: str) -> Tuple[_Token, int, bool]:
    close = _find_double_close(text, start) if quote == '"' else _find_single_close(text, start)
    if close < 0:
        content = text[start + 1 :]
        return _Token("phrase", content, start, len(text), close=-1), len(text), True
    proximity = ""
    end = close + 1
    if end < len(text) and text[end] == "~":
        digits = end + 1
        while digits < len(text) and text[digits].isdigit():
            digits += 1
        if digits > end + 1:
            proximity = text[end + 1 : digits]
            end = digits
    return (
        _Token("phrase", text[start + 1 : close], start, end, close=close, proximity=proximity),
        end,
        False,
    )


def _find_double_close(text: str, start: int) -> int:
    j = start + 1
    while j < len(text):
        if text[j] == '"':
            return j
        j += 1
    return -1


def _find_single_close(text: str, start: int) -> int:
    j = start + 1
    while j < len(text):
        if text[j] == "'" and _is_single_closer(text, j):
            return j
        j += 1
    return -1


def _is_single_open(text: str, index: int) -> bool:
    return index == 0 or not text[index - 1].isalpha()


def _is_single_closer(text: str, index: int) -> bool:
    return index + 1 == len(text) or not text[index + 1].isalpha()


def _edit(
    text: str, tokens: Sequence[_Token]
) -> Tuple[str, List[QueryQuoteIssue], List[QueryQuoteIssue]]:
    issues: List[QueryQuoteIssue] = []
    notes: List[QueryQuoteIssue] = []
    replacements: List[Tuple[int, int, str]] = []
    single_quoted = False
    recased = False
    grouping = False
    ranges = False

    for token in tokens:
        if token.kind == "phrase" and text[token.start] == "'" and token.close >= 0:
            replacements.append((token.start, token.start + 1, '"'))
            replacements.append((token.close, token.close + 1, '"'))
            single_quoted = True
        elif token.kind == "operator" and token.text != token.text.upper():
            replacements.append((token.start, token.end, token.text.upper()))
            recased = True

    for token in tokens:
        if token.kind != "open" or token.match < 0:
            continue
        closer = tokens[token.match]
        inner = [item for item in tokens if token.start < item.start < closer.start]
        if token.text == "[":
            if _groups_boolean(inner):
                replacements.append((token.start, token.end, "("))
                replacements.append((closer.start, closer.end, ")"))
                grouping = True
        elif _is_date_range(inner):
            replacements.append((token.start, token.end, "["))
            replacements.append((closer.start, closer.end, "]"))
            ranges = True

    if single_quoted:
        issues.append(
            QueryQuoteIssue(
                "single_quotes",
                "Single-quoted text now uses double quotes, so the words stay in order.",
                "edit",
            )
        )
    if recased:
        issues.append(
            QueryQuoteIssue(
                "operator_case",
                "AND, OR, and NOT are written in capitals.",
                "edit",
            )
        )
    if grouping:
        issues.append(
            QueryQuoteIssue(
                "grouping_brackets",
                "Boolean groups in square brackets now use parentheses.",
                "edit",
            )
        )
    if ranges:
        issues.append(
            QueryQuoteIssue(
                "range_parentheses",
                "A date range now uses square brackets.",
                "edit",
            )
        )
    if not replacements:
        return text, issues, notes
    edited = text
    for start, end, value in sorted(replacements, reverse=True):
        edited = edited[:start] + value + edited[end:]
    return edited, issues, notes


def _groups_boolean(inner: Sequence[_Token]) -> bool:
    has_operator = any(token.kind == "operator" for token in inner)
    has_to = any(token.kind == "word" and token.text.upper() == "TO" for token in inner)
    return has_operator and not has_to


def _is_date_range(inner: Sequence[_Token]) -> bool:
    if any(token.kind in {"operator", "open", "close", "phrase"} for token in inner):
        return False
    words = [token for token in inner if token.kind == "word"]
    if not any(token.text.upper() == "TO" for token in words):
        return False
    return any(_DATE.match(token.text) for token in words)


def _notes(tokens: Sequence[_Token]) -> List[QueryQuoteIssue]:
    notes: List[QueryQuoteIssue] = []
    for token in tokens:
        if token.kind == "phrase" and ("*" in token.text or "?" in token.text):
            mark = "*" if "*" in token.text else "?"
            notes.append(
                QueryQuoteIssue(
                    "wildcard_in_quotes",
                    f'The {mark} in "{token.text}" stays as written inside quotes.',
                    "note",
                )
            )
            break
    return notes


def _pieces(tokens: Sequence[_Token]) -> List[QueryPiece]:
    pieces: List[QueryPiece] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if (
            token.kind == "word"
            and index + 1 < len(tokens)
            and tokens[index + 1].kind == "colon"
        ):
            field = token.text
            index += 2
            if index < len(tokens) and tokens[index].kind in {"phrase", "word"}:
                value = tokens[index]
                pieces.append(_field_piece(field, value))
                index += 1
            else:
                pieces.append(QueryPiece(f"{field}:", "field", f"field {field}"))
            continue
        pieces.append(_piece(token))
        index += 1
    return pieces


def _field_piece(field: str, value: _Token) -> QueryPiece:
    shown = _display(value)
    if value.kind == "phrase" and " " in value.text:
        reading = f"field {field}; the words stay in this order"
    elif value.kind == "phrase":
        reading = f"field {field}; quoted term"
    else:
        reading = f"field {field}; term"
    return QueryPiece(f"{field}:{shown}", "field", reading)


def _piece(token: _Token) -> QueryPiece:
    if token.kind == "operator":
        readings = {
            "AND": "both sides are required",
            "OR": "either side may match",
            "NOT": "the next term is excluded",
        }
        return QueryPiece(token.text, "operator", readings.get(token.text.upper(), "operator"))
    if token.kind == "phrase":
        shown = _display(token)
        if token.proximity:
            reading = f"phrase; the words stay in this order, within {token.proximity} words"
        elif " " in token.text:
            reading = "phrase; the words stay in this order"
        else:
            reading = "quoted term"
        return QueryPiece(shown, "phrase", reading)
    if token.kind == "open":
        if token.text == "(":
            return QueryPiece("(", "group", "parentheses group the following terms")
        return QueryPiece("[", "range", "square brackets start a range")
    if token.kind == "close":
        if token.text == ")":
            return QueryPiece(")", "group", "end of the group")
        return QueryPiece("]", "range", "end of the range")
    if token.kind == "colon":
        return QueryPiece(":", "field", "field separator")
    return QueryPiece(token.text, "term", _word_reading(token.text))


def _display(token: _Token) -> str:
    quoted = f'"{token.text}"'
    if token.proximity:
        return f"{quoted}~{token.proximity}"
    return quoted


def _word_reading(text: str) -> str:
    if text.upper() == "TO":
        return "between the two ends of a range"
    if _DATE.match(text):
        return "date"
    if "*" in text:
        return "wildcard; * matches any ending"
    if "?" in text:
        return "wildcard; ? matches one character"
    return "term"
