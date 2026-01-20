# Encyclopedia Commands Review

**Date:** Tuesday, January 20, 2026, 10:17:59 GMT (system date)  
**Reviewer:** AI Assistant  
**Purpose:** Comprehensive review of all command-line interfaces in the encyclopedia project

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Command Interface 1: Example Script](#command-interface-1-example-script)
3. [Command Interface 2: CLI Versioned Editor](#command-interface-2-cli-versioned-editor)
4. [Command Interface 3: Browser Launcher](#command-interface-3-browser-launcher)
5. [Command Interface 4: Args Class](#command-interface-4-args-class)
6. [Issues and Recommendations](#issues-and-recommendations)
7. [Consistency Analysis](#consistency-analysis)

---

## Overview

The encyclopedia project has **four main command interfaces**:

1. **Example Script** (`Examples/create_encyclopedia_from_wordlist.py`) - Simple, user-friendly interface
2. **CLI Versioned Editor** (`encyclopedia/cli/versioned_editor.py`) - Advanced, feature-rich CLI
3. **Browser Launcher** (`encyclopedia/browser/run_browser.py`) - Web interface launcher
4. **Args Class** (`encyclopedia/cli/args.py`) - Lower-level argument handling

---

## Command Interface 1: Example Script

### File
`Examples/create_encyclopedia_from_wordlist.py`

### Entry Point
```bash
python -m Examples.create_encyclopedia_from_wordlist [OPTIONS]
```

### Purpose
Simple, beginner-friendly interface for creating encyclopedias from wordlists.

### Arguments

| Argument | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `--wordlist` | string | None | No | Path to text file with one term per line |
| `--title` | string | `"My Encyclopedia"` | No | Title for the encyclopedia |
| `--output` | string | `encyclopedia_output.html` | No | Output HTML file path |
| `--skip-deletion` | flag | `False` | No | Skip interactive deletion step |
| `--add-wikipedia` | flag | `True` | No | Add Wikipedia descriptions (default: True) |
| `--no-wikipedia` | flag | - | No | Skip Wikipedia descriptions |
| `--add-images` | flag | `False` | No | Add images from Wikipedia |
| `--batch-size` | integer | `10` | No | Number of entries to process at a time |
| `--validate` | flag | `True` | No | Validate encyclopedia completeness |
| `--no-validate` | flag | - | No | Skip validation |
| `--verbose` | flag | `False` | No | Show detailed progress |

### Example Usage
```bash
# Basic usage (uses example terms)
python -m Examples.create_encyclopedia_from_wordlist

# With custom wordlist
python -m Examples.create_encyclopedia_from_wordlist \
  --wordlist Examples/my_terms.txt \
  --title "My Encyclopedia" \
  --output my_encyclopedia.html

# Full featured
python -m Examples.create_encyclopedia_from_wordlist \
  --wordlist Examples/my_terms.txt \
  --title "Complete Encyclopedia" \
  --add-images \
  --batch-size 5 \
  --verbose \
  --output temp/encyclopedia_with_images.html
```

### Features
- ✅ Simple, intuitive interface
- ✅ Good defaults (Wikipedia enabled, validation enabled)
- ✅ Interactive deletion step
- ✅ Comprehensive error handling
- ✅ Example terms if no wordlist provided

### Issues
- ⚠️ No way to specify which features to add (always adds Wikipedia, optionally images)
- ⚠️ No way to process existing encyclopedia files
- ⚠️ No way to add features incrementally

---

## Command Interface 2: CLI Versioned Editor

### File
`encyclopedia/cli/versioned_editor.py`

### Entry Point
```bash
python -m encyclopedia.cli.versioned_editor <COMMAND> [OPTIONS]
```

### Purpose
Advanced CLI for versioned encyclopedia editing with incremental processing.

### Commands

#### 1. `create` - Create new encyclopedia
```bash
python -m encyclopedia.cli.versioned_editor create \
  --wordlist <PATH> \
  --output <PATH> \
  --title <TITLE>
```

**Arguments:**
- `--wordlist` (required): Wordlist file path
- `--output` (required): Output HTML file path
- `--title` (optional): Encyclopedia title (default: "Encyclopedia")

#### 2. `process` - Process batch of entries
```bash
python -m encyclopedia.cli.versioned_editor process \
  --input <PATH> \
  --feature <FEATURE> \
  --batch-size <N> \
  [--no-resume]
```

**Arguments:**
- `--input` (required): Input encyclopedia HTML file
- `--feature` (required): Feature name to add (`wikipedia`, `images`, etc.)
- `--batch-size` (optional): Number of entries to process (default: 10)
- `--no-resume` (optional): Process all entries, even if they already have the feature

**Features:**
- `wikipedia` - Add Wikipedia descriptions
- `images` - Add images from Wikipedia

#### 3. `next` - Show next unprocessed entry
```bash
python -m encyclopedia.cli.versioned_editor next \
  --input <PATH>
```

**Arguments:**
- `--input` (required): Input encyclopedia HTML file

#### 4. `stats` - Show encyclopedia statistics
```bash
python -m encyclopedia.cli.versioned_editor stats \
  --input <PATH>
```

**Arguments:**
- `--input` (required): Input encyclopedia HTML file

#### 5. `status` - Show detailed status and progress
```bash
python -m encyclopedia.cli.versioned_editor status \
  --input <PATH>
```

**Arguments:**
- `--input` (required): Input encyclopedia HTML file

#### 6. `streamlit` - Launch Streamlit interface
```bash
python -m encyclopedia.cli.versioned_editor streamlit \
  --input <PATH> \
  [--port <PORT>]
```

**Arguments:**
- `--input` (required): Input encyclopedia HTML file
- `--port` (optional): Port to run Streamlit on (default: 8501)

### Example Usage
```bash
# Create encyclopedia
python -m encyclopedia.cli.versioned_editor create \
  --wordlist test/wordlist_a.txt \
  --output test/encyclopedia_a.html

# Process next batch (add Wikipedia descriptions)
python -m encyclopedia.cli.versioned_editor process \
  --input test/encyclopedia_a.html \
  --feature wikipedia \
  --batch-size 10

# Process next batch (add images)
python -m encyclopedia.cli.versioned_editor process \
  --input test/encyclopedia_a.html \
  --feature images \
  --batch-size 5

# Show statistics
python -m encyclopedia.cli.versioned_editor stats \
  --input test/encyclopedia_a.html

# Launch Streamlit
python -m encyclopedia.cli.versioned_editor streamlit \
  --input test/encyclopedia_a.html
```

### Features
- ✅ Incremental processing (process in batches)
- ✅ Resume capability (skip entries that already have features)
- ✅ Multiple commands for different operations
- ✅ Status and statistics tracking
- ✅ Streamlit integration

### Issues
- ⚠️ `create` command doesn't support `--add-images` or `--batch-size` options
- ⚠️ `process` command doesn't support `--verbose` option
- ⚠️ No way to combine multiple features in one command
- ⚠️ Feature names are strings (could be enum or choices)

---

## Command Interface 3: Browser Launcher

### File
`encyclopedia/browser/run_browser.py`

### Entry Point
```bash
python encyclopedia/browser/run_browser.py [OPTIONS]
```

### Purpose
Launch the Streamlit web browser interface for searching and browsing encyclopedias.

### Arguments

| Argument | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `--port` | integer | `8501` | No | Port to run Streamlit on |
| `--file` | string | None | No | Path to encyclopedia HTML file to load automatically |
| `--check-deps` | flag | `False` | No | Check dependencies before launching |

### Example Usage
```bash
# Basic launch
python encyclopedia/browser/run_browser.py

# Custom port
python encyclopedia/browser/run_browser.py --port 8502

# Auto-load encyclopedia file
python encyclopedia/browser/run_browser.py --file my_encyclopedia.html

# Check dependencies first
python encyclopedia/browser/run_browser.py --check-deps
```

### Features
- ✅ Simple launcher interface
- ✅ Dependency checking
- ✅ Auto-load file option
- ✅ Custom port support

### Issues
- ⚠️ No way to specify which encyclopedia file to load (only via `--file` or UI)
- ⚠️ No way to configure search settings from command line

---

## Command Interface 4: Args Class

### File
`encyclopedia/cli/args.py`

### Entry Point
Not directly called - used by other components.

### Purpose
Lower-level argument handling class for encyclopedia operations.

### Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--inpath` / `-i` | string | None | Input HTML file containing encyclopedia entries |
| `--outpath` / `-o` | string | None | Output file for normalized encyclopedia |
| `--title` / `-t` | string | `"Encyclopedia"` | Title for the encyclopedia |
| `--no-normalize` | flag | `False` | Skip Wikidata ID normalization |
| `--no-synonyms` | flag | `False` | Skip synonym aggregation |
| `--stats` | flag | `False` | Show encyclopedia statistics |
| `--figures` | string | None | Source for figures (`wikipedia` or `wikidata`) |

### Features
- ✅ Lower-level API for programmatic use
- ✅ Integration with `amilib.ami_args.AbstractArgs`
- ✅ Normalization and synonym aggregation options

### Issues
- ⚠️ Not well documented for end users
- ⚠️ Less user-friendly than other interfaces
- ⚠️ No direct command-line entry point

---

## Issues and Recommendations

### Critical Issues

1. **Inconsistent Feature Support**
   - `create_encyclopedia_from_wordlist.py` supports `--add-images` and `--batch-size`
   - `versioned_editor.py create` command does NOT support these options
   - **Recommendation:** Add `--add-images` and `--batch-size` to `create` command

2. **Missing Verbose Option**
   - `versioned_editor.py process` command doesn't support `--verbose`
   - **Recommendation:** Add `--verbose` option to `process` command

3. **Feature Names as Strings**
   - `--feature` accepts any string, not validated
   - **Recommendation:** Use `choices` in argparse to restrict to valid features

### Medium Priority Issues

4. **No Combined Feature Processing**
   - Can't add Wikipedia and images in one command
   - **Recommendation:** Add `--features` option accepting multiple values

5. **Inconsistent Defaults**
   - Example script: Wikipedia enabled by default
   - Versioned editor: No Wikipedia option in `create` command
   - **Recommendation:** Standardize defaults across interfaces

6. **No Validation Option**
   - `versioned_editor.py` doesn't support validation
   - **Recommendation:** Add `--validate` / `--no-validate` options

### Low Priority Issues

7. **Documentation**
   - Some commands lack comprehensive help text
   - **Recommendation:** Add detailed help text and examples

8. **Error Messages**
   - Some error messages could be more user-friendly
   - **Recommendation:** Improve error messages with actionable suggestions

---

## Consistency Analysis

### Argument Naming

| Concept | Example Script | Versioned Editor | Browser | Args Class |
|---------|---------------|------------------|---------|------------|
| Input file | `--wordlist` | `--wordlist` / `--input` | `--file` | `--inpath` / `-i` |
| Output file | `--output` | `--output` | N/A | `--outpath` / `-o` |
| Title | `--title` | `--title` | N/A | `--title` / `-t` |
| Batch size | `--batch-size` | `--batch-size` | N/A | N/A |
| Verbose | `--verbose` | ❌ Missing | N/A | N/A |
| Images | `--add-images` | Via `--feature images` | N/A | `--figures` |

**Recommendation:** Standardize argument names across interfaces.

### Default Values

| Option | Example Script | Versioned Editor | Args Class |
|--------|---------------|------------------|------------|
| Title | `"My Encyclopedia"` | `"Encyclopedia"` | `"Encyclopedia"` |
| Batch size | `10` | `10` | N/A |
| Wikipedia | `True` | N/A | N/A |
| Validation | `True` | N/A | N/A |

**Recommendation:** Use consistent defaults across interfaces.

---

## Summary

### Strengths
- ✅ Multiple interfaces for different use cases
- ✅ Good separation of concerns
- ✅ Example script is user-friendly
- ✅ Versioned editor supports incremental processing

### Weaknesses
- ⚠️ Inconsistent feature support
- ⚠️ Missing options in some interfaces
- ⚠️ Inconsistent argument naming
- ⚠️ Some features only available in one interface

### Recommendations Priority

**High Priority:**
1. Add `--add-images` and `--batch-size` to `versioned_editor.py create`
2. Add `--verbose` to `versioned_editor.py process`
3. Add feature validation (choices) to `--feature` argument

**Medium Priority:**
4. Standardize argument names across interfaces
5. Add `--validate` option to versioned editor
6. Add combined feature processing

**Low Priority:**
7. Improve documentation and help text
8. Enhance error messages

---

*Review completed: Monday, January 19, 2026*
