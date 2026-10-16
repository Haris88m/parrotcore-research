from __future__ import annotations

from dataclasses import dataclass, field

from .body import BodyDriver
from .embodiment import ExpressionCompiler
from .lesson_engine import LessonEngine
from .memory import MemoryStore
from .models import Action, Event, EventKind, MotionFrame
from .profile import BodyProfile
from .skills._motions import MOTIONS
from .skills.builtin import BuiltinSkillSet


@dataclass
class ParrotBrain:
    """Embodied cognition runtime.

    The historical class name is preserved for compatibility.  From v0.4 the
    brain is species-agnostic when a BodyProfile is supplied: high-level skills
    emit semantic `express` actions and ExpressionCompiler maps those into the
    selected creature body's joints.
    """

    body: BodyDriver
    memory: MemoryStore
    profile: BodyProfile | None = None
    lessons: LessonEngine = field(default_factory=LessonEngine)
    builtin: BuiltinSkillSet = field(default_factory=BuiltinSkillSet)

    def emit(self, event: Event) -> list[Action]:
        actions: list[Action] = []

        if event.kind is EventKind.PHRASE:
            learned = self.memory.recall(event.value)
            if learned is not None:
                actions.append(Action("say", {"text": learned}))

        actions.extend(self.lessons.actions_for(event))
        if not actions:
            actions.extend(self.builtin.actions_for(event))

        for action in actions:
            self.execute(action)
        return actions

    def execute(self, action: Action) -> None:
        if action.kind == "say":
            print(f"[VOICE] {action.payload['text']}")
            return

        if action.kind == "pose":
            self.body.move(
                MotionFrame(
                    positions={k: float(v) for k, v in action.payload["positions"].items()},
                    duration_s=float(action.payload.get("duration_s", 0.25)),
                )
            )
            return

        if action.kind == "express":
            intent = str(action.payload["intent"])
            if self.profile is None:
                # v0.3 compatibility path for programs that constructed a brain
                # directly from reference_joints() and never supplied a profile.
                self._execute_legacy_expression(intent)
                return
            compiled = ExpressionCompiler(self.profile).compile(intent)
            for frame in compiled.frames:
                self.body.move(frame)
            return

        if action.kind == "motion":
            # v0.4 keeps the historical action kind for wire/API compatibility,
            # while the optional semantic field routes through the embodiment
            # compiler. Existing lesson files without semantic remain legacy.
            semantic = action.payload.get("semantic")
            if semantic is not None:
                if self.profile is None:
                    self._execute_legacy_expression(str(semantic))
                else:
                    compiled = ExpressionCompiler(self.profile).compile(str(semantic))
                    for frame in compiled.frames:
                        self.body.move(frame)
                return
            name = str(action.payload["name"])
            if name not in MOTIONS:
                raise ValueError(f"unknown legacy motion: {name}")
            for frame in MOTIONS[name]:
                self.body.move(frame)
            return

        if action.kind == "teach":
            self.memory.teach(str(action.payload["trigger"]), str(action.payload["response"]))
            return

        raise ValueError(f"unsupported action: {action.kind}")

    def _execute_legacy_expression(self, intent: str) -> None:
        if intent == "greeting":
            frames = MOTIONS["happy_greeting"]
        elif intent == "dance":
            frames = MOTIONS["dance"]
        elif intent == "blink":
            frames = MOTIONS["blink"]
        elif intent == "attend_left":
            frames = (MotionFrame({"neck_yaw": -40}, 0.3),)
        elif intent == "attend_right":
            frames = (MotionFrame({"neck_yaw": 40}, 0.3),)
        elif intent == "center":
            frames = (MotionFrame({"neck_yaw": 0, "neck_pitch": 0}, 0.3),)
        elif intent == "curious":
            frames = (
                MotionFrame({"neck_yaw": -15, "neck_pitch": 12}, 0.24),
                MotionFrame({"neck_yaw": 10, "neck_pitch": 8}, 0.24),
            )
        elif intent == "affirm":
            frames = (
                MotionFrame({"neck_pitch": 14}, 0.16),
                MotionFrame({"neck_pitch": -4}, 0.16),
                MotionFrame({"neck_pitch": 0}, 0.16),
            )
        elif intent == "home":
            self.body.home()
            return
        else:
            raise ValueError(f"unknown semantic expression: {intent}")
        for frame in frames:
            self.body.move(frame)


# Explicit new name for new code.  Existing imports of ParrotBrain continue to work.
EmbodiedBrain = ParrotBrain
