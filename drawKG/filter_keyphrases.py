#!/usr/bin/env python3
"""
filter_keyphrases.py - clean a keyphrase list before building the encyclopedia.

Reads the merged keyphrase CSV made by `txt2phrases merge` (columns: keyword,count) and removes
terms that should not become encyclopedia entries:

  * stop words            "in", "for", "the" ... (and phrases made only of stop words)
  * numbers               "25 °C", "20 kHz", "Origin Pro 2025", "0.05"
  * journal / publisher   "Frontiers", "MDPI", "Journal of ...", "Scientific Reports", ...
  * boilerplate           "License", "Supplementary Materials", "Editorial Manager", ...
  * very short terms      "ë", "Ar" (upper-case acronyms such as "GIS" or "AI" are kept)
  * (optional) long phrases, rare terms, organisation names, anything in your own exclude file

Writes the cleaned CSV (same columns, so the next step can use it unchanged) and a report of
every removed term with the reason, so nothing disappears silently.

Usage
-----
    python filter_keyphrases.py -i merged.csv -o merged_filtered.csv
    python filter_keyphrases.py -i merged.csv -o merged_filtered.csv --exclude my_terms.txt --min-count 2

Exclude / keep files: one term per line (case-insensitive). A line starting with  re:  is a regular
expression, and a line starting with  #  is a comment.
"""
import argparse
import csv
import os
import re
import sys

# --------------------------------------------------------------------------------------
# Built-in lists (extend them with --exclude / --journals, or switch parts off with flags)
# --------------------------------------------------------------------------------------
STOPWORDS = set("""a about above across after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have having he her here
hers him his how i if in into is it its just may me might more most must my no nor not of off on once only or other our out
over own per same shall she should so some such than that the their them then there these they this those through to too
under until up upon via very was we were what when where which while who whom why will with within without would yet you
your""".split())

# Publisher, journal and platform names (matched as whole terms, ignoring case)
PUBLISHERS_JOURNALS = [
    # publishers and platforms
    "Frontiers", "Frontiers Media", "Frontiers Media SA", "MDPI",
    "Multidisciplinary Digital Publishing Institute", "Elsevier", "Elsevier B.V.", "Springer", "Springer Nature",
    "Springer Science+Business Media", "Nature Publishing Group", "Wiley", "John Wiley & Sons", "Wiley Online Library",
    "Taylor & Francis", "Taylor and Francis", "SAGE", "SAGE Publications", "PLOS", "Public Library of Science",
    "BMC", "BioMed Central", "Hindawi", "De Gruyter", "Emerald", "Emerald Publishing", "Oxford University Press",
    "Cambridge University Press", "American Chemical Society", "American Geophysical Union", "Royal Society",
    "Royal Society of Chemistry", "IEEE", "ACM", "Copernicus Publications", "Copernicus", "Europe PMC", "PubMed",
    "PubMed Central", "PMC", "Crossref", "Google Scholar", "Scopus", "Web of Science", "ResearchGate", "ORCID",
    "Zenodo", "Figshare", "Dryad", "bioRxiv", "arXiv", "medRxiv", "Creative Commons",
    # journals (add your own with --journals)
    "Scientific Reports", "Nature Communications", "Nature Climate Change", "Nature Ecology & Evolution",
    "Nature Ecology and Evolution", "Nature Sustainability", "Nature Geoscience", "Science Advances", "PLOS ONE",
    "PLoS ONE", "PLOS Biology", "PNAS", "Proceedings of the National Academy of Sciences", "Environmental Research Letters",
    "Global Change Biology", "Ecology Letters", "Current Biology", "eLife", "Heliyon", "Heritage Science",
    "Climate Risk Management",
]
# One-word names that are also ordinary topics ("Science", "Nature", "Heritage", "Sustainability") are NOT in the list:
# add them with --exclude or --journals if your keyphrase list contains them as journal names.

# Patterns for names that are journal titles however they are worded
JOURNAL_PATTERNS = [
    r"\bjournal\b",
    r"^(the )?(proceedings|annals|transactions|bulletin|archives|annual review|reviews?) (of|in|on)\b",
    r"\b(international|european|american|british|chinese|asian|african) (journal|review|conference)\b",
    r"\bet al\.?$",
]

# Boilerplate that appears in many articles but says nothing about the topic
BOILERPLATE = [
    "license", "licence", "copyright", "all rights reserved", "terms and conditions", "privacy policy",
    "open access", "open access article", "supplementary materials", "supplementary material",
    "supplementary information", "supplemental materials", "supplemental material", "editorial manager",
    "cover letter", "corresponding author", "data availability statement", "data availability",
    "conflicts of interest", "conflict of interest", "competing interests", "funding", "funding acquisition",
    "acknowledgements", "acknowledgments", "author contributions", "ethics statement", "written informed consent",
    "informed consent", "consent form", "institutional ethics committee", "ethics committee", "peer review",
    "manuscript", "preprint", "doi", "issn", "e-mail", "email", "received", "accepted", "published",
    "article", "articles", "figure", "figures", "table", "tables",
]

ORG_WORDS = r"\b(university|institute|council|committee|agency|commission|society|association|foundation|department|ministry|corporation|company)\b"

# number + unit tokens such as "25", "0.05", "2025", "10%", "20kHz" and bare units
NUMBER_TOKEN = re.compile(r"^[±+\-−]?\d+([.,]\d+)?(%|°[CFK]?|[A-Za-zµ]{1,4})?$")
PURE_NUMBER = re.compile(r"^[±+\-−]?\d+([.,]\d+)?$")
UNIT_TOKENS = {"°c", "°f", "°", "%", "khz", "hz", "mhz", "ghz", "mm", "cm", "m", "km", "kg", "g", "mg", "µg", "µm",
               "nm", "ml", "µl", "l", "ppm", "ppb", "mol", "mmol", "h", "min", "s", "ms", "db", "kda", "bp", "kb",
               "mb", "gb", "ha", "k", "c", "µmol", "mbar", "pa", "kpa", "w", "v", "a"}


# --------------------------------------------------------------------------------------
def read_term_file(path):
    """Plain terms (lower-cased) and compiled regular expressions from a text file."""
    terms, regexes = set(), []
    if not path:
        return terms, regexes
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("re:"):
                regexes.append(re.compile(line[3:].strip(), re.IGNORECASE))
            else:
                terms.add(line.lower())
    return terms, regexes


def has_number_token(term):
    """True if any word of the term is a plain number, or a number written with a unit ('25 °C', '20 kHz')."""
    tokens = term.split()
    for i, tok in enumerate(tokens):
        if PURE_NUMBER.match(tok):
            return True
        if NUMBER_TOKEN.match(tok) and re.sub(r"^[±+\-−]?\d+([.,]\d+)?", "", tok).lower() in UNIT_TOKENS:
            return True
        if tok.lower() in UNIT_TOKENS and i > 0 and PURE_NUMBER.match(tokens[i - 1]):
            return True
    return False


def classify(term, count, opts, exclude_terms, exclude_res, keep_terms, keep_res, journal_lower, journal_res):
    """Return the reason a term is removed, or None to keep it."""
    low = term.lower()

    if low in keep_terms or any(r.search(term) for r in keep_res):
        return None
    if low in exclude_terms or any(r.search(term) for r in exclude_res):
        return "exclude list"

    words = re.findall(r"[^\W_]+(?:['’\-][^\W_]+)*", term, flags=re.UNICODE)
    if not words:
        return "no letters or digits"

    # stop words
    if not opts.keep_stopwords:
        if all(w.lower() in STOPWORDS for w in words):
            return "stop word"
        if opts.strip_edge_stopwords and (words[0].lower() in STOPWORDS or words[-1].lower() in STOPWORDS):
            return "starts/ends with stop word"

    # numbers
    if opts.digits == "any" and re.search(r"\d", term):
        return "contains a digit"
    if opts.digits == "numbers" and has_number_token(term):
        return "number"

    # journals, publishers, platforms
    if not opts.keep_journals:
        if low in journal_lower:
            return "journal / publisher"
        if any(r.search(term) for r in journal_res):
            return "journal / publisher"

    # boilerplate
    if not opts.keep_boilerplate and low in BOILERPLATE_SET:
        return "boilerplate"

    # length
    if len(term) < opts.min_length and not (term.isupper() and len(term) >= 2):
        return "too short"
    if opts.max_words and len(words) > opts.max_words:
        return f"more than {opts.max_words} words"

    # frequency
    if count < opts.min_count:
        return f"count below {opts.min_count}"

    # organisations (optional)
    if opts.drop_organisations and re.search(ORG_WORDS, term, re.IGNORECASE):
        return "organisation name"

    return None


BOILERPLATE_SET = set(BOILERPLATE)


def main():
    ap = argparse.ArgumentParser(description="Remove stop words, numbers, journal names and other unwanted terms "
                                             "from a keyphrase CSV (keyword,count).")
    ap.add_argument("-i", "--input", required=True, help="merged keyphrase CSV, e.g. merged.csv")
    ap.add_argument("-o", "--output", default=None, help="cleaned CSV (default: <input>_filtered.csv)")
    ap.add_argument("--report", default=None, help="report of removed terms (default: <output>_removed.csv)")
    ap.add_argument("--exclude", default=None, metavar="FILE", help="extra terms to remove (one per line, 're:' = regex)")
    ap.add_argument("--keep", default=None, metavar="FILE", help="terms to protect from every rule (same format)")
    ap.add_argument("--journals", default=None, metavar="FILE", help="extra journal / publisher names (one per line)")
    ap.add_argument("--min-count", type=int, default=1, help="drop terms with a count below this (default 1 = keep all)")
    ap.add_argument("--min-length", type=int, default=3, help="drop terms shorter than this, except upper-case acronyms (default 3)")
    ap.add_argument("--max-words", type=int, default=0, help="drop terms with more words than this (default 0 = no limit)")
    ap.add_argument("--digits", choices=["numbers", "any", "none"], default="numbers",
                    help="numbers = drop terms with a plain number or number+unit (default); "
                         "any = drop every term containing a digit (also 'P3', 'BG11'); none = keep all")
    ap.add_argument("--strip-edge-stopwords", action="store_true",
                    help="also drop phrases that start or end with a stop word (would remove 'in situ treatment')")
    ap.add_argument("--drop-organisations", action="store_true",
                    help="also drop names containing University, Institute, Council, Agency, Commission ...")
    ap.add_argument("--keep-stopwords", action="store_true", help="do not remove stop words")
    ap.add_argument("--keep-journals", action="store_true", help="do not remove journal / publisher names")
    ap.add_argument("--keep-boilerplate", action="store_true", help="do not remove boilerplate (License, Supplementary ...)")
    opts = ap.parse_args()

    if not os.path.isfile(opts.input):
        sys.exit(f"Error: input file not found: {opts.input}")
    stem, _ = os.path.splitext(opts.input)
    out_path = opts.output or f"{stem}_filtered.csv"
    rep_path = opts.report or f"{os.path.splitext(out_path)[0]}_removed.csv"

    exclude_terms, exclude_res = read_term_file(opts.exclude)
    keep_terms, keep_res = read_term_file(opts.keep)
    extra_j, _ = read_term_file(opts.journals)
    journal_lower = {t.lower() for t in PUBLISHERS_JOURNALS} | extra_j
    journal_res = [re.compile(p, re.IGNORECASE) for p in JOURNAL_PATTERNS]

    # ---- read ----
    with open(opts.input, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r]
    if not rows:
        sys.exit("Error: the input file is empty")
    header = rows[0]
    has_header = not (len(header) > 1 and re.fullmatch(r"\d+(\.\d+)?", header[1].strip() or "x"))
    body = rows[1:] if has_header else rows
    names = [h.strip() for h in header] if has_header else ["keyword", "count"]
    kcol = next((i for i, n in enumerate(names) if n.lower() in ("keyword", "keyphrase", "term", "phrase")), 0)
    ccol = next((i for i, n in enumerate(names) if n.lower() in ("count", "frequency", "freq", "n")), 1 if len(names) > 1 else None)

    kept, removed = [], []
    for r in body:
        if kcol >= len(r):
            continue
        term = re.sub(r"\s+", " ", r[kcol]).strip().strip("\"'")
        try:
            count = int(float(r[ccol])) if ccol is not None and ccol < len(r) and r[ccol].strip() else 1
        except ValueError:
            count = 1
        reason = classify(term, count, opts, exclude_terms, exclude_res, keep_terms, keep_res, journal_lower, journal_res)
        (removed if reason else kept).append((term, count, reason))

    # ---- write ----
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["keyword", "count"])
        for term, count, _ in sorted(kept, key=lambda x: (-x[1], x[0].lower())):
            w.writerow([term, count])
    with open(rep_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["keyword", "count", "reason"])
        for term, count, reason in sorted(removed, key=lambda x: (x[2], -x[1])):
            w.writerow([term, count, reason])

    # ---- summary ----
    print(f"Read {len(body)} terms: kept {len(kept)}, removed {len(removed)}")
    by_reason = {}
    for term, count, reason in removed:
        by_reason.setdefault(reason, []).append(term)
    for reason, terms in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        sample = ", ".join(terms[:6]) + (" ..." if len(terms) > 6 else "")
        print(f"  {reason:28} {len(terms):5}   {sample}")
    print(f"Cleaned list : {os.path.abspath(out_path)}")
    print(f"Removed terms: {os.path.abspath(rep_path)}   (check it, and protect anything wrong with --keep)")


if __name__ == "__main__":
    main()
