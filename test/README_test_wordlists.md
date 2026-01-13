# Test Wordlists

These wordlists are used for testing the versioned encyclopedia system, particularly for testing merging functionality.

## Wordlist A (`wordlist_a.txt`)

20 climate-related terms focusing on:
- Climate change basics
- Greenhouse gases
- Environmental processes
- Ecosystems

**Terms:** climate change, greenhouse gas, carbon dioxide, global warming, renewable energy, fossil fuels, methane, IPCC, greenhouse effect, atmosphere, carbon cycle, ocean acidification, sea level rise, biodiversity, ecosystem, photosynthesis, deforestation, weather, climate, temperature

## Wordlist B (`wordlist_b.txt`)

20 energy and climate policy terms focusing on:
- Renewable energy sources
- Energy efficiency
- Climate policy
- Sustainability

**Terms:** climate change, greenhouse gas, carbon dioxide, solar energy, wind power, hydroelectric, geothermal, nuclear energy, bioenergy, energy efficiency, carbon footprint, emissions, mitigation, adaptation, climate policy, sustainability, renewable resources, clean energy, green technology, environmental impact

## Overlapping Terms

The two wordlists share **3 common terms**:
1. **climate change**
2. **greenhouse gas**
3. **carbon dioxide**

These overlapping terms will be used to test:
- Merging personal encyclopedias
- Handling duplicate entries
- Conflict resolution
- Version history preservation

## Usage

### Create Encyclopedia A
```bash
python -m encyclopedia.cli.versioned_editor create \
    --wordlist test/wordlist_a.txt \
    --output test/encyclopedia_a.html \
    --title "Climate Encyclopedia A"
```

### Create Encyclopedia B
```bash
python -m encyclopedia.cli.versioned_editor create \
    --wordlist test/wordlist_b.txt \
    --output test/encyclopedia_b.html \
    --title "Climate Encyclopedia B"
```

### Test Merging (Future)
```bash
# When merge functionality is implemented
python -m encyclopedia.cli.versioned_editor merge \
    --input test/encyclopedia_a.html test/encyclopedia_b.html \
    --output test/encyclopedia_merged.html
```

## Expected Results

When merging:
- **Total unique terms**: 37 (20 + 20 - 3 duplicates)
- **Duplicate handling**: 3 entries should be merged (climate change, greenhouse gas, carbon dioxide)
- **Conflict resolution**: If entries differ, should use specified strategy
- **History preservation**: Both histories should be preserved
