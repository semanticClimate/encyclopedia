"""
Indexer for building and managing Whoosh search indexes.

Builds searchable indexes from encyclopedia HTML files.
"""

from pathlib import Path
from typing import List, Optional
import re

# Check for required dependencies
try:
    from lxml.html import fromstring, tostring
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    raise ImportError(
        "lxml is required but not installed. "
        "Install with: pip install lxml"
    )

try:
    from whoosh import index
    from whoosh.fields import Schema, TEXT, ID, STORED, KEYWORD, NUMERIC
    from whoosh.analysis import StemmingAnalyzer
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False
    raise ImportError(
        "whoosh is required but not installed. "
        "Install with: pip install whoosh"
    )

from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.browser.models import EncyclopediaEntry


class EncyclopediaIndexer:
    """Builds and manages Whoosh search indexes for encyclopedias."""
    
    # Whoosh Schema
    SCHEMA = Schema(
        entry_id=ID(stored=True, unique=True),
        term=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        search_terms=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        canonical_term=TEXT(stored=True),
        wikidata_id=ID(stored=True),
        wikipedia_url=STORED,
        description_html=STORED,  # Full HTML content
        description_text=TEXT(analyzer=StemmingAnalyzer()),  # Plain text for search
        synonyms=KEYWORD(stored=True, commas=True),
        category=KEYWORD(stored=True),
        entry_index=NUMERIC(stored=True),
    )
    
    def __init__(self, index_dir: Optional[Path] = None):
        """Initialize indexer.
        
        Args:
            index_dir: Directory to store index files (default: temp directory)
        """
        if index_dir is None:
            import tempfile
            index_dir = Path(tempfile.gettempdir()) / "encyclopedia_index"
        
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self._index = None
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text for searching.
        
        Args:
            html_content: HTML string
            
        Returns:
            Plain text content
        """
        if not html_content:
            return ""
        
        try:
            # Parse HTML and extract text
            doc = fromstring(html_content)
            # Remove script and style elements
            for script in doc.xpath("//script | //style"):
                script.getparent().remove(script)
            # Get text content
            text = doc.text_content()
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            # Fallback: simple regex removal of HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    
    def build_index_from_encyclopedia(self, encyclopedia: AmiEncyclopedia, 
                                      index_name: str = "encyclopedia") -> Path:
        """Build search index from AmiEncyclopedia instance.
        
        Args:
            encyclopedia: AmiEncyclopedia instance
            index_name: Name for the index
            
        Returns:
            Path to the index directory
        """
        # Create index directory
        index_path = self.index_dir / index_name
        index_path.mkdir(parents=True, exist_ok=True)
        
        # Create or open index
        if index.exists_in(str(index_path)):
            idx = index.open_dir(str(index_path))
        else:
            idx = index.create_in(str(index_path), self.SCHEMA)
        
        writer = idx.writer()
        
        # Index all entries
        for idx_num, entry_dict in enumerate(encyclopedia.entries):
            # Extract entry data
            term = entry_dict.get('term', entry_dict.get('search_term', ''))
            search_term = entry_dict.get('search_term', term)
            canonical_term = entry_dict.get('canonical_term', term)
            wikidata_id = entry_dict.get('wikidata_id', '')
            wikipedia_url = entry_dict.get('wikipedia_url', '')
            description_html = entry_dict.get('description_html', '')
            description_text = self._html_to_text(description_html)
            
            # Get synonyms
            synonyms = entry_dict.get('synonyms', [])
            if isinstance(synonyms, str):
                synonyms = [synonyms]
            elif not isinstance(synonyms, list):
                synonyms = []
            
            # Generate entry ID
            entry_id = wikidata_id if wikidata_id else f"entry_{idx_num}"
            
            # Add to index
            writer.add_document(
                entry_id=str(entry_id),
                term=term,
                search_terms=search_term,
                canonical_term=canonical_term,
                wikidata_id=str(wikidata_id) if wikidata_id else "",
                wikipedia_url=wikipedia_url,
                description_html=description_html,
                description_text=description_text,
                synonyms=",".join(synonyms) if synonyms else "",
                category="",
                entry_index=idx_num,
            )
        
        writer.commit()
        self._index = idx
        
        return index_path
    
    def build_index_from_html_file(self, html_file: Path, 
                                   index_name: str = "encyclopedia") -> Path:
        """Build search index from encyclopedia HTML file.
        
        Supports both dictionary format (role='ami_dictionary') and 
        encyclopedia format (role='ami_encyclopedia') HTML files.
        
        Args:
            html_file: Path to encyclopedia HTML file
            index_name: Name for the index
            
        Returns:
            Path to the index directory
        """
        # Check HTML format first
        html_content = html_file.read_text(encoding='utf-8')
        html_root = fromstring(html_content.encode('utf-8'))
        
        # Check if it's encyclopedia format or dictionary format
        encyclopedia_div = html_root.xpath(".//div[@role='ami_encyclopedia']")
        dictionary_div = html_root.xpath(".//div[@role='ami_dictionary']")
        
        if encyclopedia_div:
            # It's encyclopedia format - extract entries directly
            return self._build_index_from_encyclopedia_html(html_file, index_name)
        elif dictionary_div:
            # It's dictionary format - use standard method
            encyclopedia = AmiEncyclopedia()
            encyclopedia.create_from_html_file(html_file)
            return self.build_index_from_encyclopedia(encyclopedia, index_name)
        else:
            raise ValueError(
                "HTML file must contain div with role='ami_dictionary' or role='ami_encyclopedia'"
            )
    
    def _build_index_from_encyclopedia_html(self, html_file: Path,
                                            index_name: str = "encyclopedia") -> Path:
        """Build index directly from encyclopedia format HTML.
        
        Args:
            html_file: Path to encyclopedia HTML file
            index_name: Name for the index
            
        Returns:
            Path to the index directory
        """
        # Parse HTML
        html_content = html_file.read_text(encoding='utf-8')
        html_root = fromstring(html_content.encode('utf-8'))
        
        # Find encyclopedia container
        encyclopedia_divs = html_root.xpath(".//div[@role='ami_encyclopedia']")
        if not encyclopedia_divs:
            raise ValueError("No encyclopedia container found in HTML")
        
        encyclopedia_div = encyclopedia_divs[0]
        title = encyclopedia_div.get('title', 'Encyclopedia')
        
        # Find all entry divs
        entry_divs = encyclopedia_div.xpath(".//div[@role='ami_entry']")
        
        # Create index directory
        index_path = self.index_dir / index_name
        index_path.mkdir(parents=True, exist_ok=True)
        
        # Create or open index
        if index.exists_in(str(index_path)):
            idx = index.open_dir(str(index_path))
        else:
            idx = index.create_in(str(index_path), self.SCHEMA)
        
        writer = idx.writer()
        
        # Index all entries
        for idx_num, entry_div in enumerate(entry_divs):
            # Extract entry data from div attributes and content
            term = entry_div.get('term', '')
            if not term:
                # Try to get from text content
                term_text = entry_div.text_content().strip() if hasattr(entry_div, 'text_content') else ''
                if term_text:
                    term = term_text.split('\n')[0].strip()
            
            if not term:
                continue  # Skip entries without terms
            
            # Get Wikidata ID
            wikidata_id = (
                entry_div.get('wikidataID') or 
                entry_div.get('wikidataid') or 
                entry_div.get('wikidata_id') or 
                ''
            )
            
            # Extract Wikipedia URL from links
            wikipedia_url = ''
            wiki_links = entry_div.xpath(".//a[contains(@href, 'wikipedia.org/wiki/')]")
            if wiki_links:
                wikipedia_url = wiki_links[0].get('href', '')
            
            # Extract description HTML
            description_html = ''
            # Get all content except checkboxes and metadata
            desc_elements = []
            for child in entry_div:
                # Skip checkbox containers and metadata
                if child.tag == 'div' and child.get('class') == 'entry-checkboxes':
                    continue
                if child.tag == 'div' and child.get('class') == 'wikidata-category':
                    continue
                # Include other content
                desc_elements.append(child)
            
            if desc_elements:
                # Convert elements to HTML string
                from amilib.xml_lib import XmlLib
                description_html = ''.join([
                    XmlLib.element_to_string(elem) for elem in desc_elements
                ])
            
            description_text = self._html_to_text(description_html)
            
            # Extract synonyms from list if present
            synonyms = []
            synonym_lists = entry_div.xpath(".//ul[@class='synonym_list']//li")
            for li in synonym_lists:
                synonym_text = li.text_content().strip() if hasattr(li, 'text_content') else (li.text or '').strip()
                if synonym_text:
                    synonyms.append(synonym_text)
            
            # Generate entry ID
            entry_id = wikidata_id if wikidata_id else f"entry_{idx_num}"
            
            # Add to index
            writer.add_document(
                entry_id=str(entry_id),
                term=term,
                search_terms=term,  # Use term as search term
                canonical_term=term,
                wikidata_id=str(wikidata_id) if wikidata_id else "",
                wikipedia_url=wikipedia_url,
                description_html=description_html,
                description_text=description_text,
                synonyms=",".join(synonyms) if synonyms else "",
                category="",
                entry_index=idx_num,
            )
        
        writer.commit()
        self._index = idx
        
        return index_path
    
    def get_index(self, index_name: str = "encyclopedia"):
        """Get or open search index.
        
        Args:
            index_name: Name of the index
            
        Returns:
            Whoosh index object
        """
        if self._index is None:
            index_path = self.index_dir / index_name
            if index.exists_in(str(index_path)):
                self._index = index.open_dir(str(index_path))
            else:
                raise ValueError(f"Index '{index_name}' not found. Build it first.")
        
        return self._index
    
    def index_exists(self, index_name: str = "encyclopedia") -> bool:
        """Check if index exists.
        
        Args:
            index_name: Name of the index
            
        Returns:
            True if index exists, False otherwise
        """
        index_path = self.index_dir / index_name
        return index.exists_in(str(index_path))
