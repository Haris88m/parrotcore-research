from __future__ import annotations

from pathlib import Path

from .body import SimulatedBody
from .brain import EmbodiedBrain
from .memory import MemoryStore
from .profile import BodyProfile, load_profile
from .safety import SafetyGate


def simulated_runtime(profile: BodyProfile, memory: MemoryStore | None = None, realtime: bool = False) -> EmbodiedBrain:
    safety = SafetyGate(profile.joints)
    body = SimulatedBody(safety=safety, realtime=realtime)
    return EmbodiedBrain(body=body, memory=memory or MemoryStore(), profile=profile)


def simulated_runtime_from_path(profile_path: str | Path, memory_path: str = ":memory:", realtime: bool = False) -> EmbodiedBrain:
    return simulated_runtime(load_profile(profile_path), MemoryStore(memory_path), realtime=realtime)
