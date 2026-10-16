from __future__ import annotations

from dataclasses import dataclass, field

from .telemetry import FaultKind


@dataclass
class FaultInjection:
    """Explicit simulation-only faults. Defaults are all safe/off."""
    watchdog_lost: bool = False
    stalled_joints: set[str] = field(default_factory=set)
    forced_tof_distance_m: float | None = None
    forced_touch: bool | None = None
    extra_load_factor: float = 0.0
    forced_temperature_c: float | None = None

    def clear(self) -> None:
        self.watchdog_lost = False
        self.stalled_joints.clear()
        self.forced_tof_distance_m = None
        self.forced_touch = None
        self.extra_load_factor = 0.0
        self.forced_temperature_c = None

    def active_labels(self) -> tuple[str, ...]:
        labels=[]
        if self.watchdog_lost: labels.append(FaultKind.WATCHDOG_LOSS.value)
        if self.stalled_joints: labels.append(FaultKind.SERVO_STALL.value+":"+",".join(sorted(self.stalled_joints)))
        if self.forced_tof_distance_m is not None: labels.append("tof_override")
        if self.extra_load_factor: labels.append("extra_load")
        if self.forced_temperature_c is not None: labels.append("temperature_override")
        return tuple(labels)
