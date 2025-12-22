# SemanticCorpus: Structure and Process Proposal

**Date:** December 12, 2025  
**Project:** SemanticCorpus for JOSS Publication  
**Status:** Proposal

---

## Executive Summary

This document proposes the structure, process, and open-source tool integration for **SemanticCorpus**, a lightweight personal research corpus management system. The system is designed for individual and group use, supporting 100-10,000 documents with semantic enrichment, content-based relationship discovery, and knowledge graph construction.

---

## 1. System Requirements Summary

### Core Features
- **Personal/Group Corpus**: Designed for local machine storage
- **Document Ingestion**: From search (pygetpapers) or collections (e.g., IPCC)
- **Format Transformation**: Convert to HTML if needed
- **Semantic Structuring**: Structure HTML using JATS
- **Keyphrase Extraction**: Extract keyphrases for classification and search
- **DataTable Display**: Display content in interactive data tables
- **CRUD Operations**: Create, Read, Update, Delete documents
- **Lightweight Storage**: Filesystem-based with BAGIT compliance
- **Interdocument Links**: Create links by text similarity
- **Knowledge Graph**: Build knowledge graph from similarities

---

## 2. Proposed Project Structure

### 2.1 Directory Structure

```
semantic_corpus/
├── semantic_corpus/              # Main package
│   ├── __init__.py              # Empty (style guide compliance)
│   ├── core/                    # Core functionality
│   │   ├── __init__.py
│   │   ├── corpus_manager.py    # Main corpus management
│   │   ├── repository_interface.py  # Repository abstraction
│   │   ├── repository_factory.py    # Repository factory
│   │   └── exceptions.py         # Custom exceptions
│   ├── ingestion/               # Document ingestion
│   │   ├── __init__.py
│   │   ├── pygetpapers_ingester.py  # pygetpapers integration
│   │   ├── collection_ingester.py   # Collection ingestion (IPCC, etc.)
│   │   └── metadata_extractor.py    # Metadata extraction
│   ├── transformation/          # Format transformation
│   │   ├── __init__.py
│   │   ├── pdf_to_html.py       # PDF conversion
│   │   ├── xml_to_html.py       # XML conversion
│   │   ├── jats_processor.py    # JATS structuring
│   │   └── html_normalizer.py   # HTML normalization
│   ├── semantification/         # Semantic enrichment
│   │   ├── __init__.py
│   │   ├── id_generator.py      # Semantic ID generation
│   │   ├── term_extractor.py    # Keyphrase extraction
│   │   ├── annotation_adder.py  # Semantic annotation
│   │   └── structure_detector.py # Document structure detection
│   ├── similarity/               # Similarity analysis
│   │   ├── __init__.py
│   │   ├── text_similarity.py   # Text similarity computation
│   │   ├── feature_extractor.py # Feature extraction
│   │   └── similarity_matrix.py # Similarity matrix builder
│   ├── graph/                    # Knowledge graph
│   │   ├── __init__.py
│   │   ├── graph_builder.py     # Graph construction
│   │   ├── link_creator.py       # Interdocument link creation
│   │   └── graph_visualizer.py  # Graph visualization
│   ├── storage/                  # Storage management
│   │   ├── __init__.py
│   │   ├── bagit_manager.py     # BAGIT compliance
│   │   ├── filesystem_store.py  # Filesystem storage
│   │   └── manifest_generator.py # Manifest generation
│   ├── validation/               # Quality validation
│   │   ├── __init__.py
│   │   ├── conversion_validator.py  # Conversion quality checks
│   │   ├── metadata_validator.py    # Metadata validation
│   │   └── quality_reporter.py      # Quality reporting
│   ├── display/                  # Display/UI
│   │   ├── __init__.py
│   │   ├── datatable_generator.py   # DataTable generation
│   │   └── html_renderer.py         # HTML rendering
│   └── utils.py                  # Utility functions
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py              # Test configuration
│   ├── test_corpus_core.py      # Core tests
│   ├── test_ingestion.py        # Ingestion tests
│   ├── test_transformation.py   # Transformation tests
│   ├── test_semantification.py  # Semantification tests
│   ├── test_similarity.py       # Similarity tests
│   ├── test_graph.py            # Graph tests
│   └── test_integration.py      # Integration tests
├── docs/                         # Documentation
│   ├── README.md                # Main README
│   ├── ARCHITECTURE.md          # Architecture documentation
│   ├── API.md                   # API reference
│   ├── WORKFLOW.md              # Workflow guide
│   └── CONTRIBUTING.md          # Contribution guide
├── examples/                     # Example scripts
│   ├── ingest_pygetpapers.py   # pygetpapers ingestion example
│   ├── ingest_ipcc.py          # IPCC collection example
│   └── build_knowledge_graph.py # Knowledge graph example
├── pyproject.toml               # Project configuration
├── README.md                     # Project README
└── LICENSE                       # License file
```

### 2.2 Corpus Structure (BAGIT-Compliant)

```
{corpus_name}/
├── bag-info.txt                 # BAGIT metadata
├── bagit.txt                    # BAGIT version
├── manifest-md5.txt             # File checksums
├── data/                        # BAGIT payload
│   ├── documents/               # Original documents
│   │   ├── pdf/                 # PDF files
│   │   ├── xml/                 # XML files
│   │   └── html/                # HTML files
│   ├── semantic/                # Semantically enriched HTML
│   │   └── {doc_id}_semantic.html
│   ├── metadata/                # Document metadata
│   │   └── {doc_id}_metadata.json
│   ├── keyphrases/              # Extracted keyphrases
│   │   └── {doc_id}_keyphrases.json
│   └── indices/                 # Search indices
│       └── term_index.json
├── relations/                   # Document relationships
│   ├── similarity_matrix.json   # Similarity scores
│   ├── similarity_graph.graphml # GraphML format
│   └── related_documents.json  # Related document pairs
├── analysis/                    # Analysis results
│   ├── validation_report.html
│   ├── quality_metrics.json
│   └── corpus_statistics.json
└── provenance/                  # Provenance tracking
    ├── ingestion_log.json
    └── processing_history.json
```

---

## 3. Process Workflow

### 3.1 High-Level Workflow

```
┌─────────────────────┐
│ 1. Ingestion        │ ← pygetpapers JSON or collection files
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Validation       │ ← Metadata & file validation
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Transformation    │ ← PDF/XML → HTML (if needed)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. JATS Structuring │ ← Structure HTML with JATS
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 5. Semantification  │ ← Add semantic IDs & annotations
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 6. Keyphrase Extract│ ← Extract keyphrases for search
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 7. Similarity Analysis│ ← Compute text similarity
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 8. Graph Building   │ ← Build knowledge graph
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 9. Link Creation    │ ← Create interdocument links
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 10. DataTable Gen    │ ← Generate display tables
└─────────────────────┘
```

### 3.2 Detailed Process Steps

#### Step 1: Ingestion
- **Input**: pygetpapers JSON (`eupmc_result.json`) or collection files
- **Process**:
  - Parse metadata from JSON or file headers
  - Locate document files (PDF, XML, HTML)
  - Extract bibliographic metadata (title, authors, DOI, etc.)
  - Create corpus structure with BAGIT compliance
  - Generate initial manifest
- **Output**: Corpus directory with documents and metadata

#### Step 2: Validation
- **Metadata Validation**:
  - Check required fields (title, authors, identifiers)
  - Validate identifier formats (DOI, PMCID, PMID)
  - Detect duplicates
- **File Validation**:
  - Verify file existence and accessibility
  - Check file integrity
  - Validate file formats
- **Output**: Validation report with flagged issues

#### Step 3: Transformation
- **PDF → HTML**: Use existing amilib PDF conversion
- **XML → HTML**: Convert XML (JATS, TEI, etc.) to HTML
- **HTML Normalization**: Clean and normalize HTML structure
- **Output**: Standardized HTML documents

#### Step 4: JATS Structuring
- **Structure Detection**: Identify document sections (headings, paragraphs)
- **JATS Mapping**: Map HTML structure to JATS elements
- **Semantic Markup**: Add JATS-compliant semantic attributes
- **Output**: JATS-structured HTML documents

#### Step 5: Semantification
- **ID Generation**: Generate unique semantic IDs for paragraphs/sections
- **Structure Annotation**: Add semantic markup (RDFa, HTML5 semantic elements)
- **Term Identification**: Identify key terms and concepts
- **Output**: Semantically enriched HTML with IDs

#### Step 6: Keyphrase Extraction
- **Extraction Methods**:
  - TF-IDF based extraction
  - KeyBERT (BERT-based extraction)
  - YAKE (Yet Another Keyword Extractor)
- **Classification**: Categorize keyphrases by domain/topic
- **Indexing**: Build searchable keyphrase index
- **Output**: Keyphrase JSON files and search index

#### Step 7: Similarity Analysis
- **Feature Extraction**: Extract text features (TF-IDF, embeddings)
- **Similarity Computation**: 
  - Cosine similarity (TF-IDF vectors)
  - Semantic similarity (sentence embeddings)
  - Abstract similarity
- **Thresholding**: Apply similarity thresholds
- **Output**: Similarity matrix (sparse format)

#### Step 8: Graph Building
- **Node Creation**: Create graph nodes for documents
- **Edge Creation**: Create edges based on similarity scores
- **Graph Structure**: Build NetworkX graph
- **Output**: GraphML file and NetworkX graph object

#### Step 9: Link Creation
- **Link Generation**: Create HTML links between similar documents
- **Link Annotation**: Add link metadata (similarity score, reason)
- **Navigation Structure**: Build navigable link structure
- **Output**: HTML documents with interdocument links

#### Step 10: DataTable Generation
- **Table Creation**: Generate DataTables from corpus metadata
- **Interactive Features**: Add search, sort, filter capabilities
- **Visualization**: Include graph visualization
- **Output**: Interactive HTML tables with DataTables.js

---

## 4. Open Source Tools Integration

### 4.1 Document Processing

#### **PDF Processing**
- **PyMuPDF (fitz)**: PDF text extraction and conversion
  - **License**: AGPL-3.0 / Commercial
  - **Use Case**: PDF → text extraction
  - **Integration**: Already used in amilib

#### **XML/HTML Processing**
- **lxml**: XML/HTML parsing and processing
  - **License**: BSD
  - **Use Case**: XML parsing, HTML manipulation
  - **Integration**: Already used in amilib

#### **JATS Processing**
- **jats2html** (or custom XSLT): JATS to HTML conversion
  - **License**: Various (check specific tool)
  - **Use Case**: JATS XML → HTML conversion
  - **Note**: amilib has JATS XSLT resources

### 4.2 Keyphrase Extraction

#### **KeyBERT**
- **License**: MIT
- **Use Case**: BERT-based keyphrase extraction
- **Integration**: Already used in corpus_module
- **Advantages**: High quality, semantic understanding

#### **YAKE (Yet Another Keyword Extractor)**
- **License**: MIT
- **Use Case**: Unsupervised keyphrase extraction
- **Advantages**: Fast, no training required, multilingual

#### **scikit-learn TfidfVectorizer**
- **License**: BSD
- **Use Case**: TF-IDF based keyphrase extraction
- **Integration**: Already used in corpus_module
- **Advantages**: Fast, well-tested, configurable

### 4.3 Similarity and NLP

#### **scikit-learn**
- **License**: BSD
- **Use Case**: TF-IDF vectorization, cosine similarity
- **Integration**: Already used in corpus_module

#### **sentence-transformers**
- **License**: Apache 2.0
- **Use Case**: Semantic similarity using transformer models
- **Advantages**: State-of-the-art semantic similarity

#### **spaCy**
- **License**: MIT
- **Use Case**: NLP preprocessing, text processing
- **Advantages**: Fast, production-ready

### 4.4 Graph and Network Analysis

#### **NetworkX**
- **License**: BSD
- **Use Case**: Graph construction and analysis
- **Integration**: Already used in amilib (ami_graph.py)
- **Advantages**: Comprehensive graph library

#### **graphviz**
- **License**: EPL-1.0
- **Use Case**: Graph visualization
- **Integration**: Already used in amilib
- **Advantages**: High-quality graph rendering

### 4.5 Storage and Data Management

#### **bagit-python**
- **License**: CC0 1.0
- **Use Case**: BAGIT bag creation and validation
- **Advantages**: Standard compliance, preservation-ready

#### **pandas**
- **License**: BSD
- **Use Case**: Data manipulation, CSV handling
- **Integration**: Already used in corpus_module
- **Advantages**: Powerful data analysis

### 4.6 Display and UI

#### **DataTables.js** (via datatables-module)
- **License**: MIT
- **Use Case**: Interactive HTML tables
- **Integration**: Already used in amilib (datatables_module)
- **Advantages**: Rich features, good documentation

#### **D3.js** (optional)
- **License**: BSD-3-Clause
- **Use Case**: Advanced graph visualization
- **Advantages**: Highly customizable

### 4.7 Integration with Existing Tools

#### **pygetpapers**
- **License**: Apache 2.0
- **Use Case**: Document search and download
- **Integration**: Read JSON output, use directory structure
- **Status**: External dependency

#### **amilib**
- **License**: (Check amilib license)
- **Use Case**: HTML processing, PDF conversion, graph operations
- **Integration**: Import and use amilib modules
- **Status**: Internal dependency

---

## 5. Implementation Strategy

### 5.1 Phase 1: Core Infrastructure (Weeks 1-2)
- Set up project structure
- Implement corpus manager with BAGIT support
- Create ingestion modules (pygetpapers, collections)
- Basic validation framework

### 5.2 Phase 2: Transformation and Semantification (Weeks 3-4)
- PDF/XML to HTML conversion
- JATS structuring
- Semantic ID generation
- Basic annotation

### 5.3 Phase 3: Keyphrase Extraction (Week 5)
- Integrate KeyBERT
- Integrate YAKE
- TF-IDF extraction
- Keyphrase indexing

### 5.4 Phase 4: Similarity and Graph (Weeks 6-7)
- Text similarity computation
- Similarity matrix generation
- Graph building with NetworkX
- Interdocument link creation

### 5.5 Phase 5: Display and Polish (Week 8)
- DataTable generation
- HTML rendering
- Visualization
- Documentation

---

## 6. Dependencies Summary

### Core Dependencies
```python
# Document Processing
lxml>=4.9.0
PyMuPDF>=1.23.0

# NLP and Keyphrase Extraction
keybert>=0.8.0
yake>=0.4.8
scikit-learn>=1.3.0
sentence-transformers>=2.2.0

# Graph and Network
networkx>=3.1
graphviz>=0.20.0

# Storage
bagit>=1.8.0
pandas>=2.0.0

# Utilities
pathlib2>=2.3.7  # Python < 3.4 compatibility
```

### Integration Dependencies
- **amilib**: Internal dependency (HTML processing, PDF conversion)
- **pygetpapers**: External dependency (document search/download)
- **datatables-module**: Internal dependency (table generation)

---

## 7. Code Style Compliance

Following amilib style guide:
- **Absolute imports**: `from semantic_corpus.core.corpus_manager import CorpusManager`
- **Empty __init__.py**: All `__init__.py` files should be empty
- **No mocks in tests**: Use real implementations
- **No magic strings**: Use class constants
- **Path construction**: Use `Path("a") / "b" / "c"` format
- **TDD approach**: Test-driven development

---

## 8. Testing Strategy

### Test Categories
1. **Unit Tests**: Individual module functionality
2. **Integration Tests**: Cross-module workflows
3. **End-to-End Tests**: Full pipeline execution
4. **Performance Tests**: Large corpus handling

### Test Data
- Small test corpus (10-20 documents)
- Medium test corpus (100 documents)
- Large test corpus (1000+ documents) for performance

---

## 9. Documentation Requirements

### For JOSS Publication
1. **README.md**: Project overview, installation, quick start
2. **ARCHITECTURE.md**: System architecture and design decisions
3. **API.md**: API reference documentation
4. **WORKFLOW.md**: Detailed workflow guide
5. **EXAMPLES.md**: Usage examples
6. **CONTRIBUTING.md**: Contribution guidelines

### Code Documentation
- Docstrings for all public methods
- Type hints for function signatures
- Inline comments for complex logic

---

## 10. Next Steps

1. **Review and Approve**: Review this proposal with team
2. **Set Up Repository**: Create semantic_corpus repository
3. **Initialize Project**: Set up project structure and dependencies
4. **Begin Phase 1**: Start with core infrastructure
5. **Iterate**: Follow TDD approach, iterate on design

---

## References

- **amilib**: https://github.com/petermr/amilib
- **pygetpapers**: https://github.com/petermr/pygetpapers
- **BAGIT Specification**: https://datatracker.ietf.org/doc/html/rfc8493
- **JATS**: https://jats.nlm.nih.gov/
- **KeyBERT**: https://github.com/MaartenGr/KeyBERT
- **YAKE**: https://github.com/LIAAD/yake
- **NetworkX**: https://networkx.org/
- **JOSS**: https://joss.theoj.org/

---

*Document created: December 12, 2025*  
*Status: Proposal - Awaiting Review*




