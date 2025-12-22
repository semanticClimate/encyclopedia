# Migration Plan Summary

**Quick Reference for Encyclopedia Code Migration**

## What's Moving

| From (`../amilib`) | To (`encyclopedia`) |
|-------------------|---------------------|
| `ami_encyclopedia.py` | `encyclopedia/core/encyclopedia.py` |
| `ami_encyclopedia_cluster.py` | `encyclopedia/clustering/clusterer.py` |
| `ami_encyclopedia_args.py` | `encyclopedia/cli/args.py` |
| `ami_encyclopedia_util.py` | `encyclopedia/utils/link_extractor.py` |
| `encyclopedia.css` | `encyclopedia/resources/encyclopedia.css` |

## What Stays in amilib

- `ami_dict.py` - Dictionary creation
- `wikimedia.py` - Wikipedia/Wikidata/Wiktionary lookups
- `ami_html.py` - HTML utilities
- All other utility modules

## Key Changes

### Import Paths

**Before:**
```python
from amilib.ami_encyclopedia import AmiEncyclopedia
```

**After:**
```python
from encyclopedia.core.encyclopedia import AmiEncyclopedia
# Or
from encyclopedia import AmiEncyclopedia
```

### Dependencies

Add to `requirements.txt`:
```
amilib>=1.0.0
```

### Structure

```
encyclopedia/
├── encyclopedia/          # NEW package
│   ├── core/             # Main encyclopedia class
│   ├── clustering/       # Clustering functionality
│   ├── cli/             # CLI arguments
│   └── utils/           # Utilities
├── Keyword_extraction/   # Existing
├── Dictionary/          # Existing
└── test/               # Existing + new tests
```

## Timeline

6 weeks total:
- Week 1: Preparation
- Week 2: Code migration
- Week 3: Testing
- Week 4: Documentation
- Week 5: Backward compatibility
- Week 6: Release

## Backward Compatibility

**Recommended approach**: Keep deprecated imports in `amilib` with warnings for 1-2 release cycles.

## See Full Plan

For detailed migration steps, see: `docs/migration_plan.md`


