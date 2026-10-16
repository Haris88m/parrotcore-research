from __future__ import annotations

from dataclasses import dataclass
from math import fabs
from typing import Mapping

from .collision import estimate_collision
from .dynamics import Trajectory, TrajectoryPlanner
from .faults import FaultInjection
from .hardware import HardwareBaseline
from .profile import BodyProfile
from .stability import estimate_stability
from .telemetry import FaultKind, IMUState, TelemetryFrame


@dataclass(frozen=True)
class PhysicsAssumptions:
    ambient_temp_c: float = 24.0
    initial_servo_temp_c: float = 28.0
    thermal_gain_c_per_a_s: float = 0.20
    cooling_per_s: float = 0.020
    overtemp_c: float = 70.0
    rail_current_limit_a: float = 6.0
    proximity_stop_m: float = 0.08
    default_tof_distance_m: float = 0.60


@dataclass(frozen=True)
class SimulatedRun:
    trajectory: Trajectory
    telemetry: tuple[TelemetryFrame, ...]


class DynamicsSimulator:
    """Joint-space digital-twin simulator with explicit safety-state semantics.

    v0.5.2 distinguishes a fault *condition* from its safety response:
    - proximity inhibits motion while keeping the actuator rail available;
    - watchdog loss and overtemperature latch actuator power off immediately;
    - overcurrent records the detected current spike and latches the rail off;
    - a latched rail remains off until ``reset_safety`` is called.

    This is still a simulator. Timing of physical eFuse/load-switch action must
    later be measured on the bench rig.
    """

    def __init__(
        self,
        profile: BodyProfile,
        sample_hz: float = 50.0,
        assumptions: PhysicsAssumptions = PhysicsAssumptions(),
        hardware: HardwareBaseline | None = None,
    ):
        self.profile = profile
        self.planner = TrajectoryPlanner(profile.joints, sample_hz)
        self.assumptions = assumptions
        self.injection = FaultInjection()
        self.hardware = hardware
        self.temperatures = {name: assumptions.initial_servo_temp_c for name in profile.joints}
        self.safety_latched = False
        self.safety_reason: str | None = None

    def reset_safety(self) -> None:
        """Reset the simulation safety latch after the initiating fault is cleared."""
        self.safety_latched = False
        self.safety_reason = None

    def clear_faults_and_reset_safety(self) -> None:
        self.injection.clear()
        self.reset_safety()

    def _latch(self, reason: FaultKind) -> None:
        self.safety_latched = True
        self.safety_reason = reason.value

    def run(self, start: Mapping[str, float], target: Mapping[str, float], requested_duration_s: float | None = None) -> SimulatedRun:
        trajectory = self.planner.plan(start, target, requested_duration_s)
        dt = 1.0 / trajectory.sample_hz
        sim = self.profile.simulation
        if self.hardware is not None:
            nominal_voltage = self.hardware.servo_regulator.output_voltage_v
            compute_typical_w = self.hardware.electronics_baseline_power_w
            rail_current_limit_a = self.hardware.modeling.servo_software_current_limit_a
        else:
            nominal_voltage = sim.get("servo_voltage_v", 6.0)
            idle_a = sim.get("servo_idle_current_a", 0.12)
            moving_a = sim.get("servo_moving_current_a", 0.35)
            peak_a = sim.get("servo_peak_current_a", 0.80)
            compute_typical_w = sim.get("compute_typical_w", 10.0)
            rail_current_limit_a = self.assumptions.rail_current_limit_a

        out: list[TelemetryFrame] = []
        previous_positions = dict(start)

        for sample in trajectory.samples:
            faults: set[FaultKind] = set()
            commanded_positions = dict(sample.positions)
            positions = dict(commanded_positions)
            velocities = dict(sample.velocities)
            servo_current: dict[str, float] = {}
            motion_inhibited = False
            actuator_power_enabled = not self.safety_latched

            tof = (
                self.injection.forced_tof_distance_m
                if self.injection.forced_tof_distance_m is not None
                else self.assumptions.default_tof_distance_m
            )
            touch = bool(self.injection.forced_touch) if self.injection.forced_touch is not None else False

            # Conditions known before issuing motion are handled pre-emptively.
            if self.injection.watchdog_lost:
                faults.add(FaultKind.WATCHDOG_LOSS)
                self._latch(FaultKind.WATCHDOG_LOSS)
                actuator_power_enabled = False
                motion_inhibited = True
            if self.injection.forced_temperature_c is not None and self.injection.forced_temperature_c >= self.assumptions.overtemp_c:
                faults.add(FaultKind.OVERTEMP)
                self._latch(FaultKind.OVERTEMP)
                actuator_power_enabled = False
                motion_inhibited = True
            if tof < self.assumptions.proximity_stop_m:
                faults.add(FaultKind.PROXIMITY)
                motion_inhibited = True

            if self.safety_latched:
                actuator_power_enabled = False
                motion_inhibited = True

            if motion_inhibited:
                positions = dict(previous_positions)
                velocities = {name: 0.0 for name in self.profile.joints}

            for name, spec in self.profile.joints.items():
                if not actuator_power_enabled:
                    current = 0.0
                    peak_a = self.hardware.servo_for_joint(name).stall_current_a if self.hardware is not None else peak_a
                else:
                    speed_frac = min(1.0, fabs(velocities[name]) / max(spec.max_speed, 1e-9))
                    if self.hardware is not None:
                        servo = self.hardware.servo_for_joint(name)
                        # No mechanism-specific current/load curve exists yet.
                        # Interpolate manufacturer no-load->stall endpoints with
                        # an explicit replaceable load fraction.
                        load_fraction = min(1.0, self.hardware.modeling.nominal_dynamic_load_fraction * speed_frac)
                        current = servo.no_load_current_a + (servo.stall_current_a - servo.no_load_current_a) * load_fraction
                        peak_a = servo.stall_current_a
                    else:
                        current = idle_a + (moving_a - idle_a) * speed_frac
                    current *= 1.0 + max(0.0, self.injection.extra_load_factor)

                    if name in self.injection.stalled_joints:
                        faults.add(FaultKind.SERVO_STALL)
                        positions[name] = float(previous_positions.get(name, spec.home))
                        velocities[name] = 0.0
                        current = peak_a

                servo_current[name] = min(peak_a, current)
                temp = self.temperatures[name]
                temp += self.assumptions.thermal_gain_c_per_a_s * servo_current[name] * dt
                temp -= max(0.0, temp - self.assumptions.ambient_temp_c) * self.assumptions.cooling_per_s * dt
                if self.injection.forced_temperature_c is not None:
                    temp = self.injection.forced_temperature_c
                self.temperatures[name] = temp

            rail_current = sum(servo_current.values())
            if actuator_power_enabled and rail_current >= rail_current_limit_a:
                # Preserve the detected transient in telemetry, then latch the
                # simulated safety switch off for subsequent samples.
                faults.add(FaultKind.OVERCURRENT)
                self._latch(FaultKind.OVERCURRENT)
                motion_inhibited = True
                positions = dict(previous_positions)
                velocities = {name: 0.0 for name in self.profile.joints}
                actuator_power_enabled = False

            max_temp = max(self.temperatures.values())
            if max_temp >= self.assumptions.overtemp_c:
                faults.add(FaultKind.OVERTEMP)
                self._latch(FaultKind.OVERTEMP)
                actuator_power_enabled = False
                motion_inhibited = True
                positions = dict(previous_positions)
                velocities = {name: 0.0 for name in self.profile.joints}

            stability = estimate_stability(self.profile, positions)
            if not stability.stable_proxy:
                faults.add(FaultKind.STABILITY_RISK)
            collision = estimate_collision(self.profile, positions)
            if collision.risk:
                faults.add(FaultKind.COLLISION_RISK)

            lean = positions.get("body_lean", 0.0)
            yaw = positions.get("neck_yaw", positions.get("head_yaw", 0.0)) * 0.05
            imu = IMUState(pitch_deg=float(lean), yaw_deg=float(yaw))

            # When a pre-existing safety latch has removed servo power, the
            # rail reads 0V/0A. For a newly detected overcurrent frame the
            # measured transient is retained at nominal voltage for diagnosis.
            detected_overcurrent_this_frame = FaultKind.OVERCURRENT in faults and rail_current > 0.0
            rail_voltage = nominal_voltage if (actuator_power_enabled or detected_overcurrent_this_frame) else 0.0
            system_power = rail_voltage * rail_current + compute_typical_w

            out.append(
                TelemetryFrame(
                    t_s=sample.t_s,
                    positions=positions,
                    velocities=velocities,
                    servo_current_a=servo_current,
                    rail_voltage_v=rail_voltage,
                    rail_current_a=rail_current,
                    system_power_w=system_power,
                    max_servo_temp_c=max_temp,
                    imu=imu,
                    tof_distance_m=tof,
                    touch=touch,
                    stability_margin_m=stability.margin_m,
                    faults=tuple(sorted(faults, key=lambda f: f.value)),
                    actuator_power_enabled=actuator_power_enabled,
                    motion_inhibited=motion_inhibited,
                    safety_latched=self.safety_latched,
                    safety_reason=self.safety_reason,
                )
            )
            previous_positions = positions

        return SimulatedRun(trajectory, tuple(out))
