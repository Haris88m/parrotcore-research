from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from typing import Iterable, Mapping

from .kinematics import CreatureGeometry, compute_creature_geometry, compute_geometry
from .models import MotionFrame
from .profile import BodyProfile
from .hardware import HardwareBaseline


@dataclass(frozen=True)
class SimulationAssumptions:
    """Fallback engineering assumptions until measured prototype data replaces them."""
    servo_voltage_v: float = 6.0
    servo_idle_current_a: float = 0.12
    servo_moving_current_a: float = 0.35
    servo_peak_current_a: float = 0.80
    compute_typical_w: float = 10.0
    compute_peak_w: float = 25.0
    model_mass_kg: float = 1.8
    target_height_m: float = 0.34
    watchdog_s: float = 0.75


@dataclass(frozen=True)
class EffectivenessMetrics:
    degrees_of_freedom: int
    joint_travel_total: float
    neck_yaw_span_deg: float
    neck_pitch_span_deg: float
    wing_span_command_deg: float
    beak_span_deg: float
    tail_span_deg: float
    lean_span_deg: float
    watchdog_cutoff_s: float
    servo_idle_w: float
    servo_all_moving_w: float
    servo_peak_w: float
    system_typical_motion_w: float
    system_peak_w: float
    estimated_mass_kg: float
    target_height_m: float


@dataclass(frozen=True)
class CreatureEffectiveness:
    species: str
    role: str
    degrees_of_freedom: int
    total_joint_travel: float
    expression_count: int
    capability_count: int
    yaw_span_deg: float
    pitch_span_deg: float
    wing_command_span_deg: float
    beak_span_deg: float
    tail_expression_span_deg: float
    servo_idle_w: float
    servo_all_moving_w: float
    servo_peak_w: float
    system_typical_motion_w: float
    system_peak_w: float
    estimated_mass_kg: float
    target_height_m: float
    watchdog_cutoff_s: float


def _span(joints: Mapping[str, object], name: str, fallback: float = 0.0) -> float:
    if name not in joints:
        return fallback
    spec = joints[name]
    return float(spec.maximum) - float(spec.minimum)


def effectiveness(joints: Mapping[str, object], assumptions: SimulationAssumptions = SimulationAssumptions()) -> EffectivenessMetrics:
    """Historical parrot metrics API retained for v0.3 compatibility."""
    def span(name: str) -> float:
        return _span(joints, name)

    n = len(joints)
    idle = n * assumptions.servo_voltage_v * assumptions.servo_idle_current_a
    moving = n * assumptions.servo_voltage_v * assumptions.servo_moving_current_a
    peak = n * assumptions.servo_voltage_v * assumptions.servo_peak_current_a
    return EffectivenessMetrics(
        degrees_of_freedom=n,
        joint_travel_total=sum(_span(joints, k) for k in joints if k != "eyelids"),
        neck_yaw_span_deg=span("neck_yaw"),
        neck_pitch_span_deg=span("neck_pitch"),
        wing_span_command_deg=span("wing_left") + span("wing_right"),
        beak_span_deg=span("beak"),
        tail_span_deg=span("tail_pitch"),
        lean_span_deg=span("body_lean"),
        watchdog_cutoff_s=assumptions.watchdog_s,
        servo_idle_w=idle,
        servo_all_moving_w=moving,
        servo_peak_w=peak,
        system_typical_motion_w=moving + assumptions.compute_typical_w,
        system_peak_w=peak + assumptions.compute_peak_w,
        estimated_mass_kg=assumptions.model_mass_kg,
        target_height_m=assumptions.target_height_m,
    )


def creature_effectiveness(
    profile: BodyProfile,
    assumptions: SimulationAssumptions = SimulationAssumptions(),
    hardware: HardwareBaseline | None = None,
) -> CreatureEffectiveness:
    sim = profile.simulation
    watchdog = sim.get("watchdog_s", assumptions.watchdog_s)
    n = len(profile.joints)
    if hardware is not None:
        voltage = hardware.servo_regulator.output_voltage_v
        idle_current = hardware.mapped_servo_no_load_current_a
        moving_current = 0.0
        for joint in hardware.actuator_map:
            servo = hardware.servo_for_joint(joint)
            moving_current += servo.no_load_current_a + (servo.stall_current_a - servo.no_load_current_a) * hardware.modeling.nominal_dynamic_load_fraction
        peak_current = hardware.mapped_servo_all_stall_current_a
        idle = voltage * idle_current
        moving = voltage * moving_current
        peak = voltage * peak_current
        compute_typical = hardware.electronics_baseline_power_w
        compute_peak = hardware.electronics_baseline_power_w
    else:
        voltage = sim.get("servo_voltage_v", assumptions.servo_voltage_v)
        idle_a = sim.get("servo_idle_current_a", assumptions.servo_idle_current_a)
        moving_a = sim.get("servo_moving_current_a", assumptions.servo_moving_current_a)
        peak_a = sim.get("servo_peak_current_a", assumptions.servo_peak_current_a)
        compute_typical = sim.get("compute_typical_w", assumptions.compute_typical_w)
        compute_peak = sim.get("compute_peak_w", assumptions.compute_peak_w)
        idle = n * voltage * idle_a
        moving = n * voltage * moving_a
        peak = n * voltage * peak_a

    yaw = max(_span(profile.joints, "neck_yaw"), _span(profile.joints, "head_yaw"))
    pitch = max(_span(profile.joints, "neck_pitch"), _span(profile.joints, "head_pitch"))
    tail = max(_span(profile.joints, "tail_pitch"), _span(profile.joints, "tail_fan"))
    return CreatureEffectiveness(
        species=profile.species,
        role=profile.role,
        degrees_of_freedom=n,
        total_joint_travel=sum(_span(profile.joints, name) for name in profile.joints if name != "eyelids"),
        expression_count=len(profile.expressions),
        capability_count=len(profile.capabilities),
        yaw_span_deg=yaw,
        pitch_span_deg=pitch,
        wing_command_span_deg=_span(profile.joints, "wing_left") + _span(profile.joints, "wing_right"),
        beak_span_deg=_span(profile.joints, "beak"),
        tail_expression_span_deg=tail,
        servo_idle_w=idle,
        servo_all_moving_w=moving,
        servo_peak_w=peak,
        system_typical_motion_w=moving + compute_typical,
        system_peak_w=peak + compute_peak,
        estimated_mass_kg=sim.get("model_mass_kg", assumptions.model_mass_kg),
        target_height_m=sim.get("target_height_m", assumptions.target_height_m),
        watchdog_cutoff_s=watchdog,
    )


def interpolate_motion(frames: Iterable[MotionFrame], start_pose: Mapping[str, float], fps: int = 30) -> list[dict[str, float]]:
    pose = dict(start_pose)
    result = [dict(pose)]
    for frame in frames:
        target = dict(pose)
        target.update({k: float(v) for k, v in frame.positions.items()})
        steps = max(1, round(max(0.0, frame.duration_s) * fps))
        for i in range(1, steps + 1):
            t = i / steps
            u = t * t * (3.0 - 2.0 * t)
            result.append({k: pose.get(k, 0.0) + (target[k] - pose.get(k, 0.0)) * u for k in target})
        pose = target
    return result


def geometry_extent(g: CreatureGeometry) -> dict[str, float]:
    xs, ys, zs = zip(*g.points.values())
    return {"width_m": max(xs) - min(xs), "depth_m": max(ys) - min(ys), "height_m": max(zs) - min(zs)}


def max_tip_speed(poses: Iterable[Mapping[str, float]], fps: int = 30) -> dict[str, float]:
    """Historical parrot-only tip-speed helper retained for v0.3 tests."""
    names = ["beak_tip", "wing_l_tip", "wing_r_tip", "tail_tip", "head_center"]
    prev = None
    maxima = {k: 0.0 for k in names}
    for pose in poses:
        g = compute_geometry(pose)
        cur = {k: g.points[k] for k in names}
        if prev is not None:
            for k in names:
                d = sqrt(sum((cur[k][i] - prev[k][i]) ** 2 for i in range(3)))
                maxima[k] = max(maxima[k], d * fps)
        prev = cur
    return maxima


def creature_tip_speed(profile: BodyProfile, poses: Iterable[Mapping[str, float]], fps: int = 30) -> dict[str, float]:
    names = ["beak_tip", "wing_l_tip", "wing_r_tip", "head_center"]
    prev = None
    maxima = {k: 0.0 for k in names}
    for pose in poses:
        g = compute_creature_geometry(profile, pose)
        cur = {k: g.points[k] for k in names if k in g.points}
        if prev is not None:
            for k in cur:
                if k in prev:
                    d = sqrt(sum((cur[k][i] - prev[k][i]) ** 2 for i in range(3)))
                    maxima[k] = max(maxima.get(k, 0.0), d * fps)
        prev = cur
    return maxima


def metrics_dict(metrics) -> dict[str, float | int | str]:
    return asdict(metrics)
