from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Mapping

from .kinematics import compute_creature_geometry
from .profile import BodyProfile


def _distance(a, b) -> float:
    return sqrt(sum((a[i]-b[i])**2 for i in range(3)))


@dataclass(frozen=True)
class CollisionEstimate:
    risk: bool
    reasons: tuple[str, ...]
    minimum_clearance_m: float


def estimate_collision(profile: BodyProfile, pose: Mapping[str, float]) -> CollisionEstimate:
    """Conceptual self/floor collision proxy, not a substitute for CAD collision checking."""
    g = compute_creature_geometry(profile, pose)
    reasons: list[str] = []
    clearances: list[float] = []
    floor_exempt = {"perch_l", "perch_r", "foot_l", "foot_r"}
    for name, point in g.points.items():
        if name not in floor_exempt:
            c = point[2] - 0.005
            clearances.append(c)
            if c < 0:
                reasons.append(f"{name}:floor")

    hc = g.points.get("head_center")
    if hc:
        for wing in ("wing_l_tip", "wing_r_tip"):
            if wing in g.points:
                c = _distance(hc, g.points[wing]) - 0.045
                clearances.append(c)
                if c < 0:
                    reasons.append(f"{wing}:head")

    # Wing tips should remain on their own sides of the torso centerline.
    if "wing_l_tip" in g.points:
        c = -g.points["wing_l_tip"][0] - 0.012
        clearances.append(c)
        if c < 0: reasons.append("wing_left:centerline")
    if "wing_r_tip" in g.points:
        c = g.points["wing_r_tip"][0] - 0.012
        clearances.append(c)
        if c < 0: reasons.append("wing_right:centerline")

    return CollisionEstimate(bool(reasons), tuple(sorted(set(reasons))), min(clearances) if clearances else 1.0)
