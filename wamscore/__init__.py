"""wamscore: reference implementations of physics-grounded world-action model metrics.

Metrics follow the definitions in the survey "Visual World-Action Models for
Embodied AI and Autonomous Driving" (Singh):

* interpenetration_volume_ratio  - IVR, geometric plausibility of rollouts
* depth_normal_consistency       - E_dn, temporal rigidity of generated surfaces
* action_counterfactual_sensitivity - Delta_act, dependence of rollouts on actions
* intervention_report            - executed / wrong / no-action intervention test
"""

from .ivr import interpenetration_volume_ratio, ivr_per_step
from .depth_normal import depth_normal_consistency, normals_from_depth, reproject_depth
from .action_sensitivity import (
    InterventionResult,
    action_counterfactual_sensitivity,
    intervention_report,
    mean_iou,
)

__all__ = [
    "interpenetration_volume_ratio",
    "ivr_per_step",
    "depth_normal_consistency",
    "normals_from_depth",
    "reproject_depth",
    "action_counterfactual_sensitivity",
    "intervention_report",
    "InterventionResult",
    "mean_iou",
]

__version__ = "0.1.0"
