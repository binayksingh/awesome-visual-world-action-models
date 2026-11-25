# Awesome Visual World-Action Models

Companion repository for the survey **"Visual World-Action Models for Embodied AI and Autonomous Driving: A Systematic Survey of Spatial Representations, Generative Dynamics, and Benchmarks"** (Singh and Lobo, submitted to *The Visual Computer*).

It contains:

- a curated, taxonomy-ordered **paper list** (robotics and autonomous driving);
- **leaderboards** of results as reported by the original papers (NAVSIM, nuScenes, Occ3D, LIBERO, CALVIN);
- **`wamscore`**, a reference implementation of the three physics-grounded diagnostics proposed in the survey (IVR, E_dn, Δ_act);
- all **figures** of the survey as vector PDF and 300-dpi PNG, free to reuse with attribution.

Contributions of papers and newly reported results are welcome — see [How this list stays current](#how-this-list-stays-current).

<!-- BEGIN:STATS -->
<!-- END:STATS -->
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![arXiv watch](../../actions/workflows/arxiv-watch.yml/badge.svg)](../../actions/workflows/arxiv-watch.yml)

## What's new

<!-- BEGIN:NEWS -->
<!-- END:NEWS -->

## How this list stays current

- **Every Monday** a GitHub Action searches arXiv for new world-model and world-action-model papers and opens an issue listing candidates ranked by relevance.
- A maintainer ticks the relevant ones and comments `/add <arXiv-ID> <category>`, or anyone opens an [**Add paper**](../../issues/new?template=add-paper.yml) issue. A bot fetches the title, authors and year from arXiv and opens a pull request.
- Merging the pull request rebuilds this README, the leaderboards and [`docs/papers.bib`](docs/papers.bib) automatically.
- On the **1st of every month** the repository is released as a new version, which [Zenodo](https://zenodo.org) archives with a citable DOI.

![Survey roadmap](figures/fig02_roadmap.png)

## Contents

- [Taxonomy](#taxonomy)
- [Leaderboards](#leaderboards)
- [Physics-grounded metrics (`wamscore`)](#physics-grounded-metrics-wamscore)
- [Paper list](#paper-list)
- [Figures](#figures)
- [Citation](#citation)

## Taxonomy

World-Action Models (WAMs) jointly model future world states and actions, p(z_{t+1:t+H}, a_{t:t+H-1} | o_{1:t}, a_{1:t-1}, l). The survey organizes them along three axes:

| Axis | Options |
|---|---|
| I. Spatial state | latent embeddings · 2D pixel/video · 3D/4D explicit geometry (3DGS, occupancy, point clouds) |
| II. Action–world coupling | cascaded (world → policy) · joint end-to-end · planning-in-the-loop (MPC / trajectory scoring) |
| III. Temporal engine | spatio-temporal diffusion / flow matching · autoregressive transformers · state-space recurrent latents |

![Taxonomy](figures/fig04_taxonomy.png)
![Milestones](figures/fig03_milestones.png)

## Leaderboards

<!-- BEGIN:LEADERBOARDS -->
<!-- END:LEADERBOARDS -->

To add a result, open an [**Add result**](../../issues/new?template=add-result.yml) issue or edit the CSV in [`data/leaderboards/`](data/leaderboards).

## Physics-grounded metrics (`wamscore`)

Perceptual scores such as FVD do not tell you whether a rollout is physically possible or whether it responds to the action. `wamscore` implements the three diagnostics defined in Section 5.4 of the survey:

| Metric | Question it answers | Better |
|---|---|---|
| **IVR** – Interpenetration Volume Ratio | How much of the predicted agent volume overlaps rigid obstacles? | lower |
| **E_dn** – Depth-Normal Temporal Consistency | Do generated surfaces stay rigid from frame to frame? | lower |
| **Δ_act** – Action-Counterfactual Sensitivity | Do different actions produce proportionally different rollouts? | > 0 (0 = action ignored) |

It also includes `intervention_report`, which scores a forecaster under executed, wrong, and no-action conditions, following [Does the Action Matter?](https://arxiv.org/abs/2611.24840) (WAM-AD Workshop @ WACV 2027).

```bash
pip install -e .
python -m pytest tests          # 9 tests
python examples/evaluate_rollouts.py
```

Settings are edited in the `EvalConfig` dataclass at the top of `examples/evaluate_rollouts.py` (no command-line arguments). With no paths set, the script runs on a synthetic scene:

```
IVR       : 0.5000  (lower is better)
E_dn      : 0.0200  (lower is better)
Delta_act : 2.9394  (0 = action ignored)
```

Minimal use in your own code:

```python
from wamscore import interpenetration_volume_ratio, action_counterfactual_sensitivity

ivr = interpenetration_volume_ratio(agent_occ, env_occ)          # bool (H, X, Y, Z)
dact = action_counterfactual_sensitivity(rollouts, actions)      # K rollouts, K actions
```

## WAM Reporting Checklist (WAM-RC)

When you benchmark a world-action model, please report:

1. **Closed-loop latency** – ms per action chunk and effective Hz on a named GPU (decoding, denoising, MPC included).
2. **Perceptual and physical metrics together** – FVD/LPIPS plus IVR, collision rate, E_dn, and Δ_act or an intervention test.
3. **Data provenance** – web-video, simulation, and teleoperation hours separately.
4. **Failure breakdown** – occlusion, lighting, long-horizon chaining, and a perturbation suite.
5. **Benchmark protocol** – benchmark version and split, metric definition, seeds/trials, any best-of-N selection.
6. **Ethical and safety compliance** – torque/velocity limits, emergency stops, privacy safeguards.

## Paper list

Papers marked 🆕 were added after the survey was submitted. Machine-readable copies: [`data/papers.yaml`](data/papers.yaml) and [`docs/papers.bib`](docs/papers.bib).

<!-- BEGIN:PAPERS -->
<!-- END:PAPERS -->

## Figures

Every figure of the survey is in [`figures/`](figures) as a vector PDF and a 300-dpi PNG. You may reuse them in papers, slides, and teaching with attribution to the survey (see the license note below).

![Driving WAM pipeline](figures/fig11_driving.png)

## Citation

If this repository or the survey helps your work, please cite the survey:

```bibtex
@article{singh2027visualwam,
  author  = {Singh, Binay Kumar and Lobo, Niels Da Vitoria},
  title   = {Visual World-Action Models for Embodied {AI} and Autonomous Driving: A Systematic Survey of Spatial Representations, Generative Dynamics, and Benchmarks},
  journal = {The Visual Computer},
  year    = {2027},
  note    = {Under review}
}
```

and, if you use the leaderboards or paper list, the repository (the DOI always resolves to the latest monthly release):

```bibtex
@software{singh_awesome_visual_wam,
  author    = {Singh, Binay Kumar and Lobo, Niels Da Vitoria},
  title     = {Awesome Visual World-Action Models: paper list, leaderboards, and wamscore},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://github.com/binayksingh/awesome-visual-world-action-models}
}
```

The full reference list of the survey is in [`docs/references.bib`](docs/references.bib).

## License

Code (`wamscore/`, `examples/`, `tests/`) is released under the MIT License. Figures are shared for reuse with attribution; the final figure license will follow the journal's publication agreement. Icons in the figures are from [Microsoft Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (MIT License).
