# Engineering Log — 16 August 2026

## Objective

Continue ParrotCore autonomously after deciding that Parrot remains the first robot but the technology must support other creatures.

## Work completed

1. Copied the v0.3 working baseline into a versioned v0.4 project folder.
2. Preserved v0.3 firmware, FeatherBus, Windows scripts and safety runtime.
3. Extended `BodyProfile` with species, morphology, role, capabilities, semantic expressions and simulation metadata.
4. Added load-time rejection for expression references to unknown joints and out-of-limit positions.
5. Implemented `SemanticIntent`, `ExpressionCompiler` and `CreatureRegistry`.
6. Converted built-in behavior selection from parrot-specific servo commands to semantic motion metadata.
7. Preserved the old `motion` action API after a compatibility test identified a regression.
8. Added the explicit `EmbodiedBrain` alias while retaining `ParrotBrain` for existing code.
9. Added simulated runtime factories for arbitrary profiles.
10. Added Owl and Raven body profiles beside the Parrot reference profile.
11. Added species-specific kinematic providers for Parrot, Owl and Raven.
12. Added generic creature effectiveness metrics.
13. Added a local browser Creature Lab with species switching, semantic behaviors, joint sliders, teaching memory and E-stop controls.
14. Added side-by-side MP4/GIF multi-creature simulation.
15. Added conceptual GLB/STL home models for all three creatures.
16. Added eight v0.4 embodiment tests.
17. Ran the complete suite: **21/21 tests passed**.

## Defect found and resolved

**Issue:** v0.3 `test_builtin_greeting_moves` required a `motion` action, but the first v0.4 implementation emitted a new `express` action.  
**Resolution:** retain `motion` as the API action kind and add a `semantic` field. The brain routes semantic motions through `ExpressionCompiler`; legacy motion names without the field still use the v0.3 motion library.  
**Result:** backward compatibility restored without abandoning the new abstraction.

## Current hard boundary

No physical hardware is connected in this environment. Therefore these remain unvalidated:

- servo torque;
- actual current draw;
- linkage collisions;
- acoustic motor noise;
- thermal behavior;
- battery endurance;
- center-of-mass stability;
- camera/microphone placement;
- physical E-stop wiring;
- ESP-IDF compilation/flashing on target hardware.

## Next implementation target

v0.5: motion dynamics + telemetry + fault injection. This is the layer required before perception can safely command real mechanics.

---

# Continuation — v0.5

## Work completed after v0.4 checkpoint

1. Promoted the working v0.4 tree into v0.5.
2. Extended `JointSpec` with speed, acceleration and jerk envelopes.
3. Implemented a quintic `TrajectoryPlanner` that extends unsafe requested durations automatically.
4. Added trajectory samples with position, velocity, acceleration and jerk.
5. Added `TelemetryFrame` and `FaultKind` models.
6. Implemented simulated current, power and servo-temperature estimates.
7. Added IMU, ToF and touch telemetry values.
8. Added a center-of-mass/perch stability proxy.
9. Added a conceptual floor/self-collision proxy.
10. Added explicit fault injection for watchdog loss, servo stall, close proximity, overtemperature, extra load and all-servo stall.
11. Added simulated overcurrent classification.
12. Added an interactive browser Dynamics Lab.
13. Ran a live Dynamics Lab HTTP smoke test, including Raven behavior and watchdog-loss fault propagation: PASS.
14. Added a Parrot dynamics/fault MP4, GIF and CSV telemetry output.
15. Added a cross-species dynamics benchmark and fault probe.
16. Normal benchmark surfaced zero fault frames for Parrot, Owl and Raven.
17. All three species surfaced expected watchdog, proximity, overtemperature and all-servo-stall fault probes.
18. Added 11 v0.5 tests; full suite is now **32/32 passing**.
19. Added master project documentation and v0.5 dynamics documentation.

## v0.5 simulated normal benchmark

- Owl: max rail current 1.23 A; max system power 17.39 W; minimum stability proxy 24.1 mm.
- Parrot: max rail current 1.41 A; max system power 18.47 W; minimum stability proxy 19.5 mm.
- Raven: max rail current 1.42 A; max system power 20.53 W; minimum stability proxy 14.8 mm.

All values above are model outputs based on assumptions, not hardware measurements.

## Next engineering objective

v0.6 will introduce perception/attention interfaces with replayable synthetic inputs. Perception will output semantic targets and remain downstream of the v0.5 trajectory/safety boundary.

---

## v0.5.1 - hardware-grounding pass

### Objective
Replace generic electrical simulation assumptions with an actual purchasable Parrot V1 baseline without pretending mechanical performance has been measured.

### Work completed
- selected exact reference servos, compute, battery, regulators, camera, microphones, audio, IMU, ToF, touch and power monitors;
- captured official manufacturer source URLs and evidence classes;
- added `HardwareBaseline` loader;
- mapped five high-load joints to STS3215 and three compact joints to ST-3036;
- changed Parrot Dynamics Lab to use the hardware baseline;
- derived 328.1g actuator mass, 1.14A aggregate no-load-running current and 13.6A aggregate stall current;
- selected 3S power source because the high-current 6V regulator needs more input margin than a discharged 2S pack can reliably provide at heavy load;
- selected separate 6V servo and 5V compute rails;
- set simulated servo current fault threshold to 12A;
- detected PWM-vs-smart-servo firmware mismatch and formally deprecated PWM as the Parrot V1 transport;
- implemented Feetech packet encoding and manufacturer protocol examples as tests;
- updated BOM, reference pinout, validation report and project records.

### Test status
44/44 Python tests pass. Dynamics Lab HTTP smoke test passes with hardware-grounded Parrot electrical endpoint data.

### Major unresolved engineering risk
The actuator selection is **not mechanically proven** until linkage moments are known. Rated/stall torque specifications cannot establish adequacy without actual lever arms, moving masses, acceleration targets, friction and shock loads. Physical neck-yaw/neck-pitch/beak bench calibration remains mandatory before full-body actuation.


## v0.5.2 - fault semantics correction

1. Investigated the apparent high fault count in the v0.5.1 safety render.
2. Determined that 16 stall + 29 proximity + 11 watchdog values were active telemetry-frame durations, not independent fault events.
3. Added rising-edge fault episode analysis.
4. Separated nominal validation from deliberate injection.
5. Added explicit actuator-power, motion-inhibit, safety-latch and safety-reason telemetry fields.
6. Corrected watchdog behavior to inhibit motion and latch actuator power off.
7. Corrected overtemperature behavior to latch actuator power off.
8. Corrected overcurrent behavior to preserve the detected transient and remove actuator power on subsequent samples.
9. Corrected proximity behavior to inhibit movement without unnecessarily latching power.
10. Added explicit safety reset semantics.
11. Updated Dynamics Lab UX to label injected tests and show latch/power state.
12. Added repository-local test path bootstrap.
13. Expanded automated suite from 44 to 52 tests: PASS.
14. Nominal hardware benchmark: zero fault episodes.
15. Deliberate safety demo: exactly three expected episodes, all response checks PASS.
16. Dynamics Lab HTTP safety-state smoke test: PASS.
