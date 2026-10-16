from pathlib import Path

from parrotcore.hardware import load_hardware_baseline
from parrotcore.physics import DynamicsSimulator
from parrotcore.profile import load_profile
from parrotcore.telemetry import FaultKind

ROOT = Path(__file__).resolve().parents[1]


def hw():
    return load_hardware_baseline(
        ROOT / "hardware" / "v1_component_baseline.toml",
        ROOT / "hardware" / "v1_actuator_map.toml",
    )


def profile():
    return load_profile(ROOT / "profiles" / "reference_parrot.toml")


def test_baseline_loads_all_reference_parrot_joints():
    baseline = hw()
    p = profile()
    assert set(baseline.actuator_map) == set(p.joints)
    assert len(baseline.actuator_map) == 8


def test_manufacturer_endpoint_derivations():
    baseline = hw()
    assert abs(baseline.mapped_servo_mass_g - 328.1) < 1e-9
    assert abs(baseline.mapped_servo_no_load_current_a - 1.14) < 1e-9
    assert abs(baseline.mapped_servo_all_stall_current_a - 13.6) < 1e-9
    assert abs(baseline.compute.operation_power_w - 4.5) < 1e-9
    assert abs(baseline.battery.energy_wh - 24.42) < 1e-9
    assert abs(baseline.battery.continuous_current_a - 55.0) < 1e-9


def test_requested_joint_speed_does_not_exceed_servo_no_load_speed():
    baseline = hw()
    p = profile()
    for joint, spec in p.joints.items():
        servo = baseline.servo_for_joint(joint)
        assert spec.max_speed <= servo.no_load_speed_deg_s


def test_servo_regulator_nominal_rating_exceeds_theoretical_all_stall_but_margin_is_small():
    baseline = hw()
    margin = baseline.servo_regulator.continuous_output_current_a - baseline.mapped_servo_all_stall_current_a
    assert margin > 0
    assert margin / baseline.mapped_servo_all_stall_current_a < 0.20


def test_hardware_grounded_normal_motion_uses_selected_rail_and_no_overcurrent():
    baseline = hw()
    p = profile()
    sim = DynamicsSimulator(p, sample_hz=50, hardware=baseline)
    run = sim.run(p.home_pose, {"neck_yaw": 35, "wing_left": 30, "wing_right": 30}, 0.4)
    assert run.telemetry
    assert all(abs(t.rail_voltage_v - 6.0) < 1e-9 for t in run.telemetry)
    assert not any(FaultKind.OVERCURRENT in t.faults for t in run.telemetry)
    assert max(t.system_power_w for t in run.telemetry) > baseline.electronics_baseline_power_w


def test_all_servo_stall_triggers_software_overcurrent_before_regulator_ceiling():
    baseline = hw()
    p = profile()
    sim = DynamicsSimulator(p, sample_hz=20, hardware=baseline)
    sim.injection.stalled_joints.update(p.joints)
    run = sim.run(p.home_pose, {"neck_yaw": 10}, 0.2)
    assert any(FaultKind.OVERCURRENT in t.faults for t in run.telemetry)
    assert abs(max(t.rail_current_a for t in run.telemetry) - 13.6) < 1e-9
    assert baseline.modeling.servo_software_current_limit_a < baseline.servo_regulator.continuous_output_current_a


def test_derated_runtime_calculation_is_lower_than_ideal():
    baseline = hw()
    load_w = 20.0
    assert baseline.ideal_runtime_h(load_w, derated=True) < baseline.ideal_runtime_h(load_w)


def test_creature_effectiveness_can_use_hardware_endpoint_data():
    from parrotcore.simulation import creature_effectiveness
    baseline = hw()
    p = profile()
    m = creature_effectiveness(p, hardware=baseline)
    assert abs(m.servo_idle_w - 6.84) < 1e-9
    assert abs(m.servo_peak_w - 81.6) < 1e-9
    assert abs(m.system_peak_w - 87.35) < 1e-9
