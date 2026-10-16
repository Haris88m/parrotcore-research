from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter

from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.kinematics import compute_creature_geometry
from parrotcore.models import MotionFrame
from parrotcore.simulation import creature_effectiveness, creature_tip_speed, interpolate_motion, metrics_dict

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 20
registry = CreatureRegistry.from_directory(ROOT / "profiles")
profiles = {p.species: p for p in registry.all()}
order = ["parrot", "owl", "raven"]

poses = {s: [dict(profiles[s].home_pose)] for s in order}
labels: list[str] = ["Home / same intelligence"]


def hold(label: str, seconds: float):
    n = max(1, round(seconds * FPS))
    for _ in range(n):
        for s in order:
            poses[s].append(dict(poses[s][-1]))
        labels.append(label)


def semantic(intent: str, label: str):
    per_species: dict[str, list[dict[str, float]]] = {}
    maxn = 0
    for s in order:
        frames = ExpressionCompiler(profiles[s]).compile(intent).frames
        seq = interpolate_motion(frames, poses[s][-1], fps=FPS)[1:]
        per_species[s] = seq
        maxn = max(maxn, len(seq))
    for i in range(maxn):
        for s in order:
            seq = per_species[s]
            poses[s].append(dict(seq[i] if i < len(seq) else seq[-1]))
        labels.append(label)


hold("Ready", 0.5)
semantic("greeting", "Semantic intent: GREETING")
hold("Listening", 0.25)
semantic("attend_left", "Semantic intent: ATTEND LEFT")
semantic("attend_right", "Semantic intent: ATTEND RIGHT")
semantic("center", "Semantic intent: CENTER")
semantic("blink", "Semantic intent: BLINK")
semantic("curious", "Semantic intent: CURIOUS")
semantic("affirm", "Semantic intent: AFFIRM")
semantic("dance", "Semantic intent: DANCE")
semantic("home", "Return home")
hold("One core · three embodiments", 0.7)

assert len({len(v) for v in poses.values()}) == 1
frames_n = len(labels)

summary = {
    "classification": "conceptual multi-embodiment kinematic simulation; not measured hardware performance",
    "platform_version": "0.4.0",
    "fps": FPS,
    "duration_s": frames_n / FPS,
    "frames": frames_n,
    "semantic_sequence": ["greeting", "attend_left", "attend_right", "center", "blink", "curious", "affirm", "dance", "home"],
    "creatures": {},
}
for s in order:
    summary["creatures"][s] = {
        "effectiveness": metrics_dict(creature_effectiveness(profiles[s])),
        "max_simulated_tip_speed_m_s": creature_tip_speed(profiles[s], poses[s], fps=FPS),
        "capabilities": sorted(profiles[s].capabilities),
        "expressions": sorted(profiles[s].expressions),
    }
(OUT / "creature_comparison_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

fig = plt.figure(figsize=(13, 7.5), dpi=105)
ax = fig.add_subplot(111, projection="3d")
ax.set_xlim(-0.72, 0.72); ax.set_ylim(-0.23, 0.22); ax.set_zlim(-0.02, 0.43)
ax.set_box_aspect((2.0, 0.8, 0.9)); ax.view_init(elev=16, azim=-58)
ax.set_xlabel("species separation / lateral (m)"); ax.set_ylabel("forward (m)"); ax.set_zlabel("height (m)")
ax.set_title("ParrotCore v0.4 — One Semantic Brain, Three Creature Digital Twins")

cats = ["perch", "leg", "body", "neck", "head", "beak", "face", "lid", "wing", "tail"]
offsets = {"parrot": -0.46, "owl": 0.0, "raven": 0.46}
lines = {}
for s in order:
    for cat in cats:
        lines[(s, cat)] = ax.plot([], [], [], linewidth=3 if cat not in {"face", "lid"} else 1.4)[0]

status = ax.text2D(0.03, 0.95, "", transform=ax.transAxes, fontsize=11)
info = ax.text2D(0.03, 0.885, "", transform=ax.transAxes, fontsize=8)
for s, x in offsets.items():
    ax.text(x, -0.20, 0.405, f"{s.upper()}\n{profiles[s].role.replace('_', ' ')}", ha="center", va="center")


def update(i):
    for s in order:
        g = compute_creature_geometry(profiles[s], poses[s][i])
        buckets = {c: ([], [], []) for c in cats}
        ox = offsets[s]
        for a, b, cat in g.segments:
            xs, ys, zs = buckets[cat]
            pa, pb = g.points[a], g.points[b]
            xs += [pa[0] + ox, pb[0] + ox, float("nan")]
            ys += [pa[1], pb[1], float("nan")]
            zs += [pa[2], pb[2], float("nan")]
        for cat in cats:
            xs, ys, zs = buckets[cat]
            line = lines[(s, cat)]
            line.set_data(xs, ys); line.set_3d_properties(zs)
    status.set_text(f"{labels[i]}   t={i/FPS:0.1f}s")
    info.set_text(
        "Cognition emits the same semantic intent for all three bodies.\n"
        "Each creature profile compiles that intent into different actuator names, ranges and choreography.\n"
        "Electrical/mass metrics are assumptions until physical prototypes are measured."
    )
    return list(lines.values()) + [status, info]

ani = FuncAnimation(fig, update, frames=frames_n, interval=1000/FPS, blit=False)
ani.save(OUT / "parrotcore_v04_creature_comparison.mp4", writer=FFMpegWriter(fps=FPS, bitrate=2600))
idx = list(range(0, frames_n, 2))
ani2 = FuncAnimation(fig, lambda j: update(idx[j]), frames=len(idx), interval=1000/10, blit=False)
ani2.save(OUT / "parrotcore_v04_creature_comparison.gif", writer=PillowWriter(fps=10))
plt.close(fig)
print(json.dumps(summary, indent=2))
