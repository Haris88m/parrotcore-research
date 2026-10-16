# ParrotCore Hardware Standard v0.5.1

## Objective

Define a reusable electronics core that can inhabit multiple robotic creature bodies while keeping physical safety independent from high-level AI. Parrot is the first hardware reference; Owl/Raven remain software/digital-twin references.

## Compute cartridge

### Linux compute

**Raspberry Pi Compute Module 5** is the Parrot V1 reference compute SOM. Target configuration is a wireless 8GB RAM / 32GB eMMC class module. The cartridge carrier remains custom work; a development carrier may be used for bench bring-up.

The AI software must remain able to boot and perform core control without a cloud API or external NPU. Hardware acceleration may be added later.

### Body MCU

**ESP32-S3-WROOM** is the real-time/safety controller family.

Responsibilities:

- physical E-stop input and latch;
- independent Linux-heartbeat watchdog;
- servo-rail enable/disable;
- logical joint range checking;
- calibrated raw servo range checking;
- half-duplex smart-servo bus transport;
- servo status/current/temperature polling where supported;
- IMU/ToF/touch/power-sensor acquisition;
- deterministic fault escalation and safe-state entry;
- telemetry back to the Linux brain.

High-level AI never owns servo power directly.

## Parrot V1 actuator bus

Parrot V1 selects **Feetech half-duplex TTL smart serial servos** rather than eight independent PWM channels.

| Servo ID | Joint | Model | Logical range |
|---:|---|---|---:|
| 1 | neck_yaw | ST-3215-C001 / STS3215 | -60..+60 deg |
| 2 | neck_pitch | ST-3215-C001 / STS3215 | -35..+40 deg |
| 3 | beak | ST-3036-C001 | 0..35 deg |
| 4 | wing_left | ST-3215-C001 / STS3215 | 0..75 deg |
| 5 | wing_right | ST-3215-C001 / STS3215 | 0..75 deg |
| 6 | tail_pitch | ST-3036-C001 | -20..+35 deg |
| 7 | eyelids | ST-3036-C001 | 0..100 logical units |
| 8 | body_lean | ST-3215-C001 / STS3215 | -15..+20 deg |

**Logical limits are not raw actuator limits.** Each physical mechanism must be calibrated to establish servo center, direction, safe raw endpoints and linkage ratio before it can be enabled.

The historical MCPWM code is retained only as a generic/PWM bench reference. See `docs/SMART_SERVO_MIGRATION_V051.md`.

## Perception/sensor baseline

- Raspberry Pi Camera Module 3 Wide -> Linux compute CSI vision input.
- 2x TDK T5848 -> I2S microphones.
- ICM-42688-P -> 6-axis body IMU.
- VL53L8CX -> 8x8 near-field depth/obstacle input.
- CAP1298 -> capacitive touch/proximity electrodes.
- 2x INA228 -> battery-rail and servo-rail electrical telemetry.

Sensor placement is not final until mechanical CAD and acoustic/field-of-view tests exist.

## Audio baseline

- MAX98357A I2S Class-D amplifier.
- PUI AS04004PO-2-WR-R 4ohm / 3W rated speaker.

The amplifier can exceed the speaker's continuous rating under some conditions, so software gain/volume limits and physical acoustic testing are required.

## Power architecture

```text
3S LiPo (11.1V nominal)
       |
       +-- master protection / current measurement
       |
       +-- 6V / 15A regulator --> independent servo rail safety switch --> 8 smart servos
       |
       +-- 5V / 9A regulator  --> CM5 + camera + digital audio + logic/peripherals
```

Current manufacturer-derived actuator endpoints:

- no-load-running aggregate: 1.14A @6V;
- theoretical all-stall aggregate: 13.6A @6V;
- simulated software overcurrent threshold: 12A;
- selected servo regulator nominal rating: 15A, with thermal/input-voltage dependency.

All-stall is a **fault envelope**, not an operating target.

## Minimum physical safety requirements

A moving prototype must have all of the following before full-body motion:

1. hardware current protection on the servo rail;
2. physical E-stop able to de-energize actuator power without Linux cooperation;
3. ESP32 heartbeat timeout that de-energizes/rejects motion;
4. calibrated per-joint logical and raw limits;
5. mechanical hard stops where practical;
6. independent rail current/voltage monitoring;
7. safe LiPo charging/storage procedure outside the robot design;
8. wire/connectors sized from measured current, not from average simulator current;
9. CM5 thermal management validated in the final enclosure;
10. no high-current actuator power through Raspberry Pi GPIO/header paths.

## Smart-bus electrical boundary

Reference ESP32 pins are recorded in `board/PARROTCORE_PINOUT.csv`, but the half-duplex TTL line requires a direction-controlled external interface/buffer. The exact buffer/transceiver, pull-up/termination and connector topology remain open until bench signal-integrity testing.

## Physical bring-up sequence

1. Build only neck yaw + neck pitch + beak on a rigid bench fixture.
2. Commission each smart servo separately and assign/check its ID.
3. Establish raw center/direction/endpoint calibration with actuator torque unloaded or mechanically constrained safely.
4. Verify physical E-stop and rail enable with actuator power disconnected first.
5. Connect current monitoring and record idle/no-load movement current.
6. Validate heartbeat/watchdog shutdown by deliberately stopping brain traffic.
7. Test one joint at a time under representative load and record current, temperature, speed, backlash and acoustic noise.
8. Calculate actual torque margin using measured linkage geometry/load moments.
9. Only after acceptance, add wings/tail/body mechanisms progressively.

## Evidence policy

Manufacturer specifications and arithmetic derived from them are allowed to seed the digital twin. They are never relabeled as measured results. `hardware/v1_component_baseline.toml` is the canonical machine-readable source for V1 component parameters and modeling assumptions.
