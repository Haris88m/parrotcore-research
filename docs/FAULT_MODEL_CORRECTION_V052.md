# Fault Model Correction — ParrotCore v0.5.2

**Date:** 16 August 2026  
**Scope:** simulation fault accounting, safety-state behavior, validation UX and clean-checkout tests.

## Why v0.5.2 exists

The v0.5.1 hardware-grounded animation correctly *injected* three fault conditions, but its summary counted every telemetry frame containing a fault code. This made one fault that lasted several frames look like many independent faults.

Example from the historical v0.5.1 demo:

- neck-yaw stall: 16 active frames;
- proximity condition: 29 active frames;
- watchdog loss: 11 active frames.

Those numbers represented **duration**, not **56 independent faults**. The actual experiment contained **three deliberately injected fault episodes**.

This was a reporting defect and an HMI/validation-design defect. It did not mean the nominal robot simulation was generating 56 spontaneous faults.

## Corrected fault semantics

v0.5.2 records two separate quantities:

1. **fault episode count** — a rising edge from inactive to active;
2. **fault active-frame count** — how many telemetry frames the condition remained active.

Therefore a watchdog condition lasting 20 frames is reported as:

```text
watchdog_loss episodes: 1
watchdog_loss active frames: 20
```

and never as "20 watchdog faults".

## Safety response semantics

The simulator now separates detection from response.

| Condition | Detection | Motion response | Actuator-power response | Latching |
|---|---|---|---|---|
| Proximity < stop distance | `proximity` | inhibit commanded movement | keep rail available | no |
| Individual servo stall | `servo_stall` | stalled joint does not advance | rail remains available unless current limit trips | no by itself |
| Watchdog loss | `watchdog_loss` | inhibit all motion | actuator rail off | yes |
| Overtemperature | `overtemp` | inhibit all motion | actuator rail off | yes |
| Overcurrent | `overcurrent` | current transient recorded, motion inhibited | actuator rail latched off | yes |

A latched actuator shutdown remains in force after the initiating condition clears. `reset_safety()` is required to restore simulated actuator power. This matches the project's intended physical safety ownership more closely than v0.5.1.

## Nominal and injected scenarios are now separated

The corrected validation artifact contains two explicitly separated phases:

### Nominal validation

`greeting -> curious -> dance -> home`

Expected result:

- zero fault episodes;
- zero active fault frames;
- actuator power remains available;
- no safety latch.

### Deliberate fault-injection validation

Exactly three injected episodes:

1. neck-yaw stall;
2. object at 4 cm;
3. watchdog loss.

The purpose is to prove fault detection and safe response. These are not failures of nominal behavior.

## Test-environment correction

v0.5.1's test suite passed when the package source path was configured, but running `pytest` from a freshly unpacked repository depended on environment setup. v0.5.2 adds `tests/conftest.py` so the source-layout package is resolvable during repository-local tests.

This changes the validation command from an environment-dependent invocation into:

```bash
pytest -q
```

from the project root.

## Remaining limits

The safety behavior in this document is still software simulation. Physical timing and behavior of:

- eFuse/load switch;
- current sensor;
- ESP32 watchdog;
- actuator rail discharge;
- servo bus response;
- thermal cutoff;
- mechanical stall;

must be measured on the physical three-actuator bench rig before being treated as validated hardware safety behavior.
