from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.kinematics import compute_creature_geometry
from parrotcore.physics import DynamicsSimulator

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 20
profile = CreatureRegistry.from_directory(ROOT / "profiles").get("parrot")
sim = DynamicsSimulator(profile, sample_hz=FPS)
compiler = ExpressionCompiler(profile)

records = []
labels = []
pose = dict(profile.home_pose)


def add_expression(intent: str, label: str):
    global pose
    for frame in compiler.compile(intent).frames:
        run = sim.run(pose, frame.positions, frame.duration_s)
        # Avoid duplicate first samples at segment boundaries.
        for telem in run.telemetry[1:]:
            records.append(telem)
            labels.append(label)
        pose = dict(run.telemetry[-1].positions)


def hold(label: str, seconds: float):
    global pose
    run = sim.run(pose, pose, seconds)
    for telem in run.telemetry[1:]:
        records.append(telem); labels.append(label)
    pose = dict(run.telemetry[-1].positions)


hold("Ready / nominal", 0.5)
add_expression("greeting", "Nominal greeting")
add_expression("curious", "Nominal curiosity")
add_expression("dance", "Nominal dance")
hold("Fault lab armed", 0.35)

sim.injection.stalled_joints.add("neck_yaw")
add_expression("attend_right", "FAULT: neck yaw stall")
sim.injection.stalled_joints.clear()
hold("Stall cleared", 0.25)

sim.injection.forced_tof_distance_m = 0.04
add_expression("affirm", "FAULT: object too close")
sim.injection.forced_tof_distance_m = None

sim.injection.watchdog_lost = True
hold("FAULT: brain watchdog lost", 0.55)
sim.injection.watchdog_lost = False
add_expression("home", "Recovered / home")
hold("Simulation complete", 0.5)

# CSV telemetry output.
with (OUT / "parrotcore_v05_telemetry_demo.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["frame", "t_scene_s", "label", "rail_current_a", "system_power_w", "max_servo_temp_c", "tof_distance_m", "stability_margin_m", "faults"])
    for i, (t, label) in enumerate(zip(records, labels)):
        writer.writerow([i, i/FPS, label, t.rail_current_a, t.system_power_w, t.max_servo_temp_c, t.tof_distance_m, t.stability_margin_m, ";".join(x.value for x in t.faults)])

fault_counts = Counter(f.value for t in records for f in t.faults)
summary = {
    "classification": "conceptual dynamics/telemetry simulation; not measured hardware performance",
    "platform_version": "0.5.0",
    "species": profile.species,
    "frames": len(records),
    "fps": FPS,
    "duration_s": len(records)/FPS,
    "max_rail_current_a": max(t.rail_current_a for t in records),
    "max_system_power_w": max(t.system_power_w for t in records),
    "max_servo_temp_c": max(t.max_servo_temp_c for t in records),
    "minimum_stability_margin_m": min(t.stability_margin_m for t in records),
    "fault_frame_counts": dict(fault_counts),
    "faults_intentionally_injected": ["servo_stall:neck_yaw", "proximity", "watchdog_loss"],
}
(OUT / "parrotcore_v05_dynamics_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

fig = plt.figure(figsize=(9, 8), dpi=105)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim(-.25,.25); ax.set_ylim(-.20,.21); ax.set_zlim(-.02,.40); ax.set_box_aspect((1.1,1.0,1.0)); ax.view_init(elev=18, azim=-55)
ax.set_xlabel("lateral (m)"); ax.set_ylabel("forward (m)"); ax.set_zlabel("height (m)")
ax.set_title("ParrotCore v0.5 — Dynamics, Telemetry & Fault Injection")
cats=["perch","leg","body","neck","head","beak","face","lid","wing","tail"]
lines={cat: ax.plot([],[],[],linewidth=3 if cat not in {"face","lid"} else 1.5)[0] for cat in cats}
status=ax.text2D(.03,.95,"",transform=ax.transAxes,fontsize=11)
telemetry=ax.text2D(.03,.86,"",transform=ax.transAxes,fontsize=8)


def update(i):
    t=records[i]; g=compute_creature_geometry(profile,t.positions); buckets={c:([],[],[]) for c in cats}
    for a,b,cat in g.segments:
        xs,ys,zs=buckets[cat]; pa,pb=g.points[a],g.points[b]
        xs += [pa[0],pb[0],float('nan')]; ys += [pa[1],pb[1],float('nan')]; zs += [pa[2],pb[2],float('nan')]
    for cat,line in lines.items():
        xs,ys,zs=buckets[cat]; line.set_data(xs,ys); line.set_3d_properties(zs)
    faults=", ".join(f.value for f in t.faults) or "none"
    status.set_text(f"{labels[i]}   t={i/FPS:.1f}s")
    telemetry.set_text(
        f"rail current {t.rail_current_a:.2f} A | system {t.system_power_w:.1f} W* | max servo temp {t.max_servo_temp_c:.1f} C*\n"
        f"ToF {t.tof_distance_m:.2f} m | stability margin {t.stability_margin_m*1000:.1f} mm* | faults: {faults}\n"
        "*simulated assumptions — hardware measurements required before design validation"
    )
    return list(lines.values())+[status,telemetry]

ani=FuncAnimation(fig,update,frames=len(records),interval=1000/FPS,blit=False)
ani.save(OUT/"parrotcore_v05_dynamics_fault_demo.mp4",writer=FFMpegWriter(fps=FPS,bitrate=2500))
idx=list(range(0,len(records),2))
ani2=FuncAnimation(fig,lambda j:update(idx[j]),frames=len(idx),interval=1000/10,blit=False)
ani2.save(OUT/"parrotcore_v05_dynamics_fault_demo.gif",writer=PillowWriter(fps=10))
plt.close(fig)
print(json.dumps(summary, indent=2))
