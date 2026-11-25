import numpy as np
import pytest

from wamscore import (
    action_counterfactual_sensitivity,
    depth_normal_consistency,
    interpenetration_volume_ratio,
    intervention_report,
    ivr_per_step,
    mean_iou,
    reproject_depth,
)


def test_ivr_zero_when_disjoint():
    agent = np.zeros((3, 8, 8, 4), bool)
    env = np.zeros_like(agent)
    agent[:, 1:3, 1:3, :2] = True
    env[:, 5:7, 5:7, :] = True
    assert interpenetration_volume_ratio(agent, env) == 0.0


def test_ivr_half_overlap():
    agent = np.zeros((2, 4, 4, 1), bool)
    env = np.zeros_like(agent)
    agent[:, 0:2, 0:2, 0] = True          # 4 voxels
    env[:, 0:1, 0:2, 0] = True            # overlaps 2 of them
    assert interpenetration_volume_ratio(agent, env) == pytest.approx(0.5)


def test_ivr_skips_empty_steps():
    agent = np.zeros((2, 4, 4), bool)
    env = np.ones_like(agent)
    agent[1, 0, 0] = True
    per = ivr_per_step(agent, env)
    assert np.isnan(per[0]) and per[1] == 1.0
    assert interpenetration_volume_ratio(agent, env) == 1.0


def test_action_sensitivity_zero_for_action_blind_model():
    z = np.random.default_rng(0).normal(size=(5, 4, 4))
    rollouts = [z, z, z]
    actions = [np.array([0.0]), np.array([1.0]), np.array([2.0])]
    assert action_counterfactual_sensitivity(rollouts, actions) == 0.0


def test_action_sensitivity_linear_model():
    actions = [np.array([a]) for a in (0.0, 1.0, 3.0)]
    rollouts = [np.full((2, 2), 2.0 * a[0]) for a in actions]   # |dz| = 2*|da|*sqrt(4)
    assert action_counterfactual_sensitivity(rollouts, actions) == pytest.approx(4.0)


def test_intervention_report():
    target = np.array([0, 1, 1, 2])
    res = intervention_report(
        lambda p, t: mean_iou(p, t, num_classes=3),
        target,
        pred_executed=target.copy(),
        pred_wrong=np.array([0, 0, 0, 0]),
        pred_no_action=np.array([0, 1, 0, 2]),
    )
    assert res.gain_from_action > 0
    assert res.drop_from_wrong_action > 0
    assert res.wrong_below_no_action


def test_edn_zero_for_static_rigid_scene():
    plane = np.tile(np.linspace(2.0, 4.0, 16), (12, 1))
    depths = np.stack([plane] * 4)
    assert depth_normal_consistency(depths) == pytest.approx(0.0)


def test_edn_positive_when_surface_morphs():
    plane = np.tile(np.linspace(2.0, 4.0, 16), (12, 1))
    bumped = plane.copy()
    bumped[4:8, 4:8] += 0.5
    assert depth_normal_consistency(np.stack([plane, bumped, plane])) > 0.0


def test_reproject_identity():
    K = np.array([[10.0, 0, 8], [0, 10.0, 6], [0, 0, 1]])
    depth = np.full((12, 16), 3.0)
    out = reproject_depth(depth, K, np.eye(4))
    assert np.allclose(out, depth)
