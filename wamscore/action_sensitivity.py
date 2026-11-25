"""Action-counterfactual diagnostics.

Two complementary tools are provided.

1. ``action_counterfactual_sensitivity`` implements Delta_act from the survey:

       Delta_act = E_{a != a'} [ || z(a) - z(a') ||_2 / || a - a' ||_2 ]

   where z(a) is the rollout the world model predicts for candidate action a.
   A model whose rollouts ignore the action has Delta_act = 0.

2. ``intervention_report`` scores a forecasting task under three test-time
   conditions (executed action, wrong action, no-action model) with any task
   metric such as mIoU. It reports the accuracy gain from the executed action and
   the drop caused by a wrong action. This follows the intervention protocol of
   Singh and Lobo, "Does the Action Matter?" (WAM-AD @ WACV 2027,
   arXiv:2611.24840): an accuracy gain shows that an action is used, while the
   wrong-action drop shows how strongly forecasts depend on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Sequence

import numpy as np


def action_counterfactual_sensitivity(
    rollouts: Sequence[np.ndarray],
    actions: Sequence[np.ndarray],
    eps: float = 1e-8,
) -> float:
    """Compute Delta_act over all pairs of distinct candidate actions.

    Args:
        rollouts: K predicted rollouts z(a_k), each an array of identical shape
            (for example (H, C, H_img, W_img) latents or (H, X, Y, Z) occupancy).
        actions: K action vectors or action sequences a_k (identical shapes).
        eps: pairs whose action distance is below eps are skipped.

    Returns:
        Mean ratio of rollout distance to action distance over valid pairs.
    """
    if len(rollouts) != len(actions):
        raise ValueError("rollouts and actions must have the same length")
    if len(rollouts) < 2:
        raise ValueError("need at least two candidate actions")

    z = [np.asarray(r, dtype=np.float64).ravel() for r in rollouts]
    a = [np.asarray(x, dtype=np.float64).ravel() for x in actions]
    ratios = []
    for i, j in combinations(range(len(z)), 2):
        da = np.linalg.norm(a[i] - a[j])
        if da < eps:
            continue
        ratios.append(np.linalg.norm(z[i] - z[j]) / da)
    if not ratios:
        raise ValueError("all candidate actions are identical")
    return float(np.mean(ratios))


@dataclass
class InterventionResult:
    executed: float
    wrong: float
    no_action: float

    @property
    def gain_from_action(self) -> float:
        """Executed-action score minus the no-action model's score."""
        return self.executed - self.no_action

    @property
    def drop_from_wrong_action(self) -> float:
        """Executed-action score minus the wrong-action score."""
        return self.executed - self.wrong

    @property
    def wrong_below_no_action(self) -> bool:
        """True when a wrong action is worse than giving no action at all."""
        return self.wrong < self.no_action


def intervention_report(
    metric: Callable[[np.ndarray, np.ndarray], float],
    target: np.ndarray,
    pred_executed: np.ndarray,
    pred_wrong: np.ndarray,
    pred_no_action: np.ndarray,
) -> InterventionResult:
    """Score predictions under executed, wrong, and no-action conditions."""
    return InterventionResult(
        executed=float(metric(pred_executed, target)),
        wrong=float(metric(pred_wrong, target)),
        no_action=float(metric(pred_no_action, target)),
    )


def mean_iou(pred: np.ndarray, target: np.ndarray, num_classes: int, ignore_index: int | None = None) -> float:
    """Mean intersection-over-union over classes present in pred or target."""
    pred = np.asarray(pred).ravel()
    target = np.asarray(target).ravel()
    if ignore_index is not None:
        keep = target != ignore_index
        pred, target = pred[keep], target[keep]
    ious = []
    for c in range(num_classes):
        p, t = pred == c, target == c
        union = np.logical_or(p, t).sum()
        if union == 0:
            continue
        ious.append(np.logical_and(p, t).sum() / union)
    return float(np.mean(ious)) if ious else float("nan")
