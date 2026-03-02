"""
Tests for knowledge graph creation from encyclopedia entries.

Tests cover:
- Wikipedia link extraction from descriptions
- Shared Wikipedia links (weight calculation)
- Wikidata ancestry relationships
- Wikidata part-whole relationships
- Shared Wikidata properties
- Shared property values
- Graph creation and export

Date: March 2, 2026 (system date)
"""

import pytest
import json
from pathlib import Path
from typing import List, Dict

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


class TestWikipediaLinkExtraction:
    """Tests for extracting Wikipedia links from entry descriptions."""
    
    def test_extract_wikipedia_links_from_description(self, small_encyclopedia):
        """Test extracting Wikipedia links from HTML descriptions."""
        # Get entry with description
        entry_with_desc = None
        for entry in small_encyclopedia.entries:
            if entry.get('description_html'):
                entry_with_desc = entry
                break
        
        if not entry_with_desc:
            pytest.skip("No entry with description_html found")
        
        # Extract links using function (to be implemented)
        from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor
        
        extractor = WikipediaLinkExtractor()
        links = extractor.extract_links_from_description(entry_with_desc.get('description_html', ''))
        
        # Verify results
        assert isinstance(links, list), f"Should return list, got {type(links)}"
        
        # Check link structure
        for link in links:
            assert 'url' in link, f"Link should have 'url' key: {link}"
            assert 'text' in link, f"Link should have 'text' key: {link}"
            assert 'wikipedia.org/wiki/' in link['url'] or '/wiki/' in link['url'], \
                f"Link URL should contain Wikipedia path: {link['url']}"
        
        # Save results for human inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikipediaLinkExtraction")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "extracted_links.json")
        results_file.write_text(
            json.dumps({
                'entry_term': entry_with_desc.get('term'),
                'entry_wikidata_id': entry_with_desc.get('wikidata_id'),
                'links_found': links,
                'link_count': len(links)
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_match_links_to_encyclopedia_entries(self, small_encyclopedia):
        """Test matching extracted links to encyclopedia entries."""
        from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor
        
        extractor = WikipediaLinkExtractor()
        
        # Get entry with description
        source_entry = None
        for entry in small_encyclopedia.entries:
            if entry.get('description_html'):
                source_entry = entry
                break
        
        if not source_entry:
            pytest.skip("No entry with description_html found")
        
        # Extract links
        links = extractor.extract_links_from_description(source_entry.get('description_html', ''))
        
        # Match links to entries
        matched_links = []
        for link in links:
            target_entry = extractor.find_target_entry(link['url'], small_encyclopedia)
            if target_entry:
                matched_links.append({
                    'link': link,
                    'target_entry': {
                        'term': target_entry.get('term'),
                        'wikidata_id': target_entry.get('wikidata_id')
                    }
                })
        
        # Verify at least some links were matched (if links exist)
        if links:
            assert len(matched_links) > 0 or len(links) == 0, \
                f"Should match at least some links. Found {len(links)} links, matched {len(matched_links)}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikipediaLinkExtraction")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "matched_links.json")
        results_file.write_text(
            json.dumps({
                'source_entry': {
                    'term': source_entry.get('term'),
                    'wikidata_id': source_entry.get('wikidata_id')
                },
                'total_links': len(links),
                'matched_links': matched_links,
                'match_count': len(matched_links)
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_count_link_occurrences(self, small_encyclopedia):
        """Test counting how many times a source entry links to a target entry."""
        from encyclopedia.utils.knowledge_graph.wikipedia_extractor import WikipediaLinkExtractor
        
        extractor = WikipediaLinkExtractor()
        
        # Get two entries
        entries = [e for e in small_encyclopedia.entries if e.get('description_html')]
        if len(entries) < 2:
            pytest.skip("Need at least 2 entries with descriptions")
        
        source_entry = entries[0]
        target_entry = entries[1]
        
        # Count occurrences
        count = extractor.count_link_occurrences(source_entry, target_entry)
        
        # Verify result
        assert isinstance(count, int), f"Should return int, got {type(count)}"
        assert count >= 0, f"Count should be >= 0, got {count}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikipediaLinkExtraction")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "link_occurrences.json")
        results_file.write_text(
            json.dumps({
                'source_entry': source_entry.get('term'),
                'target_entry': target_entry.get('term'),
                'occurrence_count': count
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"


class TestSharedLinkWeights:
    """Tests for calculating weights based on shared Wikipedia links."""
    
    def test_calculate_shared_link_weight(self, small_encyclopedia):
        """Test calculating Jaccard similarity based on shared Wikipedia links."""
        from encyclopedia.utils.knowledge_graph.weight_calculator import EdgeWeightCalculator
        
        calculator = EdgeWeightCalculator()
        
        # Get two entries
        entries = [e for e in small_encyclopedia.entries if e.get('wikipedia_url') or e.get('description_html')]
        if len(entries) < 2:
            pytest.skip("Need at least 2 entries")
        
        entry1 = entries[0]
        entry2 = entries[1]
        
        # Calculate shared link weight
        weight = calculator.calculate_shared_link_weight(entry1, entry2, small_encyclopedia)
        
        # Verify result
        assert isinstance(weight, float), f"Should return float, got {type(weight)}"
        assert 0.0 <= weight <= 1.0, f"Weight should be in [0, 1], got {weight}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestSharedLinkWeights")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "shared_link_weight.json")
        results_file.write_text(
            json.dumps({
                'entry1': entry1.get('term'),
                'entry2': entry2.get('term'),
                'weight': weight,
                'jaccard_similarity': weight
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_calculate_jaccard_similarity(self, small_encyclopedia):
        """Test Jaccard similarity calculation for shared links."""
        from encyclopedia.utils.knowledge_graph.weight_calculator import EdgeWeightCalculator
        
        calculator = EdgeWeightCalculator()
        
        # Get entries with Wikipedia links
        entries = [e for e in small_encyclopedia.entries if e.get('description_html')]
        if len(entries) < 2:
            pytest.skip("Need at least 2 entries with descriptions")
        
        entry1 = entries[0]
        entry2 = entries[1]
        
        # Calculate Jaccard similarity
        similarity = calculator.calculate_shared_link_weight(entry1, entry2, small_encyclopedia)
        
        # Verify Jaccard properties
        assert 0.0 <= similarity <= 1.0, f"Jaccard similarity should be in [0, 1], got {similarity}"
        
        # If entries are identical, similarity should be 1.0
        # (This is a property test, not a strict assertion)
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestSharedLinkWeights")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "jaccard_similarity.json")
        results_file.write_text(
            json.dumps({
                'entry1': entry1.get('term'),
                'entry2': entry2.get('term'),
                'jaccard_similarity': similarity
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"


class TestWikidataRelationships:
    """Tests for extracting Wikidata relationships."""
    
    def test_fetch_wikidata_properties(self, small_encyclopedia):
        """Test fetching Wikidata properties for entries."""
        from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
        
        extractor = WikidataRelationshipExtractor()
        
        # Get entry with Wikidata ID
        entry_with_wikidata = None
        for entry in small_encyclopedia.entries:
            if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
                entry_with_wikidata = entry
                break
        
        if not entry_with_wikidata:
            pytest.skip("No entry with Wikidata ID found")
        
        # Fetch properties
        properties = extractor.fetch_wikidata_properties(entry_with_wikidata['wikidata_id'])
        
        # Verify result
        assert isinstance(properties, dict), f"Should return dict, got {type(properties)}"
        
        # Check property structure
        for prop_id, values in properties.items():
            assert prop_id.startswith('P'), f"Property ID should start with 'P', got {prop_id}"
            assert isinstance(values, list), f"Property values should be list, got {type(values)}"
            for value in values:
                assert isinstance(value, str), f"Property value should be string, got {type(value)}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikidataRelationships")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "wikidata_properties.json")
        results_file.write_text(
            json.dumps({
                'entry_term': entry_with_wikidata.get('term'),
                'wikidata_id': entry_with_wikidata.get('wikidata_id'),
                'properties': properties
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_extract_ancestry_relationships(self, small_encyclopedia):
        """Test extracting instance of and subclass of relationships."""
        from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
        
        extractor = WikidataRelationshipExtractor()
        
        # Get entry with Wikidata ID
        entry_with_wikidata = None
        for entry in small_encyclopedia.entries:
            if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
                entry_with_wikidata = entry
                break
        
        if not entry_with_wikidata:
            pytest.skip("No entry with Wikidata ID found")
        
        # Extract ancestry relationships
        relationships = extractor.extract_ancestry_relationships(entry_with_wikidata)
        
        # Verify result
        assert isinstance(relationships, list), f"Should return list, got {type(relationships)}"
        
        # Check relationship structure
        for rel in relationships:
            assert 'property_id' in rel, f"Relationship should have 'property_id': {rel}"
            assert 'target_id' in rel, f"Relationship should have 'target_id': {rel}"
            assert rel['property_id'] in ['P31', 'P279'], \
                f"Property ID should be P31 or P279, got {rel['property_id']}"
            assert rel['target_id'].startswith('Q'), \
                f"Target ID should start with 'Q', got {rel['target_id']}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikidataRelationships")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "ancestry_relationships.json")
        results_file.write_text(
            json.dumps({
                'entry_term': entry_with_wikidata.get('term'),
                'wikidata_id': entry_with_wikidata.get('wikidata_id'),
                'relationships': relationships
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_extract_part_relationships(self, small_encyclopedia):
        """Test extracting part-whole relationships."""
        from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
        
        extractor = WikidataRelationshipExtractor()
        
        # Get entry with Wikidata ID
        entry_with_wikidata = None
        for entry in small_encyclopedia.entries:
            if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
                entry_with_wikidata = entry
                break
        
        if not entry_with_wikidata:
            pytest.skip("No entry with Wikidata ID found")
        
        # Extract part relationships
        relationships = extractor.extract_part_relationships(entry_with_wikidata)
        
        # Verify result
        assert isinstance(relationships, list), f"Should return list, got {type(relationships)}"
        
        # Check relationship structure
        for rel in relationships:
            assert 'property_id' in rel, f"Relationship should have 'property_id': {rel}"
            assert 'target_id' in rel, f"Relationship should have 'target_id': {rel}"
            assert 'direction' in rel, f"Relationship should have 'direction': {rel}"
            assert rel['property_id'] in ['P527', 'P361', 'P2670'], \
                f"Property ID should be P527, P361, or P2670, got {rel['property_id']}"
            assert rel['direction'] in ['has_part', 'part_of'], \
                f"Direction should be 'has_part' or 'part_of', got {rel['direction']}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikidataRelationships")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "part_relationships.json")
        results_file.write_text(
            json.dumps({
                'entry_term': entry_with_wikidata.get('term'),
                'wikidata_id': entry_with_wikidata.get('wikidata_id'),
                'relationships': relationships
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"
    
    def test_find_shared_properties(self, small_encyclopedia):
        """Test finding shared Wikidata properties between entries."""
        from encyclopedia.utils.knowledge_graph.wikidata_extractor import WikidataRelationshipExtractor
        
        extractor = WikidataRelationshipExtractor()
        
        # Get two entries with Wikidata IDs
        entries_with_wikidata = [
            e for e in small_encyclopedia.entries 
            if e.get('wikidata_id') and e.get('wikidata_id') not in ('', 'no_wikidata_id')
        ]
        
        if len(entries_with_wikidata) < 2:
            pytest.skip("Need at least 2 entries with Wikidata IDs")
        
        entry1 = entries_with_wikidata[0]
        entry2 = entries_with_wikidata[1]
        
        # Find shared properties
        shared = extractor.find_shared_properties(entry1, entry2)
        
        # Verify result
        assert isinstance(shared, list), f"Should return list, got {type(shared)}"
        
        # Check shared property structure
        for prop in shared:
            assert 'property_id' in prop, f"Shared property should have 'property_id': {prop}"
            assert 'value_id' in prop, f"Shared property should have 'value_id': {prop}"
            assert prop['property_id'].startswith('P'), \
                f"Property ID should start with 'P', got {prop['property_id']}"
            assert prop['value_id'].startswith('Q'), \
                f"Value ID should start with 'Q', got {prop['value_id']}"
        
        # Save results
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestWikidataRelationships")
        output_dir.mkdir(parents=True, exist_ok=True)
        results_file = Path(output_dir, "shared_properties.json")
        results_file.write_text(
            json.dumps({
                'entry1': {
                    'term': entry1.get('term'),
                    'wikidata_id': entry1.get('wikidata_id')
                },
                'entry2': {
                    'term': entry2.get('term'),
                    'wikidata_id': entry2.get('wikidata_id')
                },
                'shared_properties': shared
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert results_file.exists(), f"Results file should exist at {results_file}"


class TestKnowledgeGraphBuilder:
    """Tests for building complete knowledge graphs."""
    
    def test_build_graph_with_wikipedia_links(self, small_encyclopedia):
        """Test building graph with Wikipedia description links."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=False,
            include_wikidata_parts=False,
            include_shared_properties=False,
            include_shared_values=False
        )
        
        # Verify graph structure
        assert graph is not None, "Graph should not be None"
        assert graph.number_of_nodes() > 0, f"Graph should have nodes, got {graph.number_of_nodes()}"
        
        # Check nodes have required attributes
        for node_id, node_data in graph.nodes(data=True):
            assert 'wikidata_id' in node_data or 'term' in node_data, \
                f"Node should have wikidata_id or term: {node_data}"
        
        # Check edges have required attributes
        for source, target, edge_data in graph.edges(data=True):
            assert 'relationship_type' in edge_data, \
                f"Edge should have relationship_type: {edge_data}"
            assert 'weight' in edge_data, \
                f"Edge should have weight: {edge_data}"
        
        # Save graph for inspection
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestKnowledgeGraphBuilder")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save graph statistics
        stats_file = Path(output_dir, "graph_statistics.json")
        stats_file.write_text(
            json.dumps({
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'node_ids': list(graph.nodes())[:10],  # First 10 nodes
                'edge_samples': [
                    {
                        'source': source,
                        'target': target,
                        'relationship': edge_data.get('relationship_type'),
                        'weight': edge_data.get('weight')
                    }
                    for source, target, edge_data in list(graph.edges(data=True))[:5]
                ]
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert stats_file.exists(), f"Stats file should exist at {stats_file}"
    
    def test_build_graph_with_wikidata_relationships(self, small_encyclopedia):
        """Test building graph with Wikidata relationships."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=False,
            include_wikidata_ancestry=True,
            include_wikidata_parts=True,
            include_shared_properties=True,
            include_shared_values=True
        )
        
        # Verify graph structure
        assert graph is not None, "Graph should not be None"
        assert graph.number_of_nodes() > 0, f"Graph should have nodes, got {graph.number_of_nodes()}"
        
        # Check for Wikidata relationship edges
        wikidata_edges = [
            (s, t, d) for s, t, d in graph.edges(data=True)
            if d.get('relationship_type', '').startswith('P') or 
               'property_id' in d
        ]
        
        # Save graph statistics
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestKnowledgeGraphBuilder")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stats_file = Path(output_dir, "wikidata_graph_statistics.json")
        stats_file.write_text(
            json.dumps({
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'wikidata_edges': len(wikidata_edges),
                'edge_samples': [
                    {
                        'source': source,
                        'target': target,
                        'relationship': edge_data.get('relationship_type'),
                        'property_id': edge_data.get('property_id')
                    }
                    for source, target, edge_data in wikidata_edges[:5]
                ]
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert stats_file.exists(), f"Stats file should exist at {stats_file}"
    
    def test_build_complete_graph(self, small_encyclopedia):
        """Test building complete graph with all relationship types."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=True,
            include_wikidata_parts=True,
            include_shared_properties=True,
            include_shared_values=True
        )
        
        # Verify graph structure
        assert graph is not None, "Graph should not be None"
        assert graph.number_of_nodes() > 0, f"Graph should have nodes, got {graph.number_of_nodes()}"
        
        # Count edges by type
        edge_types = {}
        for source, target, edge_data in graph.edges(data=True):
            rel_type = edge_data.get('relationship_type', 'unknown')
            edge_types[rel_type] = edge_types.get(rel_type, 0) + 1
        
        # Save complete graph statistics
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestKnowledgeGraphBuilder")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        stats_file = Path(output_dir, "complete_graph_statistics.json")
        stats_file.write_text(
            json.dumps({
                'nodes': graph.number_of_nodes(),
                'edges': graph.number_of_edges(),
                'edge_types': edge_types,
                'node_samples': [
                    {
                        'node_id': node_id,
                        'term': data.get('term'),
                        'wikidata_id': data.get('wikidata_id')
                    }
                    for node_id, data in list(graph.nodes(data=True))[:10]
                ]
            }, indent=2, default=str),
            encoding='utf-8'
        )
        
        assert stats_file.exists(), f"Stats file should exist at {stats_file}"


class TestGraphExport:
    """Tests for exporting graphs to various formats."""
    
    def test_export_graphml(self, small_encyclopedia):
        """Test exporting graph to GraphML format."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter
        
        # Build graph
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=False,
            include_wikidata_parts=False,
            include_shared_properties=False,
            include_shared_values=False
        )
        
        # Export to GraphML
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestGraphExport")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "test_graph.graphml")
        
        exporter = GraphExporter()
        exporter.export_graphml(graph, output_file)
        
        # Verify file exists and has content
        assert output_file.exists(), f"GraphML file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "GraphML file should not be empty"
        
        # Verify GraphML structure (basic check)
        content = output_file.read_text(encoding='utf-8')
        assert '<?xml' in content, "GraphML should be XML format"
        assert '<graphml' in content or '<graph' in content, "GraphML should contain graph structure"
    
    def test_export_gexf(self, small_encyclopedia):
        """Test exporting graph to GEXF format."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter
        
        # Build graph
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=False,
            include_wikidata_parts=False,
            include_shared_properties=False,
            include_shared_values=False
        )
        
        # Export to GEXF
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestGraphExport")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "test_graph.gexf")
        
        exporter = GraphExporter()
        exporter.export_gexf(graph, output_file)
        
        # Verify file exists and has content
        assert output_file.exists(), f"GEXF file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "GEXF file should not be empty"
        
        # Verify GEXF structure (basic check)
        content = output_file.read_text(encoding='utf-8')
        assert '<?xml' in content, "GEXF should be XML format"
        assert '<gexf' in content or '<graph' in content, "GEXF should contain graph structure"
    
    def test_export_json(self, small_encyclopedia):
        """Test exporting graph to JSON format."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter
        
        # Build graph
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=False,
            include_wikidata_parts=False,
            include_shared_properties=False,
            include_shared_values=False
        )
        
        # Export to JSON
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestGraphExport")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "test_graph.json")
        
        exporter = GraphExporter()
        exporter.export_json(graph, output_file)
        
        # Verify file exists and has content
        assert output_file.exists(), f"JSON file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "JSON file should not be empty"
        
        # Verify JSON structure
        data = json.loads(output_file.read_text(encoding='utf-8'))
        assert 'nodes' in data or 'graph' in data, "JSON should contain nodes or graph structure"
    
    def test_export_rdf_turtle(self, small_encyclopedia):
        """Test exporting graph to RDF/Turtle format."""
        from encyclopedia.utils.knowledge_graph.graph_builder import KnowledgeGraphBuilder
        from encyclopedia.utils.knowledge_graph.graph_exporter import GraphExporter
        
        # Build graph
        builder = KnowledgeGraphBuilder(small_encyclopedia)
        graph = builder.build_graph(
            include_wikipedia_links=True,
            include_wikidata_ancestry=True,
            include_wikidata_parts=False,
            include_shared_properties=False,
            include_shared_values=False
        )
        
        # Export to RDF/Turtle
        output_dir = Path(Resources.TEMP_DIR, "test", "encyclopedia", "TestGraphExport")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir, "test_graph.ttl")
        
        exporter = GraphExporter()
        exporter.export_rdf_turtle(graph, output_file)
        
        # Verify file exists and has content
        assert output_file.exists(), f"RDF/Turtle file should exist at {output_file}"
        assert output_file.stat().st_size > 0, "RDF/Turtle file should not be empty"
        
        # Verify RDF/Turtle structure (basic check)
        content = output_file.read_text(encoding='utf-8')
        assert '@prefix' in content or 'wd:' in content or 'wdt:' in content, \
            "RDF/Turtle should contain prefix declarations or Wikidata prefixes"
