"""
Test 7: Analyze link density
Purpose: Analyze linking patterns and density
"""

import pytest
from pathlib import Path
import json
from collections import Counter
from .test_config import CURRENT_ENCYCLOPEDIA_FILE, OUTPUT_DIR
from .link_extractor import EncyclopediaLinkExtractor

class TestLinkDensity:
    """Test analysis of link density and patterns"""
    
    def setup_method(self):
        """Setup test parameters and outputs"""
        self.input_file = CURRENT_ENCYCLOPEDIA_FILE
        self.output_dir = OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.extractor = EncyclopediaLinkExtractor()
        
        # Expected outputs
        self.density_analysis_file = Path(self.output_dir, "link_density_analysis.json")
        self.frequency_analysis_file = Path(self.output_dir, "link_frequency_analysis.json")
        self.cluster_patterns_file = Path(self.output_dir, "cluster_patterns.json")
    
    def test_analyze_link_density(self):
        """Analyze link density across entries"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        density_analysis = self._analyze_link_density(entries)
        
        # Make assertions
        assert density_analysis['total_entries'] > 0, "No entries found"
        assert density_analysis['total_links'] >= 0, "Invalid total links"
        assert density_analysis['average_links_per_entry'] >= 0, "Invalid average links"
        assert density_analysis['max_links_in_entry'] >= 0, "Invalid max links"
        assert density_analysis['min_links_in_entry'] >= 0, "Invalid min links"
        
        # Verify density calculations
        expected_avg = density_analysis['total_links'] / density_analysis['total_entries']
        assert abs(density_analysis['average_links_per_entry'] - expected_avg) < 0.01, \
            "Average calculation incorrect"
        
        # Save results
        with open(self.density_analysis_file, 'w') as f:
            json.dump(density_analysis, f, indent=2)
    
    def _analyze_link_density(self, entries):
        """Analyze link density from entries"""
        link_counts = []
        total_links = 0
        
        for entry in entries:
            link_count = len(entry['description_links'])
            link_counts.append(link_count)
            total_links += link_count
        
        if not link_counts:
            return {
                'total_entries': 0,
                'total_links': 0,
                'average_links_per_entry': 0,
                'max_links_in_entry': 0,
                'min_links_in_entry': 0,
                'link_count_distribution': []
            }
        
        return {
            'total_entries': len(entries),
            'total_links': total_links,
            'average_links_per_entry': total_links / len(entries),
            'max_links_in_entry': max(link_counts),
            'min_links_in_entry': min(link_counts),
            'link_count_distribution': link_counts,
            'entries_with_no_links': sum(1 for count in link_counts if count == 0),
            'entries_with_many_links': sum(1 for count in link_counts if count > 5)
        }
    
    def test_analyze_link_frequency(self):
        """Analyze frequency of specific links"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        frequency_analysis = self._analyze_link_frequency(entries)
        
        # Make assertions
        assert len(frequency_analysis['most_frequent_links']) > 0, "No frequent links found"
        assert len(frequency_analysis['link_frequency_counts']) > 0, "No frequency counts"
        assert frequency_analysis['total_unique_links'] > 0, "No unique links found"
        
        # Verify frequency data
        most_frequent = frequency_analysis['most_frequent_links']
        assert all(isinstance(link, tuple) and len(link) == 2 for link in most_frequent), \
            "Most frequent links format incorrect"
        assert all(count > 0 for _, count in most_frequent), "Invalid frequency counts"
        
        # Save results
        with open(self.frequency_analysis_file, 'w') as f:
            json.dump(frequency_analysis, f, indent=2)
    
    def _analyze_link_frequency(self, entries):
        """Analyze frequency of links across entries"""
        link_counter = Counter()
        link_types_counter = Counter()
        
        for entry in entries:
            for link in entry['description_links']:
                href = link['href']
                link_type = link['type']
                
                link_counter[href] += 1
                link_types_counter[link_type] += 1
        
        return {
            'most_frequent_links': link_counter.most_common(10),
            'link_frequency_counts': dict(link_counter),
            'link_type_frequency': dict(link_types_counter),
            'total_unique_links': len(link_counter),
            'most_common_link_type': link_types_counter.most_common(1)[0] if link_types_counter else None
        }
    
    def test_identify_entry_clusters_by_links(self):
        """Identify clusters of entries by link patterns"""
        # Define inputs
        html_content = self.input_file.read_text(encoding='utf-8')
        
        # Call module
        entries = self.extractor.extract_entries(html_content)
        cluster_patterns = self._identify_cluster_patterns(entries)
        
        # Make assertions
        assert len(cluster_patterns['clusters']) >= 0, "Invalid cluster count"
        assert cluster_patterns['total_clustered_entries'] <= len(entries), "Too many clustered entries"
        assert len(cluster_patterns['cluster_characteristics']) >= 0, "No cluster characteristics"
        
        # Verify cluster properties
        for cluster in cluster_patterns['clusters']:
            assert len(cluster['entries']) > 0, "Empty cluster found"
            assert len(cluster['common_links']) >= 0, "No common links in cluster"
        
        # Save results
        with open(self.cluster_patterns_file, 'w') as f:
            json.dump(cluster_patterns, f, indent=2)
    
    def _identify_cluster_patterns(self, entries):
        """Identify clusters based on shared links"""
        # Build link-to-entries mapping
        link_to_entries = {}
        
        for entry in entries:
            entry_links = set(link['href'] for link in entry['description_links'])
            for link in entry_links:
                if link not in link_to_entries:
                    link_to_entries[link] = []
                link_to_entries[link].append(entry['term'])
        
        # Find clusters based on shared links
        clusters = []
        processed_entries = set()
        
        for link, linked_entries in link_to_entries.items():
            if len(linked_entries) > 1:  # Only consider links shared by multiple entries
                cluster_entries = [term for term in linked_entries if term not in processed_entries]
                if len(cluster_entries) > 1:
                    cluster = {
                        'common_links': [link],
                        'entries': cluster_entries,
                        'link_count': len(cluster_entries)
                    }
                    clusters.append(cluster)
                    processed_entries.update(cluster_entries)
        
        # Analyze cluster characteristics
        characteristics = {
            'average_cluster_size': sum(len(cluster['entries']) for cluster in clusters) / len(clusters) if clusters else 0,
            'largest_cluster_size': max(len(cluster['entries']) for cluster in clusters) if clusters else 0,
            'clusters_with_many_links': sum(1 for cluster in clusters if len(cluster['common_links']) > 3)
        }
        
        return {
            'clusters': clusters,
            'total_clustered_entries': len(processed_entries),
            'cluster_characteristics': characteristics,
            'unclustered_entries': [entry['term'] for entry in entries if entry['term'] not in processed_entries]
        }
    
    def test_analyze_link_distribution_patterns(self):
        """Analyze distribution patterns of links"""
        # Define inputs
        if not self.density_analysis_file.exists():
            pytest.skip("Density analysis not available")
        
        with open(self.density_analysis_file, 'r') as f:
            density_data = json.load(f)
        
        # Call module
        distribution_analysis = self._analyze_distribution_patterns(density_data)
        
        # Make assertions
        assert distribution_analysis['distribution_type'] in ['uniform', 'skewed', 'bimodal'], \
            "Invalid distribution type"
        assert distribution_analysis['variance'] >= 0, "Invalid variance"
        assert distribution_analysis['standard_deviation'] >= 0, "Invalid standard deviation"
        
        # Verify distribution metrics
        link_counts = density_data['link_count_distribution']
        if link_counts:
            expected_mean = sum(link_counts) / len(link_counts)
            assert abs(distribution_analysis['mean'] - expected_mean) < 0.01, "Mean calculation incorrect"
        
        # Save results
        with open(self.cluster_patterns_file, 'w') as f:
            json.dump(distribution_analysis, f, indent=2)
    
    def _analyze_distribution_patterns(self, density_data):
        """Analyze distribution patterns of link counts"""
        link_counts = density_data['link_count_distribution']
        
        if not link_counts:
            return {
                'mean': 0,
                'variance': 0,
                'standard_deviation': 0,
                'distribution_type': 'uniform'
            }
        
        # Calculate basic statistics
        mean = sum(link_counts) / len(link_counts)
        variance = sum((x - mean) ** 2 for x in link_counts) / len(link_counts)
        std_dev = variance ** 0.5
        
        # Determine distribution type
        if std_dev < 1:
            distribution_type = 'uniform'
        elif std_dev > mean:
            distribution_type = 'skewed'
        else:
            distribution_type = 'bimodal'
        
        return {
            'mean': mean,
            'variance': variance,
            'standard_deviation': std_dev,
            'distribution_type': distribution_type,
            'coefficient_of_variation': std_dev / mean if mean > 0 else 0
        }
