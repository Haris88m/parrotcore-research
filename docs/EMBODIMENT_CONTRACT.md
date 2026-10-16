# Embodiment Contract v0.4

## Purpose

The embodiment contract separates **what the AI intends** from **how a particular creature moves**.

```text
Perception / language / planner
            |
       semantic intent
            |
   ExpressionCompiler
            |
       BodyProfile
            |
   safe MotionFrame(s)
            |
        BodyDriver
            |
 FeatherBus / simulator
```

## Semantic vocabulary implemented

- `greeting`
- `blink`
- `attend_left`
- `attend_right`
- `center`
- `curious`
- `affirm`
- `dance`
- `home` (derived automatically from joint home values)

These are intentionally small. A later planner should target this vocabulary rather than raw joint positions.

## Body profile responsibilities

Each TOML body profile defines:

1. protocol name;
2. physical actuator names;
3. controller IDs;
4. actuator minimum/maximum/home values;
5. maximum speed metadata;
6. species, morphology and intended role;
7. capability tags;
8. species-specific expression frames;
9. current simulation assumptions.

`load_profile()` rejects:

- duplicate controller IDs;
- expression frames that reference unknown joints;
- expression positions outside profile limits.

The runtime safety gate checks motion again before execution. This duplicate validation is deliberate.

## Current examples

### Parrot — `attend_left`

```text
semantic: attend_left
joint: neck_yaw
position: -40 degrees
```

### Owl — `attend_left`

```text
semantic: attend_left
joint: head_yaw
position: -72 degrees
head pitch: +4 degrees
```

### Raven — `attend_left`

```text
semantic: attend_left
joint: neck_yaw
position: -52 degrees
body lean: +3 degrees
```

Cognition sees only `attend_left`.

## Extension rule for a future creature

A new creature should require:

- one TOML profile;
- an optional digital-twin geometry provider;
- physical calibration values;
- no change to memory, language, lesson storage or core semantic skills.

If adding a creature requires editing the planner to reference its servo names, the abstraction has failed.
