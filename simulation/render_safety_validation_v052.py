from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.fault_analysis import fault_active_frame_counts, fault_episode_counts
from parrotcore.hardware import load_hardware_baseline
from parrotcore.kinematics import compute_creature_geometry
from parrotcore.physics import DynamicsSimulator
from parrotcore.telemetry import FaultKind

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 20
profile = CreatureRegistry.from_directory(ROOT / "profiles").get("parrot")
hardware = load_hardware_baseline(
    ROOT / "hardware" / "v1_component_baseline.toml",
    ROOT / "hardware" / "v1_actuator_map.toml",
)
sim = DynamicsSimulator(profile, sample_hz=FPS, hardware=hardware)
compiler = ExpressionCompiler(profile)


def sequence_runner():
    pose = dict(profile.home_pose)
    nominal_records = []
    nominal_labels = []
    fault_records = []
    fault_labels = []

    def add_expression(intent: str, label: str, records: list, labels: list):
        nonlocal pose
        for frame in compiler.compile(intent).frames:
            run = sim.run(pose, frame.positions, frame.duration_s)
            for telem in run.telemetry[1:]:
                records.append(telem)
                labels.append(label)
            pose = dict(run.telemetry[-1].positions)

    def hold(label: str, seconds: float, records: list, labels: list):
        nonlocal pose
        run = sim.run(pose, pose, seconds)
        for telem in run.telemetry[1:]:
            records.append(telem)
            labels.append(label)
        pose = dict(run.telemetry[-1].positions)

    # Nominal validation is isolated from fault injection.
    hold("NOMINAL / ready", 0.4, nominal_records, nominal_labels)
    add_expression("greeting", "NOMINAL / greeting", nominal_records, nominal_labels)
    add_expression("curious", "NOMINAL / curiosity", nominal_records, nominal_labels)
    add_expression("dance", "NOMINAL / dance", nominal_records, nominal_labels)
    add_expression("home", "NOMINAL / home", nominal_records, nominal_labels)
    hold("NOMINAL / validation complete", 0.35, nominal_records, nominal_labels)

    # Deliberate fault-injection validation. Each block is one fault episode.
    sim.clear_faults_and_reset_safety()
    hold("SAFETY TEST / armed", 0.25, fault_records, fault_labels)

    sim.injection.stalled_joints.add("neck_yaw")
    add_expression("attend_right", "INJECTED TEST 1/3 / neck-yaw stall", fault_records, fault_labels)
    sim.injection.clear()
    hold("TEST 1 cleared", 0.20, fault_records, fault_labels)

    sim.injection.forced_tof_distance_m = 0.04
    add_expression("affirm", "INJECTED TEST 2/3 / object at 4 cm", fault_records, fault_labels)
    sim.injection.clear()
    hold("TEST 2 cleared", 0.20, fault_records, fault_labels)

    sim.injection.watchdog_lost = True
    hold("INJECTED TEST 3/3 / watchdog lost", 0.35, fault_records, fault_labels)
    sim.injection.clear()
    hold("WATCHDOG condition cleared / safety remains latched", 0.20, fault_records, fault_labels)
    sim.reset_safety()
    hold("Explicit safety reset / actuator rail restored", 0.20, fault_records, fault_labels)
    add_expression("home", "RECOVERED / home", fault_records, fault_labels)

    return nominal_records, nominal_labels, fault_records, fault_labels


nominal, nominal_labels, injected, injected_labels = sequence_runner()
all_records = nominal + injected
all_labels = nominal_labels + injected_labels
all_scenarios = ["nominal"] * len(nominal) + ["fault_injection"] * len(injected)

with (OUT / "parrotcore_v052_safety_validation_telemetry.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "frame", "t_scene_s", "scenario", "label", "rail_voltage_v", "rail_current_a",
        "system_power_w", "max_servo_temp_c", "tof_distance_m", "stability_margin_m",
        "actuator_power_enabled", "motion_inhibited", "safety_latched", "safety_reason", "active_faults",
    ])
    for i, (t, scenario, label) in enumerate(zip(all_records, all_scenarios, all_labels)):
        writer.writerow([
            i, i / FPS, scenario, label, t.rail_voltage_v, t.rail_current_a, t.system_power_w,
            t.max_servo_temp_c, t.tof_distance_m, t.stability_margin_m,
            t.actuator_power_enabled, t.motion_inhibited, t.safety_latched, t.safety_reason or "",
            ";".join(x.value for x in t.faults),
        ])

nominal_episodes = fault_episode_counts(nominal)
nominal_active_frames = fault_active_frame_counts(nominal)
injected_episodes = fault_episode_counts(injected)
injected_active_frames = fault_active_frame_counts(injected)

watchdog_frames = [t for t in injected if FaultKind.WATCHDOG_LOSS in t.faults]
proximity_frames = [t for t in injected if FaultKind.PROXIMITY in t.faults]
stall_frames = [t for t in injected if FaultKind.SERVO_STALL in t.faults]
latched_after_watchdog = [
    t for t, label in zip(injected, injected_labels)
    if "safety remains latched" in label
]

summary = {
    "classification": "manufacturer-grounded electrical endpoints plus unvalidated dynamic/thermal/mechanical model; not measured hardware performance",
    "platform_version": "0.5.2",
    "hardware_baseline": hardware.baseline_id,
    "species": profile.species,
    "reporting_correction": "fault episodes are rising-edge events; active-frame counts measure duration and are not independent faults",
    "nominal_validation": {
        "frames": len(nominal),
        "duration_s": len(nominal) / FPS,
        "fault_episode_counts": nominal_episodes,
        "fault_active_frame_counts": nominal_active_frames,
        "pass_zero_faults": not nominal_episodes and not nominal_active_frames,
        "max_rail_current_a": max(t.rail_current_a for t in nominal),
        "max_system_power_w": max(t.system_power_w for t in nominal),
        "minimum_stability_margin_m": min(t.stability_margin_m for t in nominal),
    },
    "deliberate_fault_injection": {
        "expected_fault_episodes": {
            "servo_stall": 1,
            "proximity": 1,
            "watchdog_loss": 1,
        },
        "fault_episode_counts": injected_episodes,
        "fault_active_frame_counts": injected_active_frames,
        "distinct_expected_episodes": 3,
        "pass_episode_accounting": injected_episodes == {
            "servo_stall": 1,
            "proximity": 1,
            "watchdog_loss": 1,
        },
    },
    "safety_response_checks": {
        "stall_episode_detected": bool(stall_frames),
        "proximity_inhibits_motion": bool(proximity_frames) and all(t.motion_inhibited for t in proximity_frames),
        "proximity_does_not_latch_power_off": bool(proximity_frames) and all(not t.safety_latched for t in proximity_frames),
        "watchdog_inhibits_motion": bool(watchdog_frames) and all(t.motion_inhibited for t in watchdog_frames),
        "watchdog_disables_actuator_power": bool(watchdog_frames) and all(not t.actuator_power_enabled for t in watchdog_frames),
        "watchdog_latch_persists_after_condition_clears": bool(latched_after_watchdog) and all(t.safety_latched and not t.actuator_power_enabled for t in latched_after_watchdog),
    },
}
summary["overall_pass"] = (
    summary["nominal_validation"]["pass_zero_faults"]
    and summary["deliberate_fault_injection"]["pass_episode_accounting"]
    and all(summary["safety_response_checks"].values())
)

(OUT / "parrotcore_v052_safety_validation_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

fig = plt.figure(figsize=(9, 8), dpi=105)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim(-.25, .25); ax.set_ylim(-.20, .21); ax.set_zlim(-.02, .40)
ax.set_box_aspect((1.1, 1.0, 1.0)); ax.view_init(elev=18, azim=-55)
ax.set_xlabel("lateral (m)"); ax.set_ylabel("forward (m)"); ax.set_zlabel("height (m)")
ax.set_title("ParrotCore v0.5.2 - Nominal + Deliberate Safety Validation")
cats = ["perch", "leg", "body", "neck", "head", "beak", "face", "lid", "wing", "tail"]
lines = {cat: ax.plot([], [], [], linewidth=3 if cat not in {"face", "lid"} else 1.5)[0] for cat in cats}
status = ax.text2D(.03, .95, "", transform=ax.transAxes, fontsize=11)
telemetry = ax.text2D(.03, .84, "", transform=ax.transAxes, fontsize=8)


def update(i):
    t = all_records[i]
    g = compute_creature_geometry(profile, t.positions)
    buckets = {c: ([], [], []) for c in cats}
    for a, b, cat in g.segments:
        xs, ys, zs = buckets[cat]
        pa, pb = g.points[a], g.points[b]
        xs += [pa[0], pb[0], float("nan")]
        ys += [pa[1], pb[1], float("nan")]
        zs += [pa[2], pb[2], float("nan")]
    for cat, line in lines.items():
        xs, ys, zs = buckets[cat]
        line.set_data(xs, ys); line.set_3d_properties(zs)
    faults = ", ".join(f.value for f in t.faults) or "none"
    scenario = all_scenarios[i].upper()
    status.set_text(f"{scenario} | {all_labels[i]} | t={i/FPS:.1f}s")
    safety = "LATCHED: " + str(t.safety_reason) if t.safety_latched else ("MOTION INHIBITED" if t.motion_inhibited else "READY")
    telemetry.set_text(
        f"active condition: {faults} | safety: {safety} | actuator power: {'ON' if t.actuator_power_enabled else 'OFF'}\n"
        f"servo rail {t.rail_voltage_v:.1f} V / {t.rail_current_a:.2f} A | system {t.system_power_w:.1f} W* | max servo temp {t.max_servo_temp_c:.1f} C*\n"
        f"ToF {t.tof_distance_m:.2f} m | stability margin {t.stability_margin_m*1000:.1f} mm*\n"
        "*manufacturer endpoints + explicit unvalidated dynamic/thermal/mechanical model"
    )
    return list(lines.values()) + [status, telemetry]

ani = FuncAnimation(fig, update, frames=len(all_records), interval=1000/FPS, blit=False)
ani.save(OUT / "parrotcore_v052_safety_validation_demo.mp4", writer=FFMpegWriter(fps=FPS, bitrate=2500))
idx = list(range(0, len(all_records), 2))
ani2 = FuncAnimation(fig, lambda j: update(idx[j]), frames=len(idx), interval=1000/10, blit=False)
ani2.save(OUT / "parrotcore_v052_safety_validation_demo.gif", writer=PillowWriter(fps=10))
plt.close(fig)
print(json.dumps(summary, indent=2))
