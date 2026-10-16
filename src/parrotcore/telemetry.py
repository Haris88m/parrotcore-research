from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from time import monotonic


class FaultKind(str, Enum):
    WATCHDOG_LOSS = "watchdog_loss"
    SERVO_STALL = "servo_stall"
    OVERCURRENT = "overcurrent"
    OVERTEMP = "overtemp"
    PROXIMITY = "proximity"
    COLLISION_RISK = "collision_risk"
    STABILITY_RISK = "stability_risk"


@dataclass(frozen=True)
class IMUState:
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    yaw_deg: float = 0.0
    accel_x_m_s2: float = 0.0
    accel_y_m_s2: float = 0.0
    accel_z_m_s2: float = 9.81


@dataclass(frozen=True)
class TelemetryFrame:
    t_s: float
    positions: dict[str, float]
    velocities: dict[str, float]
    servo_current_a: dict[str, float]
    rail_voltage_v: float
    rail_current_a: float
    system_power_w: float
    max_servo_temp_c: float
    imu: IMUState
    tof_distance_m: float
    touch: bool
    stability_margin_m: float
    faults: tuple[FaultKind, ...] = field(default_factory=tuple)
    actuator_power_enabled: bool = True
    motion_inhibited: bool = False
    safety_latched: bool = False
    safety_reason: str | None = None
    generated_at_monotonic: float = field(default_factory=monotonic)

    def as_dict(self) -> dict[str, object]:
        raw = asdict(self)
        raw["faults"] = [f.value for f in self.faults]
        return raw
