from __future__ import annotations

from ..models import MotionFrame


MOTIONS: dict[str, tuple[MotionFrame, ...]] = {
    "blink": (
        MotionFrame({"eyelids": 100}, 0.08),
        MotionFrame({"eyelids": 0}, 0.12),
    ),
    "happy_greeting": (
        MotionFrame({"neck_pitch": -8, "wing_left": 18, "wing_right": 18}, 0.18),
        MotionFrame({"neck_yaw": -18, "wing_left": 32, "wing_right": 12}, 0.20),
        MotionFrame({"neck_yaw": 18, "wing_left": 12, "wing_right": 32}, 0.20),
        MotionFrame({"neck_yaw": 0, "neck_pitch": 0, "wing_left": 0, "wing_right": 0}, 0.22),
    ),
    "dance": (
        MotionFrame({"neck_yaw": -30, "body_lean": -7, "tail_pitch": 18}, 0.20),
        MotionFrame({"neck_yaw": 30, "body_lean": 7, "tail_pitch": -8}, 0.20),
        MotionFrame({"neck_yaw": -30, "body_lean": -7, "wing_left": 45}, 0.20),
        MotionFrame({"neck_yaw": 30, "body_lean": 7, "wing_right": 45}, 0.20),
        MotionFrame({"neck_yaw": 0, "body_lean": 0, "wing_left": 0, "wing_right": 0, "tail_pitch": 0}, 0.25),
    ),
}
