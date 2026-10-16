from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))

from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.physics import DynamicsSimulator

OUT=ROOT/'simulation'/'outputs';OUT.mkdir(parents=True,exist_ok=True)
registry=CreatureRegistry.from_directory(ROOT/'profiles')
report={"classification":"conceptual simulation benchmark; not measured hardware performance","platform_version":"0.5.0","creatures":{}}
for profile in registry.all():
    sim=DynamicsSimulator(profile,sample_hz=50);pose=dict(profile.home_pose);frames=[]
    for intent in ("greeting","curious","dance","affirm","home"):
        for motion in ExpressionCompiler(profile).compile(intent).frames:
            run=sim.run(pose,motion.positions,motion.duration_s);frames.extend(run.telemetry[1:]);pose=dict(run.telemetry[-1].positions)
    faults=Counter(f.value for t in frames for f in t.faults)
    normal={
        "frames":len(frames),
        "duration_s":len(frames)/50,
        "max_rail_current_a":max(t.rail_current_a for t in frames),
        "max_system_power_w":max(t.system_power_w for t in frames),
        "max_servo_temp_c":max(t.max_servo_temp_c for t in frames),
        "min_stability_margin_m":min(t.stability_margin_m for t in frames),
        "fault_frame_counts":dict(faults),
    }
    probes={}
    def probe(name, setup):
        s=DynamicsSimulator(profile,sample_hz=20);setup(s);yaw='head_yaw' if 'head_yaw' in profile.joints else 'neck_yaw';target={yaw:min(profile.joints[yaw].maximum, profile.joints[yaw].home+10)};r=s.run(profile.home_pose,target,.2)
        probes[name]=sorted({f.value for t in r.telemetry for f in t.faults})
    probe('watchdog_loss',lambda s:setattr(s.injection,'watchdog_lost',True))
    probe('proximity',lambda s:setattr(s.injection,'forced_tof_distance_m',.04))
    probe('overtemp',lambda s:setattr(s.injection,'forced_temperature_c',80))
    probe('all_servo_stall',lambda s:s.injection.stalled_joints.update(profile.joints))
    report['creatures'][profile.species]={"normal_behavior":normal,"fault_probes":probes}
(OUT/'v05_species_dynamics_benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
