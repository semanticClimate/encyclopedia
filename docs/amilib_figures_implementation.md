# Amilib Figures Implementation

## How Amilib Handles `--figures` Flag

When `amilib DICT --figures` is used, the following process occurs:

### 1. Entry Point: `AmiDictArgs.add_figures()` (dict_args.py:356-372)

```python
def add_figures(self):
    for entry_elem in self.ami_dict.entries:
        ami_entry = AmiEntry.create_from_element(entry_elem)
        wikipedia_page = ami_entry.lookup_and_add_wikipedia_page()
        if wikipedia_page is not None:
            ami_entry.add_figures_to_entry(wikipedia_page)
```

### 2. Core Method: `AmiEntry.add_figures_to_entry()` (ami_dict.py:563-584)

```python
def add_figures_to_entry(self, wikipedia_page):
    term = self.get_term()
    if wikipedia_page is None:
        logger.warning(f"no wikipedia page for {term}")
        return
    self.add_figures_from_wikipedia(term, wikipedia_page)
```

### 3. Figure Extraction: `AmiEntry.add_figures_from_wikipedia()` (ami_dict.py:586-602)

**Key Implementation:**

```python
def add_figures_from_wikipedia(self, term, wikipedia_page):
    """
    extract figures from Wikipedia page, either infobox or first thumbnail
    """
    # Step 1: Try to get <a> element with image from infobox
    a_elem = wikipedia_page.extract_a_elem_with_image_from_infobox()
    
    # Step 2: If no infobox image, look for <figure> elements
    figures = wikipedia_page.html_elem.xpath(".//figure")
    
    if a_elem is None and len(figures) == 0:
        logger.info(f"NO FIGURES for {term}")
        return
    
    # Step 3: Create wrapper div
    figure_div = ET.SubElement(self.element, "div")
    figure_div.attrib["title"] = "figure"
    
    # Step 4: Copy the figure element using deepcopy
    if a_elem is not None:
        figure_div.append(copy.deepcopy(a_elem))
        logger.info(f"added figure {a_elem} for {term}")
    elif len(figures) > 0:
        figure_div.append(copy.deepcopy(figures[0]))
```

### 4. Infobox Image Extraction: `WikipediaPage.extract_a_elem_with_image_from_infobox()` (wikimedia.py:1761-1780)

```python
def extract_a_elem_with_image_from_infobox(self):
    infobox = self.get_infobox()
    if infobox is None:
        logger.warning("no infobox")
        return None
    
    table = infobox.get_table()
    if table is None:
        logger.warning("no table in infobox")
        return None
    
    # Find <td> elements containing <span><a><img>
    figure_td_xpath = "tbody/tr/td[span[a[img]]]"
    figure_tds = table.xpath(figure_td_xpath)
    if len(figure_tds) == 0:
        logger.warning("no a elems with img in infobox table")
        return None
    
    td0 = figure_tds[0]
    a_elem = self.get_a_with_image_and_caption(td0)
    return a_elem
```

## Key Points

1. **Direct Embedding**: Amilib **embeds the actual `<a>` element** (containing `<img>`) directly into the dictionary entry, not just a link URL.

2. **Uses `copy.deepcopy()`**: The figure element is copied from the Wikipedia page's HTML tree into the dictionary entry's XML tree using `copy.deepcopy()`.

3. **Wrapper Div**: Creates a `<div title="figure">` wrapper around the figure.

4. **Fallback Strategy**:
   - First tries: infobox image (`extract_a_elem_with_image_from_infobox()`)
   - Falls back to: first `<figure>` element in the page

5. **Element Structure**: The `<a>` element contains an `<img>` element with the actual image source URL, so the image is embedded directly in the HTML.

## What Needs to Change in Encyclopedia

The encyclopedia currently:
- Only stores `image_link` (URL string)
- Creates a link element when rendering HTML
- Does NOT embed the actual image element

**Should be changed to:**
- Extract the `<a>` element (or `<figure>`) using the same amilib methods
- Store it as `figure_html` using `copy.deepcopy()`
- When rendering HTML, properly copy it to the new document context (already fixed)
- The image will be embedded directly, not just linked

## Implementation Steps

1. Update `add_images_feature()` in `encyclopedia/cli/versioned_editor.py` to:
   - Use `wikipedia_page.extract_a_elem_with_image_from_infobox()` 
   - Fallback to `wikipedia_page.html_elem.xpath(".//figure")`
   - Use `copy.deepcopy()` to store the element
   - Store as `figure_html` in entry dictionary

2. The HTML rendering code (already fixed) will then properly copy the element to the output HTML.
