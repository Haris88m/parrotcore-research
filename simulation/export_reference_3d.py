from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import trimesh
from trimesh.transformations import rotation_matrix
from parrotcore.kinematics import compute_geometry
from parrotcore.reference import reference_joints

OUT = ROOT / "simulation" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)


def cyl_between(a, b, radius, sections=18):
    a=np.asarray(a,dtype=float); b=np.asarray(b,dtype=float); v=b-a; L=np.linalg.norm(v)
    if L < 1e-9: return None
    m=trimesh.creation.cylinder(radius=radius,height=L,sections=sections)
    z=np.array([0.,0.,1.]); axis=np.cross(z,v/L); dot=np.clip(np.dot(z,v/L),-1,1)
    if np.linalg.norm(axis)>1e-9:
        m.apply_transform(rotation_matrix(np.arccos(dot),axis))
    elif dot < 0:
        m.apply_transform(rotation_matrix(np.pi,[1,0,0]))
    m.apply_translation((a+b)/2)
    return m

home={n:s.home for n,s in reference_joints().items()}
g=compute_geometry(home)
parts=[]
# Volumes are conceptual mechanical envelopes, not printable shell geometry.
body=trimesh.creation.icosphere(subdivisions=2,radius=1); body.apply_scale([.065,.055,.095]); body.apply_translation(g.points['body_center']); parts.append(body)
head=trimesh.creation.icosphere(subdivisions=2,radius=1); head.apply_scale([.043,.049,.043]); head.apply_translation(g.points['head_center']); parts.append(head)
for eye in ['eye_l','eye_r']:
    e=trimesh.creation.icosphere(subdivisions=1,radius=.006); e.apply_translation(g.points[eye]); parts.append(e)
# Skeleton/link envelopes.
radii={'perch':.009,'leg':.005,'body':.010,'neck':.010,'head':.007,'beak':.005,'face':.0025,'lid':.002,'wing':.008,'tail':.007}
for a,b,cat in g.segments:
    m=cyl_between(g.points[a],g.points[b],radii[cat])
    if m is not None: parts.append(m)
scene=trimesh.Scene(parts)
scene.export(OUT/'reference_parrot_home.glb')
# Also export merged STL for tools that do not read GLB. This is a visualization envelope only.
merged=trimesh.util.concatenate(parts)
merged.export(OUT/'reference_parrot_home.stl')
print('exported', OUT/'reference_parrot_home.glb')
