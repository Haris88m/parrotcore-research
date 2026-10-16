from __future__ import annotations

import argparse
from pathlib import Path

from .body import SimulatedBody
from .brain import ParrotBrain
from .creature_lab import serve as serve_creature_lab
from .dynamics_lab import serve as serve_dynamics_lab
from .embodiment import CreatureRegistry
from .lesson_engine import LessonEngine
from .memory import MemoryStore
from .models import Event, EventKind
from .profile import load_profile
from .safety import SafetyGate
from .serial_body import FeatherSerialBody
from .studio import serve


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_profiles_dir() -> Path:
    # Runtime defaults belong to the installed package, not its source checkout.
    # The sibling hardware resources are also used by the dynamics lab.
    return Path(__file__).resolve().parent / "resources" / "profiles"


def default_profile_path() -> Path:
    return default_profiles_dir() / "reference_parrot.toml"


def make_brain(memory_path: str = ":memory:", lesson_path: str | None = None, profile_path: str | Path | None = None) -> ParrotBrain:
    profile = load_profile(profile_path or default_profile_path())
    safety = SafetyGate(profile.joints)
    body = SimulatedBody(safety=safety)
    lessons = LessonEngine.from_file(lesson_path) if lesson_path else LessonEngine()
    return ParrotBrain(body=body, memory=MemoryStore(memory_path), profile=profile, lessons=lessons)


def make_physical_brain(port: str, profile_path: str, memory_path: str) -> ParrotBrain:
    profile = load_profile(profile_path)
    safety = SafetyGate(profile.joints)
    body = FeatherSerialBody.from_port(profile, safety, port)
    return ParrotBrain(body=body, memory=MemoryStore(memory_path), profile=profile)


def demo() -> None:
    registry = CreatureRegistry.from_directory(default_profiles_dir())
    print("ParrotCore v0.5.2 species-agnostic simulator")
    for species in registry.species():
        p = registry.get(species)
        brain = make_brain(profile_path=default_profiles_dir() / f"reference_{species}.toml")
        print(f"\n=== {species.upper()} / {p.role} ===")
        brain.body.home()
        for phrase in ["hello", "look left", "curious", "yes"]:
            print(f"> {phrase}")
            brain.emit(Event(EventKind.PHRASE, phrase))


def shell(brain: ParrotBrain) -> None:
    species = brain.profile.species if brain.profile else "legacy-parrot"
    print(f"ParrotCore shell [{species}]. Type 'help' for commands.")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not raw:
            continue
        low = raw.lower()
        if low in {"quit", "exit"}:
            break
        if low == "help":
            print("hello | dance | curious | yes | look left | look right | blink | home | teach A=B | status | estop | reset | quit")
            continue
        if low == "status":
            print(brain.body.status()); print({"species": species, "learned": brain.memory.all()}); continue
        if low == "estop":
            if hasattr(brain.body, "estop"): brain.body.estop(True)
            else: brain.body.safety.latch_estop()
            print("[SAFETY] emergency stop latched"); continue
        if low == "reset":
            if hasattr(brain.body, "estop"): brain.body.estop(False)
            else: brain.body.safety.reset_estop()
            print("[SAFETY] emergency stop reset"); continue
        if low.startswith("teach ") and "=" in raw:
            trigger, response = raw[6:].split("=", 1); brain.memory.teach(trigger, response)
            print(f"[MEMORY] learned {trigger.strip()!r} -> {response.strip()!r}"); continue
        try:
            actions = brain.emit(Event(EventKind.PHRASE, raw))
            if not actions: print("[BRAIN] no matching skill yet")
        except Exception as exc:
            print(f"[FAULT] {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="parrotcore")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")

    p_shell = sub.add_parser("shell")
    p_shell.add_argument("--species", choices=["parrot", "owl", "raven"], default="parrot")
    p_shell.add_argument("--memory", default=str(Path.home() / ".parrotcore_memory.sqlite3"))

    p_lesson = sub.add_parser("lesson")
    p_lesson.add_argument("path"); p_lesson.add_argument("event")
    p_lesson.add_argument("--species", choices=["parrot", "owl", "raven"], default="parrot")

    p_studio = sub.add_parser("studio")
    p_studio.add_argument("--host", default="127.0.0.1"); p_studio.add_argument("--port", type=int, default=8765)
    p_studio.add_argument("--memory", default=str(Path.home() / ".parrotcore_memory.sqlite3"))

    p_lab = sub.add_parser("creature-lab")
    p_lab.add_argument("--host", default="127.0.0.1"); p_lab.add_argument("--port", type=int, default=8770)
    p_lab.add_argument("--memory", default=str(Path.home() / ".parrotcore_memory.sqlite3"))

    p_dyn = sub.add_parser("dynamics-lab")
    p_dyn.add_argument("--host", default="127.0.0.1"); p_dyn.add_argument("--port", type=int, default=8780)

    p_hw = sub.add_parser("hardware-shell")
    p_hw.add_argument("--serial", required=True, dest="serial_port")
    p_hw.add_argument("--profile", default=str(default_profile_path()))
    p_hw.add_argument("--memory", default=str(Path.home() / ".parrotcore_memory.sqlite3"))

    args = parser.parse_args()
    if args.command == "demo":
        demo()
    elif args.command == "shell":
        shell(make_brain(memory_path=args.memory, profile_path=default_profiles_dir()/f"reference_{args.species}.toml"))
    elif args.command == "lesson":
        brain = make_brain(lesson_path=args.path, profile_path=default_profiles_dir()/f"reference_{args.species}.toml")
        brain.emit(Event(EventKind.PHRASE, args.event))
    elif args.command == "studio":
        serve(make_brain(memory_path=args.memory), args.host, args.port)
    elif args.command == "creature-lab":
        serve_creature_lab(default_profiles_dir(), args.host, args.port, args.memory)
    elif args.command == "dynamics-lab":
        serve_dynamics_lab(default_profiles_dir(), args.host, args.port)
    elif args.command == "hardware-shell":
        shell(make_physical_brain(args.serial_port, args.profile, args.memory))


if __name__ == "__main__":
    main()
