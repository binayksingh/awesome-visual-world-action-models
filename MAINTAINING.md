# Maintaining the repository

## One-time setup (about 15 minutes)

1. **Create the repo** `binayksingh/awesome-visual-world-action-models` (public) and push this folder to `main`.
2. **Let Actions write:** *Settings → Actions → General → Workflow permissions* → "Read and write permissions" and tick "Allow GitHub Actions to create and approve pull requests".
3. **Create labels:** `triage`, `add-paper`, `add-result`.
4. **Connect Zenodo:** sign in at zenodo.org with GitHub, open *GitHub* in the Zenodo menu, and switch this repository **on**. Then run the *Monthly release* workflow once by hand (*Actions → Monthly release → Run workflow*). Zenodo creates the first DOI; replace `XXXXXXX` in `docs/README.template.md` and `CITATION.cff` with the **concept DOI** (the one that always points to the latest version).
5. **Optional:** add the repo topics `world-models`, `world-action-models`, `autonomous-driving`, `embodied-ai`, `robot-learning`, `survey`, `awesome-list` so it shows up in GitHub search.

## Weekly routine (about 10 minutes)

1. Every Monday the *arXiv watch* action opens an issue titled "New candidate papers".
2. For each relevant paper, comment `/add <arXiv-ID> <category>` (several IDs: `/add 2611.00001,2611.00002 video`).
3. The bot opens a pull request per comment. Check the venue line, then merge.
4. Close the triage issue.

Everything else is automatic: the README, "What's new", the badges and `docs/papers.bib` are rebuilt on merge, and a new Zenodo version is released on the 1st of each month.

## Tuning the watcher

Edit `WatchConfig` at the top of `scripts/arxiv_watch.py` (search terms, keyword weights, `min_score`).
Raise `min_score` if the issue lists too many papers; lower it if relevant papers are missed.

## When the survey is published

Change `note = {Under review}` in the README citation and `CITATION.cff` to the volume, pages and DOI,
and set `in_survey: true` only for papers the published version cites.
