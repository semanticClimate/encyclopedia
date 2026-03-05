#!/usr/bin/env python3
"""
Create a static HTML landing page for casual browsing.

This generates a self-contained HTML file that works offline without any installation.
Perfect for casual users who just want to browse and search entries.

For advanced features (editing, complex operations), use the Streamlit browser:
    streamlit run encyclopedia/browser/app.py

HTML Browser Features:
- Table of Contents (TOC)
- Search functionality with target options
- Statistics dashboard
- Entry display
- Pagination
- Works offline (no server needed)
- No installation required

Usage:
    python Examples/create_landing_page_example.py
"""

from pathlib import Path
from encyclopedia.core.encyclopedia import AmiEncyclopedia
from encyclopedia.utils.resources import Resources


def create_landing_page_html(encyclopedia: AmiEncyclopedia) -> str:
    """
    Create a landing page HTML with TOC, search, statistics, and entry display.
    
    Args:
        encyclopedia: AmiEncyclopedia instance
        
    Returns:
        Complete HTML string for landing page
    """
    entries = encyclopedia.entries
    title = encyclopedia.title
    
    # Calculate statistics
    total_entries = len(entries)
    entries_with_descriptions = sum(1 for e in entries if e.get('description_html'))
    entries_with_images = sum(1 for e in entries if e.get('figure_html') is not None or e.get('image_link'))
    entries_with_wikidata = sum(1 for e in entries if e.get('wikidata_id') and e.get('wikidata_id') not in ('', 'no_wikidata_id'))
    
    # Group entries by first letter
    entries_by_letter = {}
    for entry in entries:
        if entry.get('term'):
            first_letter = entry['term'][0].upper()
            if not first_letter.isalpha():
                first_letter = '0-9'
            if first_letter not in entries_by_letter:
                entries_by_letter[first_letter] = []
            entries_by_letter[first_letter].append(entry)
    
    # Generate TOC HTML
    toc_html = '<div id="toc" class="toc-section">\n'
    toc_html += '<h2>Table of Contents</h2>\n'
    toc_html += '<div class="quick-jump">\n'
    for letter in sorted(entries_by_letter.keys()):
        toc_html += f'<a href="#letter-{letter}" class="quick-jump-link">{letter}</a>\n'
    toc_html += '</div>\n'
    
    for letter in sorted(entries_by_letter.keys()):
        letter_entries = entries_by_letter[letter]
        toc_html += f'<div id="letter-{letter}" class="letter-section">\n'
        toc_html += f'<h3>{letter} <span class="entry-count">({len(letter_entries)})</span></h3>\n'
        toc_html += '<ul class="entry-list">\n'
        for entry in letter_entries:
            term = entry.get('term', '')
            entry_id = f"entry-{term.lower().replace(' ', '-')}"
            has_image = '📷' if (entry.get('figure_html') is not None or entry.get('image_link')) else ''
            has_desc = '📄' if entry.get('description_html') else ''
            toc_html += f'<li><a href="#{entry_id}" class="toc-entry-link">{has_image}{has_desc} {term}</a></li>\n'
        toc_html += '</ul>\n</div>\n'
    toc_html += '</div>\n'
    
    # Generate statistics HTML
    stats_html = f'''
    <div id="statistics" class="statistics-section">
        <h2>Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_entries}</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{entries_with_descriptions}</div>
                <div class="stat-label">With Descriptions ({entries_with_descriptions*100//total_entries if total_entries > 0 else 0}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{entries_with_images}</div>
                <div class="stat-label">With Images ({entries_with_images*100//total_entries if total_entries > 0 else 0}%)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{entries_with_wikidata}</div>
                <div class="stat-label">With Wikidata ({entries_with_wikidata*100//total_entries if total_entries > 0 else 0}%)</div>
            </div>
        </div>
    </div>
    '''
    
    # Generate entries HTML
    entries_html = '<div id="entries" class="entries-section">\n'
    entries_html += '<h2>Entries</h2>\n'
    for entry in entries:
        term = entry.get('term', '')
        entry_id = f"entry-{term.lower().replace(' ', '-')}"
        entries_html += f'<div id="{entry_id}" class="entry-card" role="ami_entry">\n'
        entries_html += f'<h3 class="entry-term">{term}</h3>\n'
        
        if entry.get('wikidata_id') and entry.get('wikidata_id') not in ('', 'no_wikidata_id'):
            entries_html += f'<div class="entry-metadata">Wikidata: <a href="https://www.wikidata.org/wiki/{entry["wikidata_id"]}" target="_blank">{entry["wikidata_id"]}</a></div>\n'
        
        if entry.get('wikipedia_url'):
            entries_html += f'<div class="entry-metadata">Wikipedia: <a href="{entry["wikipedia_url"]}" target="_blank">View Article</a></div>\n'
        
        if entry.get('description_html'):
            entries_html += f'<div class="entry-description">{entry["description_html"]}</div>\n'
        elif entry.get('definition_html'):
            entries_html += f'<div class="entry-definition">{entry["definition_html"]}</div>\n'
        
        if entry.get('synonyms'):
            synonyms = [s for s in entry['synonyms'] if s != term]
            if synonyms:
                entries_html += f'<div class="entry-synonyms">Synonyms: {", ".join(synonyms)}</div>\n'
        
        entries_html += '</div>\n'
    entries_html += '</div>\n'
    
    # Complete HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Landing Page</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        header h1 {{
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .search-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .search-controls {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}
        
        .search-input-wrapper {{
            flex: 1;
            min-width: 200px;
            display: flex;
            gap: 10px;
        }}
        
        #search-box {{
            flex: 1;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #ddd;
            border-radius: 5px;
        }}
        
        #search-box:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .search-options {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }}
        
        .search-option-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        .search-option-group label {{
            font-size: 0.9em;
            font-weight: bold;
            color: #666;
        }}
        
        .search-option-group select {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 0.95em;
        }}
        
        .search-button {{
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .search-button:hover {{
            background: #5568d3;
        }}
        
        .clear-button {{
            padding: 15px 25px;
            background: #999;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .clear-button:hover {{
            background: #777;
        }}
        
        .search-results-info {{
            margin-top: 15px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .back-to-search {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1em;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            display: none;
        }}
        
        .back-to-search.visible {{
            display: block;
        }}
        
        .back-to-search:hover {{
            background: #5568d3;
        }}
        
        .toc-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .quick-jump {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .quick-jump-link {{
            padding: 8px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.3s;
        }}
        
        .quick-jump-link:hover {{
            background: #5568d3;
        }}
        
        .letter-section {{
            margin-bottom: 20px;
        }}
        
        .letter-section h3 {{
            color: #667eea;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #667eea;
        }}
        
        .entry-count {{
            color: #666;
            font-size: 0.8em;
            font-weight: normal;
        }}
        
        .entry-list {{
            list-style: none;
            columns: 3;
            column-gap: 20px;
        }}
        
        .entry-list li {{
            margin-bottom: 5px;
            break-inside: avoid;
        }}
        
        .toc-entry-link {{
            color: #333;
            text-decoration: none;
            padding: 3px 5px;
            border-radius: 3px;
            transition: background 0.2s;
        }}
        
        .toc-entry-link:hover {{
            background: #f0f0f0;
        }}
        
        .statistics-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .stat-card {{
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        
        .entries-section {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .entry-card {{
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            background: #fafafa;
            transition: box-shadow 0.3s;
        }}
        
        .entry-card:hover {{
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        
        .entry-term {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.5em;
        }}
        
        .entry-metadata {{
            margin-bottom: 10px;
            font-size: 0.9em;
            color: #666;
        }}
        
        .entry-metadata a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .entry-metadata a:hover {{
            text-decoration: underline;
        }}
        
        .entry-description, .entry-definition {{
            margin-top: 15px;
            line-height: 1.8;
        }}
        
        .entry-synonyms {{
            margin-top: 10px;
            font-style: italic;
            color: #666;
        }}
        
        .hidden {{
            display: none;
        }}
        
        @media (max-width: 768px) {{
            .entry-list {{
                columns: 1;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <p style="text-align: center; opacity: 0.9;">Encyclopedia Landing Page</p>
        </div>
    </header>
    
    <div class="container">
        <div class="search-section">
            <div class="search-controls">
                <div class="search-input-wrapper">
                    <input type="text" id="search-box" placeholder="Search entries... (e.g., climate, atom, DNA)" autocomplete="off">
                    <button class="search-button" id="search-button">Search</button>
                    <button class="clear-button" id="clear-button">Clear</button>
                </div>
            </div>
            <div class="search-options">
                <div class="search-option-group">
                    <label for="search-target">Search In:</label>
                    <select id="search-target">
                        <option value="all">All Fields</option>
                        <option value="term">Term Only</option>
                        <option value="definition">Definition Only</option>
                        <option value="description">Description Only</option>
                    </select>
                </div>
                <div class="search-option-group">
                    <label for="search-type">Search Type:</label>
                    <select id="search-type">
                        <option value="partial">Partial Match</option>
                        <option value="exact">Exact Match</option>
                        <option value="regex">Regular Expression</option>
                        <option value="word">Whole Word</option>
                    </select>
                </div>
            </div>
            <div id="search-results-info" class="search-results-info" style="display: none;"></div>
        </div>
        
        <button id="back-to-search" class="back-to-search" title="Back to Search (Esc)">↑ Back to Search</button>
        
        {stats_html}
        
        {toc_html}
        
        {entries_html}
    </div>
    
    <script>
        // Search functionality
        const searchBox = document.getElementById('search-box');
        const searchButton = document.getElementById('search-button');
        const clearButton = document.getElementById('clear-button');
        const searchTarget = document.getElementById('search-target');
        const searchType = document.getElementById('search-type');
        const searchResultsInfo = document.getElementById('search-results-info');
        const backToSearchButton = document.getElementById('back-to-search');
        const entryCards = document.querySelectorAll('.entry-card');
        const tocLinks = document.querySelectorAll('.toc-entry-link');
        const searchSection = document.querySelector('.search-section');
        
        let currentSearchQuery = '';
        let searchTimeout = null;
        
        // Extract plain text from HTML
        function extractText(html) {{
            if (!html) return '';
            const div = document.createElement('div');
            div.innerHTML = html;
            return div.textContent || div.innerText || '';
        }}
        
        // Search function
        function performSearch(query) {{
            if (!query || query.trim() === '') {{
                // Show all entries
                entryCards.forEach(card => {{
                    card.classList.remove('hidden');
                }});
                searchResultsInfo.style.display = 'none';
                backToSearchButton.classList.remove('visible');
                return;
            }}
            
            const target = searchTarget.value;
            const type = searchType.value;
            const searchTerm = query.trim();
            let regex = null;
            
            // Build regex based on search type
            try {{
                if (type === 'exact') {{
                    regex = new RegExp('^' + searchTerm.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + '$', 'i');
                }} else if (type === 'regex') {{
                    regex = new RegExp(searchTerm, 'i');
                }} else if (type === 'word') {{
                    regex = new RegExp('\\\\b' + searchTerm.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b', 'i');
                }} else {{ // partial
                    regex = new RegExp(searchTerm.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&'), 'i');
                }}
            }} catch (e) {{
                searchResultsInfo.textContent = 'Invalid regular expression';
                searchResultsInfo.style.display = 'block';
                return;
            }}
            
            let matchCount = 0;
            
            entryCards.forEach(card => {{
                const term = card.querySelector('.entry-term').textContent;
                const definitionElem = card.querySelector('.entry-definition');
                const descriptionElem = card.querySelector('.entry-description');
                const definition = definitionElem ? extractText(definitionElem.innerHTML) : '';
                const description = descriptionElem ? extractText(descriptionElem.innerHTML) : '';
                
                let matches = false;
                
                // Check based on search target
                if (target === 'term') {{
                    matches = regex.test(term);
                }} else if (target === 'definition') {{
                    matches = regex.test(definition);
                }} else if (target === 'description') {{
                    matches = regex.test(description);
                }} else {{ // all
                    matches = regex.test(term) || regex.test(definition) || regex.test(description);
                }}
                
                if (matches) {{
                    card.classList.remove('hidden');
                    matchCount++;
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
            
            // Update results info
            if (matchCount > 0) {{
                searchResultsInfo.textContent = `Found ${{matchCount}} ${{matchCount === 1 ? 'entry' : 'entries'}}`;
                searchResultsInfo.style.display = 'block';
                backToSearchButton.classList.add('visible');
                
                // Scroll to first result
                const firstVisible = Array.from(entryCards).find(card => !card.classList.contains('hidden'));
                if (firstVisible) {{
                    setTimeout(() => {{
                        firstVisible.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}, 100);
                }}
            }} else {{
                searchResultsInfo.textContent = 'No entries found';
                searchResultsInfo.style.display = 'block';
                backToSearchButton.classList.add('visible');
            }}
            
            currentSearchQuery = query;
        }}
        
        // Search button click
        searchButton.addEventListener('click', () => {{
            performSearch(searchBox.value);
        }});
        
        // Clear button click
        clearButton.addEventListener('click', () => {{
            searchBox.value = '';
            performSearch('');
            searchBox.focus();
        }});
        
        // Enter key in search box
        searchBox.addEventListener('keydown', (e) => {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                performSearch(searchBox.value);
            }} else if (e.key === 'Escape') {{
                clearButton.click();
            }}
            // Let normal key events (including backspace) work normally
        }});
        
        // Real-time search with debouncing
        searchBox.addEventListener('input', (e) => {{
            // Clear previous timeout
            if (searchTimeout) {{
                clearTimeout(searchTimeout);
            }}
            
            // Debounce search
            searchTimeout = setTimeout(() => {{
                performSearch(e.target.value);
            }}, 300); // Wait 300ms after user stops typing
        }});
        
        // Back to search button
        backToSearchButton.addEventListener('click', () => {{
            searchSection.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
            searchBox.focus();
        }});
        
        // Keyboard shortcut: Esc to clear, Ctrl+F or Cmd+F to focus search
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && searchBox.value) {{
                clearButton.click();
            }} else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
                e.preventDefault();
                searchBox.focus();
                searchBox.select();
            }}
        }});
        
        // Smooth scrolling for TOC links
        tocLinks.forEach(link => {{
            link.addEventListener('click', (e) => {{
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>
'''
    
    return html


def main():
    """Create example landing page from cached encyclopedia."""
    # Try to load from cache
    cache_dir = Path(Path(__file__).parent.parent, "test", "encyclopedia", "fixtures", "cache")
    cache_files = list(cache_dir.glob("encyclopedia_*.html"))
    
    if not cache_files:
        print("No cached encyclopedia found. Please run tests first to create cached encyclopedias.")
        return
    
    # Load first cached encyclopedia
    cache_file = cache_files[0]
    print(f"Loading encyclopedia from cache: {cache_file.name}")
    encyclopedia = AmiEncyclopedia()
    encyclopedia.create_from_html_file(cache_file)
    
    print(f"\nCreating landing page for '{encyclopedia.title}' with {len(encyclopedia.entries)} entries...")
    
    # Generate landing page HTML
    landing_page_html = create_landing_page_html(encyclopedia)
    
    # Save to temp directory
    output_dir = Resources.get_temp_dir("examples", "landing_page")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = encyclopedia.title.lower().replace(' ', '_')
    output_file = Path(output_dir, f"{safe_title}_landing_page.html")
    
    output_file.write_text(landing_page_html, encoding='utf-8')
    
    print(f"\n✓ Landing page created successfully!")
    print(f"  File: {output_file}")
    print(f"  Entries: {len(encyclopedia.entries)}")
    print(f"\nOpen in browser to view: file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
