## Semantic Knowledge Graph from Scientific Literature

### Script: [build_semantic_kg.py](https://github.com/semanticClimate/encyclopedia/blob/renu/drawKG/build_semantic_kg.py)

## [Link to Colab notebook](https://colab.research.google.com/drive/1LR162sAcj1sasTjgwerg4gJ_h6kAlmNi?usp=sharing) 

### semanticClimate Knowledge Graph Builder

A Python tool for converting an encyclopedia-style HTML file and supporting literature data into an interactive knowledge graph. The graph connects terms, concepts, and source papers while preserving evidence and provenance information.

## Features

- Builds an interactive HTML knowledge graph from an encyclopedia HTML file.
- Adds term co-occurrence relationships based on evidence in extracted text.
- Supports hierarchy, abbreviation, Wikipedia-link, and ontology-concept relationships.
- Can use paper text and extracted keyword/phrase data to associate terms with source papers.
- Exports graph edges, nodes, paper information, and graph data for further analysis.
- Supports graph colouring and filtering options to help explore the resulting network.
- Records evidence types and source-paper provenance for graph relationships.

## Workflow

1. Prepare an encyclopedia HTML file.
2. Optionally provide extracted text and paper directories.
3. Run the script to build the graph.
4. Open the generated HTML file in a browser to explore the network.
5. Use the CSV and JSON outputs for inspection, analysis, or reuse.

## Requirements

- Python 3.10 or newer is recommended.
- `beautifulsoup4`
- `networkx`
- `pyvis`
- `pandas`

## Installation

Create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install the packages:

```bash
pip install beautifulsoup4 networkx pyvis pandas
```

## Input files

### Encyclopedia HTML

Pass the encyclopedia HTML file with `--input`. The HTML is expected to contain encyclopedia entries using the `role="ami_entry"` markup.

### Extracted text directory (optional)

Pass a directory of extracted text files with `--text-dir`. The script can use this text to identify term co-occurrence and evidence.

### Paper directory (optional)

Pass a directory of paper text files with `--papers-dir` to associate graph terms and relationships with source papers.

### Merged phrases and aliases (optional)

- `--merged-csv`: CSV file containing merged terms or phrases.
- `--aliases-csv`: CSV file containing term aliases.
- `--add-merged-phrases`: include merged phrases in graph construction.

Check the script's command-line help and expected CSV columns before preparing these optional files.

## Basic usage

Run the script from the directory containing it:

```bash
python build_semantic_kg_counts_v2_generic.py \
  --input encyclopediaTest.html \
  --output output-result/semantic_KG_counts_v2.html
```

On Windows PowerShell, the command can also be written on one line:

```powershell
python build_semantic_kg_counts_v2_generic.py --input encyclopediaTest.html --output output-result/semantic_KG_counts_v2.html
```

With extracted text and source papers:

```bash
python build_semantic_kg_counts_v2_generic.py \
  --input encyclopediaTest.html \
  --output output-result/semantic_KG_counts_v2.html \
  --text-dir text_all \
  --papers-dir paper_all
```

> Replace the example filenames and directories with paths available in your project. Ensure that the script filename matches the file in your repository.

## Main command-line options

| Option | Purpose |
|---|---|
| `--input` | Input encyclopedia HTML file. |
| `--output` | Output interactive HTML graph. |
| `--text-dir` | Directory containing extracted text used for evidence and co-occurrence. |
| `--papers-dir` | Directory containing source-paper text files. |
| `--merged-csv` | Optional CSV of merged phrases or terms. |
| `--aliases-csv` | Optional CSV of aliases. |
| `--add-merged-phrases` | Include merged phrases. |
| `--min-phrase-count` | Minimum phrase count threshold. |
| `--edges-csv` | Set the output path for edge data. |
| `--nodes-csv` | Set the output path for node data. |
| `--min-cooc` | Minimum co-occurrence threshold. |
| `--top-k` | Limit the number of co-occurrence neighbours per term. |
| `--max-fanout` | Limit the number of outgoing connections in supported graph-building steps. |
| `--extra-noise` | Configure additional noise terms or filtering. |
| `--no-cooccurrence` | Disable co-occurrence relationships. |
| `--no-hierarchy` | Disable hierarchy relationships. |
| `--no-abbreviations` | Disable abbreviation relationships. |
| `--label-font-size` | Configure graph label font size. |
| `--label-min-px` | Configure minimum label size in pixels. |
| `--wiki-links` | Enable Wikipedia term links. |
| `--no-ontology` | Disable ontology concept nodes and Wikipedia-link processing. |
| `--onto-min-terms` | Set the minimum terms for ontology concepts. |
| `--onto-max-fanout` | Limit ontology-related connections. |
| `--onto-max-concepts` | Limit the number of ontology concepts. |
| `--color-by` | Choose the graph colouring mode. |
| `--max-figures` | Limit the number of figures considered. |
| `--desc-chars` | Limit description length. |
| `--max-groups` | Limit the number of groups. |

For the full list of supported options and their exact defaults, run:

```bash
python build_semantic_kg_counts_v2_generic.py --help
```

## Relationship types

The graph can include the following types of relationships:

- **Co-occurrence:** terms appearing in the same or adjacent sentences.
- **Hierarchy:** hierarchical relationships represented in the input data.
- **Abbreviation:** links between abbreviations and their expanded forms.
- **Wikipedia link:** links between terms and Wikipedia resources.
- **Ontology concept:** connections between terms and ontology concept nodes.

Co-occurrence weighting uses a higher weight for terms found in the same sentence than for terms found in adjacent sentences. The implementation uses 1.0 for same-sentence evidence and 0.5 for adjacent-sentence evidence, with a Dice-style score and top-k filtering.

**Important:** Co-occurrence indicates textual association, not causation or a confirmed scientific relationship.

## Outputs

The script can produce:

- **Interactive HTML graph:** the network for exploration in a web browser.
- **Edges CSV:** relationship records and supporting evidence.
- **Nodes CSV:** graph-node metadata.
- **Papers CSV:** source-paper information.
- **Graph JSON:** a machine-readable graph representation.

Use the output options (such as `--edges-csv` and `--nodes-csv`) to specify CSV paths where supported. Check the script's help for the complete output configuration.

## Evidence and provenance

Graph data may include fields such as:

- `evidence`
- `evidence_type`
- `source_paper_ids`
- evidence counts
- same-sentence and adjacent-sentence counts
- source-paper IDs by evidence type
- `provenance_status`

These fields help users inspect why a relationship was added and which papers support the recorded evidence. Provenance depends on the quality and availability of the input text and metadata.

## Node and edge identifiers

The implementation uses stable-style identifiers with prefixes:

- `N0001`: term node
- `C0001`: ontology concept node
- `E00001`: edge

## Graph exploration

Open the generated HTML file in a modern web browser. Depending on the selected options and available input data, you can explore connections, inspect terms and concepts, and view source/evidence information. The `--color-by` option controls available colouring modes; check `--help` for the supported values.

## Example project layout

```text
project/
├── build_semantic_kg_counts_v2_generic.py
├── encyclopediaTest.html
├── text_all/
│   └── extracted text files
├── paper_all/
│   └── source paper text files
└── output-result/
    ├── semantic_KG_counts_v2.html
    ├── edges.csv
    ├── nodes.csv
    ├── papers.csv
    └── graph.json
```

This is an illustrative layout; the script's actual output filenames depend on its configuration.

## Limitations and considerations

- The graph depends on the quality of the encyclopedia HTML, extracted text, and paper metadata.
- Sentence segmentation and text extraction can introduce errors.
- A co-occurrence edge should not be interpreted as proof of causation.
- Missing paper identifiers or incomplete metadata can limit provenance.
- Large corpora may produce large graph files and may require filtering to remain easy to explore.

## Troubleshooting

### The graph is empty or has very few nodes

- Check that the input file exists and contains entries with the expected `role="ami_entry"` markup.
- Confirm that optional text and paper directories contain readable files.
- Review filters such as `--min-cooc`, `--top-k`, and fan-out limits.

### Source-paper links are missing

- Check the paper text filenames and metadata.
- Confirm that the extracted terms occur in the source text.
- Inspect the exported edge and node CSV files for provenance fields.

### The output directory does not exist

Create it before running the command, or use an existing directory:

```powershell
New-Item -ItemType Directory -Force output-result
```

## Reproducibility

For reproducible results:

1. Keep a copy of the input encyclopedia HTML.
2. Record the text and paper corpus versions.
3. Save the exact command and script version used.
4. Retain the CSV and JSON outputs alongside the HTML graph.

## Contributing

Issues, bug reports, and improvements are welcome. Before submitting changes, please include a small reproducible input example and the command used to generate the result.

## License

Add the license used by this repository here. Do not assume a license until it has been selected for the project.

