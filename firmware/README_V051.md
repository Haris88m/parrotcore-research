# ESP32 firmware status at v0.5.1

`firmware/esp32s3/main/main.c` is the historical v0.2 PWM body-controller reference. It remains useful for the original generic RC-servo bench path, but it is **not the selected Parrot V1 actuator transport** after the v0.5.1 hardware baseline.

Parrot V1 now targets Feetech half-duplex TTL smart servos. `src/parrotcore/feetech_protocol.py` implements and tests the packet format on the Linux/software side. The ESP32 smart-bus firmware should not be finalized until:

1. the half-duplex bus buffer/transceiver circuit is selected;
2. servo IDs are commissioned one at a time;
3. raw centers/directions/limits are measured;
4. current-sense/e-stop hardware is designed;
5. the target ESP-IDF toolchain is available for compile/flash validation.

Safety authority does not change: ESP32 must own physical E-stop, heartbeat watchdog, logical limits, calibrated raw limits, rail enable and actuator fault escalation.
