# ParrotCore Project State — v0.5.2

**Project:** Project AI robots / ParrotCore  
**Checkpoint date:** 16 August 2026  
**Status:** species-agnostic embodied-AI runtime; Parrot V1 datasheet-grounded component baseline; corrected safety/fault semantics; physical mechanics and hardware safety still unvalidated.

## Architecture

```text
local cognition / lessons / future perception
                 |
          semantic intent
                 |
        ExpressionCompiler
                 |
          BodyProfile
                 |
        trajectory planner
                 |
   safety / telemetry / fault policy
                 |
 simulator OR FeatherBus to ESP32
                 |
       calibrated actuator bus
```

Parrot remains Robot #1. Owl and Raven remain comparison embodiments. Only Parrot currently has a selected V1 hardware baseline.

## Historical checkpoints

- **v0.5.0:** constrained trajectories, telemetry, collision/stability proxies and fault injection.
- **v0.5.1:** first datasheet-grounded Parrot V1 component/electrical baseline and Feetech smart-servo migration.
- **v0.5.2:** fault-episode accounting and safety-response correction.

## V1 hardware baseline — unchanged from v0.5.1

Selected reference parts include:

- Raspberry Pi Compute Module 5;
- ESP32-S3-WROOM target MCU;
- 5x Feetech STS3215-class smart servos;
- 3x Feetech ST-3036-class smart servos;
- 3S 11.1 V 2200 mAh LiPo;
- Pololu 6 V / 15 A servo regulator;
- Pololu 5 V / 9 A compute regulator;
- Camera Module 3 Wide;
- 2x TDK T5848 microphones;
- MAX98357A amplifier + PUI 4-ohm/3 W speaker;
- ICM-42688-P IMU;
- VL53L8CX ToF;
- CAP1298 touch controller;
- 2x INA228 power monitors.

## Hardware-grounded endpoints

| Quantity | V1 value |
|---|---:|
| Selected actuator mass | 328.1 g |
| Aggregate servo no-load-running current | 1.14 A @ 6 V |
| Aggregate theoretical all-stall current | 13.6 A @ 6 V |
| Theoretical all-stall servo power | 81.6 W |
| CM5 typical operation power reference | 4.5 W |
| Battery nominal energy | 24.42 Wh |
| Servo regulator nominal rating | 15 A @ 6 V |
| Simulated servo-current trip threshold | 12 A |

These are manufacturer specifications or direct arithmetic from them, except the 12 A threshold, which is a project safety setting.

## v0.5.2 fault correction

Historical v0.5.1 animation metrics counted active telemetry frames. This made three injected conditions appear as dozens of faults.

v0.5.2 distinguishes:

- **fault episodes** = rising-edge events;
- **active fault frames** = duration.

The corrected safety-validation run reports:

### Nominal phase

- fault episodes: **0**;
- active fault frames: **0**;
- result: **PASS**.

### Deliberate injection phase

- neck-yaw stall episodes: **1**;
- proximity episodes: **1**;
- watchdog-loss episodes: **1**;
- distinct deliberately injected episodes: **3**.

The corresponding active-frame counts are duration only and are not treated as separate failures.

## Safety response

v0.5.2 now models response as well as detection:

- proximity: motion inhibited, rail remains available;
- watchdog: all motion inhibited, actuator rail off, safety latched;
- overtemperature: actuator rail off, safety latched;
- overcurrent: transient retained for diagnosis, rail latched off for subsequent frames;
- explicit safety reset required after a latched shutdown.

## Validation

**52 / 52 automated Python tests pass.**

Additional validation:

- clean repository-root `pytest -q`: PASS;
- nominal hardware-grounded benchmark: zero fault episodes;
- all-servo-stall probe: one `servo_stall` + one `overcurrent` episode, rail latched off;
- corrected safety-validation metrics: PASS;
- corrected MP4 container validation with ffprobe: PASS.

## Evidence classes

1. manufacturer specification;
2. derived from manufacturer specification;
3. engineering model/allowance;
4. measured prototype data.

Category 4 remains empty for V1.

## Hard physical boundary

Still unvalidated:

- actual linkage torque and load;
- raw servo centers/directions/end stops;
- movement/stall transient current;
- smart-bus signal integrity;
- eFuse/load-switch/E-stop circuit;
- actual watchdog cutoff time;
- regulator thermals;
- battery sag/runtime/charging safety;
- complete mass/center of gravity;
- true collision/perch stability;
- actuator backlash/noise/lifetime;
- microphone/speaker acoustics;
- sensor accuracy and enclosure effects;
- CM5 thermal solution;
- ESP32 smart-bus firmware build/flash;
- regulatory/product safety requirements.

## Next milestone

Software: **v0.6 perception and attention**.  
Parallel physical gate: **neck-yaw + neck-pitch + beak smart-servo bench rig** with raw calibration, INA228 measurements, watchdog shutdown and independent physical E-stop validation.
