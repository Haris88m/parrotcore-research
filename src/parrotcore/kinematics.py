from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin
from typing import Mapping

from .profile import BodyProfile

Vec3 = tuple[float, float, float]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return a[0] + b[0], a[1] + b[1], a[2] + b[2]


def _scale(v: Vec3, s: float) -> Vec3:
    return v[0] * s, v[1] * s, v[2] * s


def _rot_x(v: Vec3, deg: float) -> Vec3:
    a = radians(deg)
    c, s = cos(a), sin(a)
    x, y, z = v
    return x, y * c - z * s, y * s + z * c


def _rot_z(v: Vec3, deg: float) -> Vec3:
    a = radians(deg)
    c, s = cos(a), sin(a)
    x, y, z = v
    return x * c - y * s, x * s + y * c, z


def _body(v: Vec3, lean_deg: float, center_z: float = 0.17) -> Vec3:
    return _add((0.0, 0.0, center_z), _rot_x(v, -lean_deg))


@dataclass(frozen=True)
class CreatureGeometry:
    points: dict[str, Vec3]
    segments: tuple[tuple[str, str, str], ...]
    joint_positions: dict[str, Vec3]
    species: str = "generic"


# Historical public name retained for v0.3 code.
BirdGeometry = CreatureGeometry


def _head_basis(head_center: Vec3, yaw: float, pitch: float):
    forward = _rot_z(_rot_x((0, 1, 0), -pitch), -yaw)
    right = _rot_z((1, 0, 0), -yaw)
    up = _rot_z(_rot_x((0, 0, 1), -pitch), -yaw)

    def local(x: float, y: float, z: float) -> Vec3:
        return (
            head_center[0] + right[0] * x + forward[0] * y + up[0] * z,
            head_center[1] + right[1] * x + forward[1] * y + up[1] * z,
            head_center[2] + right[2] * x + forward[2] * y + up[2] * z,
        )

    return local


def compute_geometry(pose: Mapping[str, float]) -> CreatureGeometry:
    """Reference parrot conceptual 3D kinematic skeleton (v0.3 compatible)."""
    yaw = float(pose.get("neck_yaw", 0.0))
    pitch = float(pose.get("neck_pitch", 0.0))
    beak = float(pose.get("beak", 0.0))
    wl = float(pose.get("wing_left", 0.0))
    wr = float(pose.get("wing_right", 0.0))
    tail = float(pose.get("tail_pitch", 0.0))
    lids = float(pose.get("eyelids", 0.0))
    lean = float(pose.get("body_lean", 0.0))

    body_center = _body((0, 0, 0), lean)
    chest = _body((0, 0.035, 0.025), lean)
    body_top = _body((0, 0.005, 0.105), lean)
    body_bottom = _body((0, 0, -0.095), lean)
    neck_base = _body((0, 0.012, 0.11), lean)
    neck_vec = _rot_z(_rot_x((0, 0.018, 0.068), -pitch), -yaw)
    head_center = _add(neck_base, neck_vec)
    head_local = _head_basis(head_center, yaw, pitch)

    beak_base = head_local(0, 0.041, -0.004)
    beak_tip = head_local(0, 0.078, -0.004 - 0.00045 * beak)
    eye_l = head_local(-0.023, 0.022, 0.016)
    eye_r = head_local(0.023, 0.022, 0.016)
    lid_drop = 0.00017 * lids
    lid_l = head_local(-0.023, 0.023, 0.025 - lid_drop)
    lid_r = head_local(0.023, 0.023, 0.025 - lid_drop)

    wing_l_hinge = _body((-0.064, 0.0, 0.045), lean)
    wing_r_hinge = _body((0.064, 0.0, 0.045), lean)

    def wing_tip(side: float, angle: float) -> Vec3:
        a = radians(angle)
        local = (side * (0.085 + 0.075 * sin(a)), -0.018, -0.05 + 0.105 * sin(a))
        return _body(local, lean)

    wing_l_tip = wing_tip(-1.0, wl)
    wing_r_tip = wing_tip(1.0, wr)
    wing_l_mid = tuple((wing_l_hinge[i] + wing_l_tip[i]) / 2 for i in range(3))
    wing_r_mid = tuple((wing_r_hinge[i] + wing_r_tip[i]) / 2 for i in range(3))
    tail_base = _body((0, -0.055, -0.035), lean)
    tail_local = _rot_x((0, -0.12, -0.018), tail)
    tail_tip = _add(tail_base, _rot_x(tail_local, -lean))

    points = {
        "perch_l": (-0.22, 0.0, 0.0), "perch_r": (0.22, 0.0, 0.0),
        "foot_l": (-0.032, 0.0, 0.018), "foot_r": (0.032, 0.0, 0.018),
        "body_center": body_center, "chest": chest, "body_top": body_top, "body_bottom": body_bottom,
        "neck_base": neck_base, "head_center": head_center,
        "beak_base": beak_base, "beak_tip": beak_tip,
        "eye_l": eye_l, "eye_r": eye_r, "lid_l": lid_l, "lid_r": lid_r,
        "wing_l_hinge": wing_l_hinge, "wing_l_mid": wing_l_mid, "wing_l_tip": wing_l_tip,
        "wing_r_hinge": wing_r_hinge, "wing_r_mid": wing_r_mid, "wing_r_tip": wing_r_tip,
        "tail_base": tail_base, "tail_tip": tail_tip,
    }
    segments = (
        ("perch_l", "perch_r", "perch"),
        ("foot_l", "body_bottom", "leg"), ("foot_r", "body_bottom", "leg"),
        ("body_bottom", "body_center", "body"), ("body_center", "body_top", "body"),
        ("body_center", "chest", "body"), ("body_top", "neck_base", "neck"),
        ("neck_base", "head_center", "neck"), ("head_center", "beak_base", "head"),
        ("beak_base", "beak_tip", "beak"),
        ("head_center", "eye_l", "face"), ("head_center", "eye_r", "face"),
        ("eye_l", "lid_l", "lid"), ("eye_r", "lid_r", "lid"),
        ("wing_l_hinge", "wing_l_mid", "wing"), ("wing_l_mid", "wing_l_tip", "wing"),
        ("wing_r_hinge", "wing_r_mid", "wing"), ("wing_r_mid", "wing_r_tip", "wing"),
        ("tail_base", "tail_tip", "tail"),
    )
    joint_positions = {
        "neck_yaw": neck_base, "neck_pitch": neck_base, "beak": beak_base,
        "wing_left": wing_l_hinge, "wing_right": wing_r_hinge, "tail_pitch": tail_base,
        "eyelids": head_center, "body_lean": body_center,
    }
    return CreatureGeometry(points=points, segments=segments, joint_positions=joint_positions, species="parrot")


def compute_owl_geometry(pose: Mapping[str, float]) -> CreatureGeometry:
    yaw = float(pose.get("head_yaw", 0.0))
    pitch = float(pose.get("head_pitch", 0.0))
    beak = float(pose.get("beak", 0.0))
    wl = float(pose.get("wing_left", 0.0))
    wr = float(pose.get("wing_right", 0.0))
    tail = float(pose.get("tail_pitch", 0.0))
    lids = float(pose.get("eyelids", 0.0))
    lean = float(pose.get("body_lean", 0.0))

    center_z = 0.155
    body_center = _body((0, 0, 0), lean, center_z)
    body_top = _body((0, 0.0, 0.095), lean, center_z)
    body_bottom = _body((0, 0.0, -0.09), lean, center_z)
    head_base = _body((0, 0.005, 0.10), lean, center_z)
    head_center = _add(head_base, _rot_z(_rot_x((0, 0.006, 0.052), -pitch), -yaw))
    local = _head_basis(head_center, yaw, pitch)

    eye_l = local(-0.032, 0.031, 0.014)
    eye_r = local(0.032, 0.031, 0.014)
    lid_drop = 0.00022 * lids
    lid_l = local(-0.032, 0.032, 0.026 - lid_drop)
    lid_r = local(0.032, 0.032, 0.026 - lid_drop)
    beak_base = local(0, 0.041, -0.008)
    beak_tip = local(0, 0.064, -0.012 - 0.00035 * beak)

    wing_l_hinge = _body((-0.067, 0.0, 0.040), lean, center_z)
    wing_r_hinge = _body((0.067, 0.0, 0.040), lean, center_z)

    def owl_wing(side: float, angle: float) -> Vec3:
        a = radians(angle)
        return _body((side * (0.075 + 0.055 * sin(a)), -0.018, -0.045 + 0.075 * sin(a)), lean, center_z)

    wing_l_tip = owl_wing(-1, wl); wing_r_tip = owl_wing(1, wr)
    wing_l_mid = tuple((wing_l_hinge[i] + wing_l_tip[i]) / 2 for i in range(3))
    wing_r_mid = tuple((wing_r_hinge[i] + wing_r_tip[i]) / 2 for i in range(3))
    tail_base = _body((0, -0.045, -0.052), lean, center_z)
    tail_tip = _add(tail_base, _rot_x((0, -0.075, -0.012), tail - lean))
    ear_l = local(-0.045, -0.006, 0.045); ear_r = local(0.045, -0.006, 0.045)

    points = {
        "perch_l": (-0.20, 0, 0), "perch_r": (0.20, 0, 0),
        "foot_l": (-0.030, 0, 0.017), "foot_r": (0.030, 0, 0.017),
        "body_center": body_center, "body_top": body_top, "body_bottom": body_bottom,
        "head_base": head_base, "head_center": head_center, "ear_l": ear_l, "ear_r": ear_r,
        "beak_base": beak_base, "beak_tip": beak_tip,
        "eye_l": eye_l, "eye_r": eye_r, "lid_l": lid_l, "lid_r": lid_r,
        "wing_l_hinge": wing_l_hinge, "wing_l_mid": wing_l_mid, "wing_l_tip": wing_l_tip,
        "wing_r_hinge": wing_r_hinge, "wing_r_mid": wing_r_mid, "wing_r_tip": wing_r_tip,
        "tail_base": tail_base, "tail_tip": tail_tip,
    }
    segments = (
        ("perch_l", "perch_r", "perch"),
        ("foot_l", "body_bottom", "leg"), ("foot_r", "body_bottom", "leg"),
        ("body_bottom", "body_center", "body"), ("body_center", "body_top", "body"),
        ("body_top", "head_base", "neck"), ("head_base", "head_center", "neck"),
        ("head_center", "ear_l", "head"), ("head_center", "ear_r", "head"),
        ("head_center", "beak_base", "head"), ("beak_base", "beak_tip", "beak"),
        ("head_center", "eye_l", "face"), ("head_center", "eye_r", "face"),
        ("eye_l", "lid_l", "lid"), ("eye_r", "lid_r", "lid"),
        ("wing_l_hinge", "wing_l_mid", "wing"), ("wing_l_mid", "wing_l_tip", "wing"),
        ("wing_r_hinge", "wing_r_mid", "wing"), ("wing_r_mid", "wing_r_tip", "wing"),
        ("tail_base", "tail_tip", "tail"),
    )
    joint_positions = {
        "head_yaw": head_base, "head_pitch": head_base, "beak": beak_base,
        "wing_left": wing_l_hinge, "wing_right": wing_r_hinge, "tail_pitch": tail_base,
        "eyelids": head_center, "body_lean": body_center,
    }
    return CreatureGeometry(points, segments, joint_positions, "owl")


def compute_raven_geometry(pose: Mapping[str, float]) -> CreatureGeometry:
    yaw = float(pose.get("neck_yaw", 0.0))
    pitch = float(pose.get("neck_pitch", 0.0))
    beak = float(pose.get("beak", 0.0))
    wl = float(pose.get("wing_left", 0.0))
    wr = float(pose.get("wing_right", 0.0))
    tail_fan = float(pose.get("tail_fan", 0.0))
    lids = float(pose.get("eyelids", 0.0))
    lean = float(pose.get("body_lean", 0.0))

    center_z = 0.17
    body_center = _body((0, 0, 0), lean, center_z)
    body_top = _body((0, 0.003, 0.10), lean, center_z)
    body_bottom = _body((0, 0.0, -0.095), lean, center_z)
    neck_base = _body((0, 0.010, 0.102), lean, center_z)
    head_center = _add(neck_base, _rot_z(_rot_x((0, 0.020, 0.062), -pitch), -yaw))
    local = _head_basis(head_center, yaw, pitch)
    eye_l = local(-0.020, 0.024, 0.014); eye_r = local(0.020, 0.024, 0.014)
    lid_drop = 0.00016 * lids
    lid_l = local(-0.020, 0.025, 0.023 - lid_drop); lid_r = local(0.020, 0.025, 0.023 - lid_drop)
    beak_base = local(0, 0.038, -0.005)
    beak_tip = local(0, 0.091, -0.008 - 0.00035 * beak)

    wing_l_hinge = _body((-0.060, 0.0, 0.044), lean, center_z)
    wing_r_hinge = _body((0.060, 0.0, 0.044), lean, center_z)

    def raven_wing(side: float, angle: float) -> Vec3:
        a = radians(angle)
        return _body((side * (0.080 + 0.070 * sin(a)), -0.030, -0.055 + 0.095 * sin(a)), lean, center_z)

    wing_l_tip = raven_wing(-1, wl); wing_r_tip = raven_wing(1, wr)
    wing_l_mid = tuple((wing_l_hinge[i] + wing_l_tip[i]) / 2 for i in range(3))
    wing_r_mid = tuple((wing_r_hinge[i] + wing_r_tip[i]) / 2 for i in range(3))
    tail_base = _body((0, -0.055, -0.040), lean, center_z)
    fan = 0.03 + 0.0008 * tail_fan
    tail_l = _add(tail_base, (-fan, -0.135, -0.020))
    tail_r = _add(tail_base, (fan, -0.135, -0.020))
    tail_tip = _add(tail_base, (0, -0.150, -0.025))

    points = {
        "perch_l": (-0.22, 0, 0), "perch_r": (0.22, 0, 0),
        "foot_l": (-0.033, 0, 0.018), "foot_r": (0.033, 0, 0.018),
        "body_center": body_center, "body_top": body_top, "body_bottom": body_bottom,
        "neck_base": neck_base, "head_center": head_center,
        "beak_base": beak_base, "beak_tip": beak_tip,
        "eye_l": eye_l, "eye_r": eye_r, "lid_l": lid_l, "lid_r": lid_r,
        "wing_l_hinge": wing_l_hinge, "wing_l_mid": wing_l_mid, "wing_l_tip": wing_l_tip,
        "wing_r_hinge": wing_r_hinge, "wing_r_mid": wing_r_mid, "wing_r_tip": wing_r_tip,
        "tail_base": tail_base, "tail_l": tail_l, "tail_r": tail_r, "tail_tip": tail_tip,
    }
    segments = (
        ("perch_l", "perch_r", "perch"),
        ("foot_l", "body_bottom", "leg"), ("foot_r", "body_bottom", "leg"),
        ("body_bottom", "body_center", "body"), ("body_center", "body_top", "body"),
        ("body_top", "neck_base", "neck"), ("neck_base", "head_center", "neck"),
        ("head_center", "beak_base", "head"), ("beak_base", "beak_tip", "beak"),
        ("head_center", "eye_l", "face"), ("head_center", "eye_r", "face"),
        ("eye_l", "lid_l", "lid"), ("eye_r", "lid_r", "lid"),
        ("wing_l_hinge", "wing_l_mid", "wing"), ("wing_l_mid", "wing_l_tip", "wing"),
        ("wing_r_hinge", "wing_r_mid", "wing"), ("wing_r_mid", "wing_r_tip", "wing"),
        ("tail_base", "tail_l", "tail"), ("tail_base", "tail_r", "tail"), ("tail_base", "tail_tip", "tail"),
    )
    joint_positions = {
        "neck_yaw": neck_base, "neck_pitch": neck_base, "beak": beak_base,
        "wing_left": wing_l_hinge, "wing_right": wing_r_hinge, "tail_fan": tail_base,
        "eyelids": head_center, "body_lean": body_center,
    }
    return CreatureGeometry(points, segments, joint_positions, "raven")


def compute_creature_geometry(profile: BodyProfile, pose: Mapping[str, float]) -> CreatureGeometry:
    species = profile.species.lower()
    if species == "parrot":
        return compute_geometry(pose)
    if species == "owl":
        return compute_owl_geometry(pose)
    if species == "raven":
        return compute_raven_geometry(pose)
    raise ValueError(f"no digital-twin geometry provider registered for species {profile.species!r}")
