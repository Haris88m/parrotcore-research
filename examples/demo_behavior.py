from parrotcore.body import SimulatedBody
from parrotcore.brain import ParrotBrain
from parrotcore.memory import MemoryStore
from parrotcore.models import Event, EventKind
from parrotcore.reference import reference_joints
from parrotcore.safety import SafetyGate

body = SimulatedBody(SafetyGate(reference_joints()))
brain = ParrotBrain(body=body, memory=MemoryStore())

brain.emit(Event(EventKind.PHRASE, "hello"))
brain.memory.teach("banana", "yellow")
brain.emit(Event(EventKind.PHRASE, "banana"))
