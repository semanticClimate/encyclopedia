# Simple Encyclopedia Example

This directory contains a simple example encyclopedia demonstrating the key features of the encyclopedia system.

## Files

- **`simple_encyclopedia_example.html`** - A complete HTML encyclopedia with 10 entries
- **`encyclopedia_structure_overview.dot`** - Graphviz source for the structure diagram
- **`encyclopedia_structure_overview.svg`** - Interactive SVG diagram of the encyclopedia structure

## Features Demonstrated

### 1. **Synonym Groups** (2 groups)
- **Group 1**: Climate Change ↔ Global Warming (Wikidata ID: Q7942)
- **Group 2**: Carbon Dioxide ↔ CO₂ (Wikidata ID: Q1218)

### 2. **Wikimedia-Enhanced Entries** (9 entries)
- All entries have Wikipedia links
- 9 entries have Wikidata IDs
- Some entries have Wikidata categories

### 3. **Cross-References** (15+ links)
- Internal links between entries using anchor tags
- Links appear in entry descriptions
- Example: "Climate Change" links to "Greenhouse Gas" and "Fossil Fuels"

### 4. **Entry Types**
- **Enhanced entries**: Have Wikidata IDs, Wikipedia links, and rich descriptions
- **Basic entries**: Have Wikipedia links but no Wikidata ID (e.g., IPCC)

## Structure Overview

The SVG diagram (`encyclopedia_structure_overview.svg`) shows:
- **Synonym groups** (green boxes) - Entries that share the same Wikidata ID
- **Individual entries** (yellow boxes) - Standalone entries with Wikidata IDs
- **Basic entries** (red boxes) - Entries without Wikidata IDs
- **Cross-references** (dashed gray lines) - Links between entries in descriptions

## How to View

1. Open `simple_encyclopedia_example.html` in a web browser
2. View `encyclopedia_structure_overview.svg` in a browser or image viewer
   - In SVG viewers that support links, nodes are clickable and will navigate to the HTML file

## Entry Details

| Entry | Wikidata ID | Synonyms | Links To |
|-------|-------------|----------|----------|
| Climate Change | Q7942 | Global Warming | Greenhouse Gas, Fossil Fuels |
| Global Warming | Q7942 | Climate Change | Greenhouse Gas |
| Greenhouse Gas | Q13138 | - | Greenhouse Effect |
| Carbon Dioxide | Q1218 | CO₂ | Greenhouse Gas, Climate Change |
| CO₂ | Q1218 | Carbon Dioxide | Fossil Fuels |
| Fossil Fuels | Q188425 | - | Carbon Dioxide, Greenhouse Gas, Climate Change |
| IPCC | - | - | Climate Change |
| Greenhouse Effect | Q193078 | - | Greenhouse Gas, Global Warming |
| Methane | Q1490 | - | Greenhouse Gas, Carbon Dioxide |
| Renewable Energy | Q188836 | - | Climate Change, Fossil Fuels |

## Statistics

- **Total Entries**: 10
- **Entries with Wikidata IDs**: 9 (90%)
- **Synonym Groups**: 2
- **Entries with Wikipedia Links**: 10 (100%)
- **Internal Cross-References**: 15+

