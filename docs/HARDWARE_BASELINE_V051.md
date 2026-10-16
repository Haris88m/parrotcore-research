# ParrotCore V1 Hardware Baseline - v0.5.1

**Checkpoint:** 2026-08-16  
**Purpose:** replace placeholder electrical parameters with selected manufacturer-specified components while preserving a strict boundary between data-sheet facts, derived values, engineering models and future measurements.

## 1. Selected reference stack

| Function | V1 reference component | Qty | Grounded facts used by simulator/project |
|---|---|---:|---|
| Main AI compute | Raspberry Pi Compute Module 5, wireless target, 8GB/32GB class | 1 | 5V supply; typical idle current 0.4A; typical operation current 0.9A; manufacturer notes application dependence |
| Body controller | ESP32-S3-WROOM-1-N16R8 target | 1 | ESP32-S3 family: dual-core LX7 up to 240MHz, 512KB internal SRAM, Wi-Fi/BLE |
| Large actuators | Feetech ST-3215-C001 / STS3215 | 5 | 6-7.4V; 55g; 0.238s/60deg no-load @6V; 0.15A no-load running; 6.5kg.cm rated torque; 19.5kg.cm stall torque; 2.0A stall current; TTL smart-bus feedback |
| Compact actuators | Feetech ST-3036-C001 | 3 | 4.8-7.4V; 17.7g; 0.09s/60deg no-load @6V; 0.13A max no-load running; 1.5kg.cm rated torque; 4.5kg.cm stall torque; 1.2A stall current; TTL smart-bus feedback |
| Battery | Gens ace G-Tech 2200mAh 3S 11.1V 25C LiPo | 1 | 2.2Ah; 11.1V nominal; 25C; 169g |
| Servo regulator | Pololu D24V150F6 | 1 | 6V; nominal 15A class; thermal/input-voltage limits apply; 19g |
| Compute regulator | Pololu D24V90F5 | 1 | 5V; nominal 9A; typical efficiency range 80-95%; 4.8g |
| Vision | Raspberry Pi Camera Module 3 Wide | 1 | 4608x2592; 120deg diagonal FoV; 25x24x12.4mm |
| Microphones | TDK InvenSense T5848 | 2 | I2S 24-bit PCM; 133dB AOP; Acoustic Activity Detect as low as 20uA |
| Audio amp | Analog Devices MAX98357A | 1 | 2.5-5.5V; I2S; up to 3.2W into 4ohm at 5V |
| Speaker | PUI Audio AS04004PO-2-WR-R | 1 | 4ohm; 3W rated; 4W max; 82dB SPL; 11.9g |
| IMU | TDK InvenSense ICM-42688-P | 1 | 6-axis; 0.88mA low-noise 6-axis mode; +/-2000dps; +/-16g |
| Near-field depth | ST VL53L8CX | 1 | 8x8 zones; up to 4m; 65deg diagonal FoV |
| Touch | Microchip CAP1298 | 1 | 8 capacitive channels + proximity detection |
| Power telemetry | TI INA228 | 2 | 20-bit power monitor; current/voltage/temp/power/energy/charge; 640uA typical operating current |

Exact primary-source URLs are maintained in `hardware/SOURCE_REGISTER.md` and `hardware/v1_component_baseline.toml`.

## 2. Actuator assignment

- STS3215 x5: neck yaw, neck pitch, left wing, right wing, body lean.
- ST-3036 x3: beak, tail pitch, eyelids.
- Reference servo IDs 1-8 are assigned in `hardware/v1_actuator_map.toml`.
- Raw tick mapping is deliberately **not calibrated**. No physical motion should be allowed until zero, direction, end stops and linkage ratios are measured per joint.

## 3. Derived electrical endpoints

These values are arithmetic derived directly from selected manufacturer specifications:

- Aggregate selected-servo mass: **328.1g**.
- Aggregate manufacturer no-load-running current: **1.14A @6V**.
- Aggregate theoretical all-servo stall current: **13.6A @6V**.
- Servo-rail theoretical all-stall electrical load: **81.6W**.
- CM5 typical module operation power: **4.5W** (= 5V x 0.9A).
- Battery nominal energy: **24.42Wh** (= 11.1V x 2.2Ah).
- Battery C-rate theoretical current: **55A** (= 2.2Ah x 25C). This is not a verified connector/wiring/system current capability.
- Known selected-component mass subtotal from parts with captured masses (servos + battery + both regulators + speaker): **532.8g**. This is not total robot mass.

## 4. Power architecture decision

The main battery is 3S, not 2S. The selected 6V/15A regulator's dropout/minimum-input behavior rises toward roughly 7.6V at a 15A load, so a 2S LiPo would leave inadequate voltage margin as it discharges. A 3S pack gives the servo and 5V compute regulators appropriate buck-conversion headroom.

```text
3S LiPo 11.1V nominal
        |
        +-- physical master protection / current monitor
        |
        +-- 6V D24V150F6 --> servo rail --> independent e-stop/load switch --> smart servos
        |
        +-- 5V D24V90F5  --> CM5 / camera / digital audio / logic
```

The two high-current rails are separated so motor transients do not directly share the regulated compute rail.

## 5. Critical current-margin finding

The selected eight servos total **13.6A theoretical stall current**, while the servo regulator is a **15A-class** device. Nominal numerical headroom is only 1.4A (about 10.3% relative to the all-stall current), and the regulator manufacturer explicitly states achievable continuous current depends on thermal dissipation and input voltage.

Therefore:

- all-servo stall is a **fault**, not an operating mode;
- v0.5.1 uses a **12.0A software servo-rail fault threshold**;
- the physical build still requires a hardware current limit/eFuse/load switch and physical E-stop;
- sustained multi-servo load must be measured before the 15A regulator is accepted for the final body;
- if bench data approaches the limit, split servo power domains or move to a higher-margin regulator architecture.

## 6. Simulator changes

`DynamicsSimulator` can now receive a `HardwareBaseline`.

For the Parrot V1 reference:

- rail voltage comes from the selected 6V regulator;
- each joint uses the manufacturer current endpoint of its actual assigned servo;
- a stalled joint uses its actual manufacturer stall-current value;
- CM5 module typical operation power uses the manufacturer 0.9A-at-5V figure;
- camera is currently a 1.25W design budget, not a measured Camera Module 3 draw;
- system dynamic current between no-load and stall is still generated by an explicit model because mechanical load curves do not exist yet.

The dynamic-current interpolation currently uses a documented **18% nominal dynamic load fraction**. That is an engineering parameter, not real data. It is intentionally isolated in `hardware/v1_component_baseline.toml` so bench data can replace it.

## 7. Current reference behavior result

The v0.5.1 greeting/curious/dance/affirm/home benchmark produces, under the current load model:

- average servo-rail current: ~**1.32A**;
- maximum servo-rail current: ~**1.78A**;
- average modeled DC load: ~**13.68W**;
- maximum modeled DC load: ~**16.43W**;
- no simulated fault frames in the normal sequence.

These are **not measured performance numbers**. They combine real hardware endpoint data with the unvalidated dynamic-load model.

The same benchmark computes a derated electrical-runtime estimate of ~**1.28h (77min)** using a 90% regulator-efficiency assumption and 80% usable-battery assumption. It is not a battery-life promise and presently excludes unresolved body-MCU/radio, audio duty-cycle and sensor-mode power.

## 8. Firmware/control consequence

The selected actuators are half-duplex TTL smart servos, not raw PWM servos. The old ESP32 MCPWM reference is therefore marked legacy. v0.5.1 adds a unit-tested Feetech packet codec and a smart-servo migration specification.

The logical-degree-to-raw-tick transformation remains blocked until physical calibration. This is deliberate: guessing raw zeros/directions on a high-current physical mechanism would defeat the safety architecture.

## 9. What is real now vs still unknown

### Manufacturer-grounded / derived from manufacturer data
- selected part numbers;
- actuator voltage, no-load speed/current, rated/stall torque, stall current, mass;
- CM5 typical current endpoints;
- selected battery nominal capacity/voltage/C rating/mass;
- regulator voltage/current ratings and published efficiency range where available;
- camera FoV/resolution/dimensions;
- audio and sensor capabilities listed above;
- arithmetic aggregates such as 13.6A all-stall and 24.42Wh nominal battery energy.

### Still requires physical evidence
- actual joint torque requirement;
- servo current for each real motion;
- backlash, noise and lifetime;
- regulator temperature at actual duty cycle;
- battery sag/runtime/thermal behavior;
- real robot mass and center of gravity;
- actual servo-to-joint calibration;
- microphone acoustic placement and echo cancellation;
- speaker loudness/feedback in the shell;
- camera placement/occlusion;
- sensor accuracy through final housing materials;
- wire, connector and bus signal integrity;
- physical E-stop power interruption;
- ESP32 smart-bus firmware on the target PCB;
- compliance and product-safety requirements.

This is the first ParrotCore checkpoint where the electrical digital twin is anchored to a coherent, purchasable V1 component set instead of generic servo/SBC placeholders.
