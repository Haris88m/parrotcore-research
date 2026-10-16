# Validation Report - ParrotCore v0.5.1

Date: 2026-08-16

## Result

**44 / 44 automated Python tests pass.**

The suite includes all legacy v0.1-v0.5 tests plus hardware-baseline and Feetech protocol tests.

## New v0.5.1 validations

- V1 hardware baseline parses successfully.
- Every Parrot joint maps to exactly one selected actuator model.
- Aggregate servo mass = 328.1g from selected manufacturer values.
- Aggregate manufacturer no-load-running current = 1.14A.
- Aggregate theoretical all-stall current = 13.6A.
- CM5 manufacturer-typical operation power derives to 4.5W.
- Battery nominal energy derives to 24.42Wh.
- Battery 25C nominal current arithmetic derives to 55A.
- Every configured Parrot joint max-speed limit is below its assigned servo's manufacturer no-load speed at 6V.
- 15A regulator nominal rating exceeds 13.6A theoretical all-stall current, while test explicitly confirms margin is below 20%.
- Hardware-grounded normal motion does not trigger the 12A simulated software current limit.
- Forced all-servo stall reaches 13.6A and triggers simulated overcurrent.
- Hardware-grounded effectiveness metrics use selected electrical endpoint data.
- Feetech PING packet matches manufacturer protocol example.
- Feetech READ packet matches manufacturer protocol example.
- Feetech raw goal-position WRITE packet matches manufacturer protocol example.
- Raw goal-position packet rejects out-of-range tick values.

## HTTP smoke test

Dynamics Lab v0.5.1: PASS.

Observed smoke-test dance request:

- 86 generated animation frames;
- 4.3s constrained trajectory duration;
- ~1.766A maximum simulated rail current;
- ~16.345W maximum modeled DC system load.

These are simulator outputs, not physical measurements.

## Claim boundary

A passing software test proves implementation consistency; it does **not** prove actuator mechanical sufficiency or hardware safety.

The following remain blocking physical validations:

- joint load/torque measurement;
- per-servo raw tick calibration;
- smart-bus electrical interface;
- current-sense shunt design;
- power switch/eFuse/E-stop circuit;
- wiring/connector current rating;
- regulator thermal behavior;
- battery discharge/charging protection strategy;
- CM5 thermal solution inside the shell;
- physical 3-actuator bench test.
