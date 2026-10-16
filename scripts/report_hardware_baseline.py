from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from parrotcore.hardware import load_hardware_baseline

h = load_hardware_baseline(
    ROOT / "hardware" / "v1_component_baseline.toml",
    ROOT / "hardware" / "v1_actuator_map.toml",
)

no_load_w = h.servo_regulator.output_voltage_v * h.mapped_servo_no_load_current_a
all_stall_w = h.servo_regulator.output_voltage_v * h.mapped_servo_all_stall_current_a
report = {
    "baseline_id": h.baseline_id,
    "evidence_warning": "No V1 physical measurements exist yet. Manufacturer endpoint data is real; dynamic/mechanical/thermal behavior remains modeled.",
    "servo_mass_g": h.mapped_servo_mass_g,
    "servo_no_load_running_current_a": h.mapped_servo_no_load_current_a,
    "servo_no_load_running_power_w": no_load_w,
    "servo_theoretical_all_stall_current_a": h.mapped_servo_all_stall_current_a,
    "servo_theoretical_all_stall_power_w": all_stall_w,
    "servo_software_current_limit_a": h.modeling.servo_software_current_limit_a,
    "servo_regulator_nominal_current_a": h.servo_regulator.continuous_output_current_a,
    "cm5_operation_power_w_typical": h.compute.operation_power_w,
    "battery_nominal_energy_wh": h.battery.energy_wh,
    "battery_theoretical_c_rate_current_a": h.battery.continuous_current_a,
    "actuator_map": h.actuator_map,
}
print(json.dumps(report, indent=2))
