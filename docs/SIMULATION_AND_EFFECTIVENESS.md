# ParrotCore v0.3 — 3D Simulation and Effectiveness

## Status classes

This document deliberately separates three categories:

- **IMPLEMENTED:** exists in the software/firmware repository and can be exercised now.
- **CONFIGURATION-DERIVED:** follows directly from the current body profile or firmware constants.
- **SIMULATION ASSUMPTION:** placeholder engineering value that must be replaced with measured prototype data.

## Current digital-twin model

The reference bird has eight controlled degrees of freedom:

| Joint | Current logical range | Purpose |
|---|---:|---|
| Neck yaw | -60° to +60° | gaze left/right |
| Neck pitch | -35° to +40° | gaze/bow up/down |
| Beak | 0° to 35° | speech/gesture |
| Left wing | 0° to 75° | flap/gesture |
| Right wing | 0° to 75° | flap/gesture |
| Tail pitch | -20° to +35° | balance/expression |
| Eyelids | 0–100% | blink/expression |
| Body lean | -15° to +20° | bow/posture |

These ranges are **configuration-derived**. Exact physical PWM endpoints and safe mechanical ranges are intentionally not assumed.

## What the current simulation proves

**IMPLEMENTED:**

- a semantic command such as `dance` resolves to the existing motion library;
- the same motion frames update the software body and the 3D twin;
- the 3D twin maps every configured joint to a visible kinematic effect;
- joint sliders cannot escape the displayed configured limits;
- safety state can be latched/reset from Studio;
- teaching memory remains independent from the animation layer;
- the digital twin can be used before expensive mechanics are built.

The included rendered demonstration executes home, greeting, gaze, blink and dance in one sequence.

## Configuration-derived capability envelope

- **8 DOF** controlled body.
- **120°** total neck-yaw command span.
- **75°** total neck-pitch command span.
- **150°** combined left/right wing command span.
- **35°** beak command span.
- **55°** tail command span.
- **35°** body-lean command span.
- **0.75 s** firmware brain-heartbeat watchdog before the body controller latches the stop state and disables servo power.

The standard motion library currently contains:

- blink: 0.20 s;
- happy greeting: 0.80 s;
- dance: 1.05 s.

## Electrical simulation assumptions

The current reference assumption set uses eight 6 V micro servos with nominal placeholder currents of 0.12 A idle, 0.35 A moving and 0.80 A peak each. It also assumes 10 W typical / 25 W peak compute consumption.

From those placeholders, the model produces:

- servo idle budget: **5.76 W**;
- all-servo moving budget: **16.8 W**;
- servo peak budget: **38.4 W**;
- combined typical motion + compute: **26.8 W**;
- combined peak design check: **63.4 W**.

These are **not hardware measurements and not final PSU specifications**. Real stall current and transient behavior must be measured on the selected actuator model; production power sizing then needs margin beyond the measured worst credible case.

## What ParrotCore is intended to achieve

### 1. A reusable robot "brain cartridge"

The same high-level AI/runtime can move between different bird shells. Each shell supplies a body profile that maps semantic joints and sensors to its own hardware. This reduces redesign work and creates a platform rather than a one-off toy.

### 2. An expressive physical AI agent

The bird can combine gaze, head posture, wings, beak, eyelids, tail and body lean into readable non-verbal behavior. The goal is not industrial manipulation; it is social presence, attention, teaching and interaction.

### 3. Teach-by-demonstration behavior

The existing persistent association system is the first layer. The target is to let a user teach a trigger, phrase, visual object, gesture or sequence and bind it to speech, pose, movement or a constrained skill without rewriting firmware.

### 4. Local-first speech, vision and memory

The architecture keeps cloud services optional. The target v1 system should be able to see, hear, respond, remember explicitly permitted facts and execute whitelisted body skills on the local compute cartridge.

### 5. Safe separation between AI and motors

The AI process does not own raw servo pulses. The ESP32-S3 remains the real-time authority for travel limits, E-stop state, watchdog and servo-power enable. A crashed or stalled high-level process therefore does not automatically retain motor control.

### 6. A robotics education/research platform

Because body profiles, behaviors, perception modules and memory are separable, the same platform can support robotics teaching, embodied-AI experiments, child-safe supervised demonstrations, museum/retail characters and hobbyist robot shells.

### 7. A foundation for a family of robots

If the cartridge/body interface is stabilized, ParrotCore can become a reference architecture for multiple birds or other small expressive creatures: one software ecosystem, multiple physical embodiments.

## What it does not achieve yet

- no validated production mechanics;
- no measured actuator torque/current/noise/thermal data;
- no autonomous vision pipeline yet;
- no local speech-recognition/TTS loop yet;
- no general language-model planner connected to the skill whitelist yet;
- no battery endurance figure;
- no child/product safety certification;
- no manufacturing-ready custom CM5 carrier or production enclosure.

Those are development milestones, not features that should be claimed today.

## Validation criteria for the physical prototype

The first three-axis neck/beak bench rig should not graduate to the full body until it passes:

1. repeatable homing and calibrated travel limits;
2. E-stop cut-off under motion;
3. watchdog cut-off after brain-link interruption;
4. measured no-load and loaded current per actuator;
5. measured peak regulator temperature;
6. no mechanically induced joint collision across the allowed pose envelope;
7. acceptable backlash and acoustic noise;
8. stable serial command/telemetry operation for an extended run.
