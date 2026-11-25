"""Interpenetration Volume Ratio (IVR).

IVR measures how much of the predicted agent (robot, gripper, or ego vehicle)
volume overlaps rigid environment structure across a rollout horizon H:

    IVR = (1/H) * sum_{tau=1..H} Vol(M_agent(t+tau) & M_env(t+tau)) / Vol(M_agent(t+tau))

A physically consistent rollout has IVR close to 0. Inputs are boolean voxel
occupancy grids with a leading time axis, e.g. shape (H, X, Y, Z). Any spatial
shape works (2D BEV grids or 3D voxels), as long as the agent and environment
grids are aligned.
"""

from __future__ import annotations

import numpy as np


def ivr_per_step(agent_occ: np.ndarray, env_occ: np.ndarray) -> np.ndarray:
    """Return the interpenetration ratio for every future step.

    Args:
        agent_occ: boolean array (H, ...) of predicted agent occupancy.
        env_occ: boolean array (H, ...) of rigid environment occupancy.

    Returns:
        float array of shape (H,). Steps where the agent occupies no voxel
        are returned as NaN, because the ratio is undefined there.
    """
    agent = np.asarray(agent_occ, dtype=bool)
    env = np.asarray(env_occ, dtype=bool)
    if agent.shape != env.shape:
        raise ValueError(f"shape mismatch: agent {agent.shape} vs env {env.shape}")
    if agent.ndim < 2:
        raise ValueError("expected a leading time axis, e.g. (H, X, Y, Z)")

    axes = tuple(range(1, agent.ndim))
    agent_vol = agent.sum(axis=axes).astype(np.float64)
    overlap = np.logical_and(agent, env).sum(axis=axes).astype(np.float64)
    out = np.full(agent.shape[0], np.nan)
    valid = agent_vol > 0
    out[valid] = overlap[valid] / agent_vol[valid]
    return out


def interpenetration_volume_ratio(agent_occ: np.ndarray, env_occ: np.ndarray) -> float:
    """Average IVR over all future steps in which the agent is visible."""
    per_step = ivr_per_step(agent_occ, env_occ)
    if np.all(np.isnan(per_step)):
        raise ValueError("agent occupancy is empty at every step")
    return float(np.nanmean(per_step))
