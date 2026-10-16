# ESP32-S3 body firmware v0.2

Target: ESP-IDF using the current object-based MCPWM driver (`driver/mcpwm_prelude.h`).

## Build

```bash
idf.py set-target esp32s3
idf.py build
idf.py -p YOUR_PORT flash monitor
```

## First boot behavior

Servo rail remains disabled and the software E-stop is latched. After verifying that the physical E-stop input is released and the mechanism is safe, the Linux host may send `{"v":0,"seq":1,"type":"estop","active":false}`.

## Important

The pulse widths in `main.c` are **reference placeholders**. Calibrate each joint with the linkage disconnected or mechanically unloaded. Do not energize an assembled bird with unverified servo endpoints.
