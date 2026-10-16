# Changelog

## 0.5.2 — Fault accounting and safety-response correction — 2026-08-16

### Corrected
- fault counts now distinguish discrete rising-edge episodes from active telemetry-frame duration;
- nominal validation is separated from deliberate fault injection;
- watchdog loss now inhibits motion and latches actuator power off;
- overtemperature latches actuator power off;
- overcurrent records the detected transient then latches the actuator rail off;
- proximity inhibits movement without falsely reporting a power shutdown;
- Dynamics Lab labels injections as deliberate safety tests and exposes latch/power state;
- repository-root pytest no longer depends on external PYTHONPATH setup.

### Validation
- 52/52 automated tests pass;
- nominal hardware-grounded behavior produces zero fault episodes;
- safety demo produces exactly three intended injected episodes;
- all-servo-stall probe produces one stall episode and one overcurrent episode, then actuator power remains off;
- corrected safety-validation metrics report overall PASS.

## 0.5.1 - Datasheet-grounded V1 hardware baseline - 2026-08-16

### Added
- exact Parrot V1 component baseline with primary-source register;
- per-joint Feetech STS3215/ST-3036 actuator assignment;
- HardwareBaseline loader and derived electrical calculations;
- hardware-grounded DynamicsSimulator mode;
- 3S battery + dual regulated rail architecture;
- 12A simulated servo-rail current fault threshold;
- v0.5.1 hardware benchmark JSON;
- Feetech smart-servo packet codec with manufacturer protocol test vectors;
- smart-servo migration, power-model and hardware-baseline documentation;
- revised BOM and smart-bus pinout.

### Engineering findings
- selected eight-servo theoretical stall current is 13.6A @6V;
- selected servo regulator is 15A class with thermally dependent continuous capability;
- sustained all-servo stall is therefore prohibited/faulted rather than designed as an operating point;
- previous PWM ESP32 implementation is legacy for Parrot V1 because selected servos use half-duplex TTL serial.

### Validation
- full suite: 44/44 tests pass;
- Dynamics Lab v0.5.1 HTTP smoke test passes;
- PING, READ and goal-position Feetech packets match manufacturer protocol examples.

## 0.5.0 — Dynamics, telemetry and fault simulation — 2026-08-16

### Added
- quintic trajectory planner;
- per-joint speed, acceleration and jerk constraints;
- automatic minimum-duration calculation;
- telemetry model for positions, velocities, servo currents, rail current, system power, temperature, IMU, ToF, touch, stability and faults;
- current/power/thermal actuator proxy;
- stability and collision proxies;
- explicit fault injection object;
- watchdog, servo-stall, proximity, overtemperature and overcurrent fault handling;
- browser Dynamics Lab;
- v0.5 dynamics/fault MP4 and GIF;
- telemetry CSV;
- cross-species dynamics benchmark JSON;
- 11 additional dynamics/fault tests.

### Validation
- full suite: 32/32 tests pass;
- Dynamics Lab HTTP smoke test passes;
- all three reference creatures surface intended fault probes;
- normal benchmark surfaces zero simulated fault frames.

## 0.4.0 — Multi-Embodiment Core — 2026-08-16

### Added
- species-agnostic semantic intent layer;
- `ExpressionCompiler` and `CreatureRegistry`;
- Parrot, Owl and Raven reference profiles;
- species-specific conceptual kinematics;
- Creature Lab;
- side-by-side comparison render;
- GLB/STL conceptual models;
- project decision/product/engineering documentation.

### Compatibility
- `ParrotBrain` retained;
- `EmbodiedBrain` alias added;
- legacy named motions remain executable;
- original v0.1-v0.3 tests remain green.
