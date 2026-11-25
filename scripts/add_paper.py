"""Add a paper to data/papers.yaml from its arXiv ID.

Metadata (title, first author, year, venue comment) is fetched from the arXiv API,
so contributors only supply the ID and a category.

Local use: edit AddConfig below and run
    python scripts/add_paper.py
In GitHub Actions the workflow `add-paper.yml` fills the same fields from an
"Add paper" issue form (through the environment variables named in AddConfig).
"""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arxiv_watch import ATOM, CFG as WATCH_CFG, parse  # noqa: E402
from common import ARXIV_RE, CATEGORIES, load_papers, save_papers, validate  # noqa: E402
import urllib.request  # noqa: E402


@dataclass
class AddConfig:
    arxiv_ids: str = ""            # one or more IDs, comma/space separated, e.g. "2610.17526"
    category: str = "video"        # one of: survey latent video 3d4d driving vla benchmark
    code: str = ""                 # optional code URL
    venue: str = ""                # optional; overrides the venue guessed from the arXiv comment


CFG = AddConfig(
    arxiv_ids=os.environ.get("WAM_ARXIV_IDS", AddConfig.arxiv_ids),
    category=os.environ.get("WAM_CATEGORY", AddConfig.category),
    code=os.environ.get("WAM_CODE", AddConfig.code),
    venue=os.environ.get("WAM_VENUE", AddConfig.venue),
)

VENUE_RE = re.compile(r"\b(CVPR|ICCV|ECCV|NeurIPS|ICLR|ICML|CoRL|RSS|ICRA|IROS|WACV|AAAI|TPAMI|RA-L|IJCV)\b[^.;,]*", re.I)


def fetch_meta(arxiv_id: str) -> dict:
    url = f"{WATCH_CFG.api}?id_list={arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "awesome-visual-wam-watcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        entries = parse(r.read().decode("utf-8"))
    if not entries or not entries[0]["title"]:
        raise SystemExit(f"arXiv ID {arxiv_id} not found")
    return entries[0]


def make_id(meta: dict, existing: set[str]) -> str:
    last = re.sub(r"[^a-z]", "", meta["authors"][0].split()[-1].lower()) or "anon"
    word = next((re.sub(r"[^a-z0-9]", "", w.lower()) for w in meta["title"].split()
                 if len(w) > 3 and w.lower() not in {"with", "from", "towards", "toward", "learning", "model", "models"}), "paper")
    base = f"{last}{meta['published'][:4]}{word}"
    key, n = base, 2
    while key in existing:
        key, n = f"{base}{n}", n + 1
    return key


def to_entry(meta: dict, cfg: AddConfig, existing: set[str]) -> dict:
    m = VENUE_RE.search(meta["comment"])
    venue = cfg.venue or (m.group(0).strip() if m else "arXiv preprint")
    entry = {
        "id": make_id(meta, existing),
        "title": meta["title"],
        "first_author": meta["authors"][0].split()[-1],
        "year": int(meta["published"][:4]),
        "venue": venue,
        "category": cfg.category,
        "arxiv": meta["arxiv"],
        "in_survey": False,
        "added": dt.datetime.now(dt.timezone.utc).date().isoformat(),
    }
    if cfg.code:
        entry["code"] = cfg.code
    return entry


def main(cfg: AddConfig) -> list[str]:
    if cfg.category not in CATEGORIES:
        raise SystemExit(f"category must be one of {list(CATEGORIES)}")
    ids = [x for x in re.split(r"[\s,]+", cfg.arxiv_ids.strip()) if x]
    if not ids:
        raise SystemExit("set arxiv_ids in AddConfig")
    papers = load_papers()
    known = {str(p.get("arxiv")) for p in papers}
    added = []
    for aid in ids:
        aid = aid.replace("arXiv:", "").split("v")[0]
        if not ARXIV_RE.match(aid):
            raise SystemExit(f"malformed arXiv id: {aid}")
        if aid in known:
            print(f"{aid} already listed, skipped")
            continue
        entry = to_entry(fetch_meta(aid), cfg, {p["id"] for p in papers})
        papers.append(entry)
        known.add(aid)
        added.append(entry["id"])
        print(f"added {entry['id']}: {entry['title']}")
    errors = validate(papers)
    if errors:
        raise SystemExit("validation failed:\n  " + "\n  ".join(errors))
    save_papers(papers)
    return added


if __name__ == "__main__":
    main(CFG)
