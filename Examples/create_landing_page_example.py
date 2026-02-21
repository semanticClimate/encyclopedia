#!/usr/bin/env python3
"""
Create an example landing page HTML file from an encyclopedia.

This creates a basic landing page with:
- Table of Contents (TOC)
- Search functionality
- Statistics dashboard
- Entry display
- Pagination

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
        }}
        
        #search-box {{
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            border: 2px solid #ddd;
            border-radius: 5px;
        }}
        
        #search-box:focus {{
            outline: none;
            border-color: #667eea;
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
            <input type="text" id="search-box" placeholder="Search entries... (e.g., climate, atom, DNA)">
        </div>
        
        {stats_html}
        
        {toc_html}
        
        {entries_html}
    </div>
    
    <script>
        // Simple client-side search
        const searchBox = document.getElementById('search-box');
        const entryCards = document.querySelectorAll('.entry-card');
        const tocLinks = document.querySelectorAll('.toc-entry-link');
        
        function searchEntries(query) {{
            const searchTerm = query.toLowerCase().trim();
            
            entryCards.forEach(card => {{
                const term = card.querySelector('.entry-term').textContent.toLowerCase();
                const description = card.querySelector('.entry-description, .entry-definition')?.textContent.toLowerCase() || '';
                
                if (searchTerm === '' || term.includes(searchTerm) || description.includes(searchTerm)) {{
                    card.classList.remove('hidden');
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
        }}
        
        searchBox.addEventListener('input', (e) => {{
            searchEntries(e.target.value);
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
    cache_dir = Path(__file__).parent.parent / "test" / "encyclopedia" / "fixtures" / "cache"
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
    output_file = output_dir / f"{safe_title}_landing_page.html"
    
    output_file.write_text(landing_page_html, encoding='utf-8')
    
    print(f"\n✓ Landing page created successfully!")
    print(f"  File: {output_file}")
    print(f"  Entries: {len(encyclopedia.entries)}")
    print(f"\nOpen in browser to view: file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
