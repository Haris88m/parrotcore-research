from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ServoSpec:
    key: str
    manufacturer: str
    model: str
    reference_voltage_v: float
    no_load_speed_sec_per_60deg: float
    no_load_current_a: float
    stall_current_a: float
    rated_torque_kg_cm: float
    stall_torque_kg_cm: float
    mass_g: float
    source_class: str

    @property
    def no_load_speed_deg_s(self) -> float:
        return 60.0 / self.no_load_speed_sec_per_60deg


@dataclass(frozen=True)
class BatterySpec:
    nominal_voltage_v: float
    capacity_ah: float
    continuous_c: float
    mass_g: float

    @property
    def energy_wh(self) -> float:
        return self.nominal_voltage_v * self.capacity_ah

    @property
    def continuous_current_a(self) -> float:
        return self.capacity_ah * self.continuous_c


@dataclass(frozen=True)
class ComputeSpec:
    supply_voltage_v: float
    idle_current_a_typical: float
    operation_current_a_typical: float

    @property
    def operation_power_w(self) -> float:
        return self.supply_voltage_v * self.operation_current_a_typical


@dataclass(frozen=True)
class RegulatorSpec:
    output_voltage_v: float
    continuous_output_current_a: float
    mass_g: float


@dataclass(frozen=True)
class ModelingAssumptions:
    nominal_dynamic_load_fraction: float
    regulator_efficiency_assumption: float
    usable_battery_fraction_assumption: float
    servo_software_current_limit_a: float


@dataclass(frozen=True)
class HardwareBaseline:
    baseline_id: str
    servos: dict[str, ServoSpec]
    actuator_map: dict[str, str]
    battery: BatterySpec
    compute: ComputeSpec
    compute_regulator: RegulatorSpec
    servo_regulator: RegulatorSpec
    camera_power_budget_w: float
    modeling: ModelingAssumptions
    raw: dict[str, Any]

    def servo_for_joint(self, joint: str) -> ServoSpec:
        key = self.actuator_map[joint]
        return self.servos[key]

    @property
    def mapped_servo_mass_g(self) -> float:
        return sum(self.servo_for_joint(j).mass_g for j in self.actuator_map)

    @property
    def mapped_servo_no_load_current_a(self) -> float:
        return sum(self.servo_for_joint(j).no_load_current_a for j in self.actuator_map)

    @property
    def mapped_servo_all_stall_current_a(self) -> float:
        return sum(self.servo_for_joint(j).stall_current_a for j in self.actuator_map)

    @property
    def electronics_baseline_power_w(self) -> float:
        # CM5 operation current is a manufacturer typical; camera power is a
        # conservative engineering budget. MCU/audio/sensor duty-cycle power
        # remains intentionally excluded until fixed or measured.
        return self.compute.operation_power_w + self.camera_power_budget_w

    def ideal_runtime_h(self, dc_load_power_w: float, *, derated: bool = False) -> float:
        if dc_load_power_w <= 0:
            raise ValueError("load power must be positive")
        energy = self.battery.energy_wh
        load = dc_load_power_w
        if derated:
            energy *= self.modeling.usable_battery_fraction_assumption
            load /= self.modeling.regulator_efficiency_assumption
        return energy / load


def load_hardware_baseline(component_path: str | Path, actuator_map_path: str | Path) -> HardwareBaseline:
    component_path = Path(component_path)
    actuator_map_path = Path(actuator_map_path)
    raw = tomllib.loads(component_path.read_text(encoding="utf-8"))
    amap = tomllib.loads(actuator_map_path.read_text(encoding="utf-8"))["map"]

    servos: dict[str, ServoSpec] = {}
    for key, spec in raw["servos"].items():
        servos[key] = ServoSpec(
            key=key,
            manufacturer=str(spec["manufacturer"]),
            model=str(spec["model"]),
            reference_voltage_v=float(spec["reference_voltage_v"]),
            no_load_speed_sec_per_60deg=float(spec["no_load_speed_sec_per_60deg"]),
            no_load_current_a=float(spec["no_load_current_a"]),
            stall_current_a=float(spec["stall_current_a"]),
            rated_torque_kg_cm=float(spec["rated_torque_kg_cm"]),
            stall_torque_kg_cm=float(spec["stall_torque_kg_cm"]),
            mass_g=float(spec["mass_g"]),
            source_class=str(spec["source_class"]),
        )

    for joint, servo_key in amap.items():
        if servo_key not in servos:
            raise ValueError(f"actuator map references unknown servo {servo_key!r} for {joint!r}")

    battery = raw["battery"]["main"]
    compute = raw["compute"]["cm5"]
    comp_reg = raw["regulators"]["compute"]
    servo_reg = raw["regulators"]["servo"]
    modeling = raw["modeling"]

    return HardwareBaseline(
        baseline_id=str(raw["baseline"]["id"]),
        servos=servos,
        actuator_map={str(k): str(v) for k, v in amap.items()},
        battery=BatterySpec(
            nominal_voltage_v=float(battery["nominal_voltage_v"]),
            capacity_ah=float(battery["capacity_ah"]),
            continuous_c=float(battery["continuous_c"]),
            mass_g=float(battery["mass_g"]),
        ),
        compute=ComputeSpec(
            supply_voltage_v=float(compute["supply_voltage_v"]),
            idle_current_a_typical=float(compute["idle_current_a_typical"]),
            operation_current_a_typical=float(compute["operation_current_a_typical"]),
        ),
        compute_regulator=RegulatorSpec(
            output_voltage_v=float(comp_reg["output_voltage_v"]),
            continuous_output_current_a=float(comp_reg["continuous_output_current_a"]),
            mass_g=float(comp_reg["mass_g"]),
        ),
        servo_regulator=RegulatorSpec(
            output_voltage_v=float(servo_reg["output_voltage_v"]),
            continuous_output_current_a=float(servo_reg["continuous_output_current_a"]),
            mass_g=float(servo_reg["mass_g"]),
        ),
        camera_power_budget_w=float(raw["camera"]["camera3_wide"]["power_budget_w"]),
        modeling=ModelingAssumptions(
            nominal_dynamic_load_fraction=float(modeling["nominal_dynamic_load_fraction"]),
            regulator_efficiency_assumption=float(modeling["regulator_efficiency_assumption"]),
            usable_battery_fraction_assumption=float(modeling["usable_battery_fraction_assumption"]),
            servo_software_current_limit_a=float(modeling["servo_software_current_limit_a"]),
        ),
        raw=raw,
    )
