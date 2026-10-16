from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .models import Action, Event


@dataclass(frozen=True)
class LessonRule:
    event_kind: str
    contains: str
    actions: tuple[Action, ...]


class LessonEngine:
    def __init__(self, rules: list[LessonRule] | None = None) -> None:
        self.rules = rules or []

    @classmethod
    def from_file(cls, path: str | Path) -> "LessonEngine":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rules: list[LessonRule] = []
        for raw in data.get("rules", []):
            actions = tuple(Action(a["kind"], dict(a.get("payload", {}))) for a in raw["actions"])
            rules.append(
                LessonRule(
                    event_kind=str(raw["event_kind"]),
                    contains=str(raw.get("contains", "")).lower(),
                    actions=actions,
                )
            )
        return cls(rules)

    def actions_for(self, event: Event) -> list[Action]:
        value = event.value.lower()
        out: list[Action] = []
        for rule in self.rules:
            if rule.event_kind != event.kind.value:
                continue
            if rule.contains and rule.contains not in value:
                continue
            out.extend(rule.actions)
        return out
