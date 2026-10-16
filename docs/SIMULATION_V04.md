# v0.4 Multi-Embodiment Simulation

## Classification

All values below are **conceptual engineering simulation results**. They are not measured hardware performance.

## Current profiles

| Property | Parrot | Owl | Raven |
|---|---:|---:|---:|
| Logical DOF | 8 | 8 | 8 |
| Semantic expressions | 8 + home | 8 + home | 8 + home |
| Capability tags | 7 | 7 | 7 |
| Yaw travel | 120° | 220° | 150° |
| Pitch travel | 75° | 75° | 80° |
| Combined wing command span | 150° | 110° | 130° |
| Beak span | 35° | 25° | 30° |
| Tail expression span | 55° | 35° | 45° |
| Assumed mass | 1.80 kg | 1.65 kg | 1.90 kg |
| Target height | 0.34 m | 0.31 m | 0.36 m |
| Assumed typical motion system power | 26.8 W | 25.36 W | 28.32 W |
| Assumed peak system power | 63.4 W | 61.0 W | 67.36 W |
| Watchdog cutoff | 0.75 s | 0.75 s | 0.75 s |

## Interpretation

The Owl currently has the largest modeled yaw envelope, which is useful for attention behavior while perched. The Parrot has the largest modeled wing command span and beak travel, favoring expressive speech/gesture. The Raven profile assumes slightly higher compute and actuator load because it is the developer/research configuration.

These are **design hypotheses** to be tested, not conclusions about which product is best.

## Side-by-side motion test

`simulation/render_creature_comparison.py` makes all three bodies execute the same sequence:

1. greeting;
2. attend left;
3. attend right;
4. center;
5. blink;
6. curious;
7. affirm;
8. dance;
9. home.

Each body receives the same semantic intent but uses independent joint choreography.

Outputs:

- `simulation/outputs/parrotcore_v04_creature_comparison.mp4`
- `simulation/outputs/parrotcore_v04_creature_comparison.gif`
- `simulation/outputs/creature_comparison_metrics.json`
- GLB/STL conceptual home models for Parrot, Owl and Raven.

## Next simulation work

The current twin is kinematic. v0.5 should add:

- velocity limits from profile metadata;
- acceleration/jerk limiting;
- actuator torque/load estimates;
- center-of-mass and perch stability estimates;
- simulated current draw per actuator;
- IMU telemetry;
- time-of-flight proximity telemetry;
- touch input;
- watchdog loss;
- stalled-servo and overcurrent fault injection;
- collision envelopes;
- speech-driven beak trajectory.
