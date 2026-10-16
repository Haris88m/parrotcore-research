from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter

from parrotcore.kinematics import compute_geometry
from parrotcore.reference import reference_joints
from parrotcore.simulation import SimulationAssumptions, effectiveness, interpolate_motion, max_tip_speed, metrics_dict
from parrotcore.skills._motions import MOTIONS
from parrotcore.models import MotionFrame

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 24

joints = reference_joints()
home = {name: spec.home for name, spec in joints.items()}
sequence = []
labels = []

def add_hold(label: str, seconds: float):
    global sequence
    n = max(1, round(seconds * FPS))
    for _ in range(n):
        sequence.append(dict(sequence[-1] if sequence else home))
        labels.append(label)

def add_motion(name: str, label: str):
    global sequence
    start = sequence[-1] if sequence else home
    poses = interpolate_motion(MOTIONS[name], start, fps=FPS)[1:]
    for p in poses:
        sequence.append(p)
        labels.append(label)

add_hold("Home / ready", 0.8)
add_motion("happy_greeting", "Greeting")
add_hold("Attention", 0.35)
# Direct gaze moves are actual v0.2 pose semantics.
for target, label in [(-40, "Look left"), (40, "Look right"), (0, "Center")]:
    frames = (MotionFrame({"neck_yaw": target}, 0.4),)
    poses = interpolate_motion(frames, sequence[-1], fps=FPS)[1:]
    for p in poses:
        sequence.append(p); labels.append(label)
add_motion("blink", "Blink")
add_hold("Ready to interact", 0.35)
add_motion("dance", "Dance")
add_hold("Home", 0.5)
# Finish in home pose smoothly.
poses = interpolate_motion((MotionFrame(home, 0.6),), sequence[-1], fps=FPS)[1:]
for p in poses:
    sequence.append(p); labels.append("Return home")

metrics = effectiveness(joints, SimulationAssumptions())
tip_speeds = max_tip_speed(sequence, fps=FPS)
summary = {
    "classification": "conceptual kinematic simulation; not measured hardware performance",
    "fps": FPS,
    "duration_s": len(sequence) / FPS,
    "frames": len(sequence),
    "effectiveness": metrics_dict(metrics),
    "max_simulated_tip_speed_m_s": tip_speeds,
    "motion_durations_s": {name: sum(f.duration_s for f in frames) for name, frames in MOTIONS.items()},
}
(OUT / "simulation_metrics.json").write_text(json.dumps(summary, indent=2))

fig = plt.figure(figsize=(8, 8), dpi=110)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim(-0.24, 0.24); ax.set_ylim(-0.20, 0.20); ax.set_zlim(-0.02, 0.39)
ax.set_box_aspect((1.2, 1.0, 1.0))
ax.view_init(elev=18, azim=-55)
ax.set_xlabel("lateral (m)"); ax.set_ylabel("forward (m)"); ax.set_zlabel("height (m)")
ax.set_title("ParrotCore v0.3 — 8-DOF Digital Twin")

# Use one line object per semantic category so the frame update is cheap.
cats = ["perch","leg","body","neck","head","beak","face","lid","wing","tail"]
lines = {cat: ax.plot([], [], [], linewidth=3 if cat not in {"face","lid"} else 1.5, label=cat)[0] for cat in cats}
status = ax.text2D(0.03, 0.94, "", transform=ax.transAxes)
info = ax.text2D(0.03, 0.885, "", transform=ax.transAxes, fontsize=8)
body_mass = ax.scatter([], [], [], s=850, marker='o', depthshade=True, label='_body volume')
head_mass = ax.scatter([], [], [], s=420, marker='o', depthshade=True, label='_head volume')
eyes = ax.scatter([], [], [], s=28, marker='o', depthshade=False, label='_eyes')
ax.legend(loc="upper right", fontsize=8)

def update(i):
    g = compute_geometry(sequence[i])
    buckets = {c: ([], [], []) for c in cats}
    for a, b, cat in g.segments:
        xs, ys, zs = buckets[cat]
        pa, pb = g.points[a], g.points[b]
        xs += [pa[0], pb[0], float('nan')]; ys += [pa[1], pb[1], float('nan')]; zs += [pa[2], pb[2], float('nan')]
    for cat, line in lines.items():
        xs, ys, zs = buckets[cat]
        line.set_data(xs, ys); line.set_3d_properties(zs)
    bc=g.points['body_center']; hc=g.points['head_center']; el=g.points['eye_l']; er=g.points['eye_r']
    body_mass._offsets3d=([bc[0]],[bc[1]],[bc[2]])
    head_mass._offsets3d=([hc[0]],[hc[1]],[hc[2]])
    eyes._offsets3d=([el[0],er[0]],[el[1],er[1]],[el[2],er[2]])
    p = sequence[i]
    status.set_text(f"{labels[i]}   t={i/FPS:0.1f}s")
    info.set_text(
        f"neck yaw {p.get('neck_yaw',0):.0f}° | pitch {p.get('neck_pitch',0):.0f}° | "
        f"wings {p.get('wing_left',0):.0f}/{p.get('wing_right',0):.0f}°\n"
        f"watchdog {metrics.watchdog_cutoff_s:.2f}s | 8 DOF | simulated system motion budget ~{metrics.system_typical_motion_w:.1f} W*\n"
        "*electrical values are assumptions until measured on hardware"
    )
    return list(lines.values()) + [body_mass, head_mass, eyes, status, info]

ani = FuncAnimation(fig, update, frames=len(sequence), interval=1000/FPS, blit=False)
ani.save(OUT / "parrotcore_3d_motion_demo.mp4", writer=FFMpegWriter(fps=FPS, bitrate=2200))
# Smaller preview GIF at 12 fps by taking every second frame.
preview_idx = list(range(0, len(sequence), 2))
ani2 = FuncAnimation(fig, lambda j: update(preview_idx[j]), frames=len(preview_idx), interval=1000/12, blit=False)
ani2.save(OUT / "parrotcore_3d_motion_preview.gif", writer=PillowWriter(fps=12))
plt.close(fig)
print(json.dumps(summary, indent=2))
