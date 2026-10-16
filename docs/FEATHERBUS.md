# FeatherBus v0

FeatherBus v0 is deliberately simple: newline-delimited UTF-8 JSON over USB serial/UART.

This is a prototype protocol, not a safety-certified fieldbus.

## Brain -> body

### Ping

```json
{"v":0,"seq":1,"type":"ping"}
```

### Set joint

```json
{"v":0,"seq":2,"type":"joint","id":0,"value":22.5,"speed":0.6}
```

### Pose

```json
{"v":0,"seq":3,"type":"pose","values":{"0":0,"1":5,"3":15,"4":15},"duration_ms":350}
```

### Emergency stop

```json
{"v":0,"seq":4,"type":"estop","active":true}
```

## Body -> brain

### Telemetry

```json
{"v":0,"seq":81,"type":"telemetry","imu":[0.0,0.0,1.0],"distance_mm":640,"estop":false,"servo_power":true}
```

### Fault

```json
{"v":0,"seq":82,"type":"fault","code":"WATCHDOG","detail":"brain heartbeat expired"}
```

## Hard rule

The MCU rejects commands outside calibrated physical limits even if the Linux safety layer has already accepted them.
