# ParrotCore Architecture Decision Log

This file records decisions that should not be reconstructed from chat history.

## ADR-0001 — Local-first brain/body separation
**Status:** Accepted  
**Decision:** High-level cognition runs on a Linux-class replaceable compute module. Hard real-time actuator output and emergency behavior remain on an independent MCU body controller. FeatherBus is the contract between them.  
**Reason:** AI workloads and safety-critical motor timing have different failure modes and update cycles.  
**Consequence:** The MCU must be able to disable actuators even if the AI process crashes.

## ADR-0002 — Parrot is the first reference body, not the platform boundary
**Status:** Accepted, v0.4  
**Decision:** Keep Parrot as Robot #1 and primary talking-companion embodiment. Make cognition, memory, perception, skill selection, safety policy and FeatherBus species-agnostic.  
**Reason:** A talking parrot is intuitive to users, but a parrot-only software core would unnecessarily prevent reuse.  
**Consequence:** Body-specific actuator names and choreography live in profiles and kinematic providers, not cognition.

## ADR-0003 — Semantic expression compiler
**Status:** Implemented, v0.4  
**Decision:** High-level behavior uses semantic intents such as `greeting`, `attend_left`, `curious`, `affirm` and `dance`. Each creature profile compiles the same intent into its own joint frames.  
**Reason:** `look at the person` should not mean `neck_yaw=40` inside cognition.  
**Consequence:** Owl can use `head_yaw`, Parrot can use `neck_yaw`, and future bodies can use a different mechanism without changing the skill.

## ADR-0004 — Three reference embodiments
**Status:** Implemented as conceptual digital twins, v0.4  
**Decision:** Maintain three comparison bodies:
- Parrot — talking/family companion.
- Owl — teaching/learning companion.
- Raven — developer/research companion.

**Consequence:** Every core behavior change should be tested against all three profiles where practical.

## ADR-0005 — Compatibility over gratuitous API breakage
**Status:** Implemented, v0.4  
**Decision:** Preserve the historical `ParrotBrain` import and `motion` action contract while carrying a `semantic` field through new built-in actions. New code may use the alias `EmbodiedBrain`.  
**Reason:** v0.3 tests and external prototypes should not silently fail merely because the architecture becomes generic.

## ADR-0006 — Simulation claims are classified
**Status:** Accepted  
**Decision:** Kinematic, electrical, mass and geometry results must be labelled as conceptual assumptions until a physical prototype produces measurements.  
**Reason:** A digital twin is useful only if modeled assumptions are not presented as validated hardware performance.

## ADR-0007 - Parrot V1 uses smart serial servos
**Status:** Accepted, v0.5.1  
**Decision:** Use Feetech ST-3215-C001/STS3215 for neck/wing/body-load joints and ST-3036-C001 for beak/tail/eyelid joints.  
**Reason:** Published current/torque/speed endpoints plus position/current/temperature/load feedback provide a much stronger path to closed-loop telemetry than anonymous PWM servos.  
**Consequence:** The old eight-channel PWM firmware is a legacy bench implementation. Production control requires a half-duplex TTL bus interface and calibrated raw-tick limits.

## ADR-0008 - 3S battery with separate 6V servo and 5V compute rails
**Status:** Accepted, v0.5.1  
**Decision:** Use an 11.1V nominal 3S pack feeding independent buck regulators: 6V for actuators and 5V for compute/peripherals.  
**Reason:** The 6V high-current regulator's dropout requirement rises near heavy load, making 2S input margin inadequate as the pack discharges. Separate regulated domains also reduce direct motor-transient coupling into compute.  
**Consequence:** Physical protection, grounding, current sensing and rail sequencing become explicit PCB requirements.

## ADR-0009 - Hardware evidence classification is mandatory
**Status:** Implemented, v0.5.1  
**Decision:** Every performance parameter must be identifiable as manufacturer specification, derived value, engineering model, or measured prototype result.  
**Reason:** The project must not confuse a digital-twin output with empirical hardware evidence.  
**Consequence:** Runtime, thermal, dynamic current, full mass and torque adequacy remain unvalidated even after component selection.

## ADR-0010 - Raw smart-servo calibration blocks physical motion
**Status:** Accepted, v0.5.1  
**Decision:** Do not convert body-profile logical degrees into Feetech raw position ticks until each actuator/mechanism has measured zero, direction, safe raw endpoints and linkage ratio.  
**Reason:** Guessing servo-center/direction values can drive a physical joint into a hard stop despite correct high-level joint limits.  
**Consequence:** The smart-bus packet layer can be implemented and tested now, but physical command translation remains calibration-gated.


## ADR-008 — Fault events and fault duration are different quantities
**Status:** Accepted, v0.5.2  
**Decision:** Every fault report must distinguish rising-edge fault episodes from active telemetry-frame duration. Nominal operation and deliberate fault injection must be reported separately.  
**Reason:** Frame-count reporting can make one sustained injected condition appear as many independent failures and leads to incorrect engineering interpretation.

## ADR-009 — Safety response is explicit simulator state
**Status:** Accepted, v0.5.2  
**Decision:** Telemetry exposes actuator-power state, motion inhibition, latch state and latch reason separately from active fault codes. Watchdog/overtemperature/overcurrent can latch the actuator rail off; proximity inhibits motion without a rail latch.  
**Reason:** Detecting a fault is not equivalent to proving that the safety system responded correctly.
