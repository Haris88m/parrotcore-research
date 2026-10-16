from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import trimesh
from trimesh.transformations import rotation_matrix

from parrotcore.embodiment import CreatureRegistry
from parrotcore.kinematics import compute_creature_geometry

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
registry = CreatureRegistry.from_directory(ROOT / "profiles")


def cyl_between(a, b, radius, sections=16):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float); v = b-a; length = np.linalg.norm(v)
    if length < 1e-9: return None
    m = trimesh.creation.cylinder(radius=radius, height=length, sections=sections)
    z=np.array([0.,0.,1.]); unit=v/length; axis=np.cross(z,unit); dot=np.clip(np.dot(z,unit),-1,1)
    if np.linalg.norm(axis)>1e-9: m.apply_transform(rotation_matrix(np.arccos(dot),axis))
    elif dot<0: m.apply_transform(rotation_matrix(np.pi,[1,0,0]))
    m.apply_translation((a+b)/2); return m


radii = {"perch":.009,"leg":.005,"body":.011,"neck":.009,"head":.007,"beak":.005,"face":.0025,"lid":.002,"wing":.008,"tail":.0065}
for profile in registry.all():
    g = compute_creature_geometry(profile, profile.home_pose)
    parts = []
    # Conceptual volumes deliberately remain simple; this is a digital-twin envelope,
    # not a printable shell or manufacturable linkage CAD file.
    body = trimesh.creation.icosphere(subdivisions=2, radius=1)
    body_scale = {"parrot":[.065,.055,.095],"owl":[.075,.060,.090],"raven":[.060,.052,.100]}[profile.species]
    body.apply_scale(body_scale); body.apply_translation(g.points["body_center"]); parts.append(body)
    head = trimesh.creation.icosphere(subdivisions=2, radius=1)
    head_scale = {"parrot":[.043,.049,.043],"owl":[.060,.054,.053],"raven":[.041,.047,.040]}[profile.species]
    head.apply_scale(head_scale); head.apply_translation(g.points["head_center"]); parts.append(head)
    for eye in ["eye_l","eye_r"]:
        if eye in g.points:
            e=trimesh.creation.icosphere(subdivisions=1,radius=.006 if profile.species!="owl" else .009)
            e.apply_translation(g.points[eye]); parts.append(e)
    for a,b,cat in g.segments:
        m=cyl_between(g.points[a],g.points[b],radii.get(cat,.005))
        if m is not None: parts.append(m)
    scene=trimesh.Scene(parts)
    scene.export(OUT/f"reference_{profile.species}_home.glb")
    trimesh.util.concatenate(parts).export(OUT/f"reference_{profile.species}_home.stl")
    print("exported", profile.species)
