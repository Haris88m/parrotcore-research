from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .kinematics import compute_creature_geometry
from .profile import BodyProfile


@dataclass(frozen=True)
class StabilityEstimate:
    com_x_m: float
    com_y_m: float
    margin_m: float
    stable_proxy: bool


def estimate_stability(profile: BodyProfile, pose: Mapping[str, float]) -> StabilityEstimate:
    """Simple center-of-mass proxy for the conceptual perched digital twin.

    This is not rigid-body dynamics. It is an early warning heuristic until CAD
    masses and a measured perch/grip model exist.
    """
    g = compute_creature_geometry(profile, pose)
    weighted = [
        ("body_center", 0.55),
        ("head_center", 0.17),
        ("wing_l_tip", 0.08),
        ("wing_r_tip", 0.08),
        ("tail_tip", 0.12),
    ]
    available = [(g.points[n], w) for n, w in weighted if n in g.points]
    total = sum(w for _, w in available)
    com_x = sum(p[0]*w for p,w in available)/total
    com_y = sum(p[1]*w for p,w in available)/total
    # Proxy grip envelope around two feet. Future CAD must replace these values.
    half_width = 0.045
    half_depth = 0.040
    margin = min(half_width - abs(com_x), half_depth - abs(com_y))
    return StabilityEstimate(com_x, com_y, margin, margin >= 0.0)
