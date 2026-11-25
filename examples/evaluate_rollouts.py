"""Example: score world-model rollouts with IVR, E_dn and Delta_act.

Edit the EvalConfig dataclass below and run `python examples/evaluate_rollouts.py`.
By default the script builds a small synthetic scene so it runs without data.
To evaluate your own model, point the paths to .npz files with these arrays:

  occupancy_npz : agent_occ (H, X, Y, Z) bool, env_occ (H, X, Y, Z) bool
  depth_npz     : depths (H, Hi, Wi) float, optional static_mask (Hi, Wi) bool
  rollouts_npz  : rollouts (K, ...) float, actions (K, ...) float
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wamscore import (  # noqa: E402
    action_counterfactual_sensitivity,
    depth_normal_consistency,
    interpenetration_volume_ratio,
)


@dataclass
class EvalConfig:
    occupancy_npz: str | None = None   # None -> synthetic example
    depth_npz: str | None = None
    rollouts_npz: str | None = None
    lambda_n: float = 1.0              # weight of the normal term in E_dn
    seed: int = 0


CFG = EvalConfig()


def synthetic_inputs(rng: np.random.Generator):
    H = 6
    agent = np.zeros((H, 32, 32, 8), bool)
    env = np.zeros_like(agent)
    env[:, 20:, :, :] = True                      # a rigid wall
    for t in range(H):                            # agent drifts into the wall
        x0 = 12 + 2 * t
        agent[t, x0:x0 + 6, 10:16, 0:4] = True

    plane = np.tile(np.linspace(2.0, 6.0, 48), (32, 1))
    depths = np.stack([plane + 0.02 * t * rng.normal(size=plane.shape) for t in range(H)])

    actions = [np.array([a]) for a in (-1.0, 0.0, 1.0)]
    base = rng.normal(size=(H, 16))
    rollouts = [base + 0.3 * a[0] for a in actions]
    return agent, env, depths, None, rollouts, actions


def main(cfg: EvalConfig) -> None:
    rng = np.random.default_rng(cfg.seed)
    agent, env, depths, static_mask, rollouts, actions = synthetic_inputs(rng)
    if cfg.occupancy_npz:
        f = np.load(cfg.occupancy_npz)
        agent, env = f["agent_occ"], f["env_occ"]
    if cfg.depth_npz:
        f = np.load(cfg.depth_npz)
        depths = f["depths"]
        static_mask = f["static_mask"] if "static_mask" in f else None
    if cfg.rollouts_npz:
        f = np.load(cfg.rollouts_npz)
        rollouts, actions = list(f["rollouts"]), list(f["actions"])

    print(f"IVR       : {interpenetration_volume_ratio(agent, env):.4f}  (lower is better)")
    print(f"E_dn      : {depth_normal_consistency(depths, static_mask=static_mask, lambda_n=cfg.lambda_n):.4f}  (lower is better)")
    print(f"Delta_act : {action_counterfactual_sensitivity(rollouts, actions):.4f}  (0 = action ignored)")


if __name__ == "__main__":
    main(CFG)
