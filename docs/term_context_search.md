# Term context search

**Date:** October 5, 2026 (system date of generation)

Encyclopedia terms are searched again in the plain text of the papers. The search ignores case and keeps the sentence around each hit, with the character offsets of the match. This is for checking unexpected hits, such as a term that only appears in an affiliation or a reference.

## Debug example

`Examples/search_term_contexts.py` prints the earliest hits. When a paper has many matches, it shows the first `contexts_to_show` and still reports the total.

```bash
python Examples/search_term_contexts.py
python Examples/search_term_contexts.py --contexts-to-show 2 --max-papers 1 --terms AMOC "climate change"
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--terms` | `AMOC`, `climate change`, `tipping` | Phrases to find. Case is ignored. |
| `--text-dir` | `~/temp/amoc0/texts` | One `.txt` file per paper. |
| `--contexts-to-show` | `2` | Earliest hits to print for each paper. |
| `--max-papers` | `0` | `0` reads every text file. |

A run limited to the first AMOC paper shows why "climate change" is a noisy term there. Three hits exist. The first two are an affiliation and a reference, not a discussion of the topic:

```text
climate change
  PMC10089918.txt  3 hits, showing 2
    1. 'Climate Change' at 714-728
       5 0000 0001 0726 5157 Oeschger Centre for [Climate Change] Research, University of Bern, Bern, Switzerland 3 grid.
    2. 'climate change' at 56163-56177
       Clark PU Pisias NG Stocker TF Weaver AJ The role of the thermohaline circulation in abrupt [climate change] Nature 2002 415 863 869 10.
```

The brackets mark the matched words. The numbers after `at` are character offsets in `~/temp/amoc0/texts/PMC10089918.txt`. The same PMC id is the folder `~/temp/amoc0/pygetpapers/PMC10089918/`. The corpus directory was renamed from `~/temp/amoc`.

The match is the whole phrase. "climate change" does not match "climate changes". "Climate change" and "climate change" do match each other. The spelling in the paper is the quoted form (`Climate Change`); the search term is the heading.

## Saved contexts

Building the wordlist with a text directory writes `wordlist_contexts.jsonl` beside `wordlist.csv`. For the AMOC run that file is `~/temp/amoc0/wordlist_contexts.jsonl`. Each line is one hit:

```json
{
  "keyword": "AMOC",
  "matched": "AMOC",
  "sentence": "Reconstructions of the AMOC suggest that this tipping point may have previously been crossed multiple times since the Last Glacial Maximum (LGM; 20 thousand years ago (ka)) 5 , with consequences recorded globally 6 .",
  "start": 23,
  "end": 27,
  "source": "PMC10089918.txt",
  "source_start": 5022,
  "source_end": 5026,
  "match_count": 72
}
```

`start` and `end` are offsets inside `sentence`. `source_start` and `source_end` are offsets in `source`. `match_count` is the total in that paper. The wordlist file keeps up to five hits per term per paper and prefers a complete sentence. The debug script instead keeps document order, so the first hit in the file is the one you see first.

Case variants are one term. The spelling that occurs most often is kept. A tie keeps an acronym such as AMOC, otherwise the lowercase form. "Climate change" and "climate change" in the AMOC wordlist are searched once, as `climate change`.

The search uses the Python standard library. The sentences come from the plain text already extracted from Europe PMC full text, not from a second model call.

Those sentences are also the context used to choose a page from a Wikipedia disambiguation list. See [Wikipedia disambiguation](wikipedia_disambiguation.md).

Each encyclopedia entry links back to the papers. The default is one sentence from each of three papers, using `source` as `https://europepmc.org/article/PMC/<PMCID>`. The matched span is marked. A control at the top of the page can show fewer examples; Reset restores the maximum, which is also the `--examples` argument (default 3).
