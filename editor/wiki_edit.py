import argparse
import os
from bs4 import BeautifulSoup
import requests

# ---------------- Load HTML dictionary ----------------
def load_dictionary(file_path):
    """Load HTML dictionary and return BeautifulSoup object"""
    if not os.path.exists(file_path):
        print(f"⚠️ File '{file_path}' not found. Creating new HTML file...")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("<html><body><div role='ami_dictionary' title='user_dict'></div></body></html>")
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup

# ---------------- Fetch Wikipedia HTML ----------------
import requests
from bs4 import BeautifulSoup

def fetch_definition_html(term):
    """
    Fetch the first meaningful paragraph from Wikipedia.
    Returns: tuple (definition_html, image_html)
    """
    url = f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return ("No Wikipedia page found for this term.", "")

        soup = BeautifulSoup(response.text, "html.parser")
        content = soup.find("div", class_="mw-parser-output")
        if not content:
            return ("No content found.", "")

        # Recursively search for the first meaningful <p>
        first_para = None
        for p in content.find_all("p"):
            text = p.get_text(strip=True)
            if text and not p.find_parents("table"):  # skip paragraphs inside tables/infobox
                first_para = str(p)
                break

        if not first_para:
            first_para = "(No definition found)"

        # Optional first image (skip infobox)
        img_div = ""
        thumb_div = content.find("div", class_="thumb")
        if thumb_div:
            img_tag = thumb_div.find("img")
            if img_tag:
                img_src = "https:" + img_tag.get("src")
                img_div = f'<div title="figure"><figure><img src="{img_src}"><figcaption>{term} image</figcaption></figure></div>'

        return first_para, img_div

    except Exception as e:
        return (f"Error fetching HTML definition: {str(e)}", "")




# ---------------- View Entry ----------------
def view_entry(args):
    soup = load_dictionary(args.file)
    entries = soup.find_all("div", role="ami_entry")
    if args.word:
        word_input = ' '.join(args.word.strip().split()).lower()
        found = False
        for entry in entries:
            term = entry.get("term") or entry.get("name")
            if term and term.lower() == word_input:
                # Heading
                heading_p = entry.find("p")
                heading_text = heading_p.get_text(" ", strip=True) if heading_p else ""
                print(f"\n📖 {heading_text}")

                # Definition
                def_p = entry.find("p", class_="wpage_first_para")
                def_text = def_p.get_text(" ", strip=True) if def_p else "(No definition)"
                print(f"\n{def_text}\n")

                # Optional image
                figure_div = entry.find("div", title="figure")
                if figure_div:
                    img_tag = figure_div.find("img")
                    if img_tag:
                        print(f"[Image URL: {img_tag.get('src')}]")
                found = True
                break
        if not found:
            print("❌ Word not found.")
    else:
        if not entries:
            print("⚠️ Dictionary is empty.")
        else:
            print("\n📚 All entries:")
            for i, entry in enumerate(entries, 1):
                term = entry.get("term") or entry.get("name")
                def_p = entry.find("p", class_="wpage_first_para")
                def_text = (def_p.get_text(" ", strip=True)[:150] + "...") if def_p else "(No definition)"
                print(f"{i}. {term}: {def_text}")

# ---------------- Add Entry ----------------
def add_entry(args):
    soup = load_dictionary(args.file)
    word = args.word.strip()
    dict_div = soup.find("div", role="ami_dictionary")
    if not dict_div:
        dict_div = soup.new_tag("div", attrs={"role": "ami_dictionary", "title": "user_dict"})
        soup.body.append(dict_div)

    # Check if word exists
    for entry in dict_div.find_all("div", role="ami_entry"):
        term = entry.get("term") or entry.get("name")
        if term and term.lower() == word.lower():
            print("⚠️ Word already exists!")
            return

    # Get definition
    if args.fetch:
        print(f"🔍 Fetching definition for '{word}' from Wikipedia...")
        definition_html, image_html = fetch_definition_html(word)
        print("✅ Fetched HTML successfully.")
    else:
        definition_html = args.definition.strip() if args.definition else input("Enter definition (HTML allowed): ").strip()
        image_html = ""

    # Create new entry
    entry_div = soup.new_tag("div", attrs={"role": "ami_entry", "name": word, "term": word})

    # First <p> - search term heading
    heading_p = soup.new_tag("p")
    heading_p.string = f"search term: {word} "
    wiki_link = soup.new_tag("a", href=f"https://en.wikipedia.org/w/index.php?search={word}")
    wiki_link.string = "Wikipedia Page"
    heading_p.append(wiki_link)
    entry_div.append(heading_p)

    # Second <p> - definition
    def_p = soup.new_tag("p", attrs={"class": "wpage_first_para"})
    def_p.append(BeautifulSoup(definition_html, "html.parser"))
    entry_div.append(def_p)

    # Optional figure
    if image_html:
        entry_div.append(BeautifulSoup(image_html, "html.parser"))

    dict_div.append(entry_div)

    with open(args.file, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))
    print("✅ Added successfully.")

# ---------------- Update Entry ----------------
def update_entry(args):
    soup = load_dictionary(args.file)
    entries = soup.find_all("div", role="ami_entry")
    word_input = ' '.join(args.word.strip().split()).lower()
    entry_div = None
    for entry in entries:
        term = entry.get("term") or entry.get("name")
        if term and term.lower() == word_input:
            entry_div = entry
            break
    if not entry_div:
        print("❌ Word not found.")
        return

    def_p = entry_div.find("p", class_="wpage_first_para")
    if not def_p:
        def_p = soup.new_tag("p", attrs={"class": "wpage_first_para"})
        entry_div.append(def_p)

    if args.fetch:
        print(f"🔍 Fetching definition for '{word_input}' from Wikipedia...")
        new_def, new_img = fetch_definition_html(word_input)
        print("✅ Fetched HTML successfully.")
    else:
        new_def = args.definition.strip() if args.definition else input(f"Current definition:\n{def_p.get_text(' ', strip=True)}\nEnter new definition (HTML allowed): ").strip()
        new_img = ""

    def_p.clear()
    def_p.append(BeautifulSoup(new_def, "html.parser"))

    # Remove old figure and append new figure if exists
    old_figure = entry_div.find("div", title="figure")
    if old_figure:
        old_figure.decompose()
    if new_img:
        entry_div.append(BeautifulSoup(new_img, "html.parser"))

    with open(args.file, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))
    print("✅ Definition updated successfully.")

# ---------------- Delete Entry ----------------
def delete_entry(args):
    soup = load_dictionary(args.file)
    entries = soup.find_all("div", role="ami_entry")
    word_input = ' '.join(args.word.strip().split()).lower()
    entry_div = None
    for entry in entries:
        term = entry.get("term") or entry.get("name")
        if term and term.lower() == word_input:
            entry_div = entry
            break
    if not entry_div:
        print("❌ Word not found.")
        return

    entry_div.decompose()
    with open(args.file, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))
    print("✅ Deleted successfully.")

# ---------------- CLI ----------------
def main():
    parser = argparse.ArgumentParser(description="📚 Wikipedia Dictionary CLI Editor")
    parser.add_argument("file", help="Path to HTML dictionary file")
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    parser_view = subparsers.add_parser("view", help="View all entries or a specific word")
    parser_view.add_argument("word", nargs="?", help="Word to view (optional)")

    parser_add = subparsers.add_parser("add", help="Add a new entry")
    parser_add.add_argument("word", help="Word to add")
    parser_add.add_argument("definition", nargs="?", help="Definition (optional if using --fetch)")
    parser_add.add_argument("--fetch", action="store_true", help="Fetch definition from Wikipedia")

    parser_update = subparsers.add_parser("update", help="Update an existing entry")
    parser_update.add_argument("word", help="Word to update")
    parser_update.add_argument("definition", nargs="?", help="New definition (optional)")
    parser_update.add_argument("--fetch", action="store_true", help="Fetch definition from Wikipedia")

    parser_delete = subparsers.add_parser("delete", help="Delete an entry")
    parser_delete.add_argument("word", help="Word to delete")

    args = parser.parse_args()

    if args.command == "view":
        view_entry(args)
    elif args.command == "add":
        add_entry(args)
    elif args.command == "update":
        update_entry(args)
    elif args.command == "delete":
        delete_entry(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()






