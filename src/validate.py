#!/usr/bin/env python3
"""Validate note fragments (chunk files) for the Java Full-Stack Notes.

Usage:
  python validate.py <topic-slug> [--only PATTERN ...] [--list]
  python validate.py --all [--list]

Examples:
  python validate.py 02-core-java --only "m04-*"
  python validate.py 05-dsa --only "m03-5*" --only "m04-*"

Exit code 1 when any ERROR is found.
"""
import argparse
import fnmatch
import pathlib
import re
import sys
from html.parser import HTMLParser

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = pathlib.Path(__file__).resolve().parent
PARTS = HERE / "parts"

ALLOWED_TAGS = {
    "article", "div", "p", "h3", "h4", "h5", "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "pre", "code", "strong", "b",
    "em", "i", "kbd", "a", "br", "hr", "sup", "sub", "small", "mark", "blockquote",
    "figure", "figcaption", "details", "summary", "span",
}
VOID = {"br", "hr"}
CO_VARIANTS = {
    "co-rule", "co-conv", "co-exc", "co-mistake", "co-tip", "co-note", "co-interview",
    "co-version", "co-real",
}
LANGS = {
    "java", "kotlin", "groovy", "sql", "bash", "shell", "plaintext", "javascript", "jsx",
    "typescript", "tsx", "xml", "html", "css", "scss", "json", "yaml", "properties", "ini",
    "dockerfile", "nginx", "http", "diff", "markdown", "python",
}
ALLOWED_CLASSES = {
    "topic", "recap", "tldr", "mintro", "co", "co-t", "out", "vs", "vs-bad", "vs-good",
    "vs-t", "tbl-wrap", "tbl", "pc", "pc-pro", "pc-con", "pc-t", "steps", "terms", "fig",
    "mermaid", "diagram", "qa", "qa-a", "cheat", "chip", "pri-must", "pri-good",
    "pri-later", "pri-con",
} | CO_VARIANTS
MERMAID_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "erDiagram",
    "stateDiagram-v2", "stateDiagram", "gitGraph",
)
ID_RE = re.compile(r"^m(\d+)-[a-z0-9]+(?:-[a-z0-9]+)*$")
FILE_RE = re.compile(r"^m(\d{2})-(\d{2})\.html$")
AMP_RE = re.compile(r"&(?!(?:[a-zA-Z][a-zA-Z0-9]{1,31}|#\d{1,7}|#[xX][0-9a-fA-F]{1,6});)")


class Frag(HTMLParser):
    def __init__(self, module_no):
        super().__init__(convert_charrefs=True)
        self.module_no = module_no
        self.errors, self.warns = [], []
        self.stack = []
        self.ids = []
        self.articles = []
        self.cur_article = None
        self.pre_depth = 0
        self.inline_code_depth = 0
        self.mermaid = []
        self.cur_mermaid = None
        self.long_lines = 0

    def err(self, msg, line=None):
        self.errors.append((line or self.getpos()[0], msg))

    def warn(self, msg, line=None):
        self.warns.append((line or self.getpos()[0], msg))

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, True)

    def _start(self, tag, attrs, selfclose):
        line = self.getpos()[0]
        a = {k: (v if v is not None else "") for k, v in attrs}
        cls = set(a.get("class", "").split())
        parent = self.stack[-1] if self.stack else None

        if tag not in ALLOWED_TAGS:
            self.err(f"<{tag}> is not allowed — if this is code or text, escape '<' as &lt;", line)
        if self.pre_depth:
            if not (tag == "code" and parent and parent["tag"] == "pre"):
                self.err(f"tag <{tag}> inside <pre> — escape '<' as &lt; (no tags inside code)", line)
        elif self.inline_code_depth:
            self.err(f"tag <{tag}> inside inline <code> — escape '<' as &lt;", line)
        if "style" in a:
            self.err("inline style attribute is not allowed", line)
        for c in cls:
            if c not in ALLOWED_CLASSES and not c.startswith("language-"):
                self.warn(f"unknown class '{c}' on <{tag}>", line)
        if "id" in a:
            self.ids.append((a["id"], line))

        if parent is not None:
            parent["children"].append((tag, cls, line))
        elif not ((tag == "div" and "mintro" in cls) or (tag == "article" and "topic" in cls)):
            self.err(f"top-level <{tag}> — only div.mintro and article.topic may be at the top level", line)

        if tag in ("h1", "h2"):
            self.err(f"<{tag}> is not allowed in fragments (h3 = article title, h4/h5 inside)", line)
        if tag == "article":
            if self.cur_article is not None:
                self.err("nested <article>", line)
            aid = a.get("id", "")
            art = {"id": aid, "line": line, "recap": "recap" in cls, "words": 0,
                   "codewords": 0, "qa": 0, "li": 0, "title": ""}
            if "topic" not in cls:
                self.err("article must have class 'topic'", line)
            if not aid:
                self.err("article without an id", line)
            else:
                m = ID_RE.match(aid)
                if not m:
                    self.err(f"bad article id '{aid}' (lowercase + hyphens, must start with m<N>-)", line)
                elif int(m.group(1)) != self.module_no:
                    self.err(f"article id '{aid}' does not match module {self.module_no} of this file", line)
            self.cur_article = art
            self.articles.append(art)
        if tag == "pre":
            self.pre_depth += 1
            if "mermaid" in cls:
                self.cur_mermaid = {"line": line, "text": []}
        if tag == "code":
            if self.pre_depth:
                langs = [c[9:] for c in cls if c.startswith("language-")]
                if not langs:
                    self.err("<pre><code> without class=\"language-…\"", line)
                elif langs[0] not in LANGS:
                    self.err(f"language '{langs[0]}' is not in the allowed list", line)
            else:
                self.inline_code_depth += 1
        if tag == "table":
            if "tbl" not in cls:
                self.err("table must have class 'tbl'", line)
            if not (parent and parent["tag"] == "div" and "tbl-wrap" in parent["cls"]):
                self.err("table must be wrapped in <div class=\"tbl-wrap\">", line)
        if tag == "div" and "co" in cls:
            if len(cls & CO_VARIANTS) != 1:
                self.err("callout needs exactly one variant class: " + ", ".join(sorted(CO_VARIANTS)), line)
        if tag == "details" and "qa" in cls and self.cur_article is not None:
            self.cur_article["qa"] += 1
        if tag == "li" and self.cur_article is not None:
            self.cur_article["li"] += 1
        if tag == "a" and not a.get("href"):
            self.warn("<a> without href", line)

        if not selfclose and tag not in VOID:
            self.stack.append({"tag": tag, "cls": cls, "line": line, "children": []})
        elif selfclose and tag == "pre":
            self.pre_depth -= 1

    def handle_endtag(self, tag):
        line = self.getpos()[0]
        if tag in VOID:
            return
        if not self.stack:
            self.err(f"stray closing </{tag}>", line)
            return
        if self.stack[-1]["tag"] != tag:
            names = [e["tag"] for e in self.stack]
            if tag in names:
                while self.stack and self.stack[-1]["tag"] != tag:
                    e = self.stack.pop()
                    self.err(f"<{e['tag']}> opened on line {e['line']} is not closed before </{tag}>", line)
                    self._closed(e)
            else:
                top = self.stack[-1]
                self.err(f"closing </{tag}> has no matching open tag (open: <{top['tag']}> from line {top['line']})", line)
                return
        self._closed(self.stack.pop())

    def _closed(self, e):
        tag, cls, kids = e["tag"], e["cls"], e["children"]
        if tag == "pre":
            self.pre_depth -= 1
            if "mermaid" in cls and self.cur_mermaid is not None:
                self.mermaid.append((self.cur_mermaid["line"], "".join(self.cur_mermaid["text"])))
                self.cur_mermaid = None
            if not ({"mermaid", "diagram"} & cls):
                if not kids or kids[0][0] != "code":
                    self.err("<pre> must contain one <code class=\"language-…\"> (or be pre.mermaid / pre.diagram)", e["line"])
        if tag == "code" and not self.pre_depth and self.inline_code_depth:
            self.inline_code_depth -= 1
        if tag == "article":
            art = self.cur_article
            if not kids or kids[0][0] != "h3":
                self.err("an article's first child must be <h3>", e["line"])
            if art and not art["recap"]:
                if len(kids) < 2 or not (kids[1][0] == "p" and "tldr" in kids[1][1]):
                    self.warn(f"article '{art['id']}' should have <p class=\"tldr\"> right after the h3", e["line"])
            self.cur_article = None
        if tag == "div" and "co" in cls:
            if not kids or not (kids[0][0] == "p" and "co-t" in kids[0][1]):
                self.err("a callout's first child must be <p class=\"co-t\">", e["line"])
        if tag == "figure" and "fig" in cls and not any(k[0] == "figcaption" for k in kids):
            self.warn("figure.fig without <figcaption>", e["line"])
        if tag == "details" and "qa" in cls and (not kids or kids[0][0] != "summary"):
            self.err("details.qa must start with <summary>", e["line"])
        if tag == "div" and "tbl-wrap" in cls:
            if not any(k[0] == "table" for k in kids):
                self.err("div.tbl-wrap without a table", e["line"])

    def handle_data(self, data):
        if self.cur_mermaid is not None:
            self.cur_mermaid["text"].append(data)
        if not self.stack:
            if data.strip():
                self.err(f"stray text outside any element: {data.strip()[:50]!r}")
            return
        if self.pre_depth:
            for ln in data.split("\n"):
                if len(ln) > 110:
                    self.long_lines += 1
        if self.cur_article is not None:
            n = len(data.split())
            if self.pre_depth:
                self.cur_article["codewords"] += n
            else:
                self.cur_article["words"] += n
            if self.stack[-1]["tag"] == "h3":
                self.cur_article["title"] += data

    def close_checks(self):
        for e in reversed(self.stack):
            self.err(f"<{e['tag']}> opened on line {e['line']} is never closed", e["line"])
        for art in self.articles:
            if not art["recap"] and art["words"] < 300:
                self.warn(f"article '{art['id']}' is thin ({art['words']} prose words) — go deeper", art["line"])
        for line, text in self.mermaid:
            check_mermaid(self, line, text)


FLOW_SQUARE = re.compile(r"[A-Za-z0-9_]+\[(?![\[(/\\])([^\]\n]*)\]")
FLOW_CURLY = re.compile(r"[A-Za-z0-9_]+\{(?!\{)([^}\n]*)\}")
FLOW_END = re.compile(r"(?:-->|---|==>|-\.->|-\.-)\s*(?:\|[^|]*\|\s*)?end\b(?![\w\[(])|^\s*end\s*[\[({>]", re.M)


def check_mermaid(p, line, text):
    raw = [l.rstrip() for l in text.strip("\n").splitlines()]
    lines = [l.strip() for l in raw if l.strip() and not l.strip().startswith("%%")]
    if not lines:
        p.err("empty mermaid block", line)
        return
    first = lines[0]
    kind = next((t for t in MERMAID_TYPES if first.startswith(t)), None)
    if not kind:
        p.err(f"mermaid block must start with one of: {', '.join(MERMAID_TYPES)} (found {first[:30]!r})", line)
        return
    if "%%{" in text:
        p.err("mermaid: no %%{init}%% directives", line)
    if re.search(r"^\s*(classDef|style|linkStyle)\b", text, re.M):
        p.warn("mermaid: remove classDef/style/linkStyle (theme handles colours)", line)
    body = "\n".join(lines[1:])
    if kind in ("flowchart", "graph"):
        for m in FLOW_SQUARE.finditer(body):
            lab = m.group(1).strip()
            if not (lab.startswith('"') and lab.endswith('"')) and re.search(r"[(){};]", lab):
                p.err(f"mermaid flowchart: quote the label [{lab[:40]}] → [\"…\"] (it has brackets/semicolons)", line)
        for m in FLOW_CURLY.finditer(body):
            lab = m.group(1).strip()
            if not (lab.startswith('"') and lab.endswith('"')) and re.search(r"[()\[\];]", lab):
                p.err(f"mermaid flowchart: quote the decision label {{{lab[:40]}}} → {{\"…\"}}", line)
        if FLOW_END.search(body):
            p.err("mermaid flowchart: a node called 'end' breaks rendering — rename it (e.g. Done)", line)
    if kind == "erDiagram":
        depth = 0
        for l in lines[1:]:
            if "{" in l:
                depth += 1
                continue
            if "}" in l:
                depth = max(0, depth - 1)
                continue
            if depth and re.search(r"[()]", l.split('"')[0]):
                p.err(f"mermaid erDiagram: attribute types cannot have brackets ({l[:40]!r}) — write varchar, not varchar(100)", line)
    if kind == "classDiagram":
        for l in lines[1:]:
            if re.search(r"<(?![|.\-*o])[A-Za-z]", l) and not re.search(r"<<\w+>>", l):
                p.err(f"mermaid classDiagram: use ~ for generics (List~String~), not <…> ({l[:40]!r})", line)
            if re.search(r"\s\+--\s", l):
                p.err(f"mermaid classDiagram: '+--' (nested class) is not supported — use '*--' ({l[:40]!r})", line)
    if kind == "gitGraph":
        ids = {}
        for l in lines[1:]:
            word = l.split()[0]
            if word not in ("commit", "branch", "checkout", "switch", "merge", "cherry-pick"):
                p.warn(f"mermaid gitGraph: unexpected line {l[:40]!r}", line)
            if word == "branch" and "/" in l:
                p.warn(f"mermaid gitGraph: avoid '/' in branch names ({l[:40]!r}) — use feature-login", line)
            m = re.search(r'id:\s*"([^"]*)"', l)
            if m:
                if m.group(1) in ids:
                    p.err(f"mermaid gitGraph: duplicate commit id \"{m.group(1)}\" (ids must be unique)", line)
                ids[m.group(1)] = True
    if kind == "sequenceDiagram":
        for l in lines[1:]:
            if re.search(r"(->>|-->>|->|-->|-x|--x|-\))", l) and ";" in l.split(":", 1)[-1]:
                p.warn(f"mermaid sequenceDiagram: avoid ';' in message text ({l[:40]!r})", line)


def validate_file(path):
    m = FILE_RE.match(path.name)
    res = {"path": path, "errors": [], "warns": [], "articles": [], "ids": []}
    if not m:
        res["errors"].append((0, f"bad file name '{path.name}' — must be mNN-CC.html"))
        return res
    module_no = int(m.group(1))
    text = path.read_text(encoding="utf-8-sig")
    p = Frag(module_no)
    try:
        p.feed(text)
        p.close()
    except Exception as ex:  # parser crash
        p.err(f"HTML parser crashed: {ex}")
    p.close_checks()
    for i, ln in enumerate(text.splitlines(), 1):
        for _ in AMP_RE.finditer(ln):
            p.warn("raw '&' — write &amp; (or a full entity like &lt;)", i)
            break
    if p.long_lines:
        p.warn(f"{p.long_lines} code line(s) longer than 110 characters — wrap them", 0)
    res.update(errors=p.errors, warns=p.warns, articles=p.articles, ids=p.ids, module=module_no)
    return res


def run(slug, patterns, show_list):
    folder = PARTS / slug
    if not folder.is_dir():
        print(f"No folder {folder}")
        return 1
    all_files = sorted(folder.glob("*.html"))
    files = [f for f in all_files if not patterns or any(fnmatch.fnmatch(f.name, pt) for pt in patterns)]
    if not files:
        print("No matching files.")
        return 1
    # duplicate ids across the whole slug folder
    every = {f: validate_file(f) for f in all_files}
    seen = {}
    for f, r in every.items():
        for i, ln in r["ids"]:
            seen.setdefault(i, []).append((f.name, ln))
    total_err = total_warn = total_words = total_code = total_art = 0
    modules = {}
    for f in files:
        r = every[f]
        for i, ln in r["ids"]:
            if len(seen[i]) > 1:
                others = ", ".join(f"{n}:{l}" for n, l in seen[i] if not (n == f.name and l == ln))
                r["errors"].append((ln, f"duplicate id '{i}' (also in {others})"))
        words = sum(a["words"] for a in r["articles"])
        code = sum(a["codewords"] for a in r["articles"])
        total_words += words
        total_code += code
        total_art += len(r["articles"])
        modules.setdefault(r.get("module"), []).extend(r["articles"])
        print(f"\n{f.name}: {len(r['articles'])} articles, {words:,} prose words, {code:,} code words"
              f" — {len(r['errors'])} errors, {len(r['warns'])} warnings")
        for ln, msg in sorted(r["errors"]):
            print(f"  ERROR line {ln}: {msg}")
        for ln, msg in sorted(r["warns"]):
            print(f"  WARN  line {ln}: {msg}")
        total_err += len(r["errors"])
        total_warn += len(r["warns"])
    for mod, arts in sorted((k, v) for k, v in modules.items() if k is not None):
        ids = {a["id"] for a in arts}
        for kind in ("interview", "cheatsheet", "practice"):
            if not any(i == f"m{mod}-{kind}" or i.startswith(f"m{mod}-{kind}-") for i in ids):
                print(f"  NOTE  module {mod}: no '{kind}' recap article yet (needed in the module's last chunk)")
        for a in arts:
            if a["recap"] and "interview" in a["id"] and a["qa"] < 8:
                print(f"  WARN  {a['id']}: only {a['qa']} questions (aim for 10–15)")
    if show_list:
        print("\nArticles:")
        for f in files:
            for a in every[f]["articles"]:
                t = " ".join(a["title"].split())
                print(f"  {a['id']:<44} {a['words']:>5}w  {t[:60]}")
    print(f"\nTOTAL {slug}: {len(files)} files, {total_art} articles, {total_words:,} prose words,"
          f" {total_code:,} code words — {total_err} errors, {total_warn} warnings")
    return 1 if total_err else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="?")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.all:
        rc = 0
        for d in sorted(p for p in PARTS.iterdir() if p.is_dir()):
            rc |= run(d.name, [], args.list)
        return rc
    if not args.slug:
        ap.error("give a topic slug or --all")
    return run(args.slug, args.only, args.list)


if __name__ == "__main__":
    sys.exit(main())
