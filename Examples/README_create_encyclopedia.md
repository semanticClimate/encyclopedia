# Create Encyclopedia from Wordlist - Example Script

This example demonstrates how to create a small encyclopedia from a wordlist and interactively delete unwanted entries.

## Files

- **`create_encyclopedia_from_wordlist.py`** - Main script that creates an encyclopedia and allows interactive deletion
- **`example_wordlist.txt`** - Example wordlist file with climate-related terms

## Quick Start

### Basic Usage (with example terms)

**Important:** Run the script from the project root directory as a module.

```bash
# From the project root directory
python -m Examples.create_encyclopedia_from_wordlist
```

Alternatively, if you have installed the package in development mode:

```bash
# Install in development mode first
pip install -e .

# Then run from anywhere
python -m Examples.create_encyclopedia_from_wordlist
```

This will:
1. Create an encyclopedia from 10 example climate-related terms
2. Fetch Wikipedia content for each term
3. Display all entries
4. Allow you to interactively delete unwanted entries
5. Save the final encyclopedia to `encyclopedia_output.html`

### Using Your Own Wordlist

Create a text file with one term per line:

```bash
# Create your wordlist
cat > my_terms.txt << EOF
term1
term2
term3
EOF

# Run the script with your wordlist (from project root)
python -m Examples.create_encyclopedia_from_wordlist --wordlist Examples/my_terms.txt --title "My Custom Encyclopedia"
```

### Command-Line Options

```bash
# From project root directory
python -m Examples.create_encyclopedia_from_wordlist [OPTIONS]

Options:
  --wordlist PATH      Path to text file with one term per line
  --title TITLE        Title for the encyclopedia (default: "My Encyclopedia")
  --output PATH        Output HTML file path (default: encyclopedia_output.html)
  --skip-deletion      Skip interactive deletion step
```

## Interactive Deletion

When the script runs, it will display all entries and allow you to:

- **Delete specific entries**: Enter entry numbers separated by commas (e.g., `1,3,5`)
- **Delete all entries**: Enter `all` (with confirmation)
- **Show entries again**: Enter `show`
- **View statistics**: Enter `stats`
- **Finish**: Enter `done`, `skip`, `quit`, or `exit`

### Example Session

```
============================================================
Encyclopedia Entries (10 total)
============================================================

  [1] climate change
      Wikidata ID: Q7942
      Wikipedia: https://en.wikipedia.org/wiki/Climate_change
      Description: Climate change refers to long-term shifts in global temperatures...

  [2] greenhouse gas
      Wikidata ID: Q13138
      Wikipedia: https://en.wikipedia.org/wiki/Greenhouse_gas
      Description: A greenhouse gas (GHG or GhG) is a gas that absorbs and emits...

...

Enter entry numbers to delete (or 'done'/'skip' to finish, 'show' to refresh, 'stats' for statistics): 8,9

  Entries to delete:
    [8] IPCC
    [9] greenhouse effect

  Delete 2 entry/entries? (yes/no): yes
  ✓ Deleted 2 entries:
      - IPCC
      - greenhouse effect

  Re-normalizing entries...
  ✓ Entries re-normalized
```

## How It Works

### Step 1: Create Dictionary
The script creates a basic dictionary structure from your wordlist using `AmiDictionary`.

### Step 2: Enhance with Wikipedia
For each term, the script:
- Looks up the Wikipedia page
- Extracts the first paragraph as description
- Extracts the Wikipedia URL
- Extracts the Wikidata ID (if available)

### Step 3: Create HTML Dictionary
Converts the dictionary to HTML format with semantic markup.

### Step 4: Create Encyclopedia
Parses the HTML dictionary and creates an `AmiEncyclopedia` object with all entries.

### Step 5: Normalize and Merge
- Groups entries by Wikidata ID (identifies synonyms)
- Merges entries with the same Wikidata ID

### Step 6: Interactive Deletion
Allows you to review and delete unwanted entries.

### Step 7: Save
Saves the final encyclopedia as an HTML file.

## Output

The script generates an HTML file containing:
- All entries with Wikipedia links
- Wikidata IDs (where available)
- Descriptions from Wikipedia
- Synonym groups (merged entries)
- Metadata and statistics

Open the HTML file in a web browser to view the encyclopedia.

## Example Wordlist Format

The wordlist file should contain one term per line:

```
climate change
greenhouse gas
carbon dioxide
global warming
renewable energy
```

Empty lines are ignored.

## Notes

- **Network Required**: The script fetches Wikipedia pages, so an internet connection is required
- **Rate Limiting**: Wikipedia may rate-limit requests if processing many terms
- **Processing Time**: Creating an encyclopedia can take time depending on the number of terms and network speed
- **Dependencies**: Requires `amilib` package to be installed and accessible

## Troubleshooting

### Import Errors
If you get import errors:

1. **Make sure you're running from the project root directory as a module:**
   ```bash
   cd /path/to/encyclopedia  # Go to project root
   python -m Examples.create_encyclopedia_from_wordlist
   ```

2. **Or install the package in development mode:**
   ```bash
   pip install -e .
   python Examples/create_encyclopedia_from_wordlist.py
   ```

3. **Verify packages are installed:**
   - `amilib` package should be installed (check with `pip list | grep amilib`)
   - The `encyclopedia` package should be available (it's in the project root)

The script will provide helpful error messages if imports fail.

### Wikipedia Lookup Failures
Some terms may not have Wikipedia pages. The script will continue processing other terms and show warnings for failed lookups.

### No Entries Remaining
If you delete all entries, the script will save an empty encyclopedia. You can always re-run with different terms.

## See Also

- [Encyclopedia Pipeline Documentation](../docs/encyclopedia_pipeline_documentation.md)
- [Encyclopedia Creation Review](../docs/encyclopedia_creation_review.md)
- [Simple Encyclopedia Example](README_example.md)
