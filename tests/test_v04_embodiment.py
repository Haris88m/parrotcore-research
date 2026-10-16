from __future__ import annotations

import unittest
from pathlib import Path

from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler, SemanticIntent
from parrotcore.kinematics import compute_creature_geometry
from parrotcore.memory import MemoryStore
from parrotcore.models import Event, EventKind
from parrotcore.runtime import simulated_runtime
from parrotcore.simulation import creature_effectiveness


ROOT = Path(__file__).resolve().parents[1]


class EmbodimentV04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = CreatureRegistry.from_directory(ROOT / "profiles")

    def test_registry_has_three_reference_creatures(self):
        self.assertEqual(self.registry.species(), ("owl", "parrot", "raven"))

    def test_profiles_share_intents_not_joint_names(self):
        parrot = self.registry.get("parrot")
        owl = self.registry.get("owl")
        p = ExpressionCompiler(parrot).compile(SemanticIntent.ATTEND_LEFT)
        o = ExpressionCompiler(owl).compile(SemanticIntent.ATTEND_LEFT)
        self.assertIn("neck_yaw", p.frames[0].positions)
        self.assertIn("head_yaw", o.frames[0].positions)
        self.assertNotEqual(p.frames[0].positions, o.frames[0].positions)

    def test_every_expression_compiles_inside_limits(self):
        for profile in self.registry.all():
            compiler = ExpressionCompiler(profile)
            for name in compiler.available():
                compiled = compiler.compile(name)
                self.assertGreater(len(compiled.frames), 0)

    def test_home_is_derived_from_each_body(self):
        raven = self.registry.get("raven")
        home = ExpressionCompiler(raven).compile(SemanticIntent.HOME).frames[-1].positions
        self.assertEqual(home["tail_fan"], 8.0)

    def test_same_phrase_executes_on_all_creatures(self):
        for profile in self.registry.all():
            brain = simulated_runtime(profile, MemoryStore())
            actions = brain.emit(Event(EventKind.PHRASE, "hello"))
            self.assertTrue(any(a.payload.get("semantic") == "greeting" for a in actions if a.kind == "motion"))
            self.assertGreater(len(brain.body.trace), 0)

    def test_geometry_joint_anchors_cover_profiles(self):
        for profile in self.registry.all():
            g = compute_creature_geometry(profile, profile.home_pose)
            self.assertEqual(set(g.joint_positions), set(profile.joints))
            self.assertGreater(g.points["head_center"][2], g.points["body_center"][2])

    def test_owl_has_larger_yaw_envelope_than_parrot(self):
        owl = creature_effectiveness(self.registry.get("owl"))
        parrot = creature_effectiveness(self.registry.get("parrot"))
        self.assertGreater(owl.yaw_span_deg, parrot.yaw_span_deg)

    def test_effectiveness_is_profile_specific(self):
        values = {p.species: creature_effectiveness(p) for p in self.registry.all()}
        self.assertEqual(values["parrot"].degrees_of_freedom, 8)
        self.assertNotEqual(values["parrot"].estimated_mass_kg, values["owl"].estimated_mass_kg)
        self.assertGreaterEqual(values["raven"].expression_count, 8)


if __name__ == "__main__":
    unittest.main()
