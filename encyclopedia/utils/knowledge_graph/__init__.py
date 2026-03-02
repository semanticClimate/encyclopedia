"""
Knowledge graph creation from encyclopedia entries.

This module provides functionality to:
- Extract Wikipedia links from entry descriptions
- Extract Wikidata relationships
- Calculate edge weights
- Build knowledge graphs
- Export graphs to various formats

Date: March 2, 2026 (system date)
"""

from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor
from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
from encyclopedia.utils.knowledge_graph.weight_calculator import EdgeWeightCalculator
from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter

__all__ = [
    'WikipediaLinkExtractor',
    'WikidataRelationshipExtractor',
    'EdgeWeightCalculator',
    'KnowledgeGraphBuilder',
    'GraphExporter',
]
