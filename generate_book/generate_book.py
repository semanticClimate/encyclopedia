#!/usr/bin/env python3
"""
generate_book.py
---------------------------------
Generate a beautiful encyclopedia-style PDF book from an HTML file.

Supports both interactive and command-line modes.

Author: Udita Agarwal
"""

import os
import sys
import argparse
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


# ---------- Argument Parser ----------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a styled encyclopedia PDF from an HTML file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--title", "-t", help="Title of the book", type=str)
    parser.add_argument("--author", "-a", help="Author name", type=str)
    parser.add_argument("--desc", "-d", help="Short description of the book", type=str)
    parser.add_argument("--input", "-i", help="Path to input HTML file", type=str)
    parser.add_argument("--output", "-o", help="Path to output PDF file", type=str, default="encyclopedia_book.pdf")
    return parser.parse_args()


# ---------- Helper Functions ----------
def normalize_path(path: str) -> str:
    if not path:
        return ""
    path = path.strip().strip('"').strip("'")
    return os.path.normpath(os.path.expanduser(path))


def fix_wikimedia_url(url: str) -> str:
    """Ensure Wikimedia and protocol-relative URLs work properly."""
    if url.startswith("//"):
        url = "https:" + url
    if "upload.wikimedia.org" in url and "/thumb/" in url:
        base, rest = url.split("/thumb/", 1)
        rest = rest.rsplit("/", 1)[0]
        url = f"{base}/{rest}"
    return url


def download_image(url: str):
    """Download and convert unsupported formats if needed."""
    try:
        url = fix_wikimedia_url(url)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        os.makedirs("images", exist_ok=True)
        filename = os.path.basename(url.split("?")[0])
        filepath = os.path.join("images", filename)

        if filename.lower().endswith((".svg", ".webp")):
            try:
                image = PILImage.open(BytesIO(resp.content)).convert("RGB")
                filepath = filepath.rsplit(".", 1)[0] + ".png"
                image.save(filepath, "PNG")
            except Exception as e:
                print(f"⚠️ Conversion failed for {url}: {e}")
                return None
        else:
            with open(filepath, "wb") as f:
                f.write(resp.content)

        print(f"✅ Downloaded image: {filename}")
        return filepath
    except Exception as e:
        print(f"⚠️ Image download failed for {url}: {e}")
        return None


def parse_encyclopedia_html(html_path):
    """Extract entries (term, definition, images) from HTML."""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    entries = []
    base_path = os.path.dirname(html_path)

    for entry in soup.find_all("div", {"role": "ami_entry"}):
        term = entry.get("term") or entry.get("name") or "Untitled"
        desc_tag = entry.find("p", {"class": "wpage_first_para"}) or entry.find("p")
        definition = desc_tag.get_text(" ", strip=True) if desc_tag else "No description available."

        images = []
        for img in entry.find_all("img"):
            img_src = img.get("src")
            if not img_src:
                continue
            if img_src.startswith(("http://", "https://", "//")):
                local_img = download_image(img_src)
                if local_img:
                    images.append(local_img)
            else:
                img_path = os.path.join(base_path, img_src)
                if os.path.exists(img_path):
                    images.append(img_path)

        entries.append({"term": term.strip(), "definition": definition.strip(), "images": images})

    print(f"✅ Extracted {len(entries)} entries.")
    return entries


# ---------- Page Number ----------
def add_page_number(canvas_obj, doc):
    page_num = canvas_obj.getPageNumber()
    text = f"Page {page_num}"
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(550, 20, text)


# ---------- PDF Builder ----------
def build_pdf(book_title, book_author, book_desc, entries, output_path="encyclopedia_book.pdf"):
    """Build and generate a styled PDF."""
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
    )

    styles = getSampleStyleSheet()
    custom_styles = {
        "title": ParagraphStyle("Title", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#1E3A8A"), spaceAfter=12),
        "author": ParagraphStyle("Author", parent=styles["Normal"], fontSize=12, textColor=colors.grey, spaceAfter=8),
        "desc": ParagraphStyle("Desc", parent=styles["Normal"], fontSize=11, leading=14, spaceAfter=20, alignment=1),
        "term": ParagraphStyle("Term", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#2563EB"), spaceBefore=10, spaceAfter=6),
        "definition": ParagraphStyle("Definition", parent=styles["BodyText"], fontSize=11, leading=15, spaceAfter=10),
    }

    elements = []

    # ---------- Front Page ----------
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph(book_title, ParagraphStyle(
        "TitleCenter", parent=styles["Title"], fontSize=28, textColor=colors.HexColor("#0F172A"), alignment=1)))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"By {book_author}", ParagraphStyle(
        "AuthorCenter", parent=styles["Normal"], fontSize=14, textColor=colors.HexColor("#4B5563"), alignment=1)))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(book_desc, custom_styles["desc"]))
    elements.append(PageBreak())

    # ---------- Table of Contents ----------
    elements.append(Paragraph("Table of Contents", custom_styles["title"]))
    elements.append(Spacer(1, 12))
    for idx, e in enumerate(entries, 1):
        elements.append(Paragraph(f"{idx}. {e['term']}", custom_styles["definition"]))
    elements.append(PageBreak())

    # ---------- Content ----------
    for e in entries:
        term, definition, images = e["term"], e["definition"], e["images"]

        elements.append(Paragraph(term, custom_styles["term"]))
        elements.append(Paragraph(definition, custom_styles["definition"]))

        for img_path in images:
            if os.path.exists(img_path):
                try:
                    img = Image(img_path)
                    iw, ih = img.wrap(0, 0)
                    max_width = 5.5 * inch
                    if iw > max_width:
                        scale = max_width / float(iw)
                        img.drawWidth = iw * scale
                        img.drawHeight = ih * scale
                    elements.append(img)
                    elements.append(Spacer(1, 10))
                except Exception as ex:
                    print(f"⚠️ Failed to insert image {img_path}: {ex}")

        elements.append(Spacer(1, 8))
        elements.append(Paragraph("<hr width='100%' color='#CBD5E1'/>", styles["Normal"]))
        elements.append(Spacer(1, 8))

    doc.build(elements, onLaterPages=add_page_number, onFirstPage=add_page_number)
    print(f"✅ PDF generated: {output_path}")
    return os.path.abspath(output_path)


# ---------- Main ----------
def main():
    print("\n📘 Encyclopedia Book Generator (PDF)\n" + "-" * 44)
    args = parse_args()

    title = args.title or input("Enter Book Title: ").strip() or "Encyclopedia"
    author = args.author or input("Enter Author Name: ").strip() or "Unknown"
    desc = args.desc or input("Enter a short description: ").strip() or "An automatically generated encyclopedia."
    html_path = normalize_path(args.input or input("Enter path to the HTML file: "))

    if not os.path.exists(html_path):
        print("❌ ERROR: HTML file path is invalid or does not exist.")
        sys.exit(1)

    output_pdf = normalize_path(args.output)
    if not output_pdf.lower().endswith(".pdf"):
        output_pdf += ".pdf"

    print("\nParsing HTML...")
    entries = parse_encyclopedia_html(html_path)
    cleaned_entries = [e for e in entries if e.get("term") and e.get("definition")]

    print(f"✅ Final cleaned entries: {len(cleaned_entries)}")
    result_path = build_pdf(title, author, desc, cleaned_entries, output_path=output_pdf)
    print(f"✅ Book created successfully: {result_path}")


if __name__ == "__main__":
    main()



