from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import JointSpec, MotionFrame


@dataclass(frozen=True)
class BodyProfile:
    """Hardware and embodiment contract for one physical creature body.

    v0.4 deliberately keeps cognition independent of species.  The profile owns
    actuator names, physical limits and species-specific expression frames.
    Older v0.2/v0.3 profiles without the optional creature/expressions sections
    remain valid and load as a generic body.
    """

    name: str
    protocol: str
    joints: dict[str, JointSpec]
    controller_ids: dict[str, int]
    species: str = "generic"
    morphology: str = "generic"
    role: str = "general"
    capabilities: frozenset[str] = field(default_factory=frozenset)
    expressions: dict[str, tuple[MotionFrame, ...]] = field(default_factory=dict)
    simulation: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def home_pose(self) -> dict[str, float]:
        return {name: spec.home for name, spec in self.joints.items()}


def _parse_expressions(data: dict[str, Any]) -> dict[str, tuple[MotionFrame, ...]]:
    result: dict[str, tuple[MotionFrame, ...]] = {}
    for name, raw_frames in data.get("expressions", {}).items():
        if not isinstance(raw_frames, list):
            raise ValueError(f"expression {name!r} must be an array of frame tables")
        frames: list[MotionFrame] = []
        for raw in raw_frames:
            positions = {str(k): float(v) for k, v in raw.get("positions", {}).items()}
            frames.append(MotionFrame(positions=positions, duration_s=float(raw.get("duration_s", 0.25))))
        result[str(name)] = tuple(frames)
    return result


def load_profile(path: str | Path) -> BodyProfile:
    path = Path(path)
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    body = data["body"]
    creature = data.get("creature", {})

    joints: dict[str, JointSpec] = {}
    controller_ids: dict[str, int] = {}
    for name, raw in data["joints"].items():
        joints[name] = JointSpec(
            name=name,
            minimum=float(raw["minimum"]),
            maximum=float(raw["maximum"]),
            home=float(raw.get("home", 0.0)),
            max_speed=float(raw.get("max_speed", 180.0)),
            max_accel=float(raw.get("max_accel", max(360.0, float(raw.get("max_speed", 180.0)) * 4.0))),
            max_jerk=float(raw.get("max_jerk", max(3000.0, float(raw.get("max_speed", 180.0)) * 30.0))),
        )
        controller_ids[name] = int(raw["controller_id"])

    if len(set(controller_ids.values())) != len(controller_ids):
        raise ValueError("duplicate controller_id in body profile")

    expressions = _parse_expressions(data)
    # Validate expression references at load time.  A malformed body profile
    # must fail before a robot is powered.
    for expr_name, frames in expressions.items():
        for frame in frames:
            for joint, value in frame.positions.items():
                if joint not in joints:
                    raise ValueError(f"expression {expr_name!r} references unknown joint {joint!r}")
                spec = joints[joint]
                if not spec.minimum <= value <= spec.maximum:
                    raise ValueError(
                        f"expression {expr_name!r} drives {joint!r} to {value}, "
                        f"outside [{spec.minimum}, {spec.maximum}]"
                    )

    simulation = {str(k): float(v) for k, v in data.get("simulation", {}).items()}
    known_top = {"body", "creature", "joints", "expressions", "simulation"}
    metadata = {k: v for k, v in data.items() if k not in known_top}

    return BodyProfile(
        name=str(body["name"]),
        protocol=str(body.get("protocol", "featherbus-v0")),
        joints=joints,
        controller_ids=controller_ids,
        species=str(creature.get("species", "generic")),
        morphology=str(creature.get("morphology", "generic")),
        role=str(creature.get("role", "general")),
        capabilities=frozenset(str(x) for x in creature.get("capabilities", [])),
        expressions=expressions,
        simulation=simulation,
        metadata=metadata,
    )
