"""Regenerate README.md and docs/papers.bib from data/.

Edit the BuildConfig dataclass below if needed, then run:
    python scripts/build_readme.py
GitHub Actions runs this automatically on every push that touches data/.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CATEGORIES, ROOT, load_leaderboard_meta, load_leaderboards, load_papers, validate  # noqa: E402


@dataclass
class BuildConfig:
    template: Path = ROOT / "docs" / "README.template.md"
    output: Path = ROOT / "README.md"
    bib_output: Path = ROOT / "docs" / "papers.bib"
    news_items: int = 10          # newest additions shown under "What's new"
    today: str | None = None      # None -> today's date (UTC)


CFG = BuildConfig()


def paper_link(p: dict) -> str:
    if p.get("arxiv"):
        return f"https://arxiv.org/abs/{p['arxiv']}"
    if p.get("doi"):
        return f"https://doi.org/{p['doi']}"
    return p.get("url", "")


def paper_line(p: dict) -> str:
    venue = f"{p['venue']}, " if p.get("venue") else ""
    line = f"- **{p['title']}** — {p['first_author']} et al., {venue}{p['year']}"
    links = []
    if paper_link(p):
        links.append(f"[[paper]]({paper_link(p)})")
    if p.get("code"):
        links.append(f"[[code]]({p['code']})")
    if links:
        line += ". " + " ".join(links)
    if not p.get("in_survey", False):
        line += " 🆕"
    return line


def section_papers(papers: list[dict]) -> str:
    out = []
    for key, name in CATEGORIES.items():
        items = sorted((p for p in papers if p["category"] == key), key=lambda p: (-int(p["year"]), p["title"].lower()))
        if not items:
            continue
        anchor = re.sub(r"[^a-z0-9 -]", "", name.lower()).replace(" ", "-")
        out.append(f"\n### {name}\n<a id=\"{anchor}\"></a>\n")
        out.extend(paper_line(p) for p in items)
    return "\n".join(out)


def section_news(papers: list[dict], n: int) -> str:
    new = [p for p in papers if not p.get("in_survey", False)]
    new.sort(key=lambda p: p["added"], reverse=True)
    if not new:
        return "_No additions since the survey was submitted yet. New papers appear here automatically._"
    return "\n".join(f"- `{p['added']}` {paper_line(p)[2:]}" for p in new[:n])


def section_stats(papers: list[dict], today: str) -> str:
    n_new = sum(1 for p in papers if not p.get("in_survey", False))
    return (f"![papers](https://img.shields.io/badge/papers-{len(papers)}-1D4ED8) "
            f"![added since survey](https://img.shields.io/badge/added_since_survey-{n_new}-0F766E) "
            f"![last update](https://img.shields.io/badge/last_update-{today.replace('-', '--')}-C2410C)")


def section_leaderboards(boards: dict[str, list[dict]], meta: dict, papers: list[dict]) -> str:
    title_of = {p["id"]: p for p in papers}
    out = ["Numbers are copied from the original papers (the `source` column says when a paper's number was taken "
           "from another paper's table). Nothing is re-run. Compare only within one table. Best value per column is bold.\n"]
    for name, rows in boards.items():
        m = meta[name]
        hib = m["higher_is_better"]
        rows = sorted(rows, key=lambda r: float(r[m["sort_by"]]), reverse=hib)
        cols = m["metric_cols"]
        extra = [c for c in rows[0].keys() if c not in cols and c not in ("method", "paper_id", "source", "note")] if rows else []
        best = {}
        for c in cols:
            vals = [float(r[c]) for r in rows if r["method"] != "Human reference"]
            best[c] = (max if hib else min)(vals) if vals else None
        arrow = "↑" if hib else "↓"
        out.append(f"### {m['title']} {arrow}\n")
        out.append("| Method | " + " | ".join(extra + cols) + " | Source |")
        out.append("|" + "---|" * (len(extra) + len(cols) + 2))
        for r in rows:
            link = paper_link(title_of[r["paper_id"]]) if r.get("paper_id") in title_of else ""
            meth = f"[{r['method']}]({link})" if link else r["method"]
            if r.get("note"):
                meth += f" <sub>{r['note']}</sub>"
            cells = [r[c] for c in extra]
            for c in cols:
                v = r[c]
                cells.append(f"**{v}**" if best[c] is not None and float(v) == best[c] and r["method"] != "Human reference" else v)
            out.append(f"| {meth} | " + " | ".join(cells) + f" | {r['source']} |")
        out.append("")
    return "\n".join(out)


def make_bib(papers: list[dict]) -> str:
    entries = []
    for p in papers:
        fields = [f"  title = {{{p['title']}}}", f"  author = {{{p['first_author']} and others}}", f"  year = {{{p['year']}}}"]
        if p.get("venue"):
            fields.append(f"  note = {{{p['venue']}}}")
        if p.get("arxiv"):
            fields.append(f"  eprint = {{{p['arxiv']}}}\n  archivePrefix = {{arXiv}}")
        if p.get("doi"):
            fields.append(f"  doi = {{{p['doi']}}}")
        if p.get("url"):
            fields.append(f"  url = {{{p['url']}}}")
        entries.append(f"@misc{{{p['id']},\n" + ",\n".join(fields) + "\n}")
    return "\n\n".join(entries) + "\n"


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- BEGIN:{name} -->)(.*?)(<!-- END:{name} -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"template has no {name} block")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", text)


def main(cfg: BuildConfig) -> None:
    errors = validate()
    if errors:
        raise SystemExit("data/ is invalid:\n  " + "\n  ".join(errors))
    papers = load_papers()
    today = cfg.today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    text = cfg.template.read_text(encoding="utf-8")
    text = replace_block(text, "STATS", section_stats(papers, today))
    text = replace_block(text, "NEWS", section_news(papers, cfg.news_items))
    text = replace_block(text, "LEADERBOARDS", section_leaderboards(load_leaderboards(), load_leaderboard_meta(), papers))
    text = replace_block(text, "PAPERS", section_papers(papers))
    cfg.output.write_text(text, encoding="utf-8")
    cfg.bib_output.write_text(make_bib(papers), encoding="utf-8")
    print(f"README.md rebuilt: {len(papers)} papers")


if __name__ == "__main__":
    main(CFG)
