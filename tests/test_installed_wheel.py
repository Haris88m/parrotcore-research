"""Run with PARROTCORE_TEST_WHEEL pointing to a freshly built wheel.

The fresh environment, isolated Python mode and unrelated working directory
prevent the source checkout or an editable install from hiding missing assets.
"""

import os
from pathlib import Path
import subprocess
import venv

import pytest


@pytest.mark.skipif(not os.environ.get("PARROTCORE_TEST_WHEEL"), reason="build a wheel and set PARROTCORE_TEST_WHEEL")
def test_installed_wheel_is_self_contained(tmp_path):
    wheel = Path(os.environ["PARROTCORE_TEST_WHEEL"]).resolve(strict=True)
    assert wheel.suffix == ".whl"
    environment = tmp_path / "isolated-env"
    venv.EnvBuilder(with_pip=True).create(environment)
    executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run(
        [str(executable), "-I", "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)],
        cwd=tmp_path, check=True, capture_output=True, text=True, timeout=60,
    )
    check = r'''
import contextlib
import io
from pathlib import Path
import sys
import parrotcore
from parrotcore.cli import default_profiles_dir, demo, make_brain
from parrotcore.embodiment import CreatureRegistry, ExpressionCompiler
from parrotcore.hardware import load_hardware_baseline

assert Path(parrotcore.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
profiles = default_profiles_dir()
assert CreatureRegistry.from_directory(profiles).species() == ("owl", "parrot", "raven")
for profile in CreatureRegistry.from_directory(profiles).all():
    assert ExpressionCompiler(profile).compile("greeting").frames
hardware = profiles.parent / "hardware"
baseline = load_hardware_baseline(hardware / "v1_component_baseline.toml", hardware / "v1_actuator_map.toml")
assert baseline.mapped_servo_all_stall_current_a == 13.6
assert make_brain().profile.species == "parrot"
output = io.StringIO()
with contextlib.redirect_stdout(output):
    demo()
assert all(species in output.getvalue() for species in ("OWL", "PARROT", "RAVEN"))
print("Installed-wheel profiles, hardware baseline and demo passed")
'''
    result = subprocess.run(
        [str(executable), "-I", "-c", check], cwd=tmp_path,
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert "Installed-wheel profiles, hardware baseline and demo passed" in result.stdout
    command = environment / ("Scripts/parrotcore.exe" if os.name == "nt" else "bin/parrotcore")
    cli_result = subprocess.run(
        [str(command), "demo"], cwd=tmp_path,
        check=True, capture_output=True, text=True, timeout=30,
    )
    assert all(species in cli_result.stdout for species in ("OWL", "PARROT", "RAVEN"))
