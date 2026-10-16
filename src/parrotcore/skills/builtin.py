from __future__ import annotations

from ..models import Action, Event, EventKind
from ..embodiment import SemanticIntent


class BuiltinSkillSet:
    """Deterministic, body-independent behaviors used before an AI policy is attached."""

    def actions_for(self, event: Event) -> list[Action]:
        if event.kind is not EventKind.PHRASE:
            return []
        text = event.value.strip().lower()

        if text in {"hello", "hi", "hello bird", "hey bird", "hello robot"}:
            return [
                Action("say", {"text": "Hello!"}),
                Action("motion", {"name": "happy_greeting", "semantic": SemanticIntent.GREETING.value}),
            ]
        if "dance" in text:
            return [
                Action("say", {"text": "Dance mode."}),
                Action("motion", {"name": "dance", "semantic": SemanticIntent.DANCE.value}),
            ]
        if "look left" in text:
            return [Action("motion", {"name": "attend_left", "semantic": SemanticIntent.ATTEND_LEFT.value})]
        if "look right" in text:
            return [Action("motion", {"name": "attend_right", "semantic": SemanticIntent.ATTEND_RIGHT.value})]
        if text in {"center", "look center", "look forward"}:
            return [Action("motion", {"name": "center", "semantic": SemanticIntent.CENTER.value})]
        if text == "blink":
            return [Action("motion", {"name": "blink", "semantic": SemanticIntent.BLINK.value})]
        if text in {"curious", "what is that", "hmm"}:
            return [Action("motion", {"name": "curious", "semantic": SemanticIntent.CURIOUS.value})]
        if text in {"yes", "correct", "good"}:
            return [Action("motion", {"name": "affirm", "semantic": SemanticIntent.AFFIRM.value})]
        if text in {"home", "rest pose"}:
            return [Action("motion", {"name": "home", "semantic": SemanticIntent.HOME.value})]
        return []
