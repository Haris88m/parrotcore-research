from pathlib import Path
from math import isclose

from parrotcore.cli import default_profile_path, default_profiles_dir, make_brain
from parrotcore.embodiment import CreatureRegistry
from parrotcore.hardware import load_hardware_baseline


ROOT = Path(__file__).resolve().parents[1]


def test_default_profiles_load_all_reference_creatures():
    registry = CreatureRegistry.from_directory(default_profiles_dir())
    assert registry.species() == ("owl", "parrot", "raven")
    assert make_brain().profile.species == "parrot"
    assert default_profile_path().is_file()


def test_default_resources_include_hardware_baseline():
    hardware = default_profiles_dir().parent / "hardware"
    baseline = load_hardware_baseline(
        hardware / "v1_component_baseline.toml",
        hardware / "v1_actuator_map.toml",
    )
    assert isclose(baseline.mapped_servo_all_stall_current_a, 13.6, rel_tol=0, abs_tol=1e-12)


def test_packaged_resources_match_research_source():
    # Keep source-level research scripts and installed defaults synchronized.
    resource_root = default_profiles_dir().parent
    for folder in ("profiles", "hardware"):
        source_files = sorted((ROOT / folder).glob("*.toml"))
        packaged_files = sorted((resource_root / folder).glob("*.toml"))
        assert [p.name for p in source_files] == [p.name for p in packaged_files]
        for source in source_files:
            assert (resource_root / folder / source.name).read_bytes() == source.read_bytes()
