# ParrotCore research source release

This is a clean source export from Haris Mekic's private development repository, based on commit `35c3e907a134c72fa67b7a1fc5d85a4c82f3a0ad` and prepared on 16 October 2026. It contains the current tracked research source, tests, documentation, component-source register and simulation data, with publication-specific documentation corrections.

## What this demonstrates

A Python semantic behavior runtime maps shared intents to three simulated creature profiles. The repository includes trajectory constraints, fault injection, telemetry, trigger-response teaching, a serial protocol boundary and an ESP32 firmware prototype. The learning primitive is an inspectable association/rule system, not foundation-model training. No hosted or paid AI model is required by the runtime or the local test suite.

The numerical outputs under `simulation/outputs/` are historical software-generated records. Component specifications have cited manufacturer sources; dynamic power, thermal behavior, runtime and geometry remain models. There are no measured V1 physical prototype results, production robotics claims or child-safety certification in this release. Do not connect physical actuators without separate calibration, hardware safety and bench verification.

## Why a clean export

The private development history, pull requests, Actions records and other account metadata are not part of this release. The `.github/` workflows were deliberately omitted. The existing MIT license and attribution are preserved. Third-party component names identify referenced hardware, not partnerships or endorsement. A name in an illustrative person-recognition example was generalized.

The root README now distinguishes the implemented deterministic runtime from future perception and model adapters and installs the test extra explicitly. The export also repairs standard wheel packaging by bundling three profiles and two hardware TOML files inside the Python package and resolving runtime defaults there. Source fixtures are retained for research scripts, with a regression test preventing the two copies from drifting. This is a publication review, not a security certification or proof of hardware readiness.

## Reproduce locally

Use Python 3.11 or later in a fresh virtual environment from the repository root.

```text
python -m venv .venv
```

Activate that environment using the instructions for your operating system, then run:

```text
python -m pip install -e ".[dev]"
python -m pytest -q
parrotcore demo
```

Optional browser labs are local development tools, not authenticated public services. Keep them on loopback. Serial hardware, firmware flashing, image/video rendering and public deployment are separate operations; none is required to run the unit tests.

## Verification scope

On 16 October 2026, the original 52 tests passed before the packaging correction. The corrected export passed **56 tests**, including three resource checks and one installed-wheel regression. The wheel regression installs the freshly built artifact into a new virtual environment with `--no-index --no-deps`, uses an unrelated working directory and isolated Python, verifies all three profiles and the hardware baseline, and runs the installed demo. No serial hardware or model API calls are involved. These are local test observations, not an independent security certification.

To reproduce the packaging gate, build a wheel with `uv build --wheel`, set `PARROTCORE_TEST_WHEEL` to the absolute path of the new `.whl`, and run `uv run --no-project --with pytest python -m pytest -q`. Without that variable, the installed-wheel test is explicitly skipped; the source tests alone are not a packaging check. Normal and editable installations are supported. The earlier missing-profile wheel defect is corrected by this export, not retroactively by the private source commit.

Historical validation documents retain their original dates and claims. Unit tests exercise software behavior only; they do not measure physical safety, robot intelligence, human outcomes or deployed reliability.
