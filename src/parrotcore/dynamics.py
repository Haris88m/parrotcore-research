from __future__ import annotations

from dataclasses import dataclass
from math import ceil, sqrt
from typing import Mapping

from .models import JointSpec


@dataclass(frozen=True)
class TrajectorySample:
    t_s: float
    positions: dict[str, float]
    velocities: dict[str, float]
    accelerations: dict[str, float]
    jerks: dict[str, float]


@dataclass(frozen=True)
class Trajectory:
    duration_s: float
    sample_hz: float
    samples: tuple[TrajectorySample, ...]


class TrajectoryPlanner:
    """Quintic minimum-jerk-ish joint-space trajectory planner.

    The normalized polynomial s(u)=10u^3-15u^4+6u^5 has zero velocity and
    acceleration at both endpoints. Duration is automatically increased until
    configured speed, acceleration and jerk envelopes are respected.
    """

    # Exact maxima for derivatives of the quintic smoothstep over u in [0,1].
    VEL_GAIN = 1.875
    ACC_GAIN = 5.773502691896258
    JERK_GAIN = 60.0

    def __init__(self, joints: Mapping[str, JointSpec], sample_hz: float = 50.0):
        if sample_hz <= 0:
            raise ValueError("sample_hz must be positive")
        self.joints = dict(joints)
        self.sample_hz = float(sample_hz)

    def minimum_duration(self, start: Mapping[str, float], target: Mapping[str, float]) -> float:
        required = 0.0
        for name, target_value in target.items():
            if name not in self.joints:
                raise ValueError(f"unknown joint {name!r}")
            spec = self.joints[name]
            tv = float(target_value)
            if not spec.minimum <= tv <= spec.maximum:
                raise ValueError(f"{name} target {tv} outside [{spec.minimum}, {spec.maximum}]")
            sv = float(start.get(name, spec.home))
            delta = abs(tv - sv)
            if delta == 0:
                continue
            if spec.max_speed <= 0 or spec.max_accel <= 0 or spec.max_jerk <= 0:
                raise ValueError(f"non-positive dynamic limit on {name}")
            t_v = self.VEL_GAIN * delta / spec.max_speed
            t_a = sqrt(self.ACC_GAIN * delta / spec.max_accel)
            t_j = (self.JERK_GAIN * delta / spec.max_jerk) ** (1.0 / 3.0)
            required = max(required, t_v, t_a, t_j)
        return required

    def plan(self, start: Mapping[str, float], target: Mapping[str, float], requested_duration_s: float | None = None) -> Trajectory:
        start_full = {name: float(start.get(name, spec.home)) for name, spec in self.joints.items()}
        target_full = dict(start_full)
        for name, value in target.items():
            if name not in self.joints:
                raise ValueError(f"unknown joint {name!r}")
            spec = self.joints[name]
            value = float(value)
            if not spec.minimum <= value <= spec.maximum:
                raise ValueError(f"{name} target {value} outside [{spec.minimum}, {spec.maximum}]")
            target_full[name] = value

        minimum = self.minimum_duration(start_full, target_full)
        requested = 0.0 if requested_duration_s is None else max(0.0, float(requested_duration_s))
        duration = max(minimum, requested, 1.0 / self.sample_hz)
        steps = max(1, int(ceil(duration * self.sample_hz)))
        duration = steps / self.sample_hz

        samples: list[TrajectorySample] = []
        for i in range(steps + 1):
            t = i / self.sample_hz
            u = min(1.0, t / duration)
            s = 10*u**3 - 15*u**4 + 6*u**5
            ds = 30*u**2 - 60*u**3 + 30*u**4
            d2s = 60*u - 180*u**2 + 120*u**3
            d3s = 60 - 360*u + 360*u**2
            pos: dict[str, float] = {}; vel: dict[str, float] = {}; acc: dict[str, float] = {}; jerk: dict[str, float] = {}
            for name, sv in start_full.items():
                delta = target_full[name] - sv
                pos[name] = sv + delta * s
                vel[name] = delta * ds / duration
                acc[name] = delta * d2s / (duration**2)
                jerk[name] = delta * d3s / (duration**3)
            samples.append(TrajectorySample(t, pos, vel, acc, jerk))

        # Force exact endpoint values against floating-point residue.
        last = samples[-1]
        samples[-1] = TrajectorySample(last.t_s, target_full, {k: 0.0 for k in target_full}, {k: 0.0 for k in target_full}, last.jerks)
        return Trajectory(duration, self.sample_hz, tuple(samples))
