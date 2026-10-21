#!/usr/bin/env python3
"""
build_semantic_kg.py - build an interactive knowledge graph from an encyclopedia + the source papers.

Unlike a graph built only from Wikipedia links, this links terms using
  (1) co-occurrence in the papers (with the supporting sentence),
  (2) term structure ("MHW threshold" -> "MHW"),
  (3) abbreviations found in the text ("sea surface temperature (SST)"),
  (4) Wikipedia page links between terms, and a Wikipedia-based ONTOLOGY: concepts that the Wikipedia
      entries of several terms link to (e.g. "Ocean", "Temperature") become ontology-concept nodes.

Every node and edge gets a stable ID (terms N0001.., ontology concepts C0001.., edges E00001..), and nodes are
grouped + colour-coded three ways (switch in the graph): Wikipedia ontology, source paper, topic cluster.

Example (Google Colab):
  !python /content/KG_demo/build_semantic_kg.py \\
      --input  /content/encyclopediaTest.html \\
      --output /content/semantic_KG_v2.html \\
      --text-dir /content/text_all \\
      --papers-dir /content/marine

In the generated graph: click a node to highlight only that term and its connections, and see the
papers (with links to Europe PMC) and sentences where it is mentioned.

Requires: beautifulsoup4 networkx pyvis pandas
"""
import re, os, sys, glob, json, math, argparse, collections, itertools, warnings, colorsys, base64, mimetypes
from urllib.parse import unquote, quote
from bs4 import BeautifulSoup
import networkx as nx
from pyvis.network import Network
import pandas as pd

warnings.filterwarnings("ignore")

ap = argparse.ArgumentParser(description="Build an interactive knowledge graph from an encyclopedia HTML and the source papers.")
ap.add_argument("--input", "-i", required=True, help="encyclopedia HTML (list of terms), e.g. encyclopediaTest.html")
ap.add_argument("--output", "-o", required=True, help="output interactive graph (HTML)")
ap.add_argument("--text-dir", "-t", default=None,
                help="folder with plain-text papers (*.txt, e.g. txt2phrases xml2txt output). "
                     "Enables co-occurrence + abbreviation links. Without it only term-structure links are built.")
ap.add_argument("--papers-dir", "-p", default=None,
                help="folder with the downloaded papers (pygetpapers output, e.g. /content/marine). Used to show each paper's "
                     "title, authors and year. Without it papers are listed by ID (PMC...) with a link to Europe PMC.")
ap.add_argument("--merged-csv", default=None, help="optional merged keyphrase CSV; used with --add-merged-phrases")
ap.add_argument("--add-merged-phrases", action="store_true", help="also add phrases from --merged-csv that are not in the encyclopedia")
ap.add_argument("--min-phrase-count", type=int, default=3, help="min count for --add-merged-phrases (default 3)")
ap.add_argument("--edges-csv", default=None, help="edge list CSV (default: <output>_edges.csv)")
ap.add_argument("--nodes-csv", default=None, help="node table CSV (default: <output>_nodes.csv)")
ap.add_argument("--min-cooc", type=float, default=1.0, help="min co-occurrence weight to keep a link (default 1; try 2-3 for 50+ papers)")
ap.add_argument("--top-k", type=int, default=6, help="keep each term's K strongest co-occurrence links (default 6)")
ap.add_argument("--max-fanout", type=int, default=40, help="skip hierarchy links to terms contained in more than N terms (default 40)")
ap.add_argument("--extra-noise", default="", help="comma-separated extra terms to drop, e.g. 'figure,table'")
ap.add_argument("--no-cooccurrence", action="store_true", help="disable co-occurrence links")
ap.add_argument("--no-hierarchy", action="store_true", help="disable term-structure links")
ap.add_argument("--no-abbreviations", action="store_true", help="disable abbreviation detection")
ap.add_argument("--label-font-size", type=int, default=14, help="node label font size in graph units (default 14)")
ap.add_argument("--label-min-px", type=int, default=9,
                help="labels appear once they would be at least this many pixels tall on screen, i.e. after zooming in (default 9; lower = labels appear earlier)")
ap.add_argument("--wiki-links", action="store_true",
                help="add Wikipedia links between terms (always on unless --no-ontology is given)")
ap.add_argument("--no-ontology", action="store_true", help="disable the Wikipedia ontology (concept nodes + term-to-term Wikipedia links)")
ap.add_argument("--onto-min-terms", type=int, default=2,
                help="a Wikipedia concept becomes an ontology node only if at least N terms link to it (default 2)")
ap.add_argument("--onto-max-fanout", type=int, default=40,
                help="ignore concepts linked from more than N terms - too generic to be useful (default 40)")
ap.add_argument("--onto-max-concepts", type=int, default=150,
                help="keep at most N ontology concepts, the ones shared by most terms (default 150)")
ap.add_argument("--color-by", choices=["ontology", "paper", "cluster"], default="ontology",
                help="initial colouring of the graph; can be switched inside the graph (default ontology)")
ap.add_argument("--max-figures", type=int, default=3, help="max figures per term shown in the hover card (default 3)")
ap.add_argument("--desc-chars", type=int, default=600, help="max characters of the encyclopedia description in the hover card (default 600)")
ap.add_argument("--max-groups", type=int, default=12,
                help="number of groups that get their own colour per grouping; the rest are shown as 'Other' (default 12)")
args = ap.parse_args()

ENCYCLOPEDIA_HTML = args.input
OUT_HTML   = args.output
_stem      = os.path.splitext(OUT_HTML)[0]
OUT_EDGES  = args.edges_csv or _stem + "_edges.csv"
OUT_NODES  = args.nodes_csv or _stem + "_nodes.csv"
TEXT_DIR   = args.text_dir
PAPERS_DIR = args.papers_dir
OUT_PAPERS = _stem + "_papers.csv"
OUT_JSON   = _stem + "_graph.json"
MERGED_CSV = args.merged_csv

USE_COOCCURRENCE  = not args.no_cooccurrence
USE_HIERARCHY     = not args.no_hierarchy
USE_ABBREVIATIONS = not args.no_abbreviations
USE_ONTOLOGY      = not args.no_ontology
USE_WIKI_LINKS    = args.wiki_links or USE_ONTOLOGY
ONTO_MIN_TERMS, ONTO_MAX_FANOUT, ONTO_MAX_CONCEPTS = args.onto_min_terms, args.onto_max_fanout, args.onto_max_concepts
MAX_GROUPS = args.max_groups
MAX_FIGS, DESC_CHARS = args.max_figures, args.desc_chars
MIN_COOC, TOP_K, MAX_FANOUT = args.min_cooc, args.top_k, args.max_fanout
ADD_MERGED_PHRASES, MIN_PHRASE_COUNT = args.add_merged_phrases, args.min_phrase_count

if not os.path.isfile(ENCYCLOPEDIA_HTML):
    sys.exit(f"Input file not found: {ENCYCLOPEDIA_HTML}")

# Paper boilerplate and figure-description words that are not scientific concepts (edit freely)
NOISE_TERMS = {"consistent", "investigation", "characteristic", "amplify", "averaged", "oceanic term",
               "ile temperature", "identified", "broader", "coherent", "slower", "blue", "software", "resources",
               "methodology", "figs", "arrows", "stipples", "terlies", "ppvf", "anomal", "predict",
               "communications", "competing interests", "conceptualization", "data availability",
               "formal analysis", "funding acquisition", "project administration", "international license",
               "nature publishing group", "supplementary dataset", "supplementary movie",
               "supplementary information", "github repository", "mathworks", "training data",
               "publicly accessible repositories", "data processing"}
NOISE_TERMS |= {x.strip().lower() for x in args.extra_noise.split(",") if x.strip()}
NOISE_PATTERN = re.compile(r"\b(gray|grey|black|red|blue|orange|magenta|dashed|solid|shaded?|shading|dots?|boxe?s?|"
                           r"contours?|stipples?)\b", re.I)   # figure-caption words: "gray shading", "black boxes", ...

# ---------------- Text normalisation ----------------
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)

def stem(w):
    w = w.lower()
    if len(w) > 4 and w.endswith("ies"):                      return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("sses", "xes", "ches", "shes")): return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")): return w[:-1]
    return w

def norm(text):
    return tuple(stem(w) for w in TOKEN_RE.findall(text))

# ---------------- 1. Load terms ----------------
with open(ENCYCLOPEDIA_HTML, encoding="utf-8") as f:
    html = re.sub(r"<sup[^>]*>.*?</sup>", "", f.read(), flags=re.S)
soup = BeautifulSoup(html, "html.parser")

# Wikipedia pages that are not articles (never ontology concepts)
WIKI_NAMESPACES = ("category:", "file:", "image:", "help:", "wikipedia:", "special:", "template:", "template talk:",
                   "portal:", "talk:", "draft:", "module:", "user:", "wikt:", "wiktionary:", "commons:", "wikidata:")
DISAMBIG = ("may refer to", "may be an abbreviation", "may stand for", "may also refer")
raw_terms, wiki_url, entry_links, is_disambig = [], {}, {}, {}
entry_desc, entry_figs = {}, {}                 # term -> description text ; term -> [[image src, caption], ...]
ENC_DIR = os.path.dirname(os.path.abspath(ENCYCLOPEDIA_HTML))
SKIP_IMG = re.compile(r"/static/|/resources/|CentralAutoLogin|Wikidata-logo|OOjs_UI_icon|Commons-logo|Wikimedia-logo", re.I)

def _num(v):
    m = re.search(r"\d+", str(v or "")); return int(m.group(0)) if m else None

def extract_figures(div):
    """Images of an encyclopedia entry as [src, caption]. Local files are embedded so the graph stays self-contained."""
    figs, seen = [], set()
    for img in div.find_all("img"):
        src = (img.get("src") or img.get("data-src") or "").strip()
        if not src or src in seen or SKIP_IMG.search(src): continue
        w, h = _num(img.get("width")), _num(img.get("height"))
        if (w is not None and w < 40) or (h is not None and h < 40): continue          # icons / bullets
        if src.startswith("//"): src = "https:" + src
        elif not re.match(r"^(https?:|data:)", src):                                  # relative path next to the encyclopedia
            fp = os.path.join(ENC_DIR, unquote(src))
            if not os.path.isfile(fp) or os.path.getsize(fp) > 300000: continue
            with open(fp, "rb") as fh:
                src = f"data:{mimetypes.guess_type(fp)[0] or 'image/png'};base64," + base64.b64encode(fh.read()).decode()
        if len(src) > 400000: continue
        seen.add(src)
        fig = img.find_parent("figure")
        cap = fig.find("figcaption").get_text(" ", strip=True) if fig and fig.find("figcaption") else ""
        cap = re.sub(r"\s+", " ", cap or img.get("alt") or img.get("title") or "").strip()
        figs.append([src, cap[:140]])
    return figs
for div in soup.find_all("div", {"role": "ami_entry"}):
    t = (div.get("term") or "").strip()
    if not t or t.lower() in NOISE_TERMS or len(t) < 3 or t.isdigit() or NOISE_PATTERN.search(t):
        continue
    raw_terms.append(t)
    a = div.find("a", class_="wikipedia-link")
    wiki_url[t] = a["href"] if a else ""
    p = div.find("p", class_="wpage_first_para")
    is_disambig[t] = bool(p and any(k in p.get_text(" ") for k in DISAMBIG))
    dp = p or div.find("p")
    entry_desc[t] = re.sub(r"\s+", " ", dp.get_text(" ")).strip() if dp else ""
    entry_figs[t] = extract_figures(div)
    links = set()
    for a in div.find_all("a", href=True):
        if "wikipedia-link" in (a.get("class") or []) or "wikidata-link" in (a.get("class") or []):
            continue
        m = re.search(r"/wiki/([^\"#]+)", a["href"])
        if m:
            title = unquote(m.group(1)).replace("_", " ").strip()
            if title and not title.lower().startswith(WIKI_NAMESPACES):
                links.add(title)
    entry_links[t] = links

if ADD_MERGED_PHRASES and MERGED_CSV and os.path.exists(MERGED_CSV):
    try:
        df = pd.read_csv(MERGED_CSV)
        low = {c.lower(): c for c in df.columns}
        pc = next((low[c] for c in ("phrase", "keyphrase", "term", "word", "text", "name") if c in low), df.columns[0])
        cc = next((low[c] for c in ("count", "freq", "frequency", "counts", "total") if c in low), None)
        if cc:
            df = df[pd.to_numeric(df[cc], errors="coerce").fillna(0) >= MIN_PHRASE_COUNT]
        extra = [str(x).strip() for x in df[pc].dropna().unique()]
        known = {norm(t) for t in raw_terms}
        added = [t for t in extra if len(t) >= 3 and not t.isdigit() and norm(t) and norm(t) not in known
                 and t.lower() not in NOISE_TERMS and not NOISE_PATTERN.search(t)]
        raw_terms += added
        for t in added: wiki_url[t] = ""; entry_links[t] = set(); is_disambig[t] = False; entry_desc[t] = ""; entry_figs[t] = []
        print(f"Added {len(added)} phrases from merged.csv")
    except Exception as e:
        print("Could not read merged.csv:", e)

# Merge trivial variants (plural / case): 'Anomalies' + 'anomaly', 'marine heatwaves' + 'marine heatwave'
vocab, display = {}, {}            # normalised tuple -> node id ; node id -> label
groups = collections.defaultdict(list)
for t in raw_terms:
    k = norm(t)
    if k: groups[k].append(t)
for k, variants in groups.items():
    label = next((v for v in variants if v == v.lower()), variants[0])
    vocab[k] = label
    display[label] = label
    for v in variants:
        wiki_url.setdefault(label, wiki_url.get(v, ""))
        if not wiki_url[label]: wiki_url[label] = wiki_url.get(v, "")
        entry_links.setdefault(label, set()).update(entry_links.get(v, set()))
        is_disambig[label] = is_disambig.get(label, False) and is_disambig.get(v, False)
        if not entry_desc.get(label): entry_desc[label] = entry_desc.get(v, "")
        entry_figs[label] = entry_figs.get(label) or entry_figs.get(v, [])
nodes = sorted(display)
print(f"Terms in encyclopedia: {len(raw_terms)}  ->  {len(nodes)} nodes after merging plural/case variants")

# ---------------- 2. Load the papers ----------------
files = sorted(glob.glob(os.path.join(TEXT_DIR, "**", "*.txt"), recursive=True)) if TEXT_DIR else []
def paper_id(fp):
    """PMC id from the path (xml2txt keeps it in the file or folder name); otherwise the file name."""
    m = re.search(r"PMC\d+", os.path.relpath(fp, TEXT_DIR), re.I)
    return m.group(0).upper() if m else os.path.splitext(os.path.basename(fp))[0]

docs = []
for fp in files:
    with open(fp, encoding="utf-8", errors="ignore") as f:
        docs.append((paper_id(fp), f.read()))
if not docs:
    print(f"⚠️ No .txt papers found ({TEXT_DIR or '--text-dir not given'}). Co-occurrence and abbreviation links are skipped.")
    USE_COOCCURRENCE = USE_ABBREVIATIONS = False
else:
    print(f"Loaded {len(docs)} paper(s) from {TEXT_DIR}")

def load_meta(pid):
    """Title / authors / year / link for a paper, from pygetpapers metadata if available."""
    meta = {"title": pid, "authors": "", "year": "", "url": ""}
    doi = ""
    if PAPERS_DIR:
        hits = glob.glob(os.path.join(PAPERS_DIR, "**", pid), recursive=True)
        folder = next((h for h in hits if os.path.isdir(h)), None)
        if folder:
            jf, xf = os.path.join(folder, "eupmc_result.json"), os.path.join(folder, "fulltext.xml")
            try:
                if os.path.exists(jf):
                    j = json.load(open(jf, encoding="utf-8"))
                    meta["title"] = re.sub(r"<[^>]+>", "", j.get("title") or pid).strip()
                    meta["authors"] = j.get("authorString", "") or ""
                    meta["year"] = str(j.get("pubYear", "") or "")
                    doi = j.get("doi", "") or ""
                elif os.path.exists(xf):
                    m = re.search(r"<article-title[^>]*>(.*?)</article-title>", open(xf, encoding="utf-8", errors="ignore").read(), re.S)
                    if m: meta["title"] = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
            except Exception:
                pass
    if pid.upper().startswith("PMC"): meta["url"] = f"https://europepmc.org/article/PMC/{pid.upper()}"
    elif doi: meta["url"] = f"https://doi.org/{doi}"
    return meta

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")
def paragraphs(text):
    for para in re.split(r"\n\s*\n", text):
        para = re.sub(r"\s+", " ", para).strip()
        if para:
            yield [s for s in SENT_SPLIT.split(para) if s.strip()]

# ---------------- 3. Abbreviations: "sea surface temperature (SST)" ----------------
def best_long_form(short, long_text):                 # Schwartz & Hearst (2003)
    s, l = len(short) - 1, len(long_text) - 1
    while s >= 0:
        c = short[s].lower()
        if not c.isalnum():
            s -= 1; continue
        while l >= 0 and (long_text[l].lower() != c or (s == 0 and l > 0 and long_text[l - 1].isalnum())):
            l -= 1
        if l < 0: return None
        s -= 1; l -= 1
    return long_text[long_text.rfind(" ", 0, l + 1) + 1:]

ABBR_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9\-]{1,9})\)")
abbrev_pairs = collections.Counter()
aliases = {}
if USE_ABBREVIATIONS:
    for _, text in docs:
        flat = re.sub(r"\s+", " ", text)
        for m in ABBR_RE.finditer(flat):
            short = m.group(1)
            if not any(ch.isupper() for ch in short): continue
            before = flat[:m.start()].rstrip().split(" ")
            n = min(len(short) + 5, len(short) * 2)
            cand = " ".join(before[-n:])
            for sf in {short, short.rstrip("s")}:
                lf = best_long_form(sf, cand) if len(sf) >= 2 else None
                if lf and len(lf.split()) >= 2:
                    abbrev_pairs[(sf, lf.strip(" ,;:"))] += 1
                    break
    for (sf, lf), c in abbrev_pairs.most_common():
        ks, kl = norm(sf), norm(lf)
        if not ks or not kl or ks == kl: continue
        a, b = vocab.get(ks), vocab.get(kl)
        if a and not b:   vocab[kl] = a; aliases.setdefault(a, set()).add(lf)    # long form -> existing acronym node
        elif b and not a: vocab[ks] = b; aliases.setdefault(b, set()).add(sf)    # acronym -> existing long-form node
    print(f"Abbreviation pairs detected in text: {len(abbrev_pairs)} (aliases added: {sum(len(v) for v in aliases.values())})")

# ---------------- 4. Find terms in every sentence ----------------
MAXN = max(len(k) for k in vocab)
def find_terms(sentence):
    toks = [stem(w) for w in TOKEN_RE.findall(sentence)]
    found = set()
    for i in range(len(toks)):
        for n in range(1, min(MAXN, len(toks) - i) + 1):
            node = vocab.get(tuple(toks[i:i + n]))
            if node: found.add(node)
    return found

freq, docfreq = collections.Counter(), collections.Counter()
w_same, w_adj, evidence = collections.Counter(), collections.Counter(), {}
term_paper = collections.defaultdict(collections.Counter)      # term -> {paper id: mentions}
snippet = {}                                                   # (term, paper id) -> first sentence
if docs:
    for pid, text in docs:
        seen = set()
        for sents in paragraphs(text):
            prev = set()
            for s in sents:
                cur = find_terms(s)
                freq.update(cur); seen |= cur
                for t in cur:
                    term_paper[t][pid] += 1
                    snippet.setdefault((t, pid), s)
                for a, b in itertools.combinations(sorted(cur), 2):
                    w_same[(a, b)] += 1
                    evidence.setdefault((a, b), s)
                for a in cur:
                    for b in prev:
                        if a != b and b not in cur and a not in prev:   # pair not already counted in one sentence
                            w_adj[tuple(sorted((a, b)))] += 1
                prev = cur
        docfreq.update(seen)

# ---------------- 5. Collect edges by layer ----------------
edges = collections.defaultdict(lambda: {"types": set(), "weight": 0.0, "evidence": "", "dir": None})
DIRECTED = {"hierarchy", "onto", "abbrev"}      # (source -> target) is meaningful for these relations
def add_edge(a, b, typ, w=1.0, ev=""):
    if a == b: return
    k = tuple(sorted((a, b)))
    e = edges[k]; e["types"].add(typ); e["weight"] += w
    if ev and not e["evidence"]: e["evidence"] = ev
    if typ in DIRECTED and e["dir"] is None: e["dir"] = (a, b)

# 5a. co-occurrence, scored with the Dice coefficient so very common words don't connect to everything
if USE_COOCCURRENCE:
    pairs = {}
    for k in set(w_same) | set(w_adj):
        w = w_same[k] + 0.5 * w_adj[k]
        if w >= MIN_COOC:
            pairs[k] = (2 * w / (freq[k[0]] + freq[k[1]]), w)
    by_node = collections.defaultdict(list)
    for k, (dice, w) in pairs.items():
        by_node[k[0]].append((dice, k)); by_node[k[1]].append((dice, k))
    keep = set()
    for n, lst in by_node.items():
        keep.update(k for _, k in sorted(lst, reverse=True)[:TOP_K])
    for k in keep:
        add_edge(*k, "cooc", pairs[k][1], evidence.get(k, ""))

# 5b. hierarchy: a term that contains another term is a more specific version of it
if USE_HIERARCHY:
    node_key = {}
    for k, n in vocab.items(): node_key.setdefault(n, k)
    cand, fan = [], collections.Counter()
    for n, k in node_key.items():
        for L in range(1, len(k)):
            for i in range(len(k) - L + 1):
                sub = vocab.get(k[i:i + L])
                if sub and sub != n:
                    cand.append((n, sub)); fan[sub] += 1
    skipped = sorted({s for s, c in fan.items() if c > MAX_FANOUT})
    for n, sub in cand:
        if fan[sub] <= MAX_FANOUT: add_edge(n, sub, "hierarchy", 1.0, f"'{n}' is a more specific form of '{sub}'")
    if skipped: print("Hierarchy skipped for very generic terms:", ", ".join(skipped))

# 5c. abbreviations / expansions that are both terms
if USE_ABBREVIATIONS:
    for (sf, lf), c in abbrev_pairs.items():
        a, b = vocab.get(norm(sf)), vocab.get(norm(lf))
        if a and b and a != b:
            add_edge(a, b, "abbrev", 1.0, f"'{sf}' is the abbreviation of '{lf}'")

# 5d. optional: Wikipedia page links (old method)
if USE_WIKI_LINKS:
    for n in nodes:
        if is_disambig.get(n): continue                       # a disambiguation page has meaningless links
        for tgt in entry_links.get(n, ()):
            m = vocab.get(norm(tgt))
            if m and m != n: add_edge(n, m, "wiki", 1.0, "Linked in Wikipedia")

# 5e. Wikipedia ontology: pages that the Wikipedia entries of several terms link to become concept nodes.
#     term --has_ontology_concept--> concept ; terms sharing a concept are therefore related through it.
concept_label, concept_url = {}, {}            # internal graph key -> display title / Wikipedia URL
if USE_ONTOLOGY:
    concept_terms, concept_name = collections.defaultdict(set), {}
    for n in nodes:
        if is_disambig.get(n): continue
        for tgt in entry_links.get(n, ()):
            k = norm(tgt)
            if (not k or vocab.get(k) or len(tgt) < 3 or re.match(r"^\d", tgt)
                    or "(identifier)" in tgt or tgt.lower() in NOISE_TERMS):
                continue                         # empty / another term (-> 'wiki' edge) / year / identifier page / noise
            concept_terms[k].add(n); concept_name.setdefault(k, tgt)
    usable = [(k, v) for k, v in concept_terms.items() if ONTO_MIN_TERMS <= len(v) <= ONTO_MAX_FANOUT]
    usable.sort(key=lambda kv: (-len(kv[1]), concept_name[kv[0]].lower()))
    for k, v in usable[:ONTO_MAX_CONCEPTS]:
        ck = "wiki:" + concept_name[k]
        concept_label[ck] = concept_name[k]
        concept_url[ck] = "https://en.wikipedia.org/wiki/" + quote(concept_name[k].replace(" ", "_"))
        for n in sorted(v):
            add_edge(n, ck, "onto", 1.0, f"'{n}' links to the Wikipedia concept '{concept_name[k]}'")
    print(f"Ontology: {len(concept_label)} Wikipedia concepts shared by >= {ONTO_MIN_TERMS} terms "
          f"(from {len(concept_terms)} distinct linked pages)")

# ---------------- 6. Graph, node/edge IDs, coverage ----------------
term_set = set(nodes)
def label_of(n):                       # display label of a graph key (term or ontology concept)
    return concept_label.get(n, n)

G = nx.Graph()
G.add_nodes_from(nodes)
G.add_nodes_from(concept_label)
for (a, b), e in edges.items():
    G.add_edge(a, b, weight=e["weight"], types=sorted(e["types"]), evidence=e["evidence"], dir=e["dir"])
connected = [n for n in G if G.degree(n) > 0]
connected_terms = [n for n in connected if n in term_set]
unconnected = sorted(term_set - set(connected))
print(f"\n✅ Connected terms: {len(connected_terms)} / {len(nodes)}   |   ontology concepts: {len(concept_label)}   |   edges: {G.number_of_edges()}")
for t in ("cooc", "hierarchy", "abbrev", "wiki", "onto"):
    c = sum(1 for _, _, d in G.edges(data=True) if t in d["types"])
    if c: print(f"   {t:<10} edges: {c}")

# Stable IDs: terms N0001.. and ontology concepts C0001.. (alphabetical), edges E00001.. (ordered by their end-point IDs)
node_id = {n: f"N{i:04d}" for i, n in enumerate(sorted(nodes, key=str.lower), 1)}
node_id.update({c: f"C{i:04d}" for i, c in enumerate(sorted(concept_label, key=lambda c: concept_label[c].lower()), 1)})
REL = {"cooc": "co_occurs_with", "hierarchy": "more_specific_than", "abbrev": "abbreviation_of",
       "wiki": "wikipedia_linked_to", "onto": "has_ontology_concept"}
edge_rows = []
for a, b, d in G.edges(data=True):
    src, tgt = d["dir"] if d["dir"] else tuple(sorted((a, b), key=lambda x: node_id[x]))
    edge_rows.append({"src": src, "tgt": tgt, "d": d})
edge_rows.sort(key=lambda r: (node_id[r["src"]], node_id[r["tgt"]]))
for i, r in enumerate(edge_rows, 1):
    r["id"] = f"E{i:05d}"
    r["rel"] = "+".join(REL[t] for t in r["d"]["types"])

# ---------------- 6b. Papers ----------------
paper_meta = {pid: load_meta(pid) for pid, _ in docs}
paper_terms = collections.defaultdict(list)                   # paper -> [[node id, mentions]]
for t in connected_terms:
    for pid, c in term_paper[t].items(): paper_terms[pid].append([node_id[t], c])
for pid in paper_terms: paper_terms[pid].sort(key=lambda x: -x[1])

# ---------------- 6c. Groups + colours: topic cluster / source paper / Wikipedia ontology ----------------
PALETTE = ["#66b2ff", "#ff9933", "#00ff99", "#ff5555", "#c792ea", "#ffd54f", "#4dd0e1",
           "#f06292", "#aed581", "#ba68c8", "#90a4ae", "#ffab91"]
OTHER_COL, NONE_COL = "#8a8f98", "#555555"

def palette_color(i):
    if i < len(PALETTE): return PALETTE[i]
    r, g, b = colorsys.hls_to_rgb(((i - len(PALETTE)) * 0.381966) % 1.0, 0.62, 0.65)   # golden-angle hues beyond the palette
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

def finalize_groups(assign, name_of, none_label):
    """assign: node -> group key (or None). The MAX_GROUPS biggest groups get their own colour, the rest 'Other'."""
    counts = collections.Counter(k for k in assign.values() if k)
    ranked = [k for k, _ in counts.most_common(MAX_GROUPS)]
    col = {k: palette_color(i) for i, k in enumerate(ranked)}
    key, color = {}, {}
    for n, k in assign.items():
        if k in col:  key[n], color[n] = k, col[k]
        elif k:       key[n], color[n] = "other", OTHER_COL
        else:         key[n], color[n] = "none", NONE_COL
    name = {k: name_of(k) for k in ranked}
    name.update({"other": "Other", "none": none_label})
    legend = [{"key": k, "color": col[k], "label": f"{name[k]} ({counts[k]})"} for k in ranked]
    n_other = sum(v for k, v in counts.items() if k not in col)
    n_none = sum(1 for k in assign.values() if not k)
    if n_other: legend.append({"key": "other", "color": OTHER_COL, "label": f"Other ({n_other})"})
    if n_none:  legend.append({"key": "none", "color": NONE_COL, "label": f"{none_label} ({n_none})"})
    return {"key": key, "color": color, "legend": legend, "name": name}

def majority(c_node, term_assign):                     # group of an ontology concept = most common group of its terms
    cnt = collections.Counter(term_assign[x] for x in G[c_node] if x in term_assign and term_assign[x])
    return cnt.most_common(1)[0][0] if cnt else None

# (i) topic clusters (Louvain on the term + concept graph)
H = G.subgraph(connected)
try:
    comms = nx.community.louvain_communities(H, weight="weight", seed=42)
except Exception:
    comms = list(nx.community.greedy_modularity_communities(H, weight="weight"))
comms = sorted(comms, key=len, reverse=True)
cluster_assign, cluster_hub = {n: None for n in connected}, {}
for i, c in enumerate(comms):
    cluster_hub[f"cluster:{i}"] = max(c, key=lambda n: H.degree(n, weight="weight"))
    for n in c: cluster_assign[n] = f"cluster:{i}"

# (ii) source paper: a term belongs to the paper that mentions it most (ties -> first paper ID)
primary_paper, paper_assign = {}, {}
for t in connected_terms:
    if term_paper[t]: primary_paper[t] = min(term_paper[t].items(), key=lambda x: (-x[1], x[0]))[0]
    paper_assign[t] = f"paper:{primary_paper[t]}" if t in primary_paper else None
for c in concept_label: paper_assign[c] = majority(c, paper_assign)

def paper_name(k):
    pid = k.split(":", 1)[1]; title = paper_meta.get(pid, {}).get("title", pid)
    return pid if title == pid else (title if len(title) <= 48 else title[:47] + "…")

# (iii) Wikipedia ontology: greedy set cover - repeatedly pick the concept that covers most still-unassigned terms
onto_assign, onto_head = {}, {}
cover = {c: {x for x in G[c] if x in term_set} for c in concept_label}
remaining = set().union(*cover.values()) if cover else set()
while remaining:
    c = max(sorted(cover), key=lambda c: len(cover[c] & remaining))
    got = cover[c] & remaining
    if not got: break
    onto_head[f"onto:{node_id[c]}"] = c
    for t in got: onto_assign[t] = f"onto:{node_id[c]}"
    remaining -= got
for t in connected_terms: onto_assign.setdefault(t, None)
for c in concept_label:
    own = f"onto:{node_id[c]}"
    onto_assign[c] = own if own in onto_head else majority(c, onto_assign)

GROUPS = {"cluster":  finalize_groups(cluster_assign, lambda k: label_of(cluster_hub[k]), "Unclustered"),
          "paper":    finalize_groups(paper_assign, paper_name, "Not found in papers"),
          "onto":     finalize_groups(onto_assign, lambda k: label_of(onto_head[k]), "No Wikipedia concept")}
MODE_OF = {"ontology": "onto", "paper": "paper", "cluster": "cluster"}
DEFMODE = MODE_OF[args.color_by]
if DEFMODE == "onto" and not concept_label: DEFMODE = "paper" if docs else "cluster"
for m, label in (("onto", "Ontology groups"), ("paper", "Paper groups"), ("cluster", "Topic clusters")):
    print(f"   {label:<16}: {len(GROUPS[m]['legend'])} legend entries")

def gname(mode, n):
    g = GROUPS[mode]; return g["name"].get(g["key"].get(n), "") if n in g["key"] else ""

# ---------------- 7. Save tables ----------------
def node_row(n):
    is_c = n in concept_label
    return {"node_id": node_id[n], "label": label_of(n), "kind": "ontology_concept" if is_c else "term",
            "mentions": 0 if is_c else freq[n], "papers": 0 if is_c else docfreq[n], "degree": G.degree(n),
            "connected": G.degree(n) > 0, "wikipedia": concept_url[n] if is_c else wiki_url.get(n, ""),
            "ontology_group": gname("onto", n), "paper_group": gname("paper", n), "topic_cluster": gname("cluster", n),
            "primary_paper": primary_paper.get(n, ""),
            "ontology_concepts": "" if is_c else ";".join(sorted(label_of(x) for x in G[n] if x in concept_label)),
            "paper_ids": "" if is_c else ";".join(p for p, _ in term_paper[n].most_common())}
node_rows = [node_row(n) for n in sorted(nodes, key=str.lower)] + \
            [node_row(c) for c in sorted(concept_label, key=lambda c: concept_label[c].lower())]
edge_table = [{"edge_id": r["id"], "source_id": node_id[r["src"]], "target_id": node_id[r["tgt"]],
               "source": label_of(r["src"]), "target": label_of(r["tgt"]), "types": "+".join(r["d"]["types"]),
               "relation": r["rel"], "weight": round(r["d"]["weight"], 3), "evidence": r["d"]["evidence"]} for r in edge_rows]
pd.DataFrame(edge_table).to_csv(OUT_EDGES, index=False)
pd.DataFrame(node_rows).to_csv(OUT_NODES, index=False)
pd.DataFrame([{"paper_id": pid, **m, "connected_terms": len(paper_terms[pid])} for pid, m in paper_meta.items()]).to_csv(OUT_PAPERS, index=False)
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump({"nodes": node_rows, "edges": edge_table}, f, ensure_ascii=False, indent=1, default=int)

# ---------------- 8. Interactive visualisation ----------------
EDGE_COLOR = {"cooc": "rgba(0,200,255,0.45)", "hierarchy": "rgba(255,153,51,0.75)",
              "abbrev": "rgba(255,0,200,0.9)", "wiki": "rgba(0,255,153,0.7)", "onto": "rgba(255,213,79,0.6)"}
GATTR = {"cluster": ("gCluster", "colCluster"), "paper": ("gPaper", "colPaper"), "onto": ("gOnto", "colOnto")}
net = Network(height="100vh", width="100%", bgcolor="#000000", font_color="#FFFFFF", cdn_resources="remote")
hover_js = {}                                   # node id -> data for the hover card
for n in connected:
    is_c = n in concept_label
    if is_c:
        size = 10 + 4 * math.log2(1 + G.degree(n))
        hover_js[node_id[n]] = {"k": "concept", "n": G.degree(n),
                                "terms": sorted(label_of(x) for x in G[n] if x in term_set)[:12]}
    else:
        size = 8 + 5 * math.log2(1 + freq[n]) + 0.4 * G.degree(n)
        d = entry_desc.get(n, "")
        if len(d) > DESC_CHARS: d = d[:DESC_CHARS].rsplit(" ", 1)[0] + "…"
        hover_js[node_id[n]] = {"k": "term", "d": "" if is_disambig.get(n) else d, "dis": bool(is_disambig.get(n)),
                                "f": entry_figs.get(n, [])[:MAX_FIGS], "m": freq[n], "p": docfreq[n],
                                "l": G.degree(n), "a": sorted(aliases.get(n, []))}
    attrs = {}
    for m, (gk, ck) in GATTR.items():
        attrs[gk], attrs[ck] = GROUPS[m]["key"][n], GROUPS[m]["color"][n]
    net.add_node(node_id[n], label=label_of(n), color=GROUPS[DEFMODE]["color"][n],
                 originalColor=GROUPS[DEFMODE]["color"][n], size=size, shape="diamond" if is_c else "dot",
                 kind="concept" if is_c else "term", wiki=concept_url[n] if is_c else wiki_url.get(n, ""), **attrs)
for r in edge_rows:
    d = r["d"]
    prim = next(t for t in ("abbrev", "hierarchy", "cooc", "wiki", "onto") if t in d["types"])
    ev = d["evidence"] or ""
    net.add_edge(node_id[r["src"]], node_id[r["tgt"]], id=r["id"], color=EDGE_COLOR[prim],
                 width=1 + math.log2(1 + d["weight"]) * 0.6, dashes=(prim == "onto"),
                 title=(f"{r['id']} · {r['rel']}\n{ev}")[:300], types=",".join(d["types"]),
                 w=round(d["weight"], 2), ev=ev, rel=r["rel"],
                 isDir=bool(d["dir"]), arrows="to" if d["dir"] else "")
net.barnes_hut(gravity=-9000, spring_length=130, central_gravity=0.2)
net.write_html(OUT_HTML)

def js_json(obj):                       # safe to embed inside <script>
    return json.dumps(obj, ensure_ascii=True).replace("</", "<\\/")

papers_js = {pid: m for pid, m in paper_meta.items()}
term_papers_js = {node_id[t]: [[pid, c, (snippet.get((t, pid), ""))[:260]] for pid, c in term_paper[t].most_common()]
                  for t in connected_terms if term_paper[t]}
legends_js = {m: GROUPS[m]["legend"] for m in GROUPS}


ui = """
<style>
.box{position:fixed;z-index:9999;background:rgba(0,0,0,.82);padding:10px;border-radius:8px;
     border:1px solid #66b2ff;color:#fff;font-family:Arial,sans-serif;font-size:13px}
#panel{top:20px;left:20px} #legend{top:20px;right:20px;max-width:260px}
#info{left:20px;bottom:20px;width:370px;max-height:52vh;overflow:auto;display:none}
#papers{right:20px;bottom:20px;width:330px;max-height:32vh;overflow:auto}
.dot{width:12px;height:12px;border-radius:50%;display:inline-block;margin-right:6px}
#info a,#papers a{color:#8fd0ff} #info h3{margin:0 0 4px 0;font-size:16px}
.muted{color:#aaa;font-size:12px} .item{margin:7px 0;padding-bottom:6px;border-bottom:1px solid #333}
.tag{font-size:11px;padding:1px 5px;border-radius:8px;background:#233;color:#9cf;margin-left:4px}
.nb{cursor:pointer;color:#ffd54f;text-decoration:underline}
mark{background:#ffd54f;color:#000;padding:0 1px}
.x{cursor:pointer;color:#aaa;font-size:16px;margin-left:8px}
.hd{cursor:pointer;font-weight:bold;user-select:none;display:flex;justify-content:space-between;align-items:center;gap:14px}
.tg{color:#8fd0ff;font-weight:normal}
.box.min .bd{display:none}
.box.min{padding:6px 10px}
.box:not(.min) .hd{margin-bottom:8px}
.lg{cursor:pointer;padding:2px 4px;border-radius:4px;margin:1px 0} .lg:hover{background:#222} .lg.on{background:#2a3b55;outline:1px solid #66b2ff}
#hovercard{position:fixed;z-index:10001;display:none;max-width:340px;pointer-events:none;background:rgba(10,10,10,.95);
  border:1px solid #66b2ff;border-radius:8px;padding:9px 11px;color:#fff;font-family:Arial,sans-serif;font-size:12.5px;box-shadow:0 4px 18px #000}
#hovercard .hc-t{font-size:15px;font-weight:bold;margin-bottom:2px} #hovercard .hc-d{margin:6px 0;line-height:1.4;color:#e8e8e8}
#hovercard .hc-f{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px} #hovercard figure{margin:0;max-width:150px}
#hovercard img{max-width:150px;max-height:110px;border-radius:4px;background:#fff;display:block}
#hovercard figcaption{font-size:10.5px;color:#aaa;margin-top:2px}
.chip{display:inline-block;font-size:11px;border:1px solid #666;border-radius:10px;padding:1px 7px;margin:2px 3px 2px 0;color:#ddd}
.chip .dot{width:8px;height:8px;margin-right:4px}
#legend select,#panel select{background:#111;color:#fff;border:1px solid #446;border-radius:4px;padding:2px}
#papers.min,#info.min{width:auto}
</style>
<div id="panel" class="box min"><div class="hd" onclick="toggleBox('panel')"><span>🔍 Search &amp; filters</span><span class="tg">▸</span></div><div class="bd">
 <input id="search" placeholder="Search term"> <button onclick="searchNode()">Go</button>
 <button onclick="clearSelection()">Reset</button><br><br>
 <b>Show links</b><br>
 <label><input type="checkbox" class="et" value="cooc" checked> co-occur in papers</label><br>
 <label><input type="checkbox" class="et" value="hierarchy" checked> more specific term</label><br>
 <label><input type="checkbox" class="et" value="abbrev" checked> abbreviation</label><br>
 <label><input type="checkbox" class="et" value="wiki" checked> Wikipedia link between terms</label><br>
 <label><input type="checkbox" class="et" value="onto" checked> ontology concept (Wikipedia)</label><br><br>
 <b>Colour nodes by</b> <select id="colorBy" onchange="setColorMode(this.value)">
  <option value="onto">Wikipedia ontology</option><option value="paper">Source paper</option><option value="cluster">Topic cluster</option></select><br><br>
 <label><input type="checkbox" id="hideOthers"> hide unrelated nodes when selecting</label><br>
 <label><input type="checkbox" id="showArrows" checked> show direction arrows (term → concept, specific → general)</label><br><br>
 <span>__CONN__ of __TOTAL__ terms connected · __NCONCEPT__ ontology concepts (◆)</span><br>
 <span class="muted">Click a node to highlight it and its links. Click empty space or press Esc to reset.</span>
</div></div>
<div id="legend" class="box"><div class="hd" onclick="toggleBox('legend')"><span id="legendtitle">Groups</span><span class="tg">▾</span></div><div class="bd">
 <div id="legendbody"></div>
 <div style="margin-top:6px" class="muted">Click a group to isolate it · click again to release<br>● term (size = mentions) · ◆ Wikipedia ontology concept · arrow = direction of the relation<br>Hover a link for its ID and supporting sentence · click a link for details</div></div></div>
<div id="info" class="box"><div class="hd" onclick="toggleBox('info')"><span id="infotitle">Details</span>
 <span><span class="tg" id="tg-info">▾</span><span class="x" onclick="event.stopPropagation();clearSelection()">×</span></span></div><div class="bd" id="infobody"></div></div>
<div id="hovercard"></div>
<div id="papers" class="box min"><div class="hd" onclick="toggleBox('papers')"><span>Source papers (__NPAPERS__)</span><span class="tg">▸</span></div><div class="bd">
 <div class="muted">click a title to open; "terms" highlights its terms</div><div id="paperlist"></div></div></div>
<script>
const PAPERS = __PAPERS__;
const TERM_PAPERS = __TERMPAPERS__;
const PAPER_TERMS = __PAPERTERMS__;
const LEGENDS = __LEGENDS__;
const HOVER = __HOVER__;
const TYPE_NAME = {cooc:"co-occur", hierarchy:"more specific", abbrev:"abbreviation", wiki:"Wikipedia link", onto:"ontology concept"};
const MODE_NAME = {onto:"Wikipedia ontology groups", paper:"Source-paper groups", cluster:"Topic clusters"};
const MODE_SHORT = {onto:"ontology", paper:"paper", cluster:"cluster"};
const GKEY = {cluster:"gCluster", paper:"gPaper", onto:"gOnto"}, GCOL = {cluster:"colCluster", paper:"colPaper", onto:"colOnto"};
let colorMode = "__COLORMODE__", selGroup = null;
const nodesDS = network.body.data.nodes, edgesDS = network.body.data.edges;
// Node labels: attached to every node with one fixed font size, and drawn only once the view is zoomed in
// far enough for them to be legible (a label is hidden while its on-screen height is below LABEL_MIN_PX).
const LABEL_FONT = __LABELFONT__, LABEL_MIN_PX = __LABELMIN__;
function labelFont(color){ return {color:color, size:LABEL_FONT, strokeWidth:3, strokeColor:"#000000"}; }
nodesDS.update(nodesDS.getIds().map(id=>({id:id, font:labelFont("#ffffff"),
                                          scaling:{label:{enabled:false, drawThreshold:LABEL_MIN_PX}}})));
let selected = null, selPaper = null;

function toggleBox(id){
  const b = document.getElementById(id); b.classList.toggle("min");
  const t = b.querySelector(".hd .tg"); if (t) t.textContent = b.classList.contains("min") ? "▸" : "▾";
}
function openInfo(title, html){
  const box = document.getElementById("info"); box.classList.remove("min");
  document.getElementById("tg-info").textContent = "▾";
  document.getElementById("infotitle").textContent = title;
  const body = document.getElementById("infobody"); body.innerHTML = html; body.scrollTop = 0;
  box.style.display = "block";
}
function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
function markTerm(text, term){
  let t = esc(text);
  try { return t.replace(new RegExp("("+esc(term).replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&")+")","ig"), "<mark>$1</mark>"); } catch(e){ return t; }
}
function enabledTypes(){ return [...document.querySelectorAll(".et:checked")].map(c=>c.value); }
function edgeOn(e,on){ return (e.types||"").split(",").some(t=>on.includes(t)); }
function paperLink(pid){
  const p = PAPERS[pid] || {title:pid,url:""};
  const t = esc(p.title || pid);
  return p.url ? '<a href="'+esc(p.url)+'" target="_blank" rel="noopener">'+t+'</a>' : t;
}

function applyView(){
  const on = enabledTypes(), hideOthers = document.getElementById("hideOthers").checked;
  const edges = edgesDS.get();
  let focus = null;
  if (selected){
    focus = new Set([selected]);
    edges.forEach(e=>{ if (edgeOn(e,on) && (e.from===selected || e.to===selected)){ focus.add(e.from); focus.add(e.to);} });
  } else if (selPaper){
    focus = new Set((PAPER_TERMS[selPaper]||[]).map(x=>x[0]));
  } else if (selGroup){
    focus = new Set(nodesDS.get().filter(n=>n[GKEY[selGroup.mode]]===selGroup.key).map(n=>n.id));
  }
  nodesDS.update(nodesDS.get().map(n=>{
    const inF = !focus || focus.has(n.id), isSel = n.id===selected;
    return {id:n.id, hidden: !!(focus && !inF && hideOthers),
            color: inF ? {background:n.originalColor, border: isSel?"#ffffff":n.originalColor,
                          highlight:{background:n.originalColor,border:"#ffffff"}}
                       : {background:"rgba(90,90,90,0.15)", border:"rgba(90,90,90,0.15)"},
            borderWidth: isSel?4:1,
            font: labelFont(inF ? "#ffffff" : "rgba(255,255,255,0.35)")};   // dimmed nodes keep a (fainter) label
  }));
  edgesDS.update(edges.map(e=>{
    let vis = edgeOn(e,on);
    if (selected) vis = vis && (e.from===selected || e.to===selected);
    else if (selPaper || selGroup) vis = vis && focus.has(e.from) && focus.has(e.to);
    const w0 = e.w0 || e.width || 1;
    return {id:e.id, hidden:!vis, w0:w0, width: selected ? Math.max(w0,2.5) : w0};
  }));
  return focus;
}

function fitFocus(focus){
  // zoom to the selection but keep it in the middle, clear of the side panels
  const ids = Array.from(focus); if(!ids.length) return;
  const pos = network.getPositions(ids); let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
  ids.forEach(i=>{ const q=pos[i]; x0=Math.min(x0,q.x); x1=Math.max(x1,q.x); y0=Math.min(y0,q.y); y1=Math.max(y1,q.y); });
  const c = document.querySelector("canvas"), W = c.clientWidth, H = c.clientHeight;
  const sc = Math.min(1.2, W/((x1-x0)*1.8+250), H/((y1-y0)*1.8+250));
  network.moveTo({position:{x:(x0+x1)/2, y:(y0+y1)/2}, scale:sc, animation:{duration:500}});
}

function selectNode(id){
  selected = id; selPaper = null; selGroup = null; renderLegend();
  const focus = applyView();
  showNodeInfo(id);
  fitFocus(focus);
}

function selectPaper(pid){
  selected = null; selPaper = pid; selGroup = null; renderLegend();
  const focus = applyView();
  const p = PAPERS[pid] || {title:pid}, terms = PAPER_TERMS[pid] || [];
  let h = '<h3>'+paperLink(pid)+'</h3>';
  h += '<div class="muted">'+esc([p.authors,p.year].filter(Boolean).join(" · "))+'</div>';
  h += '<p>'+terms.length+' graph terms mentioned (click one to inspect):</p>';
  h += terms.map(t=>'<span class="nb" onclick="selectNode(\\''+esc(t[0])+'\\')">'+esc(nodesDS.get(t[0]).label)+'</span> <span class="muted">'+esc(t[0])+' ×'+t[1]+'</span>').join(" · ");
  openInfo("Paper", h);
  if (focus.size) fitFocus(focus);
}

function groupChips(n){
  return ["onto","paper","cluster"].map(m=>{
    const g = (LEGENDS[m]||[]).find(x=>x.key===n[GKEY[m]]);
    return '<span class="chip"><span class="dot" style="background:'+n[GCOL[m]]+'"></span>'+MODE_SHORT[m]+': '
         + esc(g ? g.label.replace(/ \\(\\d+\\)$/,"") : "–")+'</span>';
  }).join("");
}

function showNodeInfo(id){
  const n = nodesDS.get(id), on = enabledTypes(), isC = n.kind==="concept";
  const links = edgesDS.get().filter(e=>edgeOn(e,on) && (e.from===id||e.to===id))
                 .map(e=>({other:e.from===id?e.to:e.from, types:e.types, w:e.w||0, ev:e.ev||"", eid:e.id,
                           dir:e.isDir ? (e.from===id ? "→ " : "← ") : ""}))
                 .sort((a,b)=>b.w-a.w);
  const tp = TERM_PAPERS[id] || [];
  let h = '<h3>'+esc(n.label)+'</h3>';
  h += '<div class="muted">ID <b>'+esc(id)+'</b> · '+(isC?'ontology concept (Wikipedia)':'term')+'</div>';
  h += '<div>'+groupChips(n)+'</div>';
  h += '<div class="muted">'+links.length+' connections'+(isC?'':' · mentioned in '+tp.length+' paper'+(tp.length===1?'':'s'))+'</div>';
  if (n.wiki) h += '<div><a href="'+esc(n.wiki)+'" target="_blank" rel="noopener">Wikipedia ↗</a></div>';
  if (!isC){
    h += '<p><b>Papers mentioning this term</b></p>';
    if (!tp.length) h += '<div class="muted">Not found in the loaded papers (the term came from the encyclopedia).</div>';
    tp.forEach(x=>{
      h += '<div class="item">'+paperLink(x[0])+' <span class="muted">×'+x[1]+(PAPERS[x[0]]&&PAPERS[x[0]].year?' · '+esc(PAPERS[x[0]].year):'')+'</span>'
         + (x[2]?'<div class="muted">“'+markTerm(x[2],n.label)+'”</div>':'')+'</div>';
    });
  }
  h += '<p><b>Connections</b> <span class="muted">(click to jump)</span></p>';
  links.forEach(l=>{
    const o = nodesDS.get(l.other);
    h += '<div class="item"><span class="nb" onclick="selectNode(\\''+esc(l.other)+'\\')">'+l.dir+(o.kind==="concept"?'◆ ':'')+esc(o.label)+'</span>'
       + ' <span class="muted">'+esc(l.other)+' · '+esc(l.eid)+'</span>'
       + l.types.split(",").map(t=>'<span class="tag">'+(TYPE_NAME[t]||t)+'</span>').join("")
       + (l.ev?'<div class="muted">'+esc(l.ev.length>170?l.ev.slice(0,170)+"…":l.ev)+'</div>':'')+'</div>';
  });
  openInfo(isC?"Ontology concept":"Term details", h);
}

function showEdgeInfo(eid){
  const e = edgesDS.get(eid); if (!e) return;
  const a = nodesDS.get(e.from), b = nodesDS.get(e.to);
  const nb = x=>'<span class="nb" onclick="selectNode(\\''+esc(x.id)+'\\')">'+(x.kind==="concept"?'◆ ':'')+esc(x.label)+'</span> <span class="muted">'+esc(x.id)+'</span>';
  let h = '<h3>Link '+esc(e.id)+'</h3>';
  h += '<div>'+nb(a)+(e.isDir?' → ':' ↔ ')+nb(b)+'</div>';
  h += '<div class="muted">relation: '+esc((e.rel||"").replace(/_/g," ").replace(/\\+/g," + "))+' · weight '+(e.w||0)+'</div>';
  h += '<div>'+(e.types||"").split(",").map(t=>'<span class="tag">'+(TYPE_NAME[t]||t)+'</span>').join("")+'</div>';
  if (e.ev) h += '<p class="muted">'+esc(e.ev)+'</p>';
  openInfo("Link details", h);
}

function renderLegend(){
  document.getElementById("legendtitle").textContent = MODE_NAME[colorMode];
  document.getElementById("colorBy").value = colorMode;
  const box = document.getElementById("legendbody");
  box.innerHTML = (LEGENDS[colorMode]||[]).map(g=>'<div class="lg'+(selGroup&&selGroup.key===g.key?' on':'')+'" data-key="'+esc(g.key)+'">'
      +'<span class="dot" style="background:'+g.color+'"></span>'+esc(g.label)+'</div>').join("");
  box.querySelectorAll(".lg").forEach(el=>el.addEventListener("click", ()=>selectGroup(el.dataset.key)));
}

function setColorMode(m){
  colorMode = m; selGroup = null; selected = null; selPaper = null;
  document.getElementById("info").style.display = "none";
  nodesDS.update(nodesDS.get().map(n=>({id:n.id, originalColor:n[GCOL[m]]})));
  applyView(); renderLegend();
}

function selectGroup(key){
  if (selGroup && selGroup.key===key){ clearSelection(); return; }
  selected = null; selPaper = null; selGroup = {mode:colorMode, key:key};
  const focus = applyView(); renderLegend();
  const g = (LEGENDS[colorMode]||[]).find(x=>x.key===key) || {label:key, color:"#888"};
  const members = nodesDS.get().filter(n=>n[GKEY[colorMode]]===key).sort((a,b)=>a.label.localeCompare(b.label));
  let h = '<h3><span class="dot" style="background:'+g.color+'"></span>'+esc(g.label)+'</h3>';
  h += '<div class="muted">'+MODE_NAME[colorMode]+' · '+members.length+' nodes (click one to inspect)</div><p>';
  h += members.map(n=>'<span class="nb" onclick="selectNode(\\''+esc(n.id)+'\\')">'+(n.kind==="concept"?'◆ ':'')+esc(n.label)+'</span>').join(" · ")+'</p>';
  openInfo("Group", h);
  if (focus && focus.size) fitFocus(focus);
}

function clearSelection(){
  selected = null; selPaper = null; selGroup = null; applyView(); renderLegend();
  document.getElementById("info").style.display = "none";
  network.fit({animation:{duration:400}});
}

function searchNode(){
  const v = document.getElementById("search").value.toLowerCase().trim(); if(!v) return;
  const all = nodesDS.get();
  const f = all.find(n=>n.label.toLowerCase()===v || n.id.toLowerCase()===v) || all.find(n=>n.label.toLowerCase().includes(v));
  if(!f) return alert("Term not in graph (it may have no links - see the _nodes.csv file)");
  selectNode(f.id);
}

network.on("click", p=>{
  if (p.nodes.length) selectNode(p.nodes[0]);
  else if (p.edges.length) showEdgeInfo(p.edges[0]);
  else if (selected||selPaper||selGroup) clearSelection();
});
document.getElementById("search").addEventListener("keydown", e=>{ if(e.key==="Enter") searchNode(); });
document.addEventListener("keydown", e=>{ if(e.key==="Escape") clearSelection(); });
function applyArrows(){
  const on = document.getElementById("showArrows").checked;
  edgesDS.update(edgesDS.get().filter(e=>e.isDir).map(e=>({id:e.id, arrows:{to:{enabled:on, scaleFactor:0.6}}})));
}
document.getElementById("showArrows").addEventListener("change", applyArrows);
document.querySelectorAll(".et,#hideOthers").forEach(cb=>cb.addEventListener("change", ()=>{
  applyView(); if (selected) showNodeInfo(selected);
}));
renderLegend();

// Hover card: description + figures from the encyclopedia, plus the term's statistics
const hc = document.getElementById("hovercard"); let hoverId = null;
function renderHover(id){
  const n = nodesDS.get(id), h = HOVER[id];
  if (!n || n.hidden || !h) return false;
  let x = '<div class="hc-t">'+esc(n.label)+' <span class="muted">'+esc(id)+'</span></div>';
  if (h.k === "concept"){
    x += '<div class="muted">Wikipedia ontology concept · shared by '+h.n+' term'+(h.n===1?'':'s')+'</div>';
    if (h.terms && h.terms.length) x += '<div class="hc-d">'+h.terms.map(esc).join(", ")+(h.n>h.terms.length?" …":"")+'</div>';
  } else {
    x += '<div class="muted">mentions: '+h.m+' · papers: '+h.p+' · links: '+h.l+'</div>';
    if (h.a && h.a.length) x += '<div class="muted">also: '+h.a.map(esc).join(", ")+'</div>';
    if (h.d) x += '<div class="hc-d">'+esc(h.d)+'</div>';
    else x += '<div class="muted" style="margin:6px 0">'+(h.dis?'Wikipedia disambiguation page – no single description.':'No description in the encyclopedia.')+'</div>';
    if (h.f && h.f.length) x += '<div class="hc-f">'+h.f.map(f=>'<figure><img src="'+esc(f[0])+'" referrerpolicy="no-referrer" onerror="this.parentNode.hidden=true">'
                                +(f[1]?'<figcaption>'+esc(f[1])+'</figcaption>':'')+'</figure>').join("")+'</div>';
  }
  hc.innerHTML = x; hc.style.display = "block"; return true;
}
function hideHover(){ hoverId = null; hc.style.display = "none"; }
function placeHover(cx, cy){
  const w = hc.offsetWidth, hh = hc.offsetHeight; let l = cx + 16, t = cy + 16;
  if (l + w > window.innerWidth - 8) l = cx - w - 16;
  if (t + hh > window.innerHeight - 8) t = window.innerHeight - hh - 8;
  hc.style.left = Math.max(8, l) + "px"; hc.style.top = Math.max(8, t) + "px";
}
(function(){
  const cv = document.querySelector("canvas"); if (!cv) return;
  cv.addEventListener("mousemove", ev=>{
    if (ev.buttons){ hideHover(); return; }                       // dragging / panning
    const r = cv.getBoundingClientRect();
    const id = network.getNodeAt({x:ev.clientX-r.left, y:ev.clientY-r.top});
    if (id !== hoverId){ hoverId = id; if (id == null || !renderHover(id)) { hoverId = null; hc.style.display = "none"; } }
    if (hoverId) placeHover(ev.clientX, ev.clientY);
  });
  cv.addEventListener("mouseleave", hideHover);
  cv.addEventListener("wheel", hideHover);
})();

(function buildPaperList(){
  const box = document.getElementById("paperlist");
  const ids = Object.keys(PAPERS).sort((a,b)=>(PAPER_TERMS[b]||[]).length-(PAPER_TERMS[a]||[]).length);
  if (!ids.length){ box.innerHTML = '<div class="muted">No papers loaded (use --text-dir).</div>'; return; }
  box.innerHTML = ids.map(pid=>{
    const p = PAPERS[pid];
    return '<div class="item">'+paperLink(pid)+'<div class="muted">'+esc([p.authors,p.year].filter(Boolean).join(" · "))+'</div>'
         + '<span class="nb" onclick="selectPaper(\\''+esc(pid).replace(/'/g,"\\\\'")+'\\')">terms ('+(PAPER_TERMS[pid]||[]).length+')</span></div>';
  }).join("");
})();
</script>
"""
ui = (ui.replace("__CONN__", str(len(connected_terms))).replace("__TOTAL__", str(len(nodes)))
        .replace("__NCONCEPT__", str(len(concept_label))).replace("__LEGENDS__", js_json(legends_js)).replace("__HOVER__", js_json(hover_js))
        .replace("__COLORMODE__", DEFMODE).replace("__NPAPERS__", str(len(papers_js)))
        .replace("__PAPERS__", js_json(papers_js)).replace("__TERMPAPERS__", js_json(term_papers_js))
        .replace("__PAPERTERMS__", js_json(dict(paper_terms)))
        .replace("__LABELFONT__", str(args.label_font_size)).replace("__LABELMIN__", str(args.label_min_px)))
with open(OUT_HTML, encoding="utf-8") as f: page = f.read()
with open(OUT_HTML, "w", encoding="utf-8") as f: f.write(page.replace("</body>", ui + "</body>"))

print(f"\n🚀 Graph saved: {OUT_HTML}")
print(f"   Edge list : {OUT_EDGES}   (edge_id, source_id, target_id, ...)\n   Node table: {OUT_NODES}  (node_id, groups; includes the {len(unconnected)} unconnected terms)"
      f"\n   Papers    : {OUT_PAPERS}\n   Graph JSON: {OUT_JSON}")
if unconnected: print("   Unconnected examples:", ", ".join(unconnected[:15]))
