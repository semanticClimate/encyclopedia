# Encyclopedia Knowledge Graph Builder

`build_KGencyclopedia.py` turns an **encyclopedia of terms** (an HTML file) and, optionally, a **folder of research papers** into an interactive, self-contained knowledge graph that opens in any web browser.

It can build two kinds of graph:

| Mode | What it shows | Needs |
|---|---|---|
| **Term graph** (`terms`) | Encyclopedia terms linked to each other through the cross-references inside the encyclopedia entries | encyclopedia HTML |
| **Paper–term graph** (`bipartite`) | Which papers mention which terms (bipartite layer), plus the term–term cross-references on top | encyclopedia HTML + papers folder |

The graph is **static** (positions are pre-computed, nothing drifts around) and every node can be clicked to isolate its neighbours and hovered for details.

---

## Contents

- [Quick start](#quick-start)
- [Requirements](#requirements)
- [Input formats](#input-formats)
- [Command-line options](#command-line-options)
- [How it works](#how-it-works)
- [Reading the graph](#reading-the-graph)
- [RDF export](#rdf-export)
- [Using the graph](#using-the-graph)
- [Customising](#customising)
- [Tips and limitations](#tips-and-limitations)
- [Troubleshooting](#troubleshooting)

---

## Quick start

```bash
# 1. install the libraries (once)
pip install beautifulsoup4 lxml networkx numpy pyvis

# 2a. term graph only
python build_KGencyclopedia.py --input encyclopedia.html -o term_KG.html

# 2b. paper-term graph (papers folder given -> bipartite mode is chosen automatically)
python build_KGencyclopedia.py --input encyclopedia.html --papers paper_all/ -o paper_term_KG.html
```

On Windows, paths work the same way:

```bat
python build_KGencyclopedia.py --input encyclopedia.html --papers D:\paper_all -o paper_term_KG.html
```

The script prints a short summary and opens the result in your browser. Add `--no-open` to skip opening it (useful on servers or in Colab).

Example console output:

```
Read 50 paper folder(s) (fulltext.xml) and 0 .txt file(s)
Graph: 45 papers + 284 terms = 329 nodes
  863 paper-term edges (bipartite layer) + 68 term-term edges = 931 edges
  Encyclopedia terms found in no paper: 16 of 300
  Most frequent terms in the corpus: temperature (642), El Niño (…), …
Saved: /path/to/paper_term_KG.html
```

---

## Requirements

- **Python 3.8+**
- Libraries:

| Library | Used for |
|---|---|
| `beautifulsoup4` | reading the encyclopedia HTML and each paper's `fulltext.xml` |
| `lxml` | faster XML parsing (optional: the script falls back to Python's built-in parser without it) |
| `networkx` | building the graph, checking it is bipartite, ordering papers, computing layouts |
| `numpy` | layout calculations |
| `pyvis` | generating the interactive web page (wraps *vis-network*) |
| `scipy` | optional, can help with paper ordering; the script falls back to alphabetical order if ordering fails |

At view time the page loads **vis-network 9.1.2** from a CDN and the Wikipedia REST API for tooltips, so the browser needs internet access.

---

## Input formats

### 1. Encyclopedia HTML (`--input`, required)

Each entry is a `<div>` with `role="ami_entry"` and a `term` attribute. The entry may contain:

- an `<a class="wikipedia-link" href="...">` pointing to the term's Wikipedia page (used for the tooltip and the ↗ button);
- ordinary links of the form `/wiki/Some_Page`. When such a link's page name matches **another entry's term** (case-insensitive, underscores treated as spaces), a term–term edge is created.

```html
<div role="ami_entry" term="biodiversity">
  <a class="wikipedia-link" href="https://en.wikipedia.org/wiki/Biodiversity">Wikipedia</a>
  <p>The variety of life ... see <a href="/wiki/Ecosystem">ecosystem</a>.</p>
</div>
```

Superscript tags (`<sup>…</sup>`, e.g. footnote markers) are removed before reading.

### 2. Papers folder (`--papers`, optional)

Two layouts are supported (they can even be mixed):

**a) Europe PMC folders** (as produced by `pygetpapers`)

```
paper_all/
├── eupmc_results.json          (ignored)
├── saved_config.ini            (ignored)
├── PMC12032349/
│   ├── eupmc_result.json       metadata
│   └── fulltext.xml            full text (JATS XML)
├── PMC12130294/
│   ├── eupmc_result.json
│   └── fulltext.xml
└── ...
```

- **Metadata** (title, first author, year, journal, DOI, PMC ID) comes from `eupmc_result.json`. Any missing field is filled from the XML header.
- **Text searched** = abstract + main body. The reference list, acknowledgements, footnotes and citation numbers are removed, so terms that only appear in a bibliography are **not** counted.

**b) Plain `.txt` files** placed directly in the folder (PMC-style header with PMC ID, DOI, title and author, then an `Abstract` heading). The body is read from `Abstract` up to `Acknowledgements` / `Footnotes` / `References`.

### 3. Metadata override CSV (`--meta`, optional)

Use it when a paper's header could not be read. Columns:

```csv
file,title,year,authors,doi
PMC12032349,Climate-driven succession in marine microbiome,2025,"Larkin, A.",10.1038/s41467-025-59382-1
```

- `file` is the folder name (e.g. `PMC12032349`) or the `.txt` file name.
- `authors`: put the first author's surname first (text before the first comma becomes the label, e.g. "Larkin 2025").
- Empty cells are ignored, so you only need to fill what you want to change.

---

## Command-line options

| Option | Default | Description |
|---|---|---|
| `--input`, `-i` | *(required)* | Encyclopedia HTML file |
| `--output`, `-o` | `semantic_KG.html` | Output graph file (folders are created if needed) |
| `--papers`, `-p` | none | Folder of papers. Giving it switches to paper–term mode |
| `--mode` | auto | `terms` or `bipartite`. Auto = `bipartite` if `--papers` is given, otherwise `terms` |
| `--meta` | none | Metadata override CSV (see above) |
| `--min-count` | `1` | Paper–term mode: minimum mentions of a term in a paper before an edge is drawn. Raise it (e.g. `3`) to remove passing mentions |
| `--no-term-links` | off | Paper–term mode: do **not** add term–term edges, giving a pure bipartite graph |
| `--theme`, `-t` | `dark` | `dark` or `light` colour theme |
| `--animate` | off | Keep the physics simulation running (nodes drift). Default is a static layout |
| `--exclude-terms` | none | Text file with one term per line to leave out of the graph (case-insensitive; lines starting with `#` are comments), e.g. publisher names or generic words |
| `--no-default-filter` | off | By default, English function words (*in*, *for*, *the* …), pure numbers and terms shorter than 3 characters (except upper-case acronyms such as `DP`) are left out. This switches that off |
| `--rdf` | none | Also write the graph as RDF (Turtle), e.g. `--rdf graph.ttl` (see [RDF export](#rdf-export)) |
| `--base-uri` | `https://example.org/kg/` | Base IRI for the identifiers minted in the RDF file. Set your own (for example a `w3id.org` or GitHub Pages address) |
| `--no-open` | off | Do not open the result in a browser |

Examples:

```bash
# pure bipartite graph, only terms mentioned at least 3 times in a paper, light theme
python build_KGencyclopedia.py -i encyclopedia.html -p paper_all -o kg.html --min-count 3 --no-term-links --theme light

# fix paper labels with a CSV
python build_KGencyclopedia.py -i encyclopedia.html -p paper_all --meta papers.csv -o kg.html
```

---

## How it works

1. **Read the encyclopedia.** Every entry gives a term, its Wikipedia URL and the list of Wikipedia pages it links to.
2. **Read the papers** (paper–term mode). Metadata is read from the JSON/XML header; the searchable text is the abstract plus main body.
3. **Match terms to papers.** Each term is searched in each paper as a **whole word**, ignoring capitalisation, and tolerating simple plurals (*dragonfly* also matches *dragonflies*). Multi-word terms allow any whitespace between words. Short ALL-CAPS terms such as `ENSO` or `AMOC` are matched **case-sensitively** to avoid matching ordinary words.
4. **Build the graph.**
   - Paper ↔ term edge, weighted by the number of mentions (kept if ≥ `--min-count`).
   - Term ↔ term edge when one encyclopedia entry links to another (unless `--no-term-links`).
   - Terms found in no paper, and papers that match no term, are dropped. The paper–term layer is verified to be bipartite.
5. **Compute a static layout** (see below).
6. **Render** with PyVis and inject the custom interface (search box, legend, tooltips, click behaviour).

### Layout (paper–term mode)

- **Papers** are placed on a large ring, ordered so that papers sharing many terms sit next to each other.
- **Terms shared by two or more papers** sit **inside** the ring, positioned by a force-directed relaxation with the papers held fixed (related terms are pulled together), followed by an overlap-removal pass.
- **Terms found in only one paper** are fanned out **just outside** that paper.

In term-graph mode a standard force-directed layout is computed once and frozen.

---

## Reading the graph

### Paper–term mode

| Element | Meaning |
|---|---|
| Rounded gray **card** | A paper, labelled *Author Year* (card text is slightly larger for papers covering more terms) |
| **Dot** | An encyclopedia term |
| Dot **size** | Frequency: total mentions in the whole corpus (see below for the per-paper view) |
| Dot **colour** | Number of papers mentioning the term: 🟢 more than ~33% of the papers, 🔵 ~17–33%, 🟠 ~7–17%, ⚪ the rest (the legend shows the exact numbers for your data) |
| **Solid** line | Paper mentions the term; thicker = more mentions |
| **Dashed pink** line | Encyclopedia cross-reference between two terms |

### Term-graph mode

Dots are terms; size and colour reflect the number of connections (green > 25, blue > 10, orange > 4, otherwise the fourth colour).

---

## RDF export

Add `--rdf graph.ttl` to also write the graph as **RDF in Turtle**, so it can be loaded into any triple store or queried with SPARQL.

```bash
python build_KGencyclopedia.py -i encyclopedia.html -p paper_all -o kg.html \
    --rdf kg.ttl --base-uri https://w3id.org/yourproject/kg/
```

| Graph element | RDF |
|---|---|
| Article | `kg:Article`, `schema:ScholarlyArticle` with `dcterms:title`, `dcterms:issued` (year), `dcterms:identifier` (DOI, PMC ID), `kg:firstAuthor`, `kg:journal`, `schema:sameAs` (DOI link), `rdfs:seeAlso` (PMC page) |
| Concept | `kg:Concept`, `skos:Concept` with `skos:prefLabel`, `schema:sameAs` (Wikipedia page), `kg:totalMentions`, `kg:articleCount` |
| Article mentions concept | `article kg:mentions concept`, plus a `kg:Mention` node with `kg:inArticle`, `kg:aboutConcept` and `kg:mentionCount` |
| Encyclopedia cross-reference | `concept skos:related concept` (written in both directions) |

The file starts with a small vocabulary (classes, properties, labels, domains and ranges) so it is self-describing. Identifiers are built from `--base-uri`, so choose an address you control before publishing the data. In term-graph mode only concepts and `skos:related` links are written.

Example SPARQL query (the ten concepts with the most mentions):

```sparql
PREFIX kg: <https://w3id.org/yourproject/kg/vocab#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT ?label ?articles ?mentions WHERE {
  ?c a kg:Concept ; skos:prefLabel ?label ;
     kg:articleCount ?articles ; kg:totalMentions ?mentions .
}
ORDER BY DESC(?mentions) LIMIT 10
```

---

## Using the graph

| Action | Result |
|---|---|
| **Hover a term** | Tooltip with the Wikipedia summary, a thumbnail, corpus total mentions, top papers, related terms, and a **↗** button that opens the Wikipedia page |
| **Hover a paper** | Tooltip with title, authors, year, journal, DOI, top terms, and a **↗** button that opens the paper (PMC or DOI) |
| **Click a node** | Only the node and its direct neighbours stay visible; everything else is faded or hidden (choose with the *Others: Faint / Hide* menu) |
| **Click a paper** | As above, **and term sizes change to the number of mentions inside that paper** (the panel tells you which size mode is active) |
| **Click empty space / Reset** | Everything returns to normal, sizes back to whole-corpus frequency |
| **Search box** | Type an exact node label (a term, or a paper label such as `Larkin 2025`) and press **Enter** or **Go** |
| **Zoom** | Small term labels appear as you zoom in. Paper cards are always labelled |
| **Drag** | You can move individual nodes by hand |

---

## Customising

Most appearance settings are plain values near the top of the script.

| What | Where |
|---|---|
| All colours (nodes, edges, panels, paper cards, tooltip) | the `THEMES` dictionary (one block for `dark`, one for `light`) |
| Colour of the four term levels | `C1`…`C4` in `THEMES` |
| Paper card colour and text colour | `PAPER`, `PAPER_FONT` in `THEMES` |
| Colour of term–term edges | `EDGE_TT`, `EDGE_TT_ON` in `THEMES` |
| Term size range | `SIZE_LO`, `SIZE_HI` (default 8 and 70) |
| Colour thresholds in paper–term mode | `TH_HI`, `TH_MID`, `TH_LOW` (fractions of the number of papers) |
| Ring size / spacing | `R` inside `bipartite_layout` |

---

## Tips and limitations

- **An edge means "appears in the text", not "is important" or "causes".** Treat co-occurrence as a starting point for reading, not as evidence of a relationship.
- Only terms found in at least one paper appear as nodes in paper–term mode. A term–term link to a term that no paper mentions is not drawn.
- The RDF export links concepts to **Wikipedia pages**, not to Wikidata or DBpedia identifiers; mapping to those is a possible next step.
- Term–term edges have **no direction**; they come from the encyclopedia's own cross-references, not from the papers.
- Matching is string-based. Synonyms and variants (*El Niño*, *El Niño event*, *ENSO events*; *SST* vs *sea surface temperature*) are **separate** nodes unless your encyclopedia merges them.
- Keyphrase lists made automatically can contain function words, publisher names and file-format words. Function words are removed by default; list other unwanted terms in a file and pass it with `--exclude-terms`.
- Very general words (e.g. *Investigation*, *Methodology*) can appear as hubs. Remove them from the encyclopedia if you want only subject terms.
- Terms nested inside longer terms count for both (*sea surface temperature* also adds a match for *temperature*).
- Large graphs get crowded in the middle. Increase `--min-count`, or use `--no-term-links`.
- Papers with no extractable text, year or first author are listed in the console so you can fix them with `--meta`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Error: input file not found` | Check the `--input` path |
| `Error: no paper folders (with fulltext.xml) or .txt files found` | `--papers` must point to the folder that **contains** the `PMC…` sub-folders (or the `.txt` files) |
| Labels show a PMC ID instead of *Author Year* | The metadata could not be read; supply `--meta papers.csv` |
| A paper is missing from the graph | It matched none of your terms (the console prints *Papers with no matching terms*) or it has no readable text |
| Page opens blank | The browser could not load vis-network from the CDN. Check your internet connection |
| Tooltips say *No Wikipedia summary available* | The Wikipedia page name could not be resolved, or there is no internet access |
| Graph looks broken after moving the HTML elsewhere | PyVis writes a `lib/` folder next to the output file. Move or share the `lib/` folder together with the HTML |
| `UnicodeEncodeError` in a Windows console | The script already switches the console to UTF-8. If it still happens, run `set PYTHONUTF8=1` first |
| Nodes keep moving | Run without `--animate` (the default is static) |

---

## Output

A single HTML file (plus the `lib/` helper folder created by PyVis). It can be opened in any modern browser, so it is easy to share or screenshot for posters and reports.
