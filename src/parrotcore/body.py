from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol

from .models import MotionFrame
from .safety import SafetyGate


class BodyDriver(Protocol):
    def move(self, frame: MotionFrame) -> None: ...
    def home(self) -> None: ...
    def status(self) -> dict[str, object]: ...


@dataclass
class SimulatedBody:
    safety: SafetyGate
    realtime: bool = False
    positions: dict[str, float] = field(default_factory=dict)
    trace: list[MotionFrame] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.positions:
            self.positions = {name: spec.home for name, spec in self.safety.joints.items()}

    def move(self, frame: MotionFrame) -> None:
        safe_positions = self.safety.check_motion(frame.positions)
        self.positions.update(safe_positions)
        accepted = MotionFrame(dict(safe_positions), max(0.0, float(frame.duration_s)))
        self.trace.append(accepted)
        pretty = ", ".join(f"{k}={v:g}" for k, v in safe_positions.items())
        print(f"[BODY] {pretty} ({accepted.duration_s:.2f}s)")
        if self.realtime and accepted.duration_s:
            time.sleep(accepted.duration_s)

    def home(self) -> None:
        frame = MotionFrame({name: spec.home for name, spec in self.safety.joints.items()}, 0.35)
        self.move(frame)

    def status(self) -> dict[str, object]:
        return {
            "positions": dict(self.positions),
            "estop": self.safety.estop_latched,
            "frames_executed": len(self.trace),
        }
