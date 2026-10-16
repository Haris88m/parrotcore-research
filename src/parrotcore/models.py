from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventKind(str, Enum):
    PHRASE = "phrase"
    PERSON_SEEN = "person_seen"
    OBJECT_SEEN = "object_seen"
    TOUCH = "touch"
    TIMER = "timer"
    SYSTEM = "system"


@dataclass(frozen=True)
class Event:
    kind: EventKind
    value: str
    confidence: float = 1.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JointSpec:
    name: str
    minimum: float
    maximum: float
    home: float = 0.0
    max_speed: float = 180.0
    max_accel: float = 720.0
    max_jerk: float = 6000.0


@dataclass(frozen=True)
class MotionFrame:
    positions: dict[str, float]
    duration_s: float = 0.25


@dataclass(frozen=True)
class Action:
    kind: str
    payload: dict[str, Any]
