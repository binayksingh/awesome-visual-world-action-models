"""Weekly arXiv watcher: find new papers that may belong in the list.

It queries the arXiv API for recent submissions matching the search terms below,
drops papers already in data/papers.yaml or already shown before (data/seen_arxiv.txt),
ranks the rest by keyword relevance, and writes `candidates.md`. The GitHub Action
`arxiv-watch.yml` posts that file as an issue; a maintainer ticks the papers to add.

Edit WatchConfig to tune the search, then run:
    python scripts/arxiv_watch.py
"""

from __future__ import annotations

import datetime as dt
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SEEN_FILE, known_arxiv_ids, load_papers, load_seen  # noqa: E402

ATOM = "{http://www.w3.org/2005/Atom}"


@dataclass
class WatchConfig:
    days_back: int = 8
    max_results_per_query: int = 100
    categories: tuple = ("cs.CV", "cs.RO", "cs.LG", "cs.AI")
    # Each query is an arXiv search expression on title+abstract.
    queries: tuple = (
        'abs:"world action model"',
        'abs:"world-action model"',
        'abs:"world model" AND (abs:robot OR abs:manipulation OR abs:embodied)',
        'abs:"world model" AND (abs:driving OR abs:"autonomous vehicle")',
        'abs:"video generation" AND abs:policy AND abs:robot',
        'abs:"occupancy" AND abs:forecasting AND abs:"world model"',
        'abs:"vision-language-action" AND (abs:"future" OR abs:"world model")',
    )
    # Keyword weights for ranking candidates (title hits count double).
    weights: dict = field(default_factory=lambda: {
        "world action model": 5, "world-action model": 5, "world model": 3, "video world model": 3,
        "action-conditioned": 2, "embodied": 1, "manipulation": 1, "driving": 1, "navsim": 2,
        "occupancy": 1, "gaussian": 1, "vision-language-action": 1, "policy": 1, "benchmark": 1,
    })
    min_score: int = 4
    output: Path = ROOT / "candidates.md"
    api: str = "https://export.arxiv.org/api/query"
    pause_s: float = 3.5           # arXiv asks for >= 3 s between calls
    today: str | None = None       # None -> today (UTC)


CFG = WatchConfig()


def build_query(expr: str, cats: tuple) -> str:
    cat_expr = " OR ".join(f"cat:{c}" for c in cats)
    return f"({expr}) AND ({cat_expr})"


def fetch(cfg: WatchConfig, expr: str) -> str:
    params = {"search_query": build_query(expr, cfg.categories), "sortBy": "submittedDate",
              "sortOrder": "descending", "max_results": cfg.max_results_per_query}
    url = f"{cfg.api}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "awesome-visual-wam-watcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def parse(feed_xml: str) -> list[dict]:
    root = ET.fromstring(feed_xml)
    out = []
    for e in root.findall(f"{ATOM}entry"):
        abs_url = e.findtext(f"{ATOM}id", "")
        arxiv_id = abs_url.rsplit("/", 1)[-1].split("v")[0]
        out.append({
            "arxiv": arxiv_id,
            "title": " ".join(e.findtext(f"{ATOM}title", "").split()),
            "summary": " ".join(e.findtext(f"{ATOM}summary", "").split()),
            "published": e.findtext(f"{ATOM}published", "")[:10],
            "authors": [a.findtext(f"{ATOM}name", "") for a in e.findall(f"{ATOM}author")],
            "comment": e.findtext("{http://arxiv.org/schemas/atom}comment", "") or "",
        })
    return out


def score(paper: dict, weights: dict) -> int:
    t, s = paper["title"].lower(), paper["summary"].lower()
    return sum(w * (2 * t.count(k) + min(s.count(k), 3)) for k, w in weights.items())


def select(entries: list[dict], cfg: WatchConfig, known: set[str], seen: set[str], today: dt.date) -> list[dict]:
    cutoff = today - dt.timedelta(days=cfg.days_back)
    picked = {}
    for p in entries:
        if p["arxiv"] in known or p["arxiv"] in seen or p["arxiv"] in picked:
            continue
        if p["published"] and dt.date.fromisoformat(p["published"]) < cutoff:
            continue
        p["score"] = score(p, cfg.weights)
        if p["score"] >= cfg.min_score:
            picked[p["arxiv"]] = p
    return sorted(picked.values(), key=lambda p: -p["score"])


def render(cands: list[dict], today: dt.date) -> str:
    lines = [f"Automated arXiv scan for {today.isoformat()} found **{len(cands)}** candidate papers.",
             "",
             "To add a paper: tick it, then open an **Add paper** issue with its arXiv ID "
             "(or comment `/add <arXiv-ID> <category>` below). Close this issue when done.",
             "Categories: `survey`, `latent`, `video`, `3d4d`, `driving`, `vla`, `benchmark`.",
             ""]
    for p in cands:
        authors = ", ".join(p["authors"][:3]) + (" et al." if len(p["authors"]) > 3 else "")
        venue = f" — _{p['comment']}_" if p["comment"] else ""
        lines.append(f"- [ ] **[{p['title']}](https://arxiv.org/abs/{p['arxiv']})** ({authors}; {p['published']}; "
                     f"score {p['score']}){venue}")
    return "\n".join(lines) + "\n"


def main(cfg: WatchConfig) -> int:
    today = dt.date.fromisoformat(cfg.today) if cfg.today else dt.datetime.now(dt.timezone.utc).date()
    entries = []
    for i, q in enumerate(cfg.queries):
        if i:
            time.sleep(cfg.pause_s)
        entries.extend(parse(fetch(cfg, q)))
    cands = select(entries, cfg, known_arxiv_ids(load_papers()), load_seen(), today)
    if cands:
        cfg.output.write_text(render(cands, today), encoding="utf-8")
        with open(SEEN_FILE, "a", encoding="utf-8") as f:
            f.writelines(p["arxiv"] + "\n" for p in cands)
    print(f"{len(cands)} candidates")
    return len(cands)


if __name__ == "__main__":
    main(CFG)
