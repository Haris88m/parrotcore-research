# Smart-servo migration - v0.5.1

## Why this migration exists

ParrotCore v0.2-v0.5 used an ESP32 MCPWM reference implementation because the actuator family had not yet been selected. The V1 hardware baseline now selects Feetech ST-3215-C001/STS3215 and ST-3036-C001 smart serial servos. Both use digital packets over half-duplex asynchronous TTL serial and provide embedded feedback.

That makes the old eight-channel raw-PWM implementation a **legacy prototype**, not the intended V1 body-bus implementation.

## What has been implemented now

`src/parrotcore/feetech_protocol.py` implements the manufacturer packet envelope and unit-tested PING, READ and goal-position WRITE encoding. The tests reproduce the manufacturer's published examples exactly.

Logical joint degrees are **not** converted to servo ticks yet. That would require unverified assumptions about horn center, direction, linkage ratio and mechanical zero. The V1 physical calibration procedure must record, per joint:

- servo ID;
- calibrated center/zero tick;
- positive direction;
- safe minimum/maximum ticks;
- logical-degrees-to-servo-ticks ratio;
- measured no-load and loaded current;
- measured travel time;
- backlash/deadband.

Only after these values exist should FeatherBus logical commands be translated to Feetech raw goal positions.

## ESP32 safety ownership remains unchanged

Even after the transport moves from PWM to smart serial, the ESP32 remains responsible for:

1. physical E-stop latching;
2. independent brain-heartbeat watchdog;
3. logical range validation;
4. calibrated raw-tick range validation;
5. servo rail power enable/disable;
6. current/temperature fault escalation;
7. rejecting motion when calibration is missing.

## Bus electronics that must be designed

The Feetech bus is half-duplex TTL. The production carrier therefore needs a direction-controlled single-wire interface/buffer between the ESP32 UART and the servo data line. The exact transceiver/buffer and termination strategy will be selected after bench signal-integrity testing; it is intentionally not guessed in v0.5.1.

## Primary sources

- Feetech product specification pages for ST-3215-C001/STS3215 and ST-3036-C001.
- Feetech Communication Protocol & Memory Table download page: https://www.feetechrc.com/en/letter-of-agreement.html

Status: packet layer verified in software; physical bus and ESP32 target build not yet validated.
