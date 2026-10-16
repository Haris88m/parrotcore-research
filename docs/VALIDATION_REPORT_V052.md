# Validation Report — ParrotCore v0.5.2

**Date:** 16 August 2026  
**Release purpose:** correct fault accounting and safety-response semantics on top of the v0.5.1 datasheet-grounded hardware baseline.

## Automated tests

**52 / 52 tests pass.**

The suite now includes dedicated regression tests for:

- frame counts versus fault episode counts;
- watchdog motion inhibition;
- watchdog actuator-power shutdown;
- watchdog safety-latch persistence;
- explicit safety reset;
- proximity motion inhibition without power latching;
- overtemperature actuator shutdown;
- all-servo-stall overcurrent latching;
- zero fault episodes during nominal hardware-grounded motion.

## Nominal hardware-grounded benchmark

The reference behavior benchmark uses the same selected v0.5.1 V1 component baseline.

Result:

- normal fault episode count: **0**;
- normal active fault-frame count: **0**;
- average modeled servo current: ~1.322 A;
- maximum modeled servo current: ~1.780 A;
- average modeled DC load: ~13.684 W;
- maximum modeled DC load: ~16.430 W.

Power/current values remain manufacturer-endpoint-grounded plus unvalidated dynamic-load assumptions; they are not measurements from a physical robot.

## Explicit all-stall safety probe

The simulator intentionally stalls all eight selected actuators.

Observed:

- simulated peak rail current: **13.6 A**;
- `servo_stall` episode count: **1**;
- `overcurrent` episode count: **1**;
- 12 A software threshold crossed: **yes**;
- safety latch set: **yes**;
- subsequent actuator power off: **yes**.

This point is classified as an invalid operating state, not a normal workload.

## Corrected rendered safety validation

`parrotcore_v052_safety_validation_demo.mp4`

Validation summary:

- nominal phase: zero faults;
- deliberate injection phase: exactly three expected episodes;
- proximity inhibits movement without latching the rail;
- watchdog inhibits motion and removes actuator power;
- watchdog latch remains after the condition is cleared;
- explicit reset restores the simulated actuator rail.

Overall safety-validation metric: **PASS**.

## What this report does not prove

It does not prove:

- physical current cutoff timing;
- physical E-stop function;
- servo torque adequacy;
- smart-bus electrical integrity;
- regulator thermal sufficiency;
- battery runtime;
- product/child safety;
- collision safety;
- physical watchdog behavior.

Those remain bench-validation gates.
