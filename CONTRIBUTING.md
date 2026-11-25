# Contributing

The README is generated. Please edit the data, not README.md.

## Add a paper (easiest)
Open an [**Add paper**](../../issues/new?template=add-paper.yml) issue with the arXiv ID and a category.
A bot fetches the title, authors, year and venue from arXiv and opens a pull request.

## Add a paper by hand
Append an entry to `data/papers.yaml`:

```yaml
- id: yu2026boxwam                # firstauthorYEARword, unique
  title: 'Box-WAM: Box Trajectories as Compact State Representations for World Action Models'
  first_author: Yu
  year: 2026
  venue: arXiv preprint
  category: video                 # survey | latent | video | 3d4d | driving | vla | baseline | benchmark
  arxiv: '2610.17526'             # or doi: / url:
  code: https://...               # optional
  in_survey: false                # true only for papers cited in the survey
  added: '2026-11-23'
```

## Add a leaderboard result
Add a row to the CSV in `data/leaderboards/`. Rules:
1. Copy numbers **exactly as reported** in the paper; nothing re-run, nothing rounded.
2. `source` is `original`, or names the paper whose table you copied the number from.
3. Put protocol differences (inputs, best-of-N, extra data) in `note`.
4. The method's paper must also be in `data/papers.yaml` (`paper_id`).

Run `python scripts/validate.py` before opening the pull request; CI runs it too.
