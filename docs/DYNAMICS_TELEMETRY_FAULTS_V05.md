# v0.5 Dynamics, Telemetry and Fault Simulation

## Purpose

v0.4 proved that one semantic brain can drive multiple creature embodiments. v0.5 adds a second safety boundary: **semantic expressions are no longer assumed to be instantaneous joint jumps**.

Every target can now be planned as a sampled trajectory with speed, acceleration and jerk envelopes before the later physical-control layer is attached.

## Trajectory model

`TrajectoryPlanner` uses the quintic polynomial:

```text
s(u) = 10u^3 - 15u^4 + 6u^5
```

It has zero velocity and acceleration at both trajectory endpoints. For each joint the planner computes a minimum duration from configured:

- maximum speed;
- maximum acceleration;
- maximum jerk.

If a caller requests a duration that is too short, the planner **extends the duration** instead of violating the dynamic envelope.

This remains a joint-space model. It is not yet torque-controlled rigid-body dynamics.

## Telemetry model

Each simulated telemetry frame contains:

- joint positions;
- joint velocities;
- estimated current per servo;
- rail voltage/current;
- estimated system power;
- maximum estimated servo temperature;
- IMU proxy;
- ToF proximity distance;
- touch state;
- stability-margin proxy;
- active fault codes.

## Fault injection implemented

- brain watchdog loss;
- individual servo stall;
- all-servo stall / overcurrent test;
- forced close-proximity object;
- forced overtemperature;
- extra simulated load.

Fault injection is simulation-only.

## Collision and stability proxies

`estimate_collision()` currently checks conceptual floor clearance, head/wing proximity and wing centerline crossing. `estimate_stability()` uses a coarse weighted center-of-mass projection against a modeled foot/grip envelope.

These are **early warning heuristics**, not CAD collision analysis or certified stability calculations.

## Cross-species normal benchmark

No fault codes were produced during the benchmark sequence (greeting → curious → dance → affirm → home) for any of the three reference creatures.

| Metric | Owl | Parrot | Raven |
|---|---:|---:|---:|
| Simulated sequence duration | 10.40 s | 10.10 s | 9.44 s |
| Max servo-rail current* | 1.23 A | 1.41 A | 1.42 A |
| Max system power* | 17.39 W | 18.47 W | 20.53 W |
| Minimum stability margin* | 24.1 mm | 19.5 mm | 14.8 mm |

`*` conceptual simulation values based on assumed servo/compute parameters.

The Raven's lower current stability margin in this model is a useful design signal, not a conclusion; the model must later be replaced with CAD mass properties and measured mechanics.

## Fault probe result

All three species successfully surfaced the intended simulated fault classes:

| Probe | Expected fault(s) | Owl | Parrot | Raven |
|---|---|---|---|---|
| Watchdog loss | `watchdog_loss` | yes | yes | yes |
| Object at 4 cm | `proximity` | yes | yes | yes |
| Forced 80 °C | `overtemp` | yes | yes | yes |
| All servos stalled | `servo_stall`, `overcurrent` | yes | yes | yes |

## Interactive tool

Run:

```text
06_RUN_DYNAMICS_LAB.bat
```

or:

```bash
PYTHONPATH=src python -m parrotcore.cli dynamics-lab
```

Then open `http://127.0.0.1:8780`.

The lab supports species switching, semantic behaviors, trajectory playback, live simulated telemetry and fault injection.

## Rendered outputs

- `simulation/outputs/parrotcore_v05_dynamics_fault_demo.mp4`
- `simulation/outputs/parrotcore_v05_dynamics_fault_demo.gif`
- `simulation/outputs/parrotcore_v05_telemetry_demo.csv`
- `simulation/outputs/parrotcore_v05_dynamics_metrics.json`
- `simulation/outputs/v05_species_dynamics_benchmark.json`
