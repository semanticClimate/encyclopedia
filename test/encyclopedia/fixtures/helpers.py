"""
Helper functions for creating test entries with various configurations.

These helpers create entry dictionaries that match the structure expected
by AmiEncyclopedia, allowing tests to create entries with specific
characteristics (with/without descriptions, images, synonyms, etc.).
"""

from typing import Dict, List, Optional
from lxml import etree as ET


def create_entry_with_all_fields(
    term: str,
    canonical_term: Optional[str] = None,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None,
    description_html: Optional[str] = None,
    definition_html: Optional[str] = None,
    figure_html: Optional[ET.Element] = None,
    image_link: Optional[str] = None,
    synonyms: Optional[List[str]] = None
) -> Dict:
    """
    Create a complete entry with all fields populated.
    
    Args:
        term: Primary term
        canonical_term: Canonical term (defaults to term)
        wikidata_id: Wikidata Q/P ID (e.g., "Q7937")
        wikipedia_url: Full Wikipedia URL
        description_html: HTML description paragraph
        definition_html: HTML definition (first sentence)
        figure_html: Image element (lxml) or None
        image_link: Image URL or None
        synonyms: List of synonym terms
        
    Returns:
        Entry dictionary matching AmiEncyclopedia entry structure
    """
    entry = {
        'term': term,
        'canonical_term': canonical_term or term,
        'wikidata_id': wikidata_id or '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': description_html or f'<p>{term} is an important concept.</p>',
        'definition_html': definition_html or f'{term} is a concept.',
        'synonyms': synonyms or []
    }
    
    if figure_html is not None:
        entry['figure_html'] = figure_html
    if image_link:
        entry['image_link'] = image_link
    
    return entry


def create_entry_without_description(
    term: str,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None,
    image_link: Optional[str] = None
) -> Dict:
    """
    Create entry without description (missing content scenario).
    
    Args:
        term: Primary term
        wikidata_id: Wikidata Q/P ID
        wikipedia_url: Full Wikipedia URL
        image_link: Image URL or None
        
    Returns:
        Entry dictionary without description_html
    """
    entry = {
        'term': term,
        'canonical_term': term,
        'wikidata_id': wikidata_id or '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': None,
        'definition_html': None,
        'synonyms': []
    }
    
    if image_link:
        entry['image_link'] = image_link
    
    return entry


def create_entry_without_image(
    term: str,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None,
    description_html: Optional[str] = None
) -> Dict:
    """
    Create entry without image (missing image scenario).
    
    Args:
        term: Primary term
        wikidata_id: Wikidata Q/P ID
        wikipedia_url: Full Wikipedia URL
        description_html: HTML description paragraph
        
    Returns:
        Entry dictionary without figure_html or image_link
    """
    entry = {
        'term': term,
        'canonical_term': term,
        'wikidata_id': wikidata_id or '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': description_html or f'<p>{term} is an important concept.</p>',
        'definition_html': f'{term} is a concept.',
        'synonyms': []
    }
    
    return entry


def create_entry_with_synonyms(
    term: str,
    synonyms: List[str],
    canonical_term: Optional[str] = None,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None,
    description_html: Optional[str] = None
) -> Dict:
    """
    Create entry with synonyms (merged entry scenario).
    
    Args:
        term: Primary term
        synonyms: List of synonym terms (includes term itself)
        canonical_term: Canonical term (defaults to term)
        wikidata_id: Wikidata Q/P ID
        wikipedia_url: Full Wikipedia URL
        description_html: HTML description paragraph
        
    Returns:
        Entry dictionary with synonyms list populated
    """
    entry = {
        'term': term,
        'canonical_term': canonical_term or term,
        'wikidata_id': wikidata_id or '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': description_html or f'<p>{term} is an important concept.</p>',
        'definition_html': f'{term} is a concept.',
        'synonyms': synonyms
    }
    
    return entry


def create_entry_with_definition(
    term: str,
    definition: str,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None
) -> Dict:
    """
    Create entry with definition only (no full description).
    
    Args:
        term: Primary term
        definition: First sentence definition
        wikidata_id: Wikidata Q/P ID
        wikipedia_url: Full Wikipedia URL
        
    Returns:
        Entry dictionary with definition_html but no description_html
    """
    entry = {
        'term': term,
        'canonical_term': term,
        'wikidata_id': wikidata_id or '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': None,
        'definition_html': definition,
        'synonyms': []
    }
    
    return entry


def create_minimal_entry(
    term: str,
    wikipedia_url: Optional[str] = None
) -> Dict:
    """
    Create minimal entry with only term and Wikipedia URL.
    
    Args:
        term: Primary term
        wikipedia_url: Full Wikipedia URL
        
    Returns:
        Minimal entry dictionary
    """
    entry = {
        'term': term,
        'canonical_term': term,
        'wikidata_id': '',
        'wikipedia_url': wikipedia_url or f'https://en.wikipedia.org/wiki/{term.replace(" ", "_")}',
        'description_html': None,
        'definition_html': None,
        'synonyms': []
    }
    
    return entry


def create_image_element(image_url: str, alt_text: Optional[str] = None) -> ET.Element:
    """
    Create an lxml image element for testing.
    
    Args:
        image_url: URL of the image
        alt_text: Alt text for the image
        
    Returns:
        lxml Element representing an image
    """
    figure = ET.Element('figure')
    img = ET.SubElement(figure, 'img')
    img.set('src', image_url)
    if alt_text:
        img.set('alt', alt_text)
    return figure
