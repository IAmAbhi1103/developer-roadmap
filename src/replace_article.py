#!/usr/bin/env python3
"""Replace one article (found by its id) in a page's chunk files with new HTML from a file.

Usage:
  python replace_article.py <topic-slug> <article-id> <new-article-file>

The new file must contain exactly one <article …id="<article-id>">…</article> and must keep every id
the old article had (h4 ids may be linked from other articles or pages). Nothing is written if a check
fails.
"""
import pathlib
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    slug, aid, newfile = sys.argv[1:4]
    new = pathlib.Path(newfile).read_text("utf-8-sig").strip()
    start_re = re.compile(r'<article\b[^>]*\bid="%s"[^>]*>' % re.escape(aid))
    if not start_re.match(new):
        print(f'ERROR: the new file must start with <article … id="{aid}">')
        return 1
    if new.count("<article") != 1 or not new.endswith("</article>"):
        print("ERROR: the new file must contain exactly one complete <article>…</article>")
        return 1
    for f in sorted((ROOT / "parts" / slug).glob("*.html")):
        text = f.read_text("utf-8-sig")
        m = start_re.search(text)
        if not m:
            continue
        end = text.find("</article>", m.end())
        if end == -1:
            print(f"ERROR: no closing </article> for {aid} in {f.name}")
            return 1
        end += len("</article>")
        old = text[m.start():end]
        old_ids = set(re.findall(r'\sid="([^"]+)"', old))
        new_ids = set(re.findall(r'\sid="([^"]+)"', new))
        missing = sorted(old_ids - new_ids)
        if missing:
            print("ERROR: the new article drops ids that may be linked from elsewhere: " + ", ".join(missing))
            return 1
        if len(new) < len(old):
            print(f"ERROR: the new article ({len(new):,} chars) is shorter than the old one "
                  f"({len(old):,} chars) — an expansion must keep and extend the content")
            return 1
        backup = ROOT / "tmp" / "backup"
        backup.mkdir(parents=True, exist_ok=True)
        (backup / f"{slug}--{f.name}--{aid}.html").write_bytes(text.encode("utf-8"))
        f.write_bytes((text[:m.start()] + new + text[end:]).encode("utf-8"))
        print(f"replaced {aid} in {f.name}: {len(old):,} → {len(new):,} characters")
        return 0
    print(f"ERROR: article {aid} not found in parts/{slug}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
