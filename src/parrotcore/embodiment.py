from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .models import MotionFrame
from .profile import BodyProfile, load_profile


class SemanticIntent(str, Enum):
    """Body-independent behavior vocabulary used by cognition and planners."""

    GREETING = "greeting"
    BLINK = "blink"
    DANCE = "dance"
    ATTEND_LEFT = "attend_left"
    ATTEND_RIGHT = "attend_right"
    CENTER = "center"
    CURIOUS = "curious"
    AFFIRM = "affirm"
    HOME = "home"


@dataclass(frozen=True)
class CompiledExpression:
    intent: str
    species: str
    frames: tuple[MotionFrame, ...]


class ExpressionCompiler:
    """Compile semantic intentions into safe, species-specific joint frames."""

    def __init__(self, profile: BodyProfile):
        self.profile = profile

    def available(self) -> tuple[str, ...]:
        return tuple(sorted(self.profile.expressions))

    def compile(self, intent: str | SemanticIntent) -> CompiledExpression:
        name = intent.value if isinstance(intent, SemanticIntent) else str(intent)
        if name == SemanticIntent.HOME.value:
            frames = (MotionFrame(self.profile.home_pose, 0.35),)
        else:
            try:
                frames = self.profile.expressions[name]
            except KeyError as exc:
                raise KeyError(
                    f"{self.profile.species} body has no expression for semantic intent {name!r}"
                ) from exc
        self._validate(frames)
        return CompiledExpression(name, self.profile.species, frames)

    def _validate(self, frames: Iterable[MotionFrame]) -> None:
        for frame in frames:
            if frame.duration_s < 0:
                raise ValueError("motion frame duration must be non-negative")
            for joint, value in frame.positions.items():
                if joint not in self.profile.joints:
                    raise ValueError(f"unknown joint {joint!r}")
                spec = self.profile.joints[joint]
                if not spec.minimum <= float(value) <= spec.maximum:
                    raise ValueError(
                        f"{joint} target {value} outside [{spec.minimum}, {spec.maximum}]"
                    )


class CreatureRegistry:
    """Load and index interchangeable creature bodies from a profile folder."""

    def __init__(self, profiles: Iterable[BodyProfile]):
        self._profiles = {p.species: p for p in profiles}
        if len(self._profiles) == 0:
            raise ValueError("registry requires at least one creature profile")

    @classmethod
    def from_directory(cls, directory: str | Path) -> "CreatureRegistry":
        paths = sorted(Path(directory).glob("*.toml"))
        profiles = [load_profile(path) for path in paths]
        return cls(profiles)

    def species(self) -> tuple[str, ...]:
        return tuple(sorted(self._profiles))

    def get(self, species: str) -> BodyProfile:
        try:
            return self._profiles[species]
        except KeyError as exc:
            raise KeyError(f"unknown creature species {species!r}; available={self.species()}") from exc

    def all(self) -> tuple[BodyProfile, ...]:
        return tuple(self._profiles[k] for k in self.species())
