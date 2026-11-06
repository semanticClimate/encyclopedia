# build_KGencyclopedia.py

## Interactive Knowledge Graph from an Encyclopedia

`build_KGencyclopedia.py` is a Python script for generating an interactive HTML knowledge graph from an encyclopedia HTML file. It supports two graph representations:

1. **Term–term graph** — connects encyclopedia terms through cross-references in their entries.
2. **Paper–term graph (bipartite layer)** — connects research papers to encyclopedia terms found in their text. Optionally, encyclopedia cross-reference links between terms can also be included.

The generated graph is an interactive, browser-based visualization with search, node focus, color legends, and Wikipedia/paper information tooltips.

---

## Features

- Reads encyclopedia entries from HTML elements with `role="ami_entry"`.
- Extracts terms, Wikipedia links, and links to other encyclopedia/Wikipedia entries.
- Builds a term–term or paper–term graph.
- Supports Europe PMC/pygetpapers paper folders containing `fulltext.xml` and `eupmc_result.json`, as well as plain `.txt` paper files.
- Reads optional paper metadata overrides from CSV.
- Counts term mentions in papers and filters paper–term connections using a minimum count.
- Uses a precomputed static layout by default; optional physics animation is available.
- Provides dark and light visualization themes.
- Supports node search, direct-neighbour focus, faint/hide display of unrelated nodes, and graph reset.
- Shows Wikipedia summaries, descriptions, thumbnails (when available), and a link to the Wikipedia page in term tooltips.
- Shows paper metadata and a link to the paper in paper tooltips.
- Displays term connectivity and, in paper–term mode, the number of papers containing a term.

## Graph representations

### 1. Term–term graph (`terms`)

- **Nodes:** encyclopedia terms.
- **Edges:** links between encyclopedia entries, when the linked target is also present in the encyclopedia.
- Isolated nodes are removed.

This representation highlights relationships and connectivity among encyclopedia concepts.

### 2. Paper–term graph (`bipartite`)

- **Paper nodes:** research papers.
- **Term nodes:** encyclopedia terms detected in paper text.
- **Paper–term edges:** a term is connected to a paper when it occurs at least the configured number of times in the paper.
- **Edge weight:** number of term matches in the paper.
- **Optional term–term edges:** encyclopedia cross-references are added as a separate layer (dashed edges).

The paper–term layer is bipartite by construction: paper nodes and term nodes form two sets, and paper–term edges connect nodes across those sets. If term–term edges are enabled, the complete graph is a **mixed-layer graph**, and is no longer strictly bipartite.

In the bipartite layout:
- Papers are arranged around a ring.
- Terms shared by multiple papers are placed inside the ring.
- Terms occurring in one paper are placed outside the ring near that paper.
- Papers sharing terms are positioned near one another.

---

## Requirements

Python 3.10+ is recommended.

Install the required packages:

```bash
pip install beautifulsoup4 networkx pyvis numpy lxml
```

`lxml` is used for XML parsing when available. The script falls back to BeautifulSoup's HTML parser if the XML parser is unavailable.

---

## Input files

### Encyclopedia HTML

The input HTML should contain encyclopedia entries in this structure:

```html
<div role="ami_entry" term="Example term">
    <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Example_term">
        Wikipedia
    </a>
    <a href="https://en.wikipedia.org/wiki/Related_term">Related term</a>
</div>
```

The script reads:
- `term` attribute of each `div[role="ami_entry"]`
- the link with class `wikipedia-link`
- links containing `/wiki/` to identify cross-referenced terms

### Paper inputs (bipartite mode)

Either of the following formats can be used:

**Europe PMC / pygetpapers folders**

Each paper folder should contain:
- `fulltext.xml`
- `eupmc_result.json` (optional metadata source)

The script extracts paper metadata from JSON and/or XML and uses the abstract and main body as text. Reference lists, acknowledgements, and selected back matter are excluded.

**Plain text papers**

Use `.txt` files directly inside the papers directory. The parser attempts to identify PMCID, DOI, title, author, year, abstract, and body from the text file's header and section structure.

### Optional metadata CSV

The CSV should contain these columns:

```csv
file,title,year,authors,doi
PMC1234567,Example paper title,2024,"Author One, Author Two",10.1234/example
```

The `file` field should match a paper folder name or `.txt` filename (with or without its extension). Non-empty `title`, `year`, `doi`, and `authors` values override parsed metadata.

---

## Usage

Run commands from the directory containing the script, or provide full paths.

### Term–term graph

```bash
python build_KGencyclopedia.py --input encyclopedia.html --output semantic_KG.html
```

Explicitly select term mode:

```bash
python build_KGencyclopedia.py -i encyclopedia.html -o semantic_KG.html --mode terms
```

### Paper–term graph

```bash
python build_KGencyclopedia.py \
  --input encyclopedia.html \
  --papers papers/ \
  --output paper_term_KG.html
```

The presence of `--papers` automatically selects bipartite mode unless `--mode` is specified.

### Pure bipartite graph (without term–term edges)

```bash
python build_KGencyclopedia.py \
  --input encyclopedia.html \
  --papers papers/ \
  --output pure_bipartite_KG.html \
  --no-term-links
```

### Paper–term graph with metadata overrides

```bash
python build_KGencyclopedia.py \
  --input encyclopedia.html \
  --papers papers/ \
  --meta paper_metadata.csv \
  --output paper_term_KG.html
```

### Light theme and animation

```bash
python build_KGencyclopedia.py \
  --input encyclopedia.html \
  --papers papers/ \
  --theme light \
  --animate \
  --output paper_term_KG_light.html
```

To prevent the output from opening automatically:

```bash
python build_KGencyclopedia.py \
  --input encyclopedia.html \
  --output semantic_KG.html \
  --no-open
```

---

## Command-line options

| Option | Description | Default |
|---|---|---|
| `--input`, `-i` | Input encyclopedia HTML (required) | — |
| `--output`, `-o` | Output graph HTML | `semantic_KG.html` |
| `--theme`, `-t` | Graph/UI theme: `dark` or `light` | `dark` |
| `--papers`, `-p` | Paper folder; enables paper–term mode | — |
| `--mode` | `terms` or `bipartite` | Auto-selected |
| `--meta` | CSV metadata overrides | — |
| `--min-count` | Minimum term mentions for a paper–term edge | `1` |
| `--no-term-links` | Disable term–term links in bipartite mode | Off |
| `--animate` | Keep physics simulation running | Off |
| `--no-open` | Do not open graph after generation | Off |

The script uses `parse_known_args()`, so unknown command-line arguments are ignored (useful in notebook environments).

---

## Interacting with the graph

- **Hover over a term:** displays a Wikipedia summary, description, thumbnail (if available), and an arrow link to Wikipedia.
- **Hover over a paper:** displays paper title, author/year/journal/DOI metadata, and a link to the paper when available.
- **Click a node:** highlights that node and its direct neighbours and connected edges.
- **Others → Faint:** dims unrelated nodes and edges while retaining the full graph.
- **Others → Hide:** hides unrelated nodes and edges.
- **Click empty graph space:** resets the graph.
- **Search:** enter a node label and select **Go** (or press Enter) to focus it.
- **Reset:** restores all nodes and edges and fits the graph to the view.
- **Wikipedia arrow (↗):** opens the term's Wikipedia page in a new tab.

---

## How to interpret the graph

- **Highly connected terms:** connect to many other terms or, in paper–term mode, occur across many papers.
- **Shared terms:** terms connected to multiple papers can indicate concepts appearing across the selected literature.
- **Single-paper terms:** terms connected to one paper may represent paper-specific topics or concepts.
- **Paper–term edge counts:** thicker edges indicate more matches of a term in that paper.
- **Term–term cross-references:** dashed pink edges in bipartite mode represent encyclopedia links, not term occurrences in papers.

Graph connectivity indicates relationships encoded by the encyclopedia or term matches in the selected text corpus. It should not be interpreted automatically as causality, semantic similarity, or scientific importance.

---

## Output

The script writes a self-contained HTML visualization (with JavaScript/CSS and graph data) to the specified output path. Open the HTML file in a modern web browser.

Example:

```text
semantic_KG.html
```

The script also prints graph statistics and the saved output path to the terminal.

---

## Notes and limitations

- Term matching is based on regular expressions and whole-word matching, with plural tolerance for most terms. Short all-uppercase acronyms (up to five characters) are case-sensitive.
- Matching is lexical: a term can be counted even when it is used in a different context or meaning.
- Paper–term edges indicate detected mentions, not validated semantic relations.
- Wikipedia tooltip summaries require an internet connection when the tooltip is first requested. Results are cached in the browser session.
- A Wikipedia summary may be unavailable for a term; the direct Wikipedia link can still be used.
- Terms absent from the paper corpus do not appear as connected term nodes in bipartite mode.
- Isolated graph nodes are removed.
- In bipartite mode, the optional term–term layer means the combined graph is not a strict bipartite graph.

## Citation / acknowledgement

If you use or adapt this script in research, please cite or acknowledge the relevant project/script and describe the encyclopedia source, paper corpus, and term-matching procedure used in your analysis.

## License

Apache License Version 2.0 | See [LICENSE](LICENSE) file for details.
