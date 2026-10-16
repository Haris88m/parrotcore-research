from __future__ import annotations

import unittest
from pathlib import Path

from parrotcore.collision import estimate_collision
from parrotcore.dynamics import TrajectoryPlanner
from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.physics import DynamicsSimulator
from parrotcore.stability import estimate_stability
from parrotcore.telemetry import FaultKind

ROOT = Path(__file__).resolve().parents[1]


class DynamicsV05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = CreatureRegistry.from_directory(ROOT / "profiles")

    def test_quintic_trajectory_hits_exact_endpoint(self):
        p = self.registry.get("parrot")
        planner = TrajectoryPlanner(p.joints, sample_hz=100)
        tr = planner.plan(p.home_pose, {"neck_yaw": 55}, 0.05)
        self.assertEqual(tr.samples[-1].positions["neck_yaw"], 55.0)
        self.assertEqual(tr.samples[-1].velocities["neck_yaw"], 0.0)
        self.assertGreater(tr.duration_s, 0.05)

    def test_dynamic_limits_respected(self):
        p = self.registry.get("owl")
        planner = TrajectoryPlanner(p.joints, sample_hz=200)
        tr = planner.plan(p.home_pose, {"head_yaw": 100, "head_pitch": 40}, 0.01)
        for sample in tr.samples:
            for name, spec in p.joints.items():
                self.assertLessEqual(abs(sample.velocities[name]), spec.max_speed * 1.001)
                self.assertLessEqual(abs(sample.accelerations[name]), spec.max_accel * 1.001)
                self.assertLessEqual(abs(sample.jerks[name]), spec.max_jerk * 1.001)

    def test_expression_targets_plan_for_all_species(self):
        for p in self.registry.all():
            planner = TrajectoryPlanner(p.joints)
            pose = dict(p.home_pose)
            for frame in ExpressionCompiler(p).compile("greeting").frames:
                tr = planner.plan(pose, frame.positions, frame.duration_s)
                pose = dict(tr.samples[-1].positions)
            self.assertTrue(all(p.joints[n].minimum <= pose[n] <= p.joints[n].maximum for n in p.joints))

    def test_normal_run_has_telemetry(self):
        p = self.registry.get("parrot")
        sim = DynamicsSimulator(p)
        run = sim.run(p.home_pose, {"neck_yaw": 30}, 0.4)
        self.assertGreater(len(run.telemetry), 2)
        self.assertGreater(run.telemetry[-1].rail_current_a, 0)
        self.assertGreater(run.telemetry[-1].system_power_w, 0)

    def test_stalled_servo_fault(self):
        p = self.registry.get("parrot")
        sim = DynamicsSimulator(p)
        sim.injection.stalled_joints.add("neck_yaw")
        run = sim.run(p.home_pose, {"neck_yaw": 30}, 0.4)
        self.assertTrue(any(FaultKind.SERVO_STALL in f.faults for f in run.telemetry))
        self.assertEqual(run.telemetry[-1].positions["neck_yaw"], p.home_pose["neck_yaw"])

    def test_watchdog_loss_fault(self):
        p = self.registry.get("raven")
        sim = DynamicsSimulator(p)
        sim.injection.watchdog_lost = True
        run = sim.run(p.home_pose, {"neck_yaw": 10}, 0.2)
        self.assertTrue(all(FaultKind.WATCHDOG_LOSS in f.faults for f in run.telemetry))

    def test_proximity_fault(self):
        p = self.registry.get("owl")
        sim = DynamicsSimulator(p)
        sim.injection.forced_tof_distance_m = 0.04
        run = sim.run(p.home_pose, {"head_pitch": 10}, 0.2)
        self.assertTrue(any(FaultKind.PROXIMITY in f.faults for f in run.telemetry))

    def test_overtemp_fault_injection(self):
        p = self.registry.get("parrot")
        sim = DynamicsSimulator(p)
        sim.injection.forced_temperature_c = 80
        run = sim.run(p.home_pose, {"neck_pitch": 5}, 0.2)
        self.assertTrue(any(FaultKind.OVERTEMP in f.faults for f in run.telemetry))

    def test_overcurrent_with_all_servos_stalled(self):
        p = self.registry.get("raven")
        sim = DynamicsSimulator(p)
        sim.injection.stalled_joints.update(p.joints)
        run = sim.run(p.home_pose, {"neck_yaw": 10}, 0.2)
        self.assertTrue(any(FaultKind.OVERCURRENT in f.faults for f in run.telemetry))

    def test_home_collision_proxy_is_clear(self):
        for p in self.registry.all():
            c = estimate_collision(p, p.home_pose)
            self.assertFalse(c.risk, (p.species, c.reasons))

    def test_home_stability_proxy_is_positive(self):
        for p in self.registry.all():
            s = estimate_stability(p, p.home_pose)
            self.assertTrue(s.stable_proxy, (p.species, s))
            self.assertGreaterEqual(s.margin_m, 0)


if __name__ == "__main__":
    unittest.main()
