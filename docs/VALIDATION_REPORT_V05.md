# Validation Report — ParrotCore v0.5.0

**Date:** 16 August 2026

## Automated regression

Command:

```bash
PYTHONPATH=src python -m unittest discover -s tests -q
```

Result: **32/32 tests passed**.

Coverage includes:

- legacy runtime compatibility;
- SafetyGate and E-stop behavior;
- FeatherBus roundtrip;
- teaching-memory behavior and cross-thread access;
- body-profile loading;
- serial-body validation before write;
- Parrot v0.3 kinematics and metrics;
- v0.4 creature registry and semantic expression compilation;
- Parrot/Owl/Raven geometry anchors;
- v0.5 quintic trajectory endpoint and dynamic-limit checks;
- normal telemetry generation;
- servo-stall, watchdog, proximity, overtemperature and overcurrent fault probes;
- home-pose collision and stability proxies.

## Interactive server smoke tests

### Creature Lab
- server startup: PASS;
- profile listing: PASS;
- switch Parrot → Owl: PASS;
- Owl greeting animation generated: PASS;
- teaching-memory roundtrip: PASS.

### Dynamics Lab
- server startup: PASS;
- switch to Raven: PASS;
- Raven greeting trajectory generated: PASS;
- watchdog fault injection propagated into telemetry: PASS.

## Render outputs

- multi-creature semantic comparison MP4/GIF: generated;
- v0.5 dynamics/fault MP4/GIF: generated;
- conceptual GLB/STL models for Parrot/Owl/Raven: generated;
- telemetry CSV: generated;
- cross-species dynamics benchmark JSON: generated.

## Physical validation status

**Not performed.** No hardware bench rig is connected in this environment. Simulated power, current, temperature, speed, collision and stability values remain assumptions/models until measured.
