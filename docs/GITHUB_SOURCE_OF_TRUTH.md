# GitHub source of truth

`Haris88m/AI-robotics` is the canonical development repository for ParrotCore.

## Baseline

- Imported baseline: ParrotCore v0.5.2
- Stable branch: `main`
- Integration branch: `develop` (created only after baseline CI is green)
- Feature work: short-lived `feature/*` branches
- Generated MP4/GIF/STL/GLB outputs are CI artifacts by default, not source-controlled binaries.

## Engineering rule

A version is not considered validated merely because files were committed. Tests, safety-model checks, hardware-grounded benchmark checks, and relevant GitHub Actions jobs must pass before promotion.

Physical actuator calibration and hardware safety remain separate validation gates and must never be inferred from simulation success.
