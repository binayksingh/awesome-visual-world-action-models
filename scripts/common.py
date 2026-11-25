"""Shared helpers: paths, categories, loading and validating the paper database."""

from __future__ import annotations

import csv
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PAPERS_YAML = DATA / "papers.yaml"
LEADERBOARD_DIR = DATA / "leaderboards"
SEEN_FILE = DATA / "seen_arxiv.txt"

# Order here is the order of sections in the README.
CATEGORIES = {
    "survey": "Surveys and tutorials",
    "latent": "Latent world models",
    "video": "Video / pixel world-action models",
    "3d4d": "3D / 4D world models",
    "driving": "Autonomous-driving world-action models",
    "vla": "Vision-language-action baselines",
    "baseline": "Non-world-model driving baselines",
    "benchmark": "Datasets, simulators, and benchmarks",
}

REQUIRED = ("id", "title", "first_author", "year", "category", "added")
ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}$")


def load_papers() -> list[dict]:
    with open(PAPERS_YAML, encoding="utf-8") as f:
        return yaml.safe_load(f)["papers"]


def save_papers(papers: list[dict]) -> None:
    with open(PAPERS_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump({"papers": papers}, f, sort_keys=False, allow_unicode=True, width=200)


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return {line.strip() for line in SEEN_FILE.read_text().splitlines() if line.strip()}


def known_arxiv_ids(papers: list[dict]) -> set[str]:
    return {str(p["arxiv"]) for p in papers if p.get("arxiv")}


def load_leaderboards() -> dict[str, list[dict]]:
    boards = {}
    for path in sorted(LEADERBOARD_DIR.glob("*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            boards[path.stem] = list(csv.DictReader(f))
    return boards


def load_leaderboard_meta() -> dict:
    with open(LEADERBOARD_DIR / "_meta.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(papers: list[dict] | None = None) -> list[str]:
    """Return a list of human-readable problems (empty list = valid)."""
    papers = load_papers() if papers is None else papers
    errors: list[str] = []
    ids, arxivs, titles = set(), set(), set()
    for i, p in enumerate(papers):
        where = f"papers[{i}] ({p.get('id', '?')})"
        for key in REQUIRED:
            if not p.get(key):
                errors.append(f"{where}: missing '{key}'")
        if p.get("category") not in CATEGORIES:
            errors.append(f"{where}: unknown category '{p.get('category')}'")
        if not (p.get("arxiv") or p.get("doi") or p.get("url")):
            errors.append(f"{where}: needs one of arxiv / doi / url")
        if p.get("arxiv") and not ARXIV_RE.match(str(p["arxiv"])):
            errors.append(f"{where}: malformed arXiv id '{p['arxiv']}'")
        for seen, key, val in ((ids, "id", p.get("id")), (arxivs, "arxiv", p.get("arxiv")),
                               (titles, "title", re.sub(r"\W", "", str(p.get("title", "")).lower()))):
            if val:
                if val in seen:
                    errors.append(f"{where}: duplicate {key} '{val}'")
                seen.add(val)

    meta = load_leaderboard_meta()
    for name, rows in load_leaderboards().items():
        if name not in meta:
            errors.append(f"leaderboard {name}.csv has no entry in _meta.yaml")
            continue
        for j, row in enumerate(rows):
            if row.get("paper_id") and row["paper_id"] not in ids:
                errors.append(f"{name}.csv row {j + 2}: paper_id '{row['paper_id']}' not in papers.yaml")
            if not row.get("source"):
                errors.append(f"{name}.csv row {j + 2}: 'source' is required (e.g. 'original')")
            for col in meta[name]["metric_cols"]:
                try:
                    float(row[col])
                except (KeyError, ValueError):
                    errors.append(f"{name}.csv row {j + 2}: '{col}' is not a number")
    return errors
