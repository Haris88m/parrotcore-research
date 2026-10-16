# ParrotCore Master Project Documentation

## 1. Mission

Build a modular embodied-AI platform whose cognition can inhabit multiple expressive creature bodies. The first reference product remains a robotic Parrot, but the underlying technology is not restricted to parrots.

## 2. Product architecture

```text
Perception / local speech / future planner
                 |
        constrained semantic intent
                 |
           Skill / Lesson layer
                 |
          ExpressionCompiler
                 |
            BodyProfile
                 |
      trajectory + safety layers
                 |
        BodyDriver / FeatherBus
                 |
        ESP32-S3 body controller
                 |
     actuators / sensors / E-stop
```

The design principle is that **AI intent must not contain raw servo assumptions**.

## 3. Reference embodiments

### Parrot
Robot #1. Primary identity: talking/family companion. Talking is semantically natural for the creature, making speech the strongest initial product story.

### Owl
Comparison body. Primary identity: teaching/learning companion. Current conceptual model emphasizes wide head rotation and expressive eye/head behavior.

### Raven
Comparison body. Primary identity: developer/research companion. Current conceptual model emphasizes sharper head/body/tail choreography and a more technical product character.

## 4. Version history

### v0.1 — software spine
- simulated body;
- SafetyGate;
- deterministic skills;
- teaching memory;
- FeatherBus definition;
- MCU firmware scaffold.

### v0.2 — physical body interface
- TOML body profiles;
- FeatherBus serial driver;
- ESP32-S3 actuator/safety baseline;
- watchdog and E-stop contract;
- browser control surface.

### v0.3 — Parrot digital twin
- eight-joint conceptual Parrot kinematics;
- 3D browser Studio;
- MP4/GIF motion simulation;
- GLB/STL conceptual geometry;
- profile-derived effectiveness assumptions.

### v0.4 — multi-embodiment platform
- species/morphology metadata;
- CreatureRegistry;
- SemanticIntent vocabulary;
- ExpressionCompiler;
- Parrot/Owl/Raven profiles;
- three kinematic providers;
- Creature Lab;
- side-by-side digital-twin animation;
- architecture decision and project ledgers;
- 21/21 tests passing.

### v0.5 - trajectory dynamics and fault simulation
- quintic trajectory planner;
- speed/acceleration/jerk limits;
- telemetry schema;
- current/power/thermal estimates;
- IMU/ToF/touch simulation values;
- stability proxy;
- collision proxy;
- watchdog/stall/proximity/overtemperature/overcurrent injection;
- Dynamics Lab;
- dynamics MP4/GIF and CSV telemetry;
- cross-species benchmark;
- 32/32 tests passing.

### v0.5.1 - datasheet-grounded Parrot V1 hardware baseline
- selected exact V1 compute, actuator, battery, regulator, camera, audio and sensor components;
- hardware source register with evidence classification;
- 5x Feetech STS3215 + 3x ST-3036 actuator map;
- HardwareBaseline loader and real manufacturer electrical endpoint integration;
- 3S dual-rail power architecture;
- 13.6A theoretical all-stall current recognized as a fault envelope against a 15A-class servo regulator;
- 12A simulated current threshold;
- Feetech half-duplex packet codec and manufacturer-example tests;
- PWM firmware marked legacy for selected Parrot V1;
- 44/44 tests passing.

## 5. Current validation status

### Verified in software
- safety limit rejection;
- E-stop latch behavior in simulator;
- FeatherBus encoding/decoding;
- persistent teaching association behavior;
- thread-safe SQLite access path;
- serial driver validates before writes;
- all three profiles load;
- same semantic intent compiles into species-specific joints;
- profile expressions are range-checked at load time;
- three digital-twin kinematic providers execute;
- trajectory endpoints and dynamic limits are tested;
- fault injection surfaces intended codes;
- Creature Lab HTTP smoke test passes;
- Dynamics Lab HTTP smoke test passes;
- 44/44 automated tests pass.

### Not yet physically validated
- actuator torque and speed under load;
- servo backlash;
- gear/linkage lifetime;
- true current and peak power;
- regulator/battery behavior;
- temperature under sustained duty;
- motor/acoustic noise;
- actual center of mass;
- real collision geometry;
- perch/grip stability;
- sensor accuracy;
- microphone/speaker feedback;
- camera placement and field of view;
- ESP32 firmware build/flash on the intended board;
- electrical EMC/ESD/safety requirements;
- child/product compliance requirements.

### Hardware evidence status at v0.5.1
Parrot electrical endpoint data is now tied to selected manufacturer parts. Dynamic current, thermal response, full mass, center of gravity, torque adequacy and runtime remain models until measured. Owl and Raven still use conceptual electrical parameters. See `docs/HARDWARE_BASELINE_V051.md`.

## 6. Current effective-property interpretation

The digital twin is useful for comparing architecture choices before hardware exists. It is **not** a source of certified performance numbers.

Current modeled behavior indicates:

- Owl has the widest head-yaw envelope (220°).
- Parrot has the widest combined wing command span (150°) and largest beak travel (35°).
- Raven has the largest modeled target height and the smallest current stability-margin proxy during the normal benchmark.
- All three can express the same semantic behavior vocabulary despite different joint names and motion profiles.

## 7. Safety philosophy

1. AI does not directly generate PWM.
2. High-level AI should only invoke constrained semantic skills/actions.
3. Software profile limits are checked before the serial body driver writes.
4. MCU firmware must independently validate commands.
5. Loss of brain heartbeat must disable actuator power.
6. A physical emergency stop must remain independent of high-level AI.
7. A complete moving body should not be assembled until a reduced bench rig validates actuators, current, limits and E-stop behavior.

## 8. Next build sequence

### v0.6 — perception and attention interfaces
- camera abstraction and synthetic camera events;
- person/object event model;
- gaze-target controller;
- audio VAD/wake-word interface;
- local STT adapter contract;
- touch events;
- perception replay fixtures for deterministic tests.

### v0.7 — local cognition and speech
- local model adapter;
- planner restricted to whitelisted semantic actions;
- retention-controlled episodic memory;
- local TTS adapter;
- speech-driven beak trajectory.

### v0.8 — skill authoring
- timeline editor;
- demonstration recording;
- skill schema validation;
- package signing metadata.

### v0.9 — physical bench prototype
Start only with neck yaw, neck pitch and beak. Add measured calibration, current sensing and physical E-stop before adding wings/tail/body mechanics.

### v1.0 — reusable cartridge
Production compute carrier, body connector standard, signed updates, recovery mode, manufacturing tests and public SDK.

## 9. Canonical project records

- `PROJECT_STATE.md`
- `PROJECT_LEDGER.json`
- `CHANGELOG.md`
- `docs/DECISION_LOG.md`
- `docs/EMBODIMENT_CONTRACT.md`
- `docs/DYNAMICS_TELEMETRY_FAULTS_V05.md`
- `docs/HARDWARE_BASELINE_V051.md`
- `docs/POWER_MODEL_V051.md`
- `docs/SMART_SERVO_MIGRATION_V051.md`
- `hardware/SOURCE_REGISTER.md`
- `docs/ENGINEERING_LOG_2026-08-16.md`
- `docs/ROADMAP.md`

These files take precedence over older conversational descriptions when they conflict with the latest implemented checkpoint.


### v0.5.2 - fault accounting and safety-response correction

The v0.5.1 rendered fault demo used per-frame fault counts. v0.5.2 corrects this by reporting rising-edge episodes separately from active-frame duration. Nominal validation and deliberate injection are separated. Watchdog and overtemperature now latch simulated actuator power off; overcurrent records the trip transient then latches off; proximity inhibits movement without a power latch. Clean repository-root tests pass 52/52. See `FAULT_MODEL_CORRECTION_V052.md` and `VALIDATION_REPORT_V052.md`.
