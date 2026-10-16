import io
import json
import tempfile
import unittest
from pathlib import Path

from parrotcore.models import MotionFrame
from parrotcore.profile import load_profile
from parrotcore.serial_body import FeatherSerialBody
from parrotcore.safety import SafetyGate


PROFILE_TEXT = '''
[body]
name="test"
protocol="featherbus-v0"
[joints.neck]
minimum=-10
maximum=10
home=0
controller_id=3
'''


class V02Tests(unittest.TestCase):
    def make_profile(self):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "p.toml"
        path.write_text(PROFILE_TEXT)
        return td, load_profile(path)

    def test_profile_loading(self):
        td, p = self.make_profile()
        self.addCleanup(td.cleanup)
        self.assertEqual(p.name, "test")
        self.assertEqual(p.controller_ids["neck"], 3)

    def test_serial_body_encodes_pose(self):
        td, p = self.make_profile()
        self.addCleanup(td.cleanup)
        stream = io.BytesIO()
        body = FeatherSerialBody(p, SafetyGate(p.joints), stream)
        body.move(MotionFrame({"neck": 7.5}, 0.2))
        obj = json.loads(stream.getvalue().decode())
        self.assertEqual(obj["type"], "pose")
        self.assertEqual(obj["values"]["3"], 7.5)
        self.assertEqual(obj["duration_ms"], 200)

    def test_serial_body_safety_before_write(self):
        td, p = self.make_profile()
        self.addCleanup(td.cleanup)
        stream = io.BytesIO()
        body = FeatherSerialBody(p, SafetyGate(p.joints), stream)
        with self.assertRaises(ValueError):
            body.move(MotionFrame({"neck": 99}, 0.2))
        self.assertEqual(stream.getvalue(), b"")


if __name__ == "__main__":
    unittest.main()

class MemoryThreadTests(unittest.TestCase):
    def test_memory_cross_thread(self):
        import threading
        from parrotcore.memory import MemoryStore
        store = MemoryStore()
        errors = []
        def worker():
            try:
                store.teach("thread", "safe")
                assert store.recall("thread") == "safe"
            except Exception as exc:
                errors.append(exc)
        t = threading.Thread(target=worker)
        t.start(); t.join()
        self.assertEqual(errors, [])
