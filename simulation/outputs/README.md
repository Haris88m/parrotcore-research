# Simulation Outputs — Current vs Historical

## Current v0.5.2 validation outputs

Use these for current fault/safety interpretation:

- `parrotcore_v052_safety_validation_demo.mp4`
- `parrotcore_v052_safety_validation_demo.gif`
- `parrotcore_v052_safety_validation_metrics.json`
- `parrotcore_v052_safety_validation_telemetry.csv`
- `v052_hardware_grounded_benchmark.json`

Current result:

- nominal behavior fault episodes: **0**;
- deliberate injected fault episodes: **3 total** — one servo stall, one proximity event, one watchdog-loss event;
- active-frame counts represent duration only;
- corrected safety-response checks: **PASS**.

## Historical outputs

Files containing `v05` or `v051` are retained for project history and reproducibility. In particular, the v0.5.1 hardware dynamics demo reported `fault_frame_counts`. Those values must **not** be interpreted as counts of independent faults.

Historical example:

```text
servo_stall active frames: 16
proximity active frames: 29
watchdog_loss active frames: 11
```

That historical run contained three intentionally injected episodes, not 56 spontaneous faults.

## GitHub repository policy (v0.5.2+)

Large generated media (`.mp4`, `.gif`, `.png`, `.glb`, `.stl`) is not committed to Git.
GitHub Actions regenerates and uploads those files as workflow artifacts. JSON/CSV validation
outputs remain versioned where they are useful as reproducible regression evidence.
