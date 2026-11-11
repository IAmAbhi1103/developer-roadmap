# Java Full-Stack Notes

Detailed study notes for every topic on the Java full-stack developer roadmap: how each concept works, the rules, conventions, exceptions and edge cases, worked examples, common mistakes and the interview angle.

**9 topics · 53 modules · 795 topic cards · about 99 hours of reading** (as of October 2026)

| # | Topic | Modules |
|---|---|---|
| 01 | [Git & GitHub](01-git-github.html) | 4 |
| 02 | [Core Java](02-core-java.html) | 8 |
| 03 | [SQL & Databases](03-sql-databases.html) | 6 |
| 04 | [Spring Boot & Backend](04-spring-boot.html) | 7 |
| 05 | [Data Structures & Algorithms](05-dsa.html) | 4 |
| 06 | [Frontend](06-frontend.html) | 7 |
| 07 | [DevOps & Deployment](07-devops.html) | 6 |
| 08 | [System Design](08-system-design.html) | 7 |
| 09 | [CS Fundamentals](09-cs-fundamentals.html) | 4 |

The roadmap these notes follow is in [roadmap.html](roadmap.html).

## How to read

Open `index.html` in any modern browser. There is nothing to install and no server to run. Code highlighting (highlight.js) and diagrams (Mermaid) load from a CDN, so those two need an internet connection.

Every page has:

- a sidebar with the table of contents and a search box that looks inside the text of every topic
- a TL;DR line at the top of each topic card, then colour-coded boxes for rules, conventions, exceptions, common mistakes, tips, version notes and interview angles
- interview questions, a cheat sheet and practice tasks at the end of each module
- **Mark revised** buttons that save your progress in the browser (localStorage)
- dark mode, copy buttons on code blocks, and a layout that works on phones and in print

## Project layout

```
index.html, 01-…09-*.html   generated pages (do not edit by hand)
roadmap.html                the roadmap
assets/                     notes.css and notes.js, shared by every page
src/
  topics.json               titles, modules, colours and descriptions of the nine pages
  parts/<page>/mNN-CC.html  page content as HTML fragments: module NN, part CC
  build.py                  builds index.html and the nine pages from src/
  validate.py               checks the fragments (tags, classes, ids, diagram syntax)
  replace_article.py        replaces one topic card in the fragments by its id
```

## Editing

Change a fragment in `src/parts/`, then run from the repository root:

```bash
python src/validate.py --all
python src/build.py
```

To check one page only, pass its folder name, for example `python src/validate.py 02-core-java`. The scripts need Python 3.8 or newer and no extra packages.
