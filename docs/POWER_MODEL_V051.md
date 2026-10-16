# Power Model - v0.5.1

## Data classes

ParrotCore now uses four explicit evidence classes:

1. `manufacturer_spec` - published by the component manufacturer.
2. `derived_from_manufacturer_spec` - arithmetic performed from manufacturer values.
3. `engineering_model` - required for simulation but not physically verified.
4. `measured` - reserved for instrumented prototype data; currently empty for V1.

## Electrical endpoints

| Quantity | Value | Class |
|---|---:|---|
| Servo rail | 6V | manufacturer spec (regulator) |
| Five STS3215 no-load-running current | 0.75A | derived |
| Three ST-3036 no-load-running current | 0.39A | derived |
| All selected servos no-load-running current | 1.14A | derived |
| Five STS3215 stall current | 10.0A | derived |
| Three ST-3036 stall current | 3.6A | derived |
| All selected servos stall current | 13.6A | derived |
| All-stall servo electrical power | 81.6W | derived |
| CM5 typical operation current | 0.9A @5V | manufacturer spec |
| CM5 typical operation power | 4.5W | derived |
| Camera design allowance | 1.25W | engineering budget |
| Battery nominal energy | 24.42Wh | derived |
| Servo regulator rating | 15A @6V | manufacturer spec, thermally dependent |
| Compute regulator rating | 9A @5V | manufacturer spec, thermally dependent |
| Software simulated current threshold | 12A | engineering safety setting |

## Runtime math

For an electrical load `Pdc`, ideal runtime is:

`runtime_h = battery_nominal_Wh / Pdc`

The current conservative planning model applies two explicit assumptions:

- usable battery energy = 80% of nominal;
- average regulator efficiency = 90%.

So:

`derated_runtime_h = (24.42Wh * 0.80) / (Pdc / 0.90)`

This is useful for comparing design alternatives but must not be used as a product runtime claim before discharge testing.

## Measurement upgrade path

Two INA228 devices are selected so the prototype can record:

- total battery-rail current/voltage/power/energy;
- servo-rail current/voltage/power/energy.

Smart-servo internal current/temperature/load feedback can then be compared to the independent rail measurement. This gives ParrotCore a calibration path from model -> real telemetry rather than leaving the simulator permanently synthetic.
