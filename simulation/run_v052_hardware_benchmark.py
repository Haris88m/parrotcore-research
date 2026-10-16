from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parrotcore.embodiment import ExpressionCompiler
from parrotcore.fault_analysis import fault_active_frame_counts, fault_episode_counts
from parrotcore.hardware import load_hardware_baseline
from parrotcore.physics import DynamicsSimulator
from parrotcore.profile import load_profile
from parrotcore.telemetry import FaultKind

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
profile = load_profile(ROOT / "profiles" / "reference_parrot.toml")
hardware = load_hardware_baseline(
    ROOT / "hardware" / "v1_component_baseline.toml",
    ROOT / "hardware" / "v1_actuator_map.toml",
)

sim = DynamicsSimulator(profile, sample_hz=50, hardware=hardware)
pose = dict(profile.home_pose)
frames = []
for intent in ("greeting", "curious", "dance", "affirm", "home"):
    for motion in ExpressionCompiler(profile).compile(intent).frames:
        run = sim.run(pose, motion.positions, motion.duration_s)
        frames.extend(run.telemetry[1:])
        pose = dict(run.telemetry[-1].positions)

max_power = max(t.system_power_w for t in frames)
avg_power = sum(t.system_power_w for t in frames) / len(frames)
max_current = max(t.rail_current_a for t in frames)
avg_current = sum(t.rail_current_a for t in frames) / len(frames)
runtime_ideal_h = hardware.ideal_runtime_h(avg_power)
runtime_derated_h = hardware.ideal_runtime_h(avg_power, derated=True)
all_stall_power_dc_w = hardware.servo_regulator.output_voltage_v * hardware.mapped_servo_all_stall_current_a + hardware.electronics_baseline_power_w

stall_sim = DynamicsSimulator(profile, sample_hz=20, hardware=hardware)
stall_sim.injection.stalled_joints.update(profile.joints)
stall_run = stall_sim.run(profile.home_pose, {"neck_yaw": 10.0}, 0.2)
stall_faults = sorted({f.value for t in stall_run.telemetry for f in t.faults})
stall_max_current = max(t.rail_current_a for t in stall_run.telemetry)
post_trip_frames = [t for t in stall_run.telemetry[1:] if t.safety_latched]

speed_margin = {}
for joint, spec in profile.joints.items():
    servo = hardware.servo_for_joint(joint)
    speed_margin[joint] = {
        "profile_max_speed_deg_s": spec.max_speed,
        "servo_no_load_speed_deg_s_at_6v": servo.no_load_speed_deg_s,
        "profile_fraction_of_no_load_speed": spec.max_speed / servo.no_load_speed_deg_s,
    }

report = {
    "platform_version": "0.5.2",
    "baseline_id": hardware.baseline_id,
    "classification": "hardware-grounded endpoints + explicit unvalidated dynamic/thermal/mechanical model",
    "fault_reporting_semantics": "episode counts represent rising-edge events; active-frame counts represent duration",
    "selected_actuation": {
        "sts3215_quantity": sum(1 for v in hardware.actuator_map.values() if v == "sts3215"),
        "st3036_quantity": sum(1 for v in hardware.actuator_map.values() if v == "st3036"),
        "aggregate_servo_mass_g": hardware.mapped_servo_mass_g,
        "aggregate_no_load_running_current_a": hardware.mapped_servo_no_load_current_a,
        "aggregate_theoretical_all_stall_current_a": hardware.mapped_servo_all_stall_current_a,
        "servo_software_current_limit_a": hardware.modeling.servo_software_current_limit_a,
        "servo_regulator_nominal_current_a": hardware.servo_regulator.continuous_output_current_a,
    },
    "joint_speed_margin": speed_margin,
    "power_baseline": {
        "cm5_module_operation_power_w": hardware.compute.operation_power_w,
        "camera_design_budget_w": hardware.camera_power_budget_w,
        "electronics_baseline_power_w": hardware.electronics_baseline_power_w,
        "theoretical_all_servo_stall_dc_load_w": all_stall_power_dc_w,
        "battery_nominal_energy_wh": hardware.battery.energy_wh,
    },
    "reference_behavior_simulation": {
        "frames": len(frames),
        "duration_s": len(frames) / 50,
        "avg_servo_rail_current_a": avg_current,
        "max_servo_rail_current_a": max_current,
        "avg_dc_load_power_w": avg_power,
        "max_dc_load_power_w": max_power,
        "ideal_runtime_h_from_avg_dc_load": runtime_ideal_h,
        "derated_runtime_h_from_avg_dc_load": runtime_derated_h,
        "fault_episode_counts": fault_episode_counts(frames),
        "fault_active_frame_counts": fault_active_frame_counts(frames),
        "pass_zero_faults": not fault_episode_counts(frames),
        "runtime_warning": "not a battery-life claim; unresolved audio/MCU/sensor duty cycles and modeled dynamic load remain",
    },
    "explicit_all_stall_safety_probe": {
        "theoretical_all_stall_current_a": hardware.mapped_servo_all_stall_current_a,
        "measured_simulated_peak_a": stall_max_current,
        "faults_observed": stall_faults,
        "fault_episode_counts": fault_episode_counts(stall_run.telemetry),
        "safety_latched": any(t.safety_latched for t in stall_run.telemetry),
        "post_trip_actuator_power_off": bool(post_trip_frames) and all(not t.actuator_power_enabled for t in post_trip_frames),
        "valid_operating_point": False,
        "reason": "all-stall current exceeds 12A software threshold; the safety model records the transient and latches the actuator rail off",
    },
}
report["overall_pass"] = (
    report["reference_behavior_simulation"]["pass_zero_faults"]
    and FaultKind.SERVO_STALL.value in stall_faults
    and FaultKind.OVERCURRENT.value in stall_faults
    and report["explicit_all_stall_safety_probe"]["safety_latched"]
    and report["explicit_all_stall_safety_probe"]["post_trip_actuator_power_off"]
)

path = OUT / "v052_hardware_grounded_benchmark.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
