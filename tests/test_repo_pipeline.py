"""Offline tests for the update pipeline (no network)."""
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import add_paper  # noqa: E402
import arxiv_watch  # noqa: E402
import build_readme  # noqa: E402
from common import load_papers, validate  # noqa: E402

FEED = (ROOT / "tests" / "fixtures" / "arxiv_feed.xml").read_text()


def test_data_is_valid():
    assert validate() == []


def test_parse_feed():
    entries = arxiv_watch.parse(FEED)
    assert [e["arxiv"] for e in entries] == ["2611.00001", "2610.17526", "2611.00002", "2601.00003"]
    assert entries[0]["title"] == "A World Action Model for Robot Manipulation"
    assert "CVPR 2027" in entries[0]["comment"]


def test_select_filters_known_old_and_irrelevant():
    cfg = arxiv_watch.WatchConfig()
    known = {str(p.get("arxiv")) for p in load_papers()}
    cands = arxiv_watch.select(arxiv_watch.parse(FEED), cfg, known, set(), dt.date(2026, 11, 23))
    assert [c["arxiv"] for c in cands] == ["2611.00001"]
    md = arxiv_watch.render(cands, dt.date(2026, 11, 23))
    assert "- [ ] **[A World Action Model for Robot Manipulation](https://arxiv.org/abs/2611.00001)**" in md


def test_add_paper_entry_from_metadata():
    meta = arxiv_watch.parse(FEED)[0]
    cfg = add_paper.AddConfig(arxiv_ids="2611.00001", category="video")
    e = add_paper.to_entry(meta, cfg, existing=set())
    assert e["id"] == "lovelace2026world"
    assert e["first_author"] == "Lovelace" and e["year"] == 2026
    assert e["venue"].startswith("CVPR 2027") and e["in_survey"] is False
    assert validate(load_papers() + [e]) == []


def test_readme_blocks_render(tmp_path):
    cfg = build_readme.BuildConfig(output=tmp_path / "README.md", bib_output=tmp_path / "papers.bib", today="2026-11-23")
    build_readme.main(cfg)
    text = (tmp_path / "README.md").read_text()
    assert "| [SimWAM](https://arxiv.org/abs/2608.07468)" in text
    assert "**91.9**" in text
    assert (tmp_path / "papers.bib").read_text().count("@misc{") == len(load_papers())
