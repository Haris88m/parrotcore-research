from __future__ import annotations

import unittest

from parrotcore.kinematics import compute_geometry
from parrotcore.models import MotionFrame
from parrotcore.reference import reference_joints
from parrotcore.simulation import SimulationAssumptions, effectiveness, interpolate_motion


class SimulationV03Tests(unittest.TestCase):
    def setUp(self):
        self.joints = reference_joints()
        self.home = {name: spec.home for name, spec in self.joints.items()}

    def test_home_geometry_has_all_joint_anchors(self):
        g = compute_geometry(self.home)
        self.assertEqual(set(g.joint_positions), set(self.joints))
        self.assertGreater(g.points["head_center"][2], g.points["body_center"][2])

    def test_neck_yaw_moves_beak_laterally(self):
        left = dict(self.home, neck_yaw=-40)
        right = dict(self.home, neck_yaw=40)
        lx = compute_geometry(left).points["beak_tip"][0]
        rx = compute_geometry(right).points["beak_tip"][0]
        self.assertNotAlmostEqual(lx, rx)
        self.assertAlmostEqual(abs(lx), abs(rx), places=5)

    def test_interpolation_finishes_at_target(self):
        poses = interpolate_motion((MotionFrame({"neck_yaw": 30}, 0.25),), self.home, fps=20)
        self.assertEqual(poses[-1]["neck_yaw"], 30)
        self.assertGreater(len(poses), 2)

    def test_effectiveness_is_profile_derived(self):
        m = effectiveness(self.joints, SimulationAssumptions())
        self.assertEqual(m.degrees_of_freedom, 8)
        self.assertEqual(m.neck_yaw_span_deg, 120)
        self.assertEqual(m.wing_span_command_deg, 150)
        self.assertEqual(m.watchdog_cutoff_s, 0.75)


if __name__ == "__main__":
    unittest.main()
