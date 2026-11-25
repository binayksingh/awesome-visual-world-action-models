"""Depth-Normal Temporal Consistency (E_dn).

E_dn penalizes non-rigid surface "morphing" between consecutive generated
frames. For each step tau, frame tau is reprojected into frame tau+1 using the
commanded camera/ego motion, and the two frames are compared on static pixels:

    E_dn = 1/(H-1) * sum_tau mean_{p in static}
           [ |D_{tau+1}(p) - D_{tau->tau+1}(p)| / D_{tau->tau+1}(p)
             + lambda_n * (1 - n_{tau+1}(p) . n_{tau->tau+1}(p)) ]

Reprojection depends on the camera model of each benchmark, so this module
expects the caller to pass depth maps that are already aligned to a common
frame (``aligned_prev``), or to use ``reproject_depth`` for a pinhole camera.
Lower is better; a rigid, static scene rendered consistently gives 0.
"""

from __future__ import annotations

import numpy as np


def normals_from_depth(depth: np.ndarray, fx: float = 1.0, fy: float = 1.0) -> np.ndarray:
    """Unit surface normals (H, W, 3) from a depth map via finite differences."""
    d = np.asarray(depth, dtype=np.float64)
    dzdx = np.gradient(d, axis=1) * fx
    dzdy = np.gradient(d, axis=0) * fy
    n = np.stack([-dzdx, -dzdy, np.ones_like(d)], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def reproject_depth(depth: np.ndarray, K: np.ndarray, T_prev_to_next: np.ndarray) -> np.ndarray:
    """Forward-warp a depth map into the next camera with a z-buffer.

    Args:
        depth: (H, W) depth of the previous frame (metres, > 0 where valid).
        K: (3, 3) pinhole intrinsics.
        T_prev_to_next: (4, 4) rigid transform from previous to next camera.

    Returns:
        (H, W) depth in the next camera; pixels that receive no point are 0.
    """
    h, w = depth.shape
    v, u = np.mgrid[0:h, 0:w]
    valid = depth > 0
    z = depth[valid]
    pix = np.stack([u[valid] * z, v[valid] * z, z], axis=0)
    pts = np.linalg.inv(K) @ pix
    pts = T_prev_to_next[:3, :3] @ pts + T_prev_to_next[:3, 3:4]
    front = pts[2] > 1e-6
    pts = pts[:, front]
    proj = K @ pts
    uu = np.round(proj[0] / proj[2]).astype(int)
    vv = np.round(proj[1] / proj[2]).astype(int)
    inside = (uu >= 0) & (uu < w) & (vv >= 0) & (vv < h)
    out = np.full((h, w), np.inf)
    np.minimum.at(out, (vv[inside], uu[inside]), pts[2, inside])
    out[np.isinf(out)] = 0.0
    return out


def depth_normal_consistency(
    depths: np.ndarray,
    aligned_prev: np.ndarray | None = None,
    static_mask: np.ndarray | None = None,
    lambda_n: float = 1.0,
) -> float:
    """Compute E_dn for a generated depth sequence.

    Args:
        depths: (H, Hi, Wi) depth maps D_1..D_H predicted (or estimated) from the
            generated frames.
        aligned_prev: optional (H-1, Hi, Wi) depth maps D_{tau->tau+1}, i.e. frame
            tau reprojected into frame tau+1. If None, the camera is assumed
            static and depths[tau] is compared directly with depths[tau+1].
        static_mask: optional boolean (H-1, Hi, Wi) or (Hi, Wi) mask of static
            pixels; dynamic agents should be excluded.
        lambda_n: weight of the normal term.
    """
    d = np.asarray(depths, dtype=np.float64)
    if d.ndim != 3 or d.shape[0] < 2:
        raise ValueError("depths must have shape (H, Hi, Wi) with H >= 2")
    prev = d[:-1] if aligned_prev is None else np.asarray(aligned_prev, dtype=np.float64)
    nxt = d[1:]
    if prev.shape != nxt.shape:
        raise ValueError("aligned_prev must have shape (H-1, Hi, Wi)")

    errs = []
    for k in range(nxt.shape[0]):
        valid = (prev[k] > 0) & (nxt[k] > 0)
        if static_mask is not None:
            m = np.asarray(static_mask, dtype=bool)
            valid &= m[k] if m.ndim == 3 else m
        if not valid.any():
            continue
        rel = np.abs(nxt[k] - prev[k]) / np.maximum(prev[k], 1e-8)
        n_prev = normals_from_depth(prev[k])
        n_next = normals_from_depth(nxt[k])
        ang = 1.0 - np.clip((n_prev * n_next).sum(-1), -1.0, 1.0)
        errs.append(float(np.mean(rel[valid] + lambda_n * ang[valid])))
    if not errs:
        raise ValueError("no valid pixels in any step")
    return float(np.mean(errs))
