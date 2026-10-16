from __future__ import annotations

from pathlib import Path

import pytest

from parrotcore.fault_analysis import fault_active_frame_counts, fault_episode_counts
from parrotcore.hardware import load_hardware_baseline
from parrotcore.physics import DynamicsSimulator
from parrotcore.profile import load_profile
from parrotcore.telemetry import FaultKind

ROOT = Path(__file__).resolve().parents[1]


def baseline_and_profile():
    hardware = load_hardware_baseline(
        ROOT / "hardware" / "v1_component_baseline.toml",
        ROOT / "hardware" / "v1_actuator_map.toml",
    )
    profile = load_profile(ROOT / "profiles" / "reference_parrot.toml")
    return hardware, profile


def test_fault_episode_count_is_not_frame_count():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.watchdog_lost = True
    run = sim.run(profile.home_pose, profile.home_pose, 0.5)
    episodes = fault_episode_counts(run.telemetry)
    active = fault_active_frame_counts(run.telemetry)
    assert episodes == {"watchdog_loss": 1}
    assert active["watchdog_loss"] > 1


def test_watchdog_immediately_inhibits_motion_and_actuator_power():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.watchdog_lost = True
    run = sim.run(profile.home_pose, {"neck_yaw": 30.0}, 0.3)
    assert all(FaultKind.WATCHDOG_LOSS in t.faults for t in run.telemetry)
    assert all(t.motion_inhibited for t in run.telemetry)
    assert all(not t.actuator_power_enabled for t in run.telemetry)
    assert all(t.rail_voltage_v == 0.0 for t in run.telemetry)
    assert all(t.rail_current_a == 0.0 for t in run.telemetry)
    assert all(t.positions["neck_yaw"] == profile.home_pose["neck_yaw"] for t in run.telemetry)


def test_watchdog_safety_latch_persists_after_injection_is_cleared():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.watchdog_lost = True
    sim.run(profile.home_pose, profile.home_pose, 0.2)
    sim.injection.clear()
    run = sim.run(profile.home_pose, {"neck_yaw": 20.0}, 0.2)
    assert all(not t.faults for t in run.telemetry)
    assert all(t.safety_latched for t in run.telemetry)
    assert all(not t.actuator_power_enabled for t in run.telemetry)
    assert all(t.motion_inhibited for t in run.telemetry)


def test_explicit_reset_restores_nominal_motion_after_watchdog():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.watchdog_lost = True
    sim.run(profile.home_pose, profile.home_pose, 0.2)
    sim.injection.clear()
    sim.reset_safety()
    run = sim.run(profile.home_pose, {"neck_yaw": 20.0}, 0.3)
    assert not any(t.faults for t in run.telemetry)
    assert run.telemetry[-1].positions["neck_yaw"] == 20.0
    assert run.telemetry[-1].actuator_power_enabled
    assert not run.telemetry[-1].safety_latched


def test_proximity_inhibits_motion_without_latching_power():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.forced_tof_distance_m = 0.04
    run = sim.run(profile.home_pose, {"neck_yaw": 20.0}, 0.3)
    assert all(FaultKind.PROXIMITY in t.faults for t in run.telemetry)
    assert all(t.motion_inhibited for t in run.telemetry)
    assert all(t.actuator_power_enabled for t in run.telemetry)
    assert all(not t.safety_latched for t in run.telemetry)
    assert all(t.positions["neck_yaw"] == profile.home_pose["neck_yaw"] for t in run.telemetry)


def test_overtemperature_latches_actuator_power_off():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.forced_temperature_c = 80.0
    run = sim.run(profile.home_pose, {"neck_pitch": 10.0}, 0.2)
    assert all(FaultKind.OVERTEMP in t.faults for t in run.telemetry)
    assert all(t.safety_latched for t in run.telemetry)
    assert all(not t.actuator_power_enabled for t in run.telemetry)


def test_all_stall_overcurrent_latches_rail_and_then_removes_power():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
    sim.injection.stalled_joints.update(profile.joints)
    run = sim.run(profile.home_pose, {"neck_yaw": 10.0}, 0.3)
    assert FaultKind.SERVO_STALL in run.telemetry[0].faults
    assert FaultKind.OVERCURRENT in run.telemetry[0].faults
    assert run.telemetry[0].safety_latched
    assert max(t.rail_current_a for t in run.telemetry) == pytest.approx(13.6)
    assert all(t.rail_current_a == 0.0 for t in run.telemetry[1:])
    assert all(not t.actuator_power_enabled for t in run.telemetry[1:])


def test_nominal_hardware_run_has_zero_fault_episodes_and_no_safety_latch():
    hardware, profile = baseline_and_profile()
    sim = DynamicsSimulator(profile, sample_hz=50, hardware=hardware)
    run = sim.run(profile.home_pose, {"neck_yaw": 30.0, "wing_left": 20.0, "wing_right": 20.0}, 0.4)
    assert fault_episode_counts(run.telemetry) == {}
    assert not any(t.safety_latched for t in run.telemetry)
    assert all(t.actuator_power_enabled for t in run.telemetry)
