from __future__ import annotations

from .models import JointSpec


def reference_joints() -> dict[str, JointSpec]:
    return {
        "neck_yaw": JointSpec("neck_yaw", -60, 60, 0),
        "neck_pitch": JointSpec("neck_pitch", -35, 40, 0),
        "beak": JointSpec("beak", 0, 35, 0),
        "wing_left": JointSpec("wing_left", 0, 75, 0),
        "wing_right": JointSpec("wing_right", 0, 75, 0),
        "tail_pitch": JointSpec("tail_pitch", -20, 35, 0),
        "eyelids": JointSpec("eyelids", 0, 100, 0),
        "body_lean": JointSpec("body_lean", -15, 20, 0),
    }
