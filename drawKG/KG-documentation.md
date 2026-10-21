# build_semantic_kg.py

## [Link to Colab notebook](https://colab.research.google.com/drive/1LR162sAcj1sasTjgwerg4gJ_h6kAlmNi?usp=sharing) 

Builds an interactive knowledge graph from an **encyclopedia HTML** (list of terms with Wikipedia entries) and the **source papers** (plain text).

Terms are linked by:

| Edge type | Meaning | Direction |
|---|---|---|
| `cooc` | terms co-occur in the same / adjacent sentences of the papers (supporting sentence stored) | undirected |
| `hierarchy` | a term contains another term ("MHW threshold" → "MHW") | specific → general |
| `abbrev` | abbreviation found in text ("sea surface temperature (SST)") | abbreviation → long form |
| `wiki` | Wikipedia entry of one term links to another term | undirected |
| `onto` | **Wikipedia ontology**: term → Wikipedia concept it links to | term → concept |

## What is new in this version

1. **Wikipedia ontology.** Pages linked from the Wikipedia entries of several terms (e.g. *Ocean*, *Climate change*) become **ontology-concept nodes** (◆ diamonds). Terms sharing a concept are related through it.
2. **Grouping + colour separation.** Nodes are grouped three ways and can be recoloured in the graph (*Colour nodes by*): **Wikipedia ontology**, **source paper**, **topic cluster**. Click a legend entry to isolate a group.
3. **IDs for nodes and edges.** Terms `N0001…`, ontology concepts `C0001…`, edges `E00001…`.
4. **Hover card.** Hovering a term shows its **description and figures from the encyclopedia**, together with its ID, mentions, papers, links and aliases. Hovering an ontology concept lists the terms that share it.
5. **Edge direction.** Directed relations (`onto`, `hierarchy`, `abbrev`) are drawn with arrowheads (toggle in the filter panel) and stored as `source → target` in the CSV/JSON.

## Install

```
pip install beautifulsoup4 networkx pyvis pandas
```

## Usage

```
python build_semantic_kg.py \
    --input      encyclopediaTest.html \
    --output     semantic_KG_v3.html \
    --text-dir   text_all \
    --papers-dir marine
```

Colab: `!python /content/KG_demo/build_semantic_kg.py -i ... -o ... -t ... -p ...`

### Options

Existing options are unchanged (`--min-cooc`, `--top-k`, `--max-fanout`, `--no-cooccurrence`, `--no-hierarchy`, `--no-abbreviations`, `--extra-noise`, `--merged-csv`, label options, ...). New ones:

| Option | Default | Description |
|---|---|---|
| `--no-ontology` | off | disable ontology concept nodes and term-to-term Wikipedia links |
| `--onto-min-terms N` | 2 | a Wikipedia concept becomes a node only if ≥ N terms link to it |
| `--onto-max-fanout N` | 40 | ignore concepts linked from more than N terms (too generic) |
| `--onto-max-concepts N` | 150 | keep at most N concepts (those shared by most terms) |
| `--color-by` | `ontology` | initial colouring: `ontology`, `paper` or `cluster` |
| `--max-figures N` | 3 | max figures per term in the hover card |
| `--desc-chars N` | 600 | max characters of the description in the hover card |
| `--max-groups N` | 12 | groups per grouping that get their own colour; the rest are grey "Other" |

Note: `--wiki-links` is now implied unless `--no-ontology` is given.

## Outputs

For `--output foo.html`:

| File | Content |
|---|---|
| `foo.html` | interactive graph |
| `foo_nodes.csv` | `node_id, label, kind (term / ontology_concept), mentions, papers, degree, connected, wikipedia, ontology_group, paper_group, topic_cluster, primary_paper, ontology_concepts, paper_ids` (includes unconnected terms) |
| `foo_edges.csv` | `edge_id, source_id, target_id, source, target, types, relation, weight, evidence` |
| `foo_papers.csv` | paper ID, title, authors, year, URL, number of connected terms |
| `foo_graph.json` | the same nodes and edges in one JSON file |

### IDs
- Terms `N0001…` and concepts `C0001…` are assigned alphabetically; edges `E00001…` are ordered by their end-point IDs. They stay the same between runs on the same input.
- `relation` values: `co_occurs_with`, `more_specific_than`, `abbreviation_of`, `wikipedia_linked_to`, `has_ontology_concept` (joined with `+` if an edge has several).
- `source_id → target_id` follows the direction in the table above; for undirected edges the order is just by ID.

## Hover card: where the content comes from

Read from each `<div role="ami_entry">` of the encyclopedia HTML:

- **Description:** the `p.wpage_first_para` paragraph (falls back to the first `<p>` of the entry). Disambiguation entries ("may refer to…") show a note instead of the text. Descriptions are cut at `--desc-chars`.
- **Figures:** the `<img>` tags of the entry, with the `<figcaption>` or `alt` text as caption. Icons (width/height under 40 px) and Wikipedia interface images are skipped. `//upload...` links become `https://`. Relative image paths are resolved next to the encyclopedia file and embedded in the graph (files up to 300 KB), so the graph stays self-contained. Remote figures are loaded by your browser when you hover, so they need an internet connection.
- Plural/case variants merged into one node use the first variant that has a description / figures.
- Terms added from `--merged-csv` have no encyclopedia entry and show "No description in the encyclopedia".
- The card is hidden while dragging, zooming or when the node is hidden by a filter. Link tooltips (ID, relation, sentence) are unchanged.

## How the groups are computed

- **Ontology group:** greedy set cover. The concept covering the most still-unassigned terms becomes a group and takes those terms; repeat. Concept nodes take their own group, or the majority group of their terms.
- **Paper group:** a term belongs to the paper that mentions it most (ties go to the first paper ID). Terms not found in any paper are "Not found in papers".
- **Topic cluster:** Louvain community detection on the term + concept graph.

## Using the graph

- **Click a node:** highlights it and its links; shows ID, group chips, Wikipedia link, papers and sentences, and connections with edge IDs (`→` / `←` show direction).
- **Click a link:** shows its ID, endpoints, relation, weight and evidence sentence.
- **Legend:** click a group to isolate it, click again to release.
- **Filter panel:** search by term or ID (e.g. `N0007`), toggle link types, switch *Colour nodes by*, hide unrelated nodes, show/hide arrows.
- **Esc / click empty space:** reset.

## Notes and limits

- Ontology quality depends on the `/wiki/` links inside each encyclopedia entry (first paragraph). If groups are too broad or too narrow, tune `--onto-min-terms` and `--onto-max-fanout`.
- The ontology is a flat set of related concepts, not an is-a hierarchy. Wikipedia categories (via the API) could be added to get one.
- Figure extraction assumes images are `<img>` tags inside each entry; if your encyclopedia stores figures differently (for example as CSS backgrounds), tell me the structure and I'll adapt `extract_figures()`.
- Tested on a small synthetic dataset (encyclopedia of 11 terms, 3 papers), including the UI logic in a simulated browser. Run it on your full data and check the groups before relying on them.
