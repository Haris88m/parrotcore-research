# Autonomous Development Roadmap

## Completed — v0.1 software spine
Simulator, SafetyGate, deterministic skills, persistent teaching memory, FeatherBus contract, MCU scaffold.

## Completed — v0.2 body interface
TOML body profiles, serial FeatherBus body driver, ESP32-S3 servo/safety baseline, browser control/teaching surface.

## Completed — v0.3 Parrot digital twin
8-DOF conceptual kinematics, browser 3D Studio, MP4/GIF/GLB/STL outputs, effectiveness assumptions.

## Completed — v0.4 multi-embodiment core
Semantic intent layer, ExpressionCompiler, CreatureRegistry, Parrot/Owl/Raven profiles and kinematics, Creature Lab, comparison animation, project ledger, 21 tests.

## Completed — v0.5 dynamics + telemetry + faults
Quintic trajectories, speed/acceleration/jerk constraints, current/power/temperature model, telemetry schema, stability/collision proxies, watchdog/stall/proximity/overtemperature/overcurrent injection, Dynamics Lab, 32 tests.

## Completed - v0.5.1 datasheet-grounded Parrot V1 baseline
Selected real actuator/compute/power/vision/audio/sensor parts, 3S dual-rail power architecture, hardware data loader, per-joint servo electrical endpoints, smart-servo packet codec, updated BOM/pinout, hardware-grounded Parrot dynamics, 44 tests. Physical measurements remain pending.


## Completed - v0.5.2 fault accounting and safety response

- discrete rising-edge fault episode counting;
- separate active-frame duration statistics;
- nominal versus deliberate fault-injection reporting;
- explicit actuator-power/motion-inhibit/safety-latch telemetry;
- watchdog, overtemperature and overcurrent latch semantics;
- proximity motion inhibition;
- 52-test regression suite;
- corrected safety-validation MP4/GIF/CSV/JSON;
- Dynamics Lab safety-state smoke test.

## Next — v0.6 perception + attention
- camera abstraction;
- synthetic/replay vision source;
- person/object detections;
- target-selection/attention state;
- gaze controller using semantic intent rather than raw joints;
- audio VAD/wake-word interface;
- local STT adapter contract;
- touch event input;
- deterministic perception replay fixtures.

## v0.7 local cognition + speech
- pluggable local model adapter;
- planner restricted to whitelisted semantic actions;
- explicit memory retention policy;
- local TTS adapter;
- speech-driven beak trajectories.

## v0.8 skill authoring
- pose/timeline editor;
- demonstration recording;
- trigger builder;
- validated skill-package import/export;
- signing metadata.

## v0.9 physical bench prototype
- neck yaw + neck pitch + beak only;
- real calibration and current sensing;
- physical E-stop and watchdog validation;
- collision/backlash/noise measurements;
- add remaining actuators only after bench acceptance.

## v1.0 reusable cartridge
Production compute carrier, standardized body connector, signed updates, recovery diagnostics, manufacturing test mode, compliance envelope and creature SDK.
