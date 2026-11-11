#!/usr/bin/env python3
"""Build the Java Full-Stack Notes pages from the fragments in src/parts.

Usage:  python src/build.py
Writes one HTML page per topic plus index.html into the repository root (the parent of src).
"""
import colorsys
import hashlib
import html
import json
import pathlib
import re
import sys
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = pathlib.Path(__file__).resolve().parent
OUT = SRC.parent
PARTS = SRC / "parts"
CFG = json.loads((SRC / "topics.json").read_text("utf-8"))

HLJS = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0"
HLJS_EXTRA = ["dockerfile", "nginx", "properties", "groovy", "http"]
# subresource-integrity hashes of the files above; regenerate them whenever HLJS or HLJS_EXTRA changes
HLJS_SRI = {
    "highlight.min.js": "sha384-F/bZzf7p3Joyp5psL90p/p89AZJsndkSoGwRpXcZhleCWhd8SnRuoYo4d0yirjJp",
    "languages/dockerfile.min.js": "sha384-H3wUmCndJNBOuIIzcLSr2zLLZYs8PYuw6qKyENk7THEnYQJvOMDBu42P9XsJSRKw",
    "languages/nginx.min.js": "sha384-p6UV3HZc7zs9wUF6j4Knk3bpx1/JnhlwDoFnKJAOogB1cUi32u31NlnZ2s2dW8IR",
    "languages/properties.min.js": "sha384-tlJaeulTOJz9iqadCPTY2JwJVayIS3pMaQkEOgibHjwjmI6Fve8TLKvsR8tfmKwa",
    "languages/groovy.min.js": "sha384-N2BpqybE0W3/jhUPUCcAr9I33RlAVfy/E+lEPCSY+NLvXJdrOUWK5+/ocIoPmA64",
    "languages/http.min.js": "sha384-wt2eEhJoUmjz8wmTq0k9WvI19Pumi9/h7B87i0wc7QMYwnCJ0dcuyfcYo/ui1M6t",
}
PRI = {
    "must": ("pri-must", "Must"),
    "good": ("pri-good", "Good to know"),
    "later": ("pri-later", "Later"),
    "con": ("pri-con", "Concept"),
}

ICONS = {
    "i-git": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="9" r="2"/><path d="M6 7v10M18 11c0 4-6 4-12 6"/>',
    "i-java": '<path d="M5 9h11v5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4z"/><path d="M16 10h1.5a2.5 2.5 0 0 1 0 5H16M8 3v3M12 3v3"/>',
    "i-db": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
    "i-leaf": '<path d="M5 19C5 10 10 5 19 5c0 9-5 14-14 14z"/><path d="M5 19c3-5 6-8 10-10"/>',
    "i-tree": '<circle cx="12" cy="5" r="2"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/><path d="M11 7l-4 9M13 7l4 9"/>',
    "i-window": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 6.5h.01M10.5 6.5h.01"/>',
    "i-cloud": '<path d="M7 18a4 4 0 0 1-.5-7.97A5.5 5.5 0 0 1 17.5 8.6 4.7 4.7 0 0 1 17 18z"/>',
    "i-sitemap": '<rect x="9" y="3" width="6" height="5" rx="1"/><rect x="3" y="16" width="6" height="5" rx="1"/><rect x="15" y="16" width="6" height="5" rx="1"/><path d="M12 8v4M6 16v-2a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v2"/>',
    "i-cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "i-route": '<circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M8 19h8a3 3 0 0 0 0-6H8a3 3 0 0 1 0-6h8"/>',
    "i-sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "i-moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
    "i-up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "i-chev": '<path d="M6 9l6 6 6-6"/>',
    "i-check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "i-info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "i-list": '<path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01"/>',
    "i-book": '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H12v16H5.5A1.5 1.5 0 0 1 4 18.5zM20 5.5A1.5 1.5 0 0 0 18.5 4H12v16h6.5a1.5 1.5 0 0 0 1.5-1.5z"/>',
    "i-compass": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    "i-search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "i-grid": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
    "i-clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "i-layers": '<path d="M12 3 2 8l10 5 10-5z"/><path d="M2 13l10 5 10-5"/>',
    "i-left": '<path d="M15 6l-6 6 6 6"/>',
    "i-right": '<path d="M9 6l6 6-6 6"/>',
    "i-x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "i-target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "i-calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "i-spark": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
}
SPRITE = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
          + "".join(f'<symbol id="{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items())
          + "</defs></svg>")

THEME_INIT = ("<script>(function(){var d=document.documentElement,t=null;d.className+=' js';"
              "try{t=localStorage.getItem('rm-theme')}catch(e){}"
              "if(t!=='dark'&&t!=='light'){t=(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light'}"
              "d.setAttribute('data-theme',t)})();</script>")

TAG_RE = re.compile(r"<[^>]+>")
PRE_RE = re.compile(r"<pre\b[^>]*>.*?</pre>", re.S)
ART_RE = re.compile(r"<article\b([^>]*)>")


def asset_ver(name):
    data = (OUT / "assets" / name).read_bytes()
    return hashlib.sha1(data).hexdigest()[:10]


def esc(s):
    return html.escape(str(s), quote=True)


def ico(name, cls=""):
    return f'<svg class="ico{(" " + cls) if cls else ""}" aria-hidden="true"><use href="#{name}"/></svg>'


def hexcolor(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def favicon(hue, icon):
    c1, c2 = hexcolor(hue, 76, 44), hexcolor(hue + 40, 80, 50)
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
           f"<stop offset='0' stop-color='{c1}'/><stop offset='1' stop-color='{c2}'/></linearGradient></defs>"
           "<rect width='32' height='32' rx='8' fill='url(#g)'/>"
           "<g transform='translate(4 4)' fill='none' stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'>"
           + ICONS[icon].replace('"', "'") + "</g></svg>")
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="/:=' ")


def stats(text):
    code = PRE_RE.findall(text)
    code_words = sum(len(TAG_RE.sub(" ", c).split()) for c in code)
    prose_words = len(TAG_RE.sub(" ", PRE_RE.sub(" ", text)).split())
    topics = 0
    for m in ART_RE.finditer(text):
        cm = re.search(r'class="([^"]*)"', m.group(1))
        classes = cm.group(1).split() if cm else []
        if "topic" in classes and "recap" not in classes:
            topics += 1
    minutes = prose_words / 200 + code_words / 120
    return {"prose": prose_words, "code": code_words, "topics": topics, "minutes": minutes}


def fmt_min(m):
    m = max(1, round(m))
    if m < 60:
        return f"{m} min"
    h = m / 60
    return f"{round(h * 2) / 2:g} h"


def chip(pri, label=None):
    cls, default = PRI.get(pri, PRI["must"])
    return f'<span class="chip {cls}">{esc(label or default)}</span>'


def hljs_script(path):
    return f'<script defer src="{HLJS}/{path}" integrity="{HLJS_SRI[path]}" crossorigin="anonymous"></script>'


def head(title, desc, hue, icon, depth_css="assets/"):
    extra = "\n".join(hljs_script(f"languages/{x}.min.js") for x in HLJS_EXTRA)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{esc(desc)}">
<title>{esc(title)}</title>
<link rel="icon" href="{favicon(hue, icon)}">
{THEME_INIT}
<link rel="stylesheet" href="{depth_css}notes.css?v={asset_ver("notes.css")}">
{hljs_script("highlight.min.js")}
{extra}
<script defer src="{depth_css}notes.js?v={asset_ver("notes.js")}"></script>
</head>"""


THEME_BTN = (f'<button class="hbtn theme" type="button" data-theme-toggle aria-label="Toggle dark mode">'
             f'{ico("i-sun", "sun")}{ico("i-moon", "moon")}</button>')

LEGEND = [
    ("co-rule", "Rule", "Must-follow rules. Break one and you get a compile error, a crash or a bug."),
    ("co-conv", "Convention", "How professionals name, structure and write it — the accepted best practice."),
    ("co-exc", "Exception / edge case", "Where a rule bends, tricky corner cases, and the runtime exceptions you will meet."),
    ("co-mistake", "Common mistake", "What people often get wrong, usually with the fix."),
    ("co-tip", "Tip", "Shortcuts and habits that save time."),
    ("co-interview", "Interview angle", "How it is asked, and what a strong answer contains."),
    ("co-real", "In real projects", "How the idea shows up in a real codebase."),
    ("co-version", "Version note", "Where Java, Spring or library versions behave differently."),
    ("co-note", "Note", "Extra detail that is worth knowing."),
]


def legend_html():
    items = "".join(f'<div class="co {c} mini"><p class="co-t">{esc(t)}</p><p>{esc(d)}</p></div>' for c, t, d in LEGEND)
    return f"""<details class="legend">
<summary>{ico("i-info")}How to read these notes</summary>
<div class="legend-body">
<p>Every topic card opens with a <b>TL;DR</b> line, then explains the idea, how it works, examples with output, and the coloured boxes below. Each module ends with <b>interview questions</b>, a <b>cheat sheet</b> and <b>practice</b>. Press <b>Mark revised</b> on a card once you can explain it aloud and write its example from memory — your progress is saved in this browser. The sidebar search looks inside the text of every topic, not just the titles.</p>
<div class="legend-grid">{items}</div>
</div>
</details>"""


def build_topic(i, t, topics):
    folder = PARTS / t["slug"]
    mods_html, mod_stats, cards = [], [], []
    for m in t["modules"]:
        files = sorted(folder.glob(f"m{m['n']:02d}-*.html")) if folder.is_dir() else []
        body = "\n".join(f.read_text("utf-8-sig").strip() for f in files)
        if not files:
            body = '<div class="pending"><p>This module is still being written.</p></div>'
        st = stats(body)
        mod_stats.append(st)
        label = m.get("label")
        sub = f'{st["topics"]} topics · about {fmt_min(st["minutes"])} of reading' if files else "Coming soon"
        mods_html.append(
            f'<section class="module" id="m{m["n"]}" data-n="{m["n"]}" data-title="{esc(m["title"])}" aria-labelledby="mod{m["n"]}-h">\n'
            f'<header class="mh"><span class="mh-n" aria-hidden="true">{m["n"]}</span><div class="mh-t">'
            f'<p class="mh-k"><span>Module {m["n"]}</span><span aria-hidden="true">·</span><span>{esc(m["when"])}</span>{chip(m["pri"], label)}</p>'
            f'<h2 id="mod{m["n"]}-h">{esc(m["title"])}</h2><p class="mh-s">{esc(sub)}</p></div></header>\n'
            f"{body}\n</section>")
        cards.append(
            f'<a class="mcard" href="#m{m["n"]}"><span class="mc-n">{m["n"]}</span><span class="mc-body">'
            f'<span class="mc-t">{esc(m["title"])}</span><span class="mc-d">{esc(m["desc"])}</span>'
            f'<span class="mc-m"><span>{esc(m["when"])}</span>{chip(m["pri"], label)}'
            f'{"<span>· " + str(st["topics"]) + " topics</span>" if files else ""}</span></span></a>')
    total = {k: sum(s[k] for s in mod_stats) for k in ("prose", "code", "topics", "minutes")}
    prev_t = topics[i - 1] if i > 0 else None
    next_t = topics[i + 1] if i + 1 < len(topics) else None
    pager = '<nav class="pager" aria-label="Other topics">'
    if prev_t:
        pager += (f'<a class="prev" href="{prev_t["slug"]}.html"><span class="pg-k">← Previous</span>'
                  f'<span class="pg-t">{esc(prev_t["num"])} · {esc(prev_t["title"])}</span></a>')
    if next_t:
        pager += (f'<a class="next" href="{next_t["slug"]}.html"><span class="pg-k">Next →</span>'
                  f'<span class="pg-t">{esc(next_t["num"])} · {esc(next_t["title"])}</span></a>')
    pager += "</nav>"
    roadmap = f'{CFG["roadmap"]}#{t["tab"]}'
    title = f'{t["num"]} · {t["title"]} — Notes'
    page = f"""{head(title, t["lede"], t["hue"], t["icon"])}
<body data-topic="{esc(t["slug"])}" style="--h:{t["hue"]};--h2:{t.get("hue2", t["hue"] + 30)}">
{SPRITE}
<div class="progress" id="progress" aria-hidden="true"></div>
<div class="bg" aria-hidden="true"></div>
<a class="skip" href="#content">Skip to content</a>
<header class="hero" id="top">
  <div class="hero-in">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">{ico("i-grid")}All notes</a><span aria-hidden="true">/</span><span>{esc(t["num"])} · {esc(t["title"])}</span></nav>
    <div class="hero-row">
      <div class="hero-mark" aria-hidden="true">{ico(t["icon"])}</div>
      <div class="hero-txt">
        <p class="kicker">Notes · {esc(t["num"])}</p>
        <h1>{esc(t["title"])}</h1>
        <p class="lede">{esc(t["lede"])}</p>
        <div class="hero-meta">
          <span class="hm">{ico("i-layers")}{len(t["modules"])} modules</span>
          <span class="hm">{ico("i-list")}{total["topics"]} topics</span>
          <span class="hm">{ico("i-clock")}about {fmt_min(total["minutes"])} of reading</span>
          <span class="hm">{ico("i-calendar")}{esc(t["when"])}</span>
        </div>
        <div class="hero-prog"><div class="hero-bar"><i id="rev-fill"></i></div><p class="hero-rev"><b id="rev-count">0</b> of {total["topics"]} topics marked revised</p></div>
      </div>
    </div>
  </div>
  <div class="hero-actions">
    <a class="hbtn" href="{esc(roadmap)}" title="Open this topic in the roadmap">{ico("i-route")}<span>Roadmap</span></a>
    {THEME_BTN}
  </div>
</header>
<div class="mbar" id="mbar">
  <button class="mbar-btn" id="toc-open" type="button" aria-controls="side" aria-expanded="false">{ico("i-list")}Contents</button>
  <span class="mbar-cur" id="mbar-cur">{esc(t["num"])} · {esc(t["title"])}</span>
  <button class="mbar-btn icon theme" type="button" data-theme-toggle aria-label="Toggle dark mode">{ico("i-sun", "sun")}{ico("i-moon", "moon")}</button>
</div>
<div class="scrim" id="scrim" hidden></div>
<div class="shell">
  <aside class="side" id="side" aria-label="Contents">
    <button class="side-x" id="side-x" type="button" aria-label="Close contents">{ico("i-x")}</button>
    <div class="side-head">
      <a class="side-topic" href="#top"><span class="st-ico">{ico(t["icon"])}</span><span><b>{esc(t.get("short", t["title"]))}</b><small>{len(t["modules"])} modules · {total["topics"]} topics</small></span></a>
      <label class="filter">{ico("i-search")}<span class="sr-only">Search these notes</span><input id="toc-filter" type="search" placeholder="Search topics and text…" autocomplete="off" spellcheck="false"></label>
      <p class="filter-info" id="filter-info" hidden></p>
    </div>
    <nav class="toc" id="toc" aria-label="Table of contents"></nav>
    <div class="side-foot"><a href="index.html">← All notes</a></div>
  </aside>
  <main class="notes" id="content">
    <section class="intro" aria-labelledby="intro-h">
      <div class="intro-card">
        <h2 class="sec-h" id="intro-h">{ico("i-compass")}What is inside</h2>
        <p class="intro-p">{esc(t["intro"])}</p>
        <div class="mcards">{"".join(cards)}</div>
      </div>
      {legend_html()}
    </section>
{chr(10).join(mods_html)}
    {pager}
    <footer class="foot"><span>{esc(CFG["site_title"])} · notes as of {esc(CFG["as_of"])}</span><a href="index.html">All notes</a><a href="{esc(roadmap)}">Roadmap</a><a href="#top">Back to top ↑</a></footer>
  </main>
</div>
<button class="totop" id="totop" type="button" aria-label="Back to top">{ico("i-up")}</button>
</body>
</html>
"""
    (OUT / f'{t["slug"]}.html').write_bytes(page.encode("utf-8"))
    return total


def build_index(results):
    topics = CFG["topics"]
    n_mod = sum(len(t["modules"]) for t in topics)
    n_top = sum(r["topics"] for r in results)
    minutes = sum(r["minutes"] for r in results)
    cards = []
    for t, r in zip(topics, results):
        mods = "".join(f"<li>{esc(m['title'])}</li>" for m in t["modules"])
        cards.append(f"""<a class="tcard hue" href="{t["slug"]}.html" style="--h:{t["hue"]};--h2:{t.get("hue2", t["hue"] + 30)}">
  <div class="tc-top"><span class="tc-ico">{ico(t["icon"])}</span><span><span class="tc-n">NOTES · {esc(t["num"])}</span><span class="tc-t">{esc(t["title"])}</span></span></div>
  <p class="tc-d">{esc(t["lede"])}</p>
  <ul class="tc-mods">{mods}</ul>
  <div class="tc-meta"><span>{ico("i-layers")}{len(t["modules"])} modules</span><span>{ico("i-list")}{r["topics"]} topics</span><span>{ico("i-clock")}about {fmt_min(r["minutes"])}</span><span>{ico("i-calendar")}{esc(t["when"])}</span></div>
  <div class="tc-prog" data-progress-for="{esc(t["slug"])}" data-total="{r["topics"]}"><i></i></div>
  <div class="tc-meta"><span data-progress-text="{esc(t["slug"])}">0 / {r["topics"]} revised</span></div>
</a>""")
    roadmap = CFG["roadmap"]
    page = f"""{head(CFG["site_title"], CFG["site_lede"], 262, "i-book")}
<body class="home" data-topic="index" style="--h:262;--h2:196">
{SPRITE}
<div class="bg" aria-hidden="true"></div>
<a class="skip" href="#content">Skip to content</a>
<header class="hero" id="top">
  <div class="hero-in">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{esc(roadmap)}">{ico("i-route")}Roadmap</a><span aria-hidden="true">/</span><span>Notes</span></nav>
    <div class="hero-row">
      <div class="hero-mark" aria-hidden="true">{ico("i-book")}</div>
      <div class="hero-txt">
        <p class="kicker">As of {esc(CFG["as_of"])}</p>
        <h1>{esc(CFG["site_title"])}</h1>
        <p class="lede">{esc(CFG["site_lede"])}</p>
        <div class="hero-meta">
          <span class="hm">{ico("i-grid")}{len(topics)} topics</span>
          <span class="hm">{ico("i-layers")}{n_mod} modules</span>
          <span class="hm">{ico("i-list")}{n_top} topic cards</span>
          <span class="hm">{ico("i-clock")}about {fmt_min(minutes)} of reading</span>
        </div>
      </div>
    </div>
  </div>
  <div class="hero-actions">{THEME_BTN}</div>
</header>
<div class="shell">
  <main id="content">
    <section class="home-sec" aria-label="Topics"><div class="tgrid">
{chr(10).join(cards)}
    </div></section>
    <section class="home-sec howto" aria-labelledby="howto-h">
      <h2 class="sec-h" id="howto-h">{ico("i-target")}How to study with these notes</h2>
      <ol class="steps">
        <li><b>Follow the roadmap order.</b> Git, then Core Java and SQL, then Spring Boot, frontend, DevOps and system design — with DSA every day alongside. CS fundamentals fit in months 9–11.</li>
        <li><b>Read one topic card, then close it and write the code yourself.</b> Where you get stuck is exactly what you did not understand yet.</li>
        <li><b>Mark a topic revised</b> only when you can explain it out loud and write its example without looking. Progress is saved in this browser.</li>
        <li><b>Revise after 1 day, 7 days and 30 days.</b> The interview questions, cheat sheet and practice at the end of every module are built for this.</li>
        <li><b>Search instead of scrolling.</b> The search box in each page's sidebar looks inside the text of every topic.</li>
      </ol>
    </section>
    <footer class="foot home-sec"><span>{esc(CFG["site_title"])} · notes as of {esc(CFG["as_of"])}</span><a href="{esc(roadmap)}">Open the roadmap</a></footer>
  </main>
</div>
</body>
</html>
"""
    (OUT / "index.html").write_bytes(page.encode("utf-8"))
    return n_top, minutes


def main():
    topics = CFG["topics"]
    results = []
    for i, t in enumerate(topics):
        r = build_topic(i, t, topics)
        results.append(r)
        print(f'{t["slug"]:<22} {r["topics"]:>4} topics  {r["prose"]:>8,} prose words  {r["code"]:>7,} code words  ~{fmt_min(r["minutes"])}')
    n, minutes = build_index(results)
    print(f"index.html             {n:>4} topics in total, about {fmt_min(minutes)} of reading")


if __name__ == "__main__":
    main()
