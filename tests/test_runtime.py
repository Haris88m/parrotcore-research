import unittest

from parrotcore.body import SimulatedBody
from parrotcore.brain import ParrotBrain
from parrotcore.memory import MemoryStore
from parrotcore.models import Event, EventKind, MotionFrame
from parrotcore.protocol import FeatherBusCodec
from parrotcore.reference import reference_joints
from parrotcore.safety import EmergencyStop, SafetyGate


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.safety = SafetyGate(reference_joints())
        self.body = SimulatedBody(self.safety)
        self.brain = ParrotBrain(self.body, MemoryStore())

    def test_joint_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.body.move(MotionFrame({"neck_yaw": 90}))

    def test_estop_rejects_motion(self):
        self.safety.latch_estop()
        with self.assertRaises(EmergencyStop):
            self.body.move(MotionFrame({"neck_yaw": 10}))

    def test_teach_and_recall(self):
        self.brain.memory.teach("red", "apple")
        actions = self.brain.emit(Event(EventKind.PHRASE, "red"))
        self.assertEqual(actions[0].kind, "say")
        self.assertEqual(actions[0].payload["text"], "apple")

    def test_builtin_greeting_moves(self):
        actions = self.brain.emit(Event(EventKind.PHRASE, "hello"))
        self.assertTrue(any(a.kind == "motion" for a in actions))
        self.assertGreater(len(self.body.trace), 0)

    def test_featherbus_roundtrip(self):
        codec = FeatherBusCodec()
        raw = codec.encode("joint", id=0, value=12.5, speed=0.4)
        obj = codec.decode(raw)
        self.assertEqual(obj["type"], "joint")
        self.assertEqual(obj["value"], 12.5)


if __name__ == "__main__":
    unittest.main()
