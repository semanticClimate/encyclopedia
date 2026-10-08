# Wikipedia disambiguation

**Date:** October 5, 2026 (system date of generation)

A term from the papers can open a Wikipedia disambiguation page. The gloss on that page is often only a few words, so the resolver downloads the lead paragraph of a shortlist of linked pages and compares those leads with the sentences already saved from the papers.

Comparison uses scikit-learn TF-IDF, which is already a project dependency. The MediaWiki API returns each lead as plain text (`prop=extracts`, `exintro=1`, `explaintext=1`).

## How a page is chosen

1. If a paper sentence defines the term, as in "sea surface temperature (SST)", and that expansion names one link on the disambiguation page, that page is chosen.
2. Otherwise the gloss and link text are ranked against the paper sentences, and the top five candidates are kept.
3. Each of those leads is scored against the same sentences. The top page is accepted when its score is at least 0.12 and at least 1.5 times the next score.
4. When two scores are that close, both titles are kept and the entry stays a choice. When nothing clears the minimum, the entry stays unresolved and names the top pages.

The encyclopedia entry records one line of this history, for example:

`Disambiguation: acronym in the papers selected Sea surface temperature. Also considered: Supersonic transport.`

The line is the paragraph with class `disambiguation-history`. When a single page is chosen, the entry then uses that page's description, Wikidata link, and image.

Paper sentences come from `wordlist_contexts.jsonl`. See [Term context search](term_context_search.md).

## Educational examples

`Examples/disambiguate_wikipedia_terms.py` runs five offline cases and prints the history line for each. The same cases are the test `test_educational_disambiguation_examples`.

```bash
python Examples/disambiguate_wikipedia_terms.py
```

| Case | Paper sentence | Result |
| --- | --- | --- |
| Acronym defined in the paper | "The sea surface temperature (SST) anomaly was positive across the North Atlantic." | Sea surface temperature |
| Lead paragraph selects the scientific sense | "Mercury concentrations in the sediment core increased during the industrial period." | Mercury (element), not the planet |
| Climate sense of an acronym | "The AMV index describes multidecadal variability of Atlantic sea surface temperature." | Atlantic multidecadal variability, not an anime music video |
| Two leads stay too close to choose | "The survey measured Atlantic temperature and Atlantic salinity." | Both Atlantic indexes are kept |
| No paper context matches a page | "The value was recorded in the supplement." | Unresolved |

## Decision

We keep this resolver. It is the ranker for a term that has already opened a disambiguation page. It is not a general Wikipedia entity linker.

entity-fishing, REL, and ReFinED do the same ranking step: candidate pages scored against surrounding text, using the page description as the meaning of each candidate. They also generate candidates from titles, redirects, and anchor text, apply a popularity prior, and can refuse a mention. Those extra steps are what would catch a normal article that is the wrong sense, such as tipping resolving to the gratuity page, and a redirect that is followed before we can see it. Our lookup never sends those cases to this resolver.

The cost of switching is a Java service and a large Wikidata index (entity-fishing), a multi-gigabyte 2019 Wikipedia index (REL), or a Transformer checkpoint and an entity catalog of several gigabytes (ReFinED). That cost is not justified for disambiguation pages in an encyclopedia of about 100 terms. Revisit entity-fishing or ReFinED only if wrong-sense articles become the problem to solve.

The resolver holds where the papers and the lead share distinctive words, as in the SST, mercury, and AMV examples. It leaves the term unresolved when the saved sentence is an affiliation or a reference. That refusal is the intended result.

## Testing on the AMOC corpus

The corpus is `~/temp/amoc0` (renamed from `~/temp/amoc`). Paper sentences are in `~/temp/amoc0/wordlist_contexts.jsonl`.

`Examples/disambiguate_wikipedia_terms.py` does not read that corpus. It runs the five offline cases above.

The corpus run is the encyclopedia build. After each Wikipedia lookup, a disambiguation page is passed to the resolver with the sentences for that term:

```bash
python Examples/amoc_query_to_encyclopedia.py --max-terms 100
```

That command also repeats the Wikipedia download for every selected term. In the encyclopedia already at `~/temp/amoc0/encyclopedia/amoc_encyclopedia.html`, five entries are disambiguation pages and are the ones this resolver would score: AMV, overshoot, proxies, SST, and tipping point. There is no separate command that scores only those five.
