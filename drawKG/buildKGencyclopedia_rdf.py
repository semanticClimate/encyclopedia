#!/usr/bin/env python3
import os, re, sys, csv, json, math, glob, argparse, subprocess, webbrowser, warnings
from urllib.parse import quote
from collections import defaultdict
from pathlib import Path
from bs4 import BeautifulSoup, FeatureNotFound
import networkx as nx
from pyvis.network import Network

for _s in (sys.stdout, sys.stderr):          # emoji/unicode in messages must not crash Windows consoles
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==========================
# Setup
# ==========================
parser = argparse.ArgumentParser(
    description="Build an interactive knowledge graph from an encyclopedia HTML file "
                "(term-term graph) or a bipartite paper-term graph from a folder of .txt papers."
)
parser.add_argument("--input", "-i", required=True,
                    help="Path to the input encyclopedia HTML file")
parser.add_argument("-o", "--output", default="semantic_KG.html",
                    help="Path for the output graph HTML (default: semantic_KG.html)")
parser.add_argument("--theme", "-t", choices=["dark", "light"], default="dark",
                    help="Color theme for the graph and UI (default: dark)")
parser.add_argument("--papers", "-p", default=None,
                    help="Folder of papers. Either Europe PMC style sub-folders (PMC123/fulltext.xml + eupmc_result.json, "
                         "as made by pygetpapers) or plain .txt files. Enables the bipartite paper-term graph")
parser.add_argument("--mode", choices=["terms", "bipartite"], default=None,
                    help="terms = term-term graph (default); bipartite = paper-term graph "
                         "(chosen automatically when --papers is given)")
parser.add_argument("--meta", default=None,
                    help="Optional CSV (columns: file,title,year,authors,doi) overriding paper metadata "
                         "(file = folder name such as PMC12032349, or the .txt file name)")
parser.add_argument("--min-count", type=int, default=1,
                    help="Bipartite: minimum mentions of a term in a paper to draw an edge (default: 1)")
parser.add_argument("--no-term-links", action="store_true",
                    help="Bipartite mode: do NOT add term-term edges (encyclopedia cross-references) "
                         "between terms; gives a pure paper-term bipartite graph")
parser.add_argument("--rdf", default=None, metavar="FILE.ttl",
                    help="Also export the graph as RDF (Turtle) to this file, e.g. graph.ttl")
parser.add_argument("--base-uri", default="https://example.org/kg/",
                    help="Base IRI used to mint identifiers in the RDF export "
                         "(default: https://example.org/kg/ - set your own, e.g. a w3id.org or GitHub Pages URL)")
parser.add_argument("--exclude-terms", default=None, metavar="FILE.txt",
                    help="Text file with one encyclopedia term per line to leave out of the graph "
                         "(case-insensitive), e.g. publisher names or generic words")
parser.add_argument("--no-default-filter", action="store_true",
                    help="Keep English function words (in, for, the ...), very short terms and pure numbers, "
                         "which are removed by default")
parser.add_argument("--animate", action="store_true",
                    help="Keep the physics simulation running (default: static layout, no motion)")
parser.add_argument("--no-open", action="store_true",
                    help="Do not open the graph in a browser when finished")
args, _ = parser.parse_known_args()  # tolerant of extra args (e.g. Colab/Jupyter)

input_file = args.input
graph_html = args.output

mode = args.mode or ("bipartite" if args.papers else "terms")
BIPARTITE = (mode == "bipartite")
TERM_LINKS = BIPARTITE and not args.no_term_links

if not os.path.isfile(input_file):
    sys.exit(f"Error: input file not found: {input_file}")
if BIPARTITE and not (args.papers and os.path.isdir(args.papers)):
    sys.exit("Error: bipartite mode needs --papers <folder with .txt files>")

out_dir = os.path.dirname(os.path.abspath(graph_html))
os.makedirs(out_dir, exist_ok=True)

warnings.filterwarnings("ignore")


# ==========================
# Theme
# ==========================
THEMES = {
    "dark": {
        "BG": "#000000", "FONT": "#FFFFFF",
        "C1": "#00ff99", "C2": "#66b2ff", "C3": "#ff9933", "C4": "#e8e8e8",
        "PANEL_BG": "rgba(0,0,0,0.7)", "TEXT": "#fff", "BORDER": "#66b2ff",
        "TIP_BG": "rgba(15,15,25,0.96)", "TIP_TEXT": "#eee", "TIP_TITLE": "#fff",
        "TIP_DESC": "#9ecbff", "TIP_FOOT": "#888", "SHADOW": "rgba(0,0,0,0.6)",
        "ARROW_BG": "#66b2ff", "ARROW_FG": "#000", "ARROW_HOVER": "#00ff99",
        "DIM_NODE": "rgba(100,100,100,0.15)", "DIM_FONT": "rgba(255,255,255,0.08)",
        "DIM_EDGE": "rgba(80,80,80,0.08)",
        "EDGE_ON": "rgba(0,255,255,0.95)", "EDGE_DEF": "rgba(0,255,255,0.85)",
        "PAPER": "#d0d0d0", "PAPER_FONT": "#111111", "EDGE_BIP": "rgba(0,255,255,0.28)",
        "EDGE_TT": "rgba(255,121,198,0.65)", "EDGE_TT_ON": "rgba(255,121,198,1)",
    },
    "light": {
        "BG": "#ffffff", "FONT": "#111111",
        "C1": "#00a86b", "C2": "#2b7de9", "C3": "#e07b00", "C4": "#7ba5a7",
        "PANEL_BG": "rgba(255,255,255,0.92)", "TEXT": "#111", "BORDER": "#2b7de9",
        "TIP_BG": "rgba(255,255,255,0.98)", "TIP_TEXT": "#222", "TIP_TITLE": "#000",
        "TIP_DESC": "#1a5fb4", "TIP_FOOT": "#666", "SHADOW": "rgba(0,0,0,0.25)",
        "ARROW_BG": "#2b7de9", "ARROW_FG": "#fff", "ARROW_HOVER": "#00a86b",
        "DIM_NODE": "rgba(150,150,150,0.20)", "DIM_FONT": "rgba(0,0,0,0.10)",
        "DIM_EDGE": "rgba(150,150,150,0.15)",
        "EDGE_ON": "rgba(0,110,170,0.95)", "EDGE_DEF": "rgba(0,130,180,0.55)",
        "PAPER": "#b0b0b0", "PAPER_FONT": "#111111", "EDGE_BIP": "rgba(0,130,180,0.25)",
        "EDGE_TT": "rgba(194,24,91,0.55)", "EDGE_TT_ON": "rgba(194,24,91,0.98)",
    },
}
T = dict(THEMES[args.theme])
if BIPARTITE:
    T["EDGE_DEF"] = T["EDGE_BIP"]   # fainter edges: the bipartite graph has many

# ==========================
# Read HTML
# ==========================
with open(input_file, "r", encoding="utf-8") as f:
    html = f.read()

html = re.sub(r'<sup[^>]*>.*?</sup>', '', html, flags=re.S)
soup = BeautifulSoup(html, "html.parser")

entries = soup.find_all("div", {"role": "ami_entry"})

# ==========================
# Build graph (NO DOMAIN)
# ==========================
nodes = {}
href_pattern = re.compile(r"/wiki/([^\"#]+)")

for div in entries:
    term = (div.get("term") or "").strip()
    if not term:
        continue

    wiki_tag = div.find("a", class_="wikipedia-link")
    wiki_url = wiki_tag["href"] if wiki_tag else ""

    links = set()
    for a in div.find_all("a", href=True):
        m = href_pattern.search(a["href"])
        if m:
            links.add(m.group(1).replace("_", " ").strip())

    nodes[term] = {
        "wiki": wiki_url,
        "links": list(links)
    }

# ==========================
# Remove unusable terms
# ==========================
# Function words such as "In" or "for" would match nearly every sentence of every paper and
# swamp the graph, so they (and very short terms / pure numbers) are dropped unless --no-default-filter is set.
STOPWORDS = set("""a about above across after again against all also am an and any are as at be because been before being
below between both but by can could did do does doing down during each few for from further had has have having he her here
hers him his how i if in into is it its just may me might more most must my no nor not of off on once only or other our out
over own per same shall she should so some such than that the their them then there these they this those through to too
under until up upon via very was we were what when where which while who whom why will with within without would yet you
your""".split())

excluded_terms = set()
if args.exclude_terms:
    with open(args.exclude_terms, encoding="utf-8") as f:
        excluded_terms = {l.strip().lower() for l in f if l.strip() and not l.startswith("#")}

def _drop_reason(term):
    low = term.strip().lower()
    if low in excluded_terms:
        return "exclude list"
    if args.no_default_filter:
        return None
    if low in STOPWORDS:
        return "function word"
    if re.fullmatch(r"[\d\W_]+", low):
        return "number/symbol"
    if len(low) < 3 and not (term.isupper() and len(term) >= 2):
        return "too short"
    return None

dropped = {t: _drop_reason(t) for t in nodes}
dropped = {t: r for t, r in dropped.items() if r}
for t in dropped:
    del nodes[t]
if dropped:
    sample = ", ".join(sorted(dropped)[:8])
    print(f"Left out {len(dropped)} unusable term(s) ({sample}{' ...' if len(dropped) > 8 else ''})")

G = nx.Graph()

# --------------------------------------------------
# Paper helpers (bipartite mode)
# --------------------------------------------------
STOP_HEADS = {"acknowledgements", "acknowledgments", "footnotes", "references", "author contributions"}

def parse_paper(path):
    """Read a PMC-style .txt paper: metadata from the header, body = Abstract .. before Acknowledgements."""
    raw = open(path, encoding="utf-8", errors="ignore").read()
    lines = [l.strip() for l in raw.splitlines()]
    stem = os.path.splitext(os.path.basename(path))[0]

    pmcid = next((l for l in lines[:60] if re.fullmatch(r"PMC\d+", l)), "")
    doi_i = next((i for i, l in enumerate(lines[:80]) if re.fullmatch(r"10\.\d{4,9}/\S+", l)), None)
    doi = lines[doi_i] if doi_i is not None else ""

    title, author, year = stem, "", ""
    if doi_i is not None and doi_i + 1 < len(lines):
        title = lines[doi_i + 1] or stem
        cand = lines[doi_i + 2] if doi_i + 2 < len(lines) else ""
        author = cand if re.fullmatch(r"[^\W\d_][\w'\- ]*", cand) else ""
        year = next((l for l in lines[doi_i + 1: doi_i + 120] if re.fullmatch(r"(19|20)\d\d", l)), "")

    start = next((i for i, l in enumerate(lines) if l.lower() == "abstract"), 0)
    stop = next((i for i in range(start + 1, len(lines)) if lines[i].lower() in STOP_HEADS), len(lines))
    body = "\n".join(lines[start:stop])

    label = f"{author} {year}".strip() or stem
    return {"file": os.path.basename(path), "stem": stem, "pmcid": pmcid, "doi": doi,
            "title": title, "year": year, "author": author, "label": label, "body": body,
            "journal": "", "authors": ""}

def _clean(x):
    return re.sub(r"\s+", " ", str(x) if x is not None else "").strip()

def _soup_xml(text):
    try:
        return BeautifulSoup(text, "xml")            # needs lxml
    except FeatureNotFound:
        return BeautifulSoup(text, "html.parser")    # works without lxml

def short_authors(author_string):
    names = [a.strip() for a in author_string.split(",") if a.strip()]
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")

def parse_paper_xml(folder):
    """Europe PMC / pygetpapers folder: metadata from eupmc_result.json, text from fulltext.xml (JATS).
    Body = abstract + main text; reference list, acknowledgements and other back matter are dropped."""
    name = os.path.basename(os.path.normpath(folder))

    meta = {}
    jpath = os.path.join(folder, "eupmc_result.json")
    if os.path.isfile(jpath):
        try:
            with open(jpath, encoding="utf-8") as f:
                meta = json.load(f)
            if isinstance(meta, list):
                meta = meta[0] if meta else {}
            if isinstance(meta, dict) and isinstance(meta.get("resultList"), dict):
                meta = (meta["resultList"].get("result") or [{}])[0]
        except Exception:
            meta = {}
    if not isinstance(meta, dict):
        meta = {}

    title   = _clean(meta.get("title")).rstrip(".")
    doi     = _clean(meta.get("doi"))
    pmcid   = _clean(meta.get("pmcid")) or (name if re.fullmatch(r"PMC\d+", name) else "")
    year    = _clean(meta.get("pubYear"))[:4] or _clean(meta.get("firstPublicationDate"))[:4]
    a_str   = _clean(meta.get("authorString")).rstrip(".")
    ji      = meta.get("journalInfo") if isinstance(meta.get("journalInfo"), dict) else {}
    journal = _clean(meta.get("journalTitle")) or _clean((ji.get("journal") or {}).get("title") if isinstance(ji.get("journal"), dict) else "")

    first = ""
    al = meta.get("authorList")
    if isinstance(al, dict) and isinstance(al.get("author"), list) and al["author"]:
        a0 = al["author"][0] if isinstance(al["author"][0], dict) else {}
        first = _clean(a0.get("lastName")) or _clean(a0.get("fullName")).rsplit(" ", 1)[0]
    if not first and a_str:
        first = a_str.split(",")[0].strip().rsplit(" ", 1)[0]

    xml_path = os.path.join(folder, "fulltext.xml")
    with open(xml_path, encoding="utf-8", errors="ignore") as f:
        soup = _soup_xml(f.read())

    am = soup.find("article-meta")            # fill gaps from the XML front matter
    if am is not None:
        if not title:
            t = am.find("article-title"); title = _clean(t.get_text(" ")) if t else ""
        if not doi:
            d = am.find("article-id", {"pub-id-type": "doi"}); doi = _clean(d.get_text()) if d else ""
        if not year:
            pd = am.find("pub-date"); y = pd.find("year") if pd else None; year = _clean(y.get_text()) if y else ""
        if not first:
            c = am.find("contrib", {"contrib-type": "author"}); sn = c.find("surname") if c else None
            first = _clean(sn.get_text()) if sn else ""
    if not journal:
        jt = soup.find("journal-title"); journal = _clean(jt.get_text(" ")) if jt else ""

    for tag in soup.find_all(["ref-list", "back", "fn-group", "xref"]):
        tag.decompose()
    parts = [ab.get_text(" ") for ab in soup.find_all("abstract")]
    bd = soup.find("body")
    parts.append(bd.get_text(" ") if bd is not None else "")
    body = _clean("\n".join(parts))

    label = f"{first} {year}".strip() or name
    return {"file": name, "stem": name, "pmcid": pmcid, "doi": doi, "title": title or name,
            "year": year, "author": first, "label": label, "body": body,
            "journal": journal, "authors": short_authors(a_str)}

def term_regex(term):
    """Whole-word match; plural tolerant; short ALL-CAPS terms (ENSO, AMOC) are case-sensitive."""
    t = re.escape(term.strip()).replace(r"\ ", r"\s+")
    acronym = term.strip().isupper() and len(term.strip()) <= 5
    pat = r"(?<!\w)" + t + ("" if acronym else r"(?:s|es)?") + r"(?!\w)"
    return re.compile(pat, 0 if acronym else re.IGNORECASE)

def paper_link(m):
    if m["pmcid"]:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{m['pmcid']}/"
    return f"https://doi.org/{m['doi']}" if m["doi"] else ""

if not BIPARTITE:
    # ---------------- term - term graph (original behaviour) ----------------
    for term, data in nodes.items():
        G.add_node(term, wiki=data["wiki"])

    lookup = {k.lower(): k for k in nodes}

    for src, data in nodes.items():
        for tgt in data["links"]:
            tgt_key = lookup.get(tgt.lower())
            if tgt_key and tgt_key != src:
                G.add_edge(src, tgt_key)

    G.remove_nodes_from(list(nx.isolates(G)))

else:
    # ---------------- bipartite graph: papers <-> terms ----------------
    xml_dirs = sorted(os.path.dirname(x) for x in
                      glob.glob(os.path.join(args.papers, "**", "fulltext.xml"), recursive=True))
    txt_files = sorted(glob.glob(os.path.join(args.papers, "*.txt")))
    if not xml_dirs and not txt_files:
        sys.exit(f"Error: no paper folders (with fulltext.xml) or .txt files found in {args.papers}")

    overrides = {}
    if args.meta:
        with open(args.meta, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                key = (row.get("file") or "").strip()
                if key:
                    overrides[key] = row
                    overrides[os.path.splitext(key)[0]] = row

    papers = []
    parsed = [parse_paper_xml(d) for d in xml_dirs] + [parse_paper(f) for f in txt_files]
    for m in parsed:
        ov = overrides.get(m["file"]) or overrides.get(m["stem"])
        if ov:
            for k in ("title", "year", "doi"):
                if (ov.get(k) or "").strip():
                    m[k] = ov[k].strip()
            if (ov.get("authors") or "").strip():
                m["author"] = ov["authors"].split(",")[0].strip()
            if (ov.get("authors") or "").strip():
                m["authors"] = short_authors(ov["authors"].strip())
            m["label"] = f"{m['author']} {m['year']}".strip() or m["stem"]
        papers.append(m)

    # make labels unique: two papers by the same first author in the same year -> "Name 2026a", "Name 2026b"
    groups = defaultdict(list)
    for m in papers:
        groups[m["label"]].append(m)
    for lab, ms in groups.items():
        if len(ms) > 1:
            for k, m in enumerate(sorted(ms, key=lambda x: x["stem"])):
                m["label"] = f"{lab}{chr(97 + k)}" if k < 26 else f"{lab} ({m['stem']})"

    print(f"Read {len(xml_dirs)} paper folder(s) (fulltext.xml) and {len(txt_files)} .txt file(s)")
    for what, bad in (("no year", [m for m in papers if not m["year"]]),
                      ("no first author", [m for m in papers if not m["author"]]),
                      ("no text found", [m for m in papers if len(m["body"]) < 200])):
        if bad:
            print(f"  Papers with {what} ({len(bad)}): {', '.join(m['stem'] for m in bad[:8])}{' ...' if len(bad) > 8 else ''}")

    regexes = {t: term_regex(t) for t in nodes}

    for m in papers:
        pid = "paper:" + m["file"]
        G.add_node(pid, kind="paper", label=m["label"], paper_title=m["title"],
                   year=m["year"], doi=m["doi"], journal=m["journal"], authors=m["authors"],
                   author=m["author"], pmcid=m["pmcid"], file=m["file"],
                   wiki=paper_link(m))
        for term, rx in regexes.items():
            n = len(rx.findall(m["body"]))
            if n >= args.min_count and n > 0:
                if term not in G:
                    G.add_node(term, kind="term", label=term, wiki=nodes[term]["wiki"])
                G.add_edge(pid, term, count=n)

    no_terms = [G.nodes[n]["label"] for n in list(G) if G.nodes[n].get("kind") == "paper" and G.degree(n) == 0]
    never_found = [t for t in nodes if t not in G]

    # the paper-term layer is bipartite by construction - verify it before adding anything else
    B = nx.Graph([(u, v) for u, v, d in G.edges(data=True) if "count" in d])
    assert nx.is_bipartite(B), "paper-term layer is not bipartite - this should not happen"
    n_pt = B.number_of_edges()

    # term-term layer: encyclopedia cross-references (entry text links to another entry's Wikipedia page)
    n_tt = 0
    if TERM_LINKS:
        lookup = {k.lower(): k for k in nodes}
        for src, data in nodes.items():
            if src not in G:
                continue
            for tgt in data["links"]:
                tgt_key = lookup.get(tgt.lower())
                if tgt_key and tgt_key != src and tgt_key in G and not G.has_edge(src, tgt_key):
                    G.add_edge(src, tgt_key, etype="term")
                    n_tt += 1

    G.remove_nodes_from(list(nx.isolates(G)))

    n_p = sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "paper")
    n_t = G.number_of_nodes() - n_p
    print(f"Graph: {n_p} papers + {n_t} terms = {G.number_of_nodes()} nodes")
    print(f"  {n_pt} paper-term edges (bipartite layer) + {n_tt} term-term edges = {G.number_of_edges()} edges")
    if not TERM_LINKS:
        print("  (term-term links switched off: pure bipartite graph)")
    if no_terms:
        print(f"  Papers with no matching terms ({len(no_terms)}): {', '.join(no_terms[:10])}")
    print(f"  Encyclopedia terms found in no paper: {len(never_found)} of {len(nodes)}")

# ==========================
# Static layout (no motion)
# ==========================
import numpy as np
import random

def paper_nbrs(G, t):
    return [n for n in G[t] if G.nodes[n].get("kind") == "paper"]

SIZE_LO, SIZE_HI = 8, 70          # node radius range (vis-network px)

def size_for(count, cmax):
    """Term node radius from a mention count (square-root scale, so hubs do not swamp everything)."""
    return SIZE_LO + (SIZE_HI - SIZE_LO) * math.sqrt(max(count, 0) / cmax) if cmax else SIZE_LO

def bipartite_layout(G):
    """Papers on a ring (similar papers side by side), terms shared by 2+ papers inside the
    ring, terms found in a single paper fanned out just outside their paper."""
    rng = random.Random(7)
    papers = [n for n, d in G.nodes(data=True) if d.get("kind") == "paper"]
    pset = set(papers)
    terms = [n for n in G if n not in pset]
    n_p = max(1, len(papers))
    R = max(450.0, 30.0 * n_p)

    # 1) order papers around the ring: papers sharing many terms become neighbours
    P = nx.Graph()
    P.add_nodes_from(papers)
    for t in terms:
        ps = paper_nbrs(G, t)
        if len(ps) < 2:
            continue
        w = 1.0 / (len(ps) - 1)            # very common terms count less
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                a, b = ps[i], ps[j]
                P.add_edge(a, b, weight=(P[a][b]["weight"] + w) if P.has_edge(a, b) else w)
    try:
        order = list(nx.spectral_ordering(P, weight="weight"))
    except Exception:
        order = sorted(papers)

    pos, ang = {}, {}
    for i, pnode in enumerate(order):
        a = 2 * math.pi * i / n_p - math.pi / 2
        ang[pnode] = a
        pos[pnode] = (R * math.cos(a), R * math.sin(a))

    shared = [t for t in terms if len(paper_nbrs(G, t)) >= 2]
    leaves = [t for t in terms if len(paper_nbrs(G, t)) < 2]

    # 2) shared terms inside the ring (papers stay fixed, terms relax between them)
    if shared:
        init = {pn: np.array(pos[pn]) for pn in papers}
        for t in shared:
            ps = paper_nbrs(G, t)
            wsum = float(sum(G[t][pn]["count"] for pn in ps))
            cx = sum(pos[pn][0] * G[t][pn]["count"] for pn in ps) / wsum
            cy = sum(pos[pn][1] * G[t][pn]["count"] for pn in ps) / wsum
            init[t] = np.array([cx + rng.uniform(-40, 40), cy + rng.uniform(-40, 40)])
        H = G.subgraph(papers + shared)
        spacing = math.sqrt(math.pi * (0.85 * R) ** 2 / len(shared))
        rel = nx.spring_layout(H, pos=init, fixed=papers, k=0.8 * spacing, iterations=250, seed=3)
        for t in shared:
            x, y = float(rel[t][0]), float(rel[t][1])
            r = math.hypot(x, y)
            if r > 0.88 * R:
                x, y = x * 0.88 * R / r, y * 0.88 * R / r
            pos[t] = (x, y)

        # nudge overlapping dots apart (sizes follow the node size used below)
        rad = {t: size_for(TOTAL[t], CMAX) for t in shared}
        for _ in range(80):
            moved = False
            for i in range(len(shared)):
                ti = shared[i]
                for j in range(i + 1, len(shared)):
                    tj = shared[j]
                    dx, dy = pos[tj][0] - pos[ti][0], pos[tj][1] - pos[ti][1]
                    d = math.hypot(dx, dy) or 0.01
                    need = rad[ti] + rad[tj] + 14
                    if d < need:
                        push = (need - d) / 2
                        ux, uy = dx / d, dy / d
                        pos[ti] = (pos[ti][0] - ux * push, pos[ti][1] - uy * push)
                        pos[tj] = (pos[tj][0] + ux * push, pos[tj][1] + uy * push)
                        moved = True
            if not moved:
                break

    # 3) single-paper terms fanned out outside their paper
    by_paper = {}
    for t in leaves:
        by_paper.setdefault(paper_nbrs(G, t)[0], []).append(t)
    sector = 2 * math.pi / n_p
    for pn, lst in by_paper.items():
        lst.sort(key=lambda t: -G[t][pn]["count"])
        half, idx, row = 0.42 * sector, 0, 0
        while idx < len(lst):
            r = R + 110 + row * 48
            cap = max(1, int(2 * half * r / 46))
            chunk = lst[idx: idx + cap]
            for j, t in enumerate(chunk):
                frac = 0.5 if len(chunk) == 1 else j / (len(chunk) - 1)
                a = ang[pn] - half + 2 * half * frac
                pos[t] = (r * math.cos(a), r * math.sin(a))
            idx += cap
            row += 1
    return pos

def force_layout(G):
    n = max(1, G.number_of_nodes())
    rel = nx.spring_layout(G, k=2.0 / math.sqrt(n), iterations=400, seed=42)
    f = 120 * math.sqrt(n)
    return {k: (float(v[0]) * f, float(v[1]) * f) for k, v in rel.items()}

if BIPARTITE:
    # corpus frequency of every term = total mentions over all papers
    TOTAL = {n: sum(G[n][p]["count"] for p in paper_nbrs(G, n))
             for n in G if G.nodes[n].get("kind") != "paper"}
    CMAX = max(TOTAL.values()) if TOTAL else 1
    top = sorted(TOTAL.items(), key=lambda kv: -kv[1])[:5]
    print("  Most frequent terms in the corpus: " + ", ".join(f"{t} ({c})" for t, c in top))

POS = bipartite_layout(G) if BIPARTITE else force_layout(G)

# ==========================
# Visualization
# ==========================
net = Network(height="100vh", width="100%", bgcolor=T["BG"], font_color=T["FONT"])

# colour thresholds for terms in bipartite mode (original 4-colour degree scheme,
# scaled to the number of papers: degree = number of papers that mention the term)
n_papers = sum(1 for _, d in G.nodes(data=True) if d.get("kind") == "paper")
TH_HI  = max(4, round(0.33 * n_papers))
TH_MID = max(3, round(0.17 * n_papers))
TH_LOW = max(2, round(0.07 * n_papers))

for node, data in G.nodes(data=True):
    deg = len(paper_nbrs(G, node)) if (BIPARTITE and data.get("kind") != "paper") else len(G[node])
    x, y = POS.get(node, (0, 0))

    if not BIPARTITE:
        # ORIGINAL COLOR LOGIC
        color = T["C1"] if deg > 25 else T["C2"] if deg > 10 else T["C3"] if deg > 4 else T["C4"]
        net.add_node(
            node,
            label=node,
            color=color,
            originalColor=color,
            originalFont=T["FONT"],
            size=10 + deg * 0.6,
            x=x, y=y,
            wiki=data.get("wiki", "")
        )
    elif data.get("kind") == "paper":
        # paper = rounded "card" with the label inside; card text grows with the number of terms
        net.add_node(
            node,
            label=data["label"],
            shape="box",
            color=T["PAPER"],
            originalColor=T["PAPER"],
            originalFont=T["PAPER_FONT"],
            margin=10,
            borderWidth=2,
            shapeProperties={"borderRadius": 10},
            scaling={"label": {"drawThreshold": 1}},
            x=x, y=y,
            kind="paper",
            paper_title=data.get("paper_title", ""),
            year=data.get("year", ""),
            doi=data.get("doi", ""),
            journal=data.get("journal", ""),
            authors=data.get("authors", ""),
            wiki=data.get("wiki", "")
        )
        net.node_map[node]["font"] = {"size": int(22 + min(10, deg / 6)), "color": T["PAPER_FONT"]}
    else:
        color = T["C1"] if deg > TH_HI else T["C2"] if deg > TH_MID else T["C3"] if deg > TH_LOW else T["C4"]
        net.add_node(
            node,
            label=node,
            shape="dot",
            color=color,
            originalColor=color,
            originalFont=T["FONT"],
            size=size_for(TOTAL[node], CMAX),          # size = frequency in the whole corpus
            baseSize=size_for(TOTAL[node], CMAX),      # remembered so Reset can restore it
            totalCount=TOTAL[node],
            x=x, y=y,
            scaling={"label": {"drawThreshold": 5 if deg > TH_LOW else 9}},   # small labels appear on zoom
            kind="term",
            wiki=data.get("wiki", "")
        )

for src, tgt, ed in G.edges(data=True):
    if BIPARTITE and "count" in ed:                      # paper - term
        w = round(0.6 + min(3.0, 0.7 * math.log2(ed["count"])), 2)
        net.add_edge(src, tgt, color=T["EDGE_DEF"], width=w, origWidth=w, count=ed["count"],
                     origColor=T["EDGE_DEF"], onColor=T["EDGE_ON"])
    elif BIPARTITE:                                      # term - term (dashed, pink)
        net.add_edge(src, tgt, color=T["EDGE_TT"], width=1.4, origWidth=1.4, dashes=True,
                     etype="term", origColor=T["EDGE_TT"], onColor=T["EDGE_TT_ON"])
    else:
        net.add_edge(src, tgt, color=T["EDGE_DEF"], width=1.6, origWidth=1.6)

if not args.animate:
    net.toggle_physics(False)     # positions are pre-computed: nothing moves

html_path = os.path.abspath(graph_html)
net.write_html(html_path)

# ==========================
# Inject UI
# ==========================
with open(html_path, "r", encoding="utf-8") as f:
    html_data = f.read()

custom_ui = r"""
<style>
#panel {
 position: fixed; top:20px; left:20px; z-index:9999;
 background: __PANEL_BG__;
 padding:10px; border-radius:8px;
 border:1px solid __BORDER__;
 color:__TEXT__; font-family:Arial;
}
#panel select, #panel input, #panel button { margin-top:4px; }
#legend {
 position: fixed; top:20px; right:20px; z-index:9999;
 background: __PANEL_BG__;
 padding:10px; border-radius:8px;
 border:1px solid __BORDER__;
 color:__TEXT__; font-family:Arial;
}
.legend-dot {
 width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px;
}

/* Wikipedia tooltip */
#wikiTip {
 position: fixed; z-index:10000; display:none;
 width:320px; max-width:90vw;
 background: __TIP_BG__;
 border:1px solid __BORDER__; border-radius:10px;
 padding:12px 14px; color:__TIP_TEXT__;
 font-family:Arial; font-size:13px; line-height:1.45;
 box-shadow:0 6px 24px __SHADOW__;
}
#wikiTip .tt-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
#wikiTip .tt-title { font-size:15px; font-weight:bold; color:__TIP_TITLE__; }
#wikiTip a.tt-arrow {
 flex:none; width:22px; height:22px; line-height:22px; text-align:center;
 border-radius:50%; background:__ARROW_BG__; color:__ARROW_FG__;
 text-decoration:none; font-weight:bold; font-size:14px;
}
#wikiTip a.tt-arrow:hover { background:__ARROW_HOVER__; }
#wikiTip .tt-desc { color:__TIP_DESC__; font-style:italic; margin:2px 0 6px; }
#wikiTip img { float:right; max-width:90px; max-height:90px; margin:0 0 6px 10px; border-radius:6px; }
#wikiTip .tt-foot { clear:both; margin-top:8px; font-size:11px; color:__TIP_FOOT__; }
</style>

<div id="panel">
 🔍 <input id="search" placeholder="Search node"><br>
 <button onclick="searchNode()">Go</button>
 <button onclick="resetGraph()">Reset</button><br>
 Others:
 <select id="mode" onchange="if(focusedId!==null) focusNode(focusedId)">
   <option value="faint">Faint</option>
   <option value="hide">Hide</option>
 </select>
 <div id="sizeInfo" style="margin-top:6px;font-size:12px;opacity:.85"></div>
</div>

<div id="legend">
 <b>🎨 Node Colors</b><br>
 __LEGEND_ROWS__
</div>

<div id="wikiTip"></div>

<script>
const BIPARTITE = __BIPARTITE__;
network.setOptions({ interaction: { hover: true, tooltipDelay: 100000 } });
if(BIPARTITE) network.setOptions({ edges: { smooth: false } });
if(!__ANIMATE__) setTimeout(() => network.fit({ animation: false }), 50);

const DIM_NODE = "__DIM_NODE__";
const DIM_FONT = "__DIM_FONT__";
const DIM_EDGE = "__DIM_EDGE__";
const EDGE_ON  = "__EDGE_ON__";
const EDGE_DEF = "__EDGE_DEF__";
const SIZE_LO = __SIZE_LO__, SIZE_HI = __SIZE_HI__;

function sizeFor(c, cmax){ return cmax ? SIZE_LO + (SIZE_HI - SIZE_LO) * Math.sqrt(c / cmax) : SIZE_LO; }

function setSizeInfo(text){
 const el = document.getElementById("sizeInfo");
 if(el) el.textContent = BIPARTITE ? text : "";
}
setSizeInfo("Node size = mentions in the whole corpus");

// term size: whole-corpus frequency by default; mentions inside one paper when a paper is clicked
function applySizes(id){
 if(!BIPARTITE) return;
 const N = network.body.data.nodes, E = network.body.data.edges;
 const node = (id !== null && id !== undefined) ? N.get(id) : null;
 if(node && node.kind === "paper"){
   const cnt = new Map(); let cmax = 0;
   E.get().forEach(e => {
     if(e.count && (e.from === id || e.to === id)){
       cnt.set(e.from === id ? e.to : e.from, e.count);
       if(e.count > cmax) cmax = e.count;
     }
   });
   N.update(N.get().filter(n => n.kind === "term").map(n => ({
     id: n.id, size: cnt.has(n.id) ? sizeFor(cnt.get(n.id), cmax) : n.baseSize
   })));
   setSizeInfo("Node size = mentions in " + node.label);
 }else{
   N.update(N.get().filter(n => n.kind === "term").map(n => ({ id: n.id, size: n.baseSize })));
   setSizeInfo("Node size = mentions in the whole corpus");
 }
}

let focusedId = null;

// ---------- FOCUS: show only direct neighbours ----------
function focusNode(id){
 focusedId = id;
 const hide = document.getElementById("mode").value === "hide";
 const keep = new Set(network.getConnectedNodes(id));
 keep.add(id);

 const N = network.body.data.nodes, E = network.body.data.edges;

 N.update(N.get().map(n => {
   const on = keep.has(n.id);
   return {
     id: n.id,
     hidden: !on && hide,
     color: on ? n.originalColor : DIM_NODE,
     font: Object.assign({}, n.font, { color: on ? (n.originalFont || "__FONT__") : DIM_FONT })
   };
 }));

 E.update(E.get().map(e => {
   const on = (e.from === id || e.to === id);
   return {
     id: e.id,
     hidden: !on && hide,
     color: on ? (e.onColor || EDGE_ON) : DIM_EDGE,
     width: on ? (e.origWidth || 1.6) + 1 : 1
   };
 }));
 applySizes(id);
}

// ---------- RESET ----------
function resetGraph(){
 focusedId = null;
 const N = network.body.data.nodes, E = network.body.data.edges;
 N.update(N.get().map(n => ({
   id: n.id, hidden: false, color: n.originalColor,
   font: Object.assign({}, n.font, { color: n.originalFont || "__FONT__" })
 })));
 E.update(E.get().map(e => ({
   id: e.id, hidden: false, color: e.origColor || EDGE_DEF, width: e.origWidth || 1.6
 })));
 applySizes(null);
 hideTip(true);
 network.fit();
}

// ---------- SEARCH ----------
function searchNode(){
 const val = document.getElementById("search").value.trim().toLowerCase();
 const found = network.body.data.nodes.get().find(n => n.label.toLowerCase() === val);
 if(found){
   focusNode(found.id);
   network.focus(found.id, { scale: 1.6 });
 }
}
document.getElementById("search").addEventListener("keydown", e => {
 if(e.key === "Enter") searchNode();
});

// ---------- WIKIPEDIA TOOLTIP ----------
const tip = document.getElementById("wikiTip");
const wikiCache = {};
let mouseX = 0, mouseY = 0, hoverId = null, hideTimer = null;

document.addEventListener("mousemove", e => { mouseX = e.clientX; mouseY = e.clientY; });

function esc(s){
 return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

function wikiInfo(node){
 // Work out host + page title from the stored Wikipedia URL (fallback: node label)
 let host = "en.wikipedia.org", title = node.label, url = node.wiki || "";
 const m = url.match(/^https?:\/\/([^\/]+)\/wiki\/([^#?]+)/);
 if(m){ host = m[1]; title = decodeURIComponent(m[2]); }
 if(!url){ url = "https://" + host + "/wiki/" + encodeURIComponent(title.replace(/ /g, "_")); }
 return { host, title, url };
}

async function fetchSummary(info){
 const key = info.host + "|" + info.title;
 if(wikiCache[key]) return wikiCache[key];
 try{
   const api = "https://" + info.host + "/api/rest_v1/page/summary/" + encodeURIComponent(info.title.replace(/ /g, "_"));
   const r = await fetch(api);
   if(!r.ok) throw new Error(r.status);
   wikiCache[key] = await r.json();
 }catch(err){
   wikiCache[key] = { error: true };
 }
 return wikiCache[key];
}

function topNeighbours(id, k){
 const E = network.body.data.edges.get().filter(e => e.count && (e.from === id || e.to === id));
 E.sort((a, b) => b.count - a.count);
 return E.slice(0, k).map(e => {
   const other = network.body.data.nodes.get(e.from === id ? e.to : e.from);
   return esc(other.label) + " (" + e.count + ")";
 });
}

function connLine(node){
 const nb = network.getConnectedNodes(node.id).map(i => network.body.data.nodes.get(i));
 const nP = nb.filter(n => n.kind === "paper").length;
 const nT = nb.length - nP;
 let txt;
 if(node.kind === "paper") txt = "Mentions <b>" + nb.length + "</b> encyclopedia terms";
 else if(BIPARTITE)        txt = "Found in <b>" + nP + "</b> paper" + (nP === 1 ? "" : "s") +
                                 (nT ? " · linked to <b>" + nT + "</b> related term" + (nT === 1 ? "" : "s") : "");
 else                      txt = "Linked to <b>" + nb.length + "</b> other entr" + (nb.length === 1 ? "y" : "ies");
 const top = topNeighbours(node.id, 6);
 let html = '<div style="margin-top:8px;font-size:12px">' + txt +
        (top.length ? '<br><span style="opacity:.8">' + (node.kind === "paper" ? "Top terms: " : "Top papers: ") +
        top.join(", ") + '</span>' : "");
 if(BIPARTITE && node.kind !== "paper"){
   html += '<br><span style="opacity:.8">Mentions in corpus: <b>' + (node.totalCount || 0) + '</b>';
   const fp = (focusedId !== null) ? network.body.data.nodes.get(focusedId) : null;
   if(fp && fp.kind === "paper"){
     const ed = network.body.data.edges.get().find(e => e.count &&
                ((e.from === fp.id && e.to === node.id) || (e.to === fp.id && e.from === node.id)));
     if(ed) html += ' · in ' + esc(fp.label) + ': <b>' + ed.count + '</b>';
   }
   html += '</span>';
 }
 if(BIPARTITE && node.kind !== "paper" && nT){
   const rel = nb.filter(n => n.kind !== "paper").map(n => esc(n.label)).sort().slice(0, 8);
   html += '<br><span style="opacity:.8">Related terms: ' + rel.join(", ") + (nT > 8 ? " …" : "") + '</span>';
 }
 return html + '</div>';
}

function placeTip(){
 const pad = 16;
 let x = mouseX + pad, y = mouseY + pad;
 const w = tip.offsetWidth, h = tip.offsetHeight;
 if(x + w > window.innerWidth  - 8) x = mouseX - w - pad;
 if(y + h > window.innerHeight - 8) y = window.innerHeight - h - 8;
 tip.style.left = Math.max(8, x) + "px";
 tip.style.top  = Math.max(8, y) + "px";
}

function renderTip(node, info, d){
 let body;
 if(d.error){
   body = '<div class="tt-desc">No Wikipedia summary available.</div>';
 }else{
   const thumb = d.thumbnail ? '<img src="' + esc(d.thumbnail.source) + '">' : "";
   const desc  = d.description ? '<div class="tt-desc">' + esc(d.description) + '</div>' : "";
   let ex = d.extract || "";
   if(ex.length > 420) ex = ex.slice(0, 420).replace(/\s+\S*$/, "") + "…";
   body = desc + thumb + '<div>' + esc(ex) + '</div>';
 }
 tip.innerHTML =
   '<div class="tt-head"><span class="tt-title">' + esc(node.label) + '</span>' +
   '<a class="tt-arrow" href="' + esc(info.url) + '" target="_blank" rel="noopener" title="Open Wikipedia page">↗</a></div>' +
   body + connLine(node) +
   '<div class="tt-foot">Click node to isolate its neighbours · ↗ opens Wikipedia</div>';
}

function renderPaperTip(node){
 const meta = [node.authors, [node.year, node.journal].filter(Boolean).join(", "), node.doi ? "DOI " + node.doi : ""].filter(Boolean).join(" · ");
 const arrow = node.wiki ? '<a class="tt-arrow" href="' + esc(node.wiki) + '" target="_blank" rel="noopener" title="Open paper">↗</a>' : "";
 tip.innerHTML =
   '<div class="tt-head"><span class="tt-title">' + esc(node.label) + '</span>' + arrow + '</div>' +
   '<div class="tt-desc">' + esc(node.paper_title || "") + '</div>' +
   (meta ? '<div>' + esc(meta) + '</div>' : "") + connLine(node) +
   '<div class="tt-foot">Click node to isolate its terms · ↗ opens the paper</div>';
}

async function showTip(id){
 const node = network.body.data.nodes.get(id);
 if(!node) return;
 if(node.kind === "paper"){
   tip.style.display = "block";
   renderPaperTip(node);
   placeTip();
   return;
 }
 const info = wikiInfo(node);

 tip.style.display = "block";
 tip.innerHTML = '<div class="tt-head"><span class="tt-title">' + esc(node.label) +
   '</span></div><div class="tt-desc">Loading Wikipedia info…</div>';
 placeTip();

 const d = await fetchSummary(info);
 if(hoverId !== id) return;          // mouse moved on
 renderTip(node, info, d);
 placeTip();
}

function hideTip(now){
 clearTimeout(hideTimer);
 const run = () => { tip.style.display = "none"; };
 if(now) run(); else hideTimer = setTimeout(run, 250);   // grace time to reach the ↗ arrow
}

tip.addEventListener("mouseenter", () => clearTimeout(hideTimer));
tip.addEventListener("mouseleave", () => hideTip(true));

network.on("hoverNode", p => { clearTimeout(hideTimer); hoverId = p.node; showTip(p.node); });
network.on("blurNode",  () => { hoverId = null; hideTip(false); });
network.on("dragStart", () => hideTip(true));
network.on("zoom",      () => hideTip(true));

// ---------- CLICK: node → isolate neighbours, empty space → reset ----------
network.on("click", p => {
 if(p.nodes.length > 0){
   focusNode(p.nodes[0]);
 }else if(focusedId !== null){
   resetGraph();
 }
});
</script>
"""

LEGEND_TERMS = """ <div><span class="legend-dot" style="background:__C1__"></span>__C1__ → Highly Connected</div>
 <div><span class="legend-dot" style="background:__C2__"></span>__C2__ → Main Topics</div>
 <div><span class="legend-dot" style="background:__C3__"></span>__C3__ → Subfields</div>
 <div><span class="legend-dot" style="background:__C4__"></span>__C4__ → Related Concepts</div>"""

LEGEND_BIPARTITE = (
 ' <div><b>Terms</b> <small>(colour = no. of papers · size = mentions)</small></div>\n'
 f' <div><span class="legend-dot" style="background:__C1__"></span>__C1__ → in more than {TH_HI} papers</div>\n'
 f' <div><span class="legend-dot" style="background:__C2__"></span>__C2__ → in {TH_MID + 1}–{TH_HI} papers</div>\n'
 f' <div><span class="legend-dot" style="background:__C3__"></span>__C3__ → in {TH_LOW + 1}–{TH_MID} papers</div>\n'
 f' <div><span class="legend-dot" style="background:__C4__"></span>__C4__ → in {TH_LOW} paper{"s" if TH_LOW != 1 else ""} or fewer</div>\n'
 ' <div style="margin-top:6px"><span style="display:inline-block;width:16px;height:11px;border-radius:3px;'
 'background:__PAPER__;margin-right:6px"></span><b>Paper</b> card</div>\n'
 ' <div><small>Inside ring = shared terms · outside = single-paper terms<br>Solid edge = term in paper (width = mentions)<br>Click a paper → size = mentions in that paper</small></div>'
)
if TERM_LINKS:
    LEGEND_BIPARTITE += (' <div style="margin-top:4px"><span style="display:inline-block;width:24px;'
                         'border-top:2px dashed __EDGE_TT__;margin-right:6px;vertical-align:middle"></span>'
                         'Term–term link <small>(encyclopedia cross-reference)</small></div>')

custom_ui = custom_ui.replace("__LEGEND_ROWS__", LEGEND_BIPARTITE if BIPARTITE else LEGEND_TERMS)
custom_ui = custom_ui.replace("__BIPARTITE__", "true" if BIPARTITE else "false")
custom_ui = custom_ui.replace("__SIZE_LO__", str(SIZE_LO)).replace("__SIZE_HI__", str(SIZE_HI))
custom_ui = custom_ui.replace("__ANIMATE__", "true" if args.animate else "false")
for key, val in T.items():
    custom_ui = custom_ui.replace(f"__{key}__", val)

html_data = html_data.replace("</body>", custom_ui + "</body>")

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_data)

print(f"🚀 Graph ready ({mode} mode, {args.theme} theme; click = isolate neighbours, hover = tooltip)")

print(f"Saved: {html_path}")

# ==========================
# RDF export (Turtle)
# ==========================
def _lit(x):
    """Turtle string literal with escaping."""
    x = str(x).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f'"{x}"'

def _ext_iri(url):
    """External IRI (e.g. a Wikipedia page): escape characters that are illegal inside <...>."""
    return "<" + re.sub(r'[\s<>"{}|\\^`]', lambda m: "%%%02X" % ord(m.group()), url) + ">"

def _slug(x):
    return quote(re.sub(r"\s+", "_", str(x).strip()), safe="-._~")

def write_rdf(G, path, base, bipartite, min_count):
    """Serialise the graph as RDF/Turtle.
    Article  a kg:Article, schema:ScholarlyArticle   (title, year, DOI, journal, first author)
    Concept  a kg:Concept, skos:Concept               (prefLabel, schema:sameAs Wikipedia page, counts)
    Article kg:mentions Concept, plus a kg:Mention node that carries the mention count
    Concept skos:related Concept                      (encyclopedia cross-references)"""
    base = base if base.endswith(("/", "#")) else base + "/"
    V = base + "vocab#"
    art = lambda n: f"<{base}article/{_slug(n)}>"
    con = lambda n: f"<{base}concept/{_slug(n)}>"
    men = lambda a, c: f"<{base}mention/{_slug(a)}--{_slug(c)}>"

    kind = lambda n: G.nodes[n].get("kind", "term")
    articles = sorted(n for n in G if kind(n) == "paper")
    concepts = sorted(n for n in G if kind(n) != "paper")
    key = lambda n: G.nodes[n].get("file") or n.replace("paper:", "", 1)

    out = []
    w = out.append
    w("@prefix kg: <%s> ." % V)
    w("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .")
    w("@prefix schema: <https://schema.org/> .")
    w("@prefix dcterms: <http://purl.org/dc/terms/> .")
    w("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
    w("@prefix owl: <http://www.w3.org/2002/07/owl#> .")
    w("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
    w("")
    w("# ---- vocabulary ----")
    w(f"<{V[:-1]}> a owl:Ontology ; rdfs:label \"Concept-centred literature knowledge graph vocabulary\" .")
    vocab = [
        ("Article", "Class", "Article", "A scholarly article in the corpus.", "rdfs:subClassOf schema:ScholarlyArticle"),
        ("Concept", "Class", "Concept", "An encyclopedia entry used as a controlled-vocabulary concept.", "rdfs:subClassOf skos:Concept"),
        ("Mention", "Class", "Mention", "The occurrences of one concept in one article, with their number.", None),
        ("mentions", "ObjectProperty", "mentions", "The article mentions the concept in its abstract or main text.",
         "rdfs:domain kg:Article ; rdfs:range kg:Concept"),
        ("inArticle", "ObjectProperty", "in article", "The article of a mention.", "rdfs:domain kg:Mention ; rdfs:range kg:Article"),
        ("aboutConcept", "ObjectProperty", "about concept", "The concept of a mention.", "rdfs:domain kg:Mention ; rdfs:range kg:Concept"),
        ("mentionCount", "DatatypeProperty", "mention count", "Number of occurrences of the concept in the article.",
         "rdfs:domain kg:Mention ; rdfs:range xsd:integer"),
        ("totalMentions", "DatatypeProperty", "total mentions", "Occurrences of the concept in the whole corpus.",
         "rdfs:domain kg:Concept ; rdfs:range xsd:integer"),
        ("articleCount", "DatatypeProperty", "article count", "Number of articles that mention the concept.",
         "rdfs:domain kg:Concept ; rdfs:range xsd:integer"),
        ("firstAuthor", "DatatypeProperty", "first author", "Surname of the first author.", "rdfs:domain kg:Article"),
        ("journal", "DatatypeProperty", "journal", "Journal title.", "rdfs:domain kg:Article"),
        ("minMentions", "DatatypeProperty", "minimum mentions", "Minimum mentions needed for an article-concept link in this graph.", None),
        ("KnowledgeGraph", "Class", "Knowledge graph", "Description of one generated graph.", None),
        ("articleTotal", "DatatypeProperty", "article total", "Number of articles in the graph.", "rdfs:domain kg:KnowledgeGraph"),
        ("conceptTotal", "DatatypeProperty", "concept total", "Number of concepts in the graph.", "rdfs:domain kg:KnowledgeGraph"),
        ("articleConceptLinks", "DatatypeProperty", "article-concept links", "Number of article-concept links.", "rdfs:domain kg:KnowledgeGraph"),
    ]
    for local, typ, label, comment, extra in vocab:
        t = {"Class": "rdfs:Class", "ObjectProperty": "owl:ObjectProperty", "DatatypeProperty": "owl:DatatypeProperty"}[typ]
        w(f"kg:{local} a {t} ; rdfs:label {_lit(label)} ; rdfs:comment {_lit(comment)}" + (f" ; {extra}" if extra else "") + " .")
    w("")

    # dataset description
    n_pt = sum(1 for u, v, d in G.edges(data=True) if "count" in d)
    w("# ---- graph ----")
    w(f"<{base}graph> a kg:KnowledgeGraph ; rdfs:label \"Literature-concept knowledge graph\" ;")
    w(f"    kg:articleTotal {len(articles)} ; kg:conceptTotal {len(concepts)} ; kg:articleConceptLinks {n_pt} ;")
    w(f"    kg:minMentions {int(min_count)} .")
    w("")

    w("# ---- articles ----")
    for n in articles:
        d = G.nodes[n]
        parts = [f"a kg:Article, schema:ScholarlyArticle", f"rdfs:label {_lit(d.get('label') or n)}"]
        if d.get("paper_title"): parts.append(f"dcterms:title {_lit(d['paper_title'])}")
        if d.get("year") and str(d["year"]).isdigit(): parts.append(f'dcterms:issued "{d["year"]}"^^xsd:gYear')
        if d.get("author"): parts.append(f"kg:firstAuthor {_lit(d['author'])}")
        if d.get("journal"): parts.append(f"kg:journal {_lit(d['journal'])}")
        if d.get("doi"):
            parts.append(f"dcterms:identifier {_lit(d['doi'])}")
            parts.append(f"schema:sameAs {_ext_iri('https://doi.org/' + d['doi'])}")
        if d.get("pmcid"): parts.append(f"dcterms:identifier {_lit(d['pmcid'])}")
        if d.get("wiki"): parts.append(f"rdfs:seeAlso {_ext_iri(d['wiki'])}")
        w(f"{art(key(n))} " + " ;\n    ".join(parts) + " .")
    w("")

    w("# ---- concepts ----")
    for n in concepts:
        d = G.nodes[n]
        paper_nb = [m for m in G[n] if kind(m) == "paper"]
        total = sum(G[n][m]["count"] for m in paper_nb)
        parts = ["a kg:Concept, skos:Concept", f"skos:prefLabel {_lit(d.get('label') or n)}@en"]
        if d.get("wiki"): parts.append(f"schema:sameAs {_ext_iri(d['wiki'])}")
        if bipartite:
            parts.append(f"kg:totalMentions {total}")
            parts.append(f"kg:articleCount {len(paper_nb)}")
        w(f"{con(n)} " + " ;\n    ".join(parts) + " .")
    w("")

    if bipartite:
        w("# ---- article-concept mentions ----")
        for a in articles:
            for c in sorted(m for m in G[a] if kind(m) != "paper"):
                cnt = G[a][c]["count"]
                w(f"{art(key(a))} kg:mentions {con(c)} .")
                w(f"{men(key(a), c)} a kg:Mention ; kg:inArticle {art(key(a))} ; kg:aboutConcept {con(c)} ; "
                  f"kg:mentionCount {cnt} .")
        w("")

    w("# ---- concept-concept relations (encyclopedia cross-references) ----")
    for u, v in sorted(tuple(sorted(e)) for e in G.edges() if kind(e[0]) != "paper" and kind(e[1]) != "paper"):
        w(f"{con(u)} skos:related {con(v)} .")
        w(f"{con(v)} skos:related {con(u)} .")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return len(articles), len(concepts)

if args.rdf:
    na, nc = write_rdf(G, args.rdf, args.base_uri, BIPARTITE, args.min_count)
    print(f"RDF (Turtle) saved: {os.path.abspath(args.rdf)}  [{na} articles, {nc} concepts]")

# Open
if not args.no_open:
    try:
        subprocess.run(["open", html_path], check=False)
    except Exception:
        webbrowser.open(Path(html_path).as_uri())
