# ParrotCore v0.5.2 - Species-Agnostic Embodied AI Robotics Platform

A research project by Haris Mekic, published through [MEKreflect](https://mekreflect.pages.dev/). Read [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) for the source-export boundary and current installation checks.

ParrotCore is a local-first robotics research prototype built around a reusable semantic behavior runtime. **Parrot remains Robot #1**, while Owl and Raven demonstrate the same software behavior interface mapped to different creature actuator layouts in simulation.

The current teaching system stores trigger-response associations and executes declarative rules. It does not train a foundation model. Speech, vision and local language-model integration remain future work; this repository does not establish a deployed robot or measured hardware performance.

v0.5.2 is a corrective safety-model release built on the datasheet-grounded Parrot V1 component baseline introduced in v0.5.1. It separates nominal behavior from deliberate fault injection and counts discrete fault episodes correctly.

## System flow

```text
AI / lessons / future perception
            |
      semantic intent
            |
   ExpressionCompiler
            |
      CreatureProfile
            |
   TrajectoryPlanner
            |
 safety + telemetry + faults
            |
 simulator / FeatherBus
            |
      ESP32-S3 body MCU
            |
 calibrated smart-servo bus
```

## What works now

- Parrot, Owl and Raven under one semantic behavior system;
- persistent trigger-response teaching memory;
- creature-specific greeting, attention, blink, curiosity, affirmation and dance;
- conceptual 3D digital twins;
- constrained quintic trajectories;
- speed/acceleration/jerk limits;
- telemetry and fault injection;
- **Parrot V1 HardwareBaseline** with selected servos, compute, battery, regulators, camera, audio and sensors;
- hardware-grounded per-joint servo current endpoints in Parrot dynamics;
- manufacturer-derived 13.6A all-stall envelope and 12A software current fault threshold;
- Feetech half-duplex smart-servo packet codec;
- browser Creature Lab and v0.5.2 Dynamics Lab;
- FeatherBus physical-body boundary;
- 52/52 automated tests reported in the recorded v0.5.2 validation. Run the test commands below to verify your checkout; this is not a new test result.

## Start on Windows

Run once:

```text
01_SETUP_WINDOWS.bat
```

Then use:

```text
05_RUN_CREATURE_LAB.bat
06_RUN_DYNAMICS_LAB.bat
07_HARDWARE_REPORT.bat
```

Dynamics Lab uses the V1 hardware electrical baseline for **Parrot**. Owl and Raven still use conceptual electrical assumptions. `07_HARDWARE_REPORT.bat` prints the selected V1 component endpoints and evidence warnings without starting a simulator.

## v0.5.2 corrected safety outputs

- `simulation/outputs/parrotcore_v052_safety_validation_demo.mp4`
- `simulation/outputs/parrotcore_v052_safety_validation_demo.gif`
- `simulation/outputs/parrotcore_v052_safety_validation_metrics.json`
- `simulation/outputs/parrotcore_v052_safety_validation_telemetry.csv`
- `simulation/outputs/v052_hardware_grounded_benchmark.json`

Historical v0.5/v0.5.1 outputs remain in the folder for reproducibility; see `simulation/outputs/README.md` before interpreting their `fault_frame_counts`.

## CLI

Both normal and editable installations include the default creature profiles and hardware baseline. The editable command below is convenient for development; `python -m pip install .` installs a normal wheel. See `PUBLIC_RELEASE.md` for the release boundary and fresh local checks.

```bash
pip install -e .
parrotcore demo
parrotcore shell --species parrot
parrotcore creature-lab
parrotcore dynamics-lab
```

Tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Read documentation in this order

1. `PROJECT_STATE.md`
2. `docs/FAULT_MODEL_CORRECTION_V052.md`
3. `docs/VALIDATION_REPORT_V052.md`
4. `docs/HARDWARE_BASELINE_V051.md`
5. `docs/POWER_MODEL_V051.md`
6. `docs/SMART_SERVO_MIGRATION_V051.md`
7. `hardware/SOURCE_REGISTER.md`
8. `docs/MASTER_PROJECT_DOCUMENTATION.md`
9. `docs/DECISION_LOG.md`
10. `docs/ROADMAP.md`
11. `PROJECT_LEDGER.json`

## Evidence boundary

Some parameters are now real **manufacturer specifications** or arithmetic derived from them. Dynamic load, thermal response, total mass, center of gravity, torque adequacy and runtime are still models. There are **no V1 measured prototype values yet**.

Physical motion remains calibration-gated. The first hardware acceptance rig is neck yaw + neck pitch + beak with real current sensing, smart-bus calibration, watchdog and independent E-stop validation.

## GitHub development model

`Haris88m/AI-robotics` is the canonical development repository from v0.5.2 onward. Generated media is produced by GitHub Actions and retained as workflow artifacts rather than committed binary source. Development proceeds through `develop` and feature branches, with `main` reserved for validated checkpoints.
