from __future__ import annotations

from dataclasses import dataclass

from .models import JointSpec


class EmergencyStop(RuntimeError):
    pass


@dataclass
class SafetyGate:
    joints: dict[str, JointSpec]
    estop_latched: bool = False

    def latch_estop(self) -> None:
        self.estop_latched = True

    def reset_estop(self) -> None:
        self.estop_latched = False

    def check_motion(self, positions: dict[str, float]) -> dict[str, float]:
        if self.estop_latched:
            raise EmergencyStop("motion rejected: emergency stop is latched")

        safe: dict[str, float] = {}
        for name, value in positions.items():
            if name not in self.joints:
                raise ValueError(f"unknown joint: {name}")
            spec = self.joints[name]
            if not spec.minimum <= float(value) <= spec.maximum:
                raise ValueError(
                    f"joint {name}={value} outside logical range "
                    f"[{spec.minimum}, {spec.maximum}]"
                )
            safe[name] = float(value)
        return safe
