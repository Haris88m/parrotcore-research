# ParrotCore V1 Hardware Source Register

Retrieved: 2026-08-16

This register distinguishes **manufacturer specification**, **derived value**, **engineering model**, and **future physical measurement**. A value must not be promoted to measured status without bench evidence.

| Subsystem | Selected component | Primary source | Status |
|---|---|---|---|
| Large smart servo | Feetech ST-3215-C001 / STS3215 | https://www.feetechrc.com/74v-19-kgcm-plastic-case-metal-tooth-magnetic-code-double-axis-ttl-series-steering-gear.html | Manufacturer specification |
| Compact smart servo | Feetech ST-3036-C001 | https://www.feetechrc.com/691673.html | Manufacturer specification |
| Main compute | Raspberry Pi Compute Module 5 | https://pip.raspberrypi.com/documents/RP-008180-DS-cm5-datasheet.pdf | Manufacturer specification |
| Camera | Raspberry Pi Camera Module 3 Wide | https://www.raspberrypi.com/products/camera-module-3/ | Manufacturer specification |
| Battery | Gens ace G-Tech 2200mAh 3S 11.1V 25C | https://genstattu.com/gens-ace-2200mah-3s-11-1v-25c-g-tech-lipo-battery-pack-with-ec3-deans-and-xt60-adapter-for-rc-plane/ | Manufacturer specification |
| 5 V regulator | Pololu D24V90F5 | https://www.pololu.com/product/2866/specs | Manufacturer specification |
| 6 V servo regulator | Pololu D24V150F6 | https://www.pololu.com/product/2882/specs | Manufacturer specification |
| Microphones | 2x TDK InvenSense T5848 | https://www.invensense.tdk.com/en-us/products/microphone/t5848 | Manufacturer specification |
| Audio amplifier | Analog Devices MAX98357A | https://www.analog.com/en/products/MAX98357A.html | Manufacturer specification |
| Speaker | PUI Audio AS04004PO-2-WR-R | https://puiaudio.com/product/speakers-and-receivers/as04004po-2-wr-r | Manufacturer specification |
| IMU | TDK InvenSense ICM-42688-P | https://www.invensense.tdk.com/en-us/products/6-axis/icm-42688-p | Manufacturer specification |
| ToF | ST VL53L8CX | https://www.st.com/en/imaging-and-photonics-solutions/vl53l8cx.html | Manufacturer specification |
| Touch | Microchip CAP1298 | https://www.microchip.com/en-us/product/cap1298 | Manufacturer specification |
| Power monitor | TI INA228 | https://www.ti.com/product/INA228 | Manufacturer specification |
| Body MCU | Espressif ESP32-S3 family / WROOM target | https://www.espressif.com/en/products/socs/esp32-s3 | Manufacturer-family specification |

## Values that are still models, not physical truth

- Dynamic servo load fraction and current between no-load and stall.
- Thermal rise/cooling constants.
- Mechanical linkage loads and required joint torque.
- Full robot mass and center of gravity.
- Regulator efficiency at the exact operating point.
- Usable battery fraction under the actual discharge profile.
- Audio duty cycle and amplifier power.
- Body-MCU/radio power.
- ToF/touch operating power until their runtime modes are fixed.

These remain explicitly tagged in `v1_component_baseline.toml` and in the validation report.
