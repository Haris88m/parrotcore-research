# ParrotCore Architecture v0.1

## 1. System split

```text
                    PARROTCORE BRAIN CARTRIDGE
+---------------------------------------------------------------+
| Linux SOM / SBC                                               |
|                                                               |
| Perception -> World State -> Goal/Policy -> Skill Scheduler    |
|      |             |              |             |              |
|      +-------------+--------------+-------------+              |
|                              |                                |
|                         Safety Gate                            |
|                              |                                |
|                    FeatherBus transport                        |
+------------------------------|--------------------------------+
                               |
                         USB/UART/CAN*
                               |
+------------------------------|--------------------------------+
| ESP32-S3 BODY CONTROLLER                                     |
| watchdog | servo PWM | IMU | touch | ToF | LEDs | power state |
+-----------+-----------+-----+-------+-----+------+-------------+
            |           |                         |
         actuators    sensors                   signals
```

`* CAN is reserved for a later electrically robust bus version.`

The Linux side is deliberately not allowed to directly generate servo pulses. If the AI process stalls, crashes or produces a nonsensical command, the body controller still owns watchdogs, travel limits and motor power shutdown.

## 2. Runtime modules

- `models.py`: typed events, actuator specs, poses and motion frames.
- `body.py`: simulator and future serial body driver.
- `safety.py`: hard actuator clamping and e-stop latch.
- `brain.py`: orchestration and default behavior policy.
- `lesson_engine.py`: declarative trigger -> action teaching system.
- `memory.py`: persistent learned associations.
- `skills/`: extension surface for built-in and third-party behaviors.
- `protocol.py`: FeatherBus v0 serializer/parser.

## 3. Behavior lifecycle

1. perception emits an event;
2. event enters the brain;
3. learned associations are checked;
4. built-in skills are evaluated;
5. selected actions pass through the safety gate;
6. body driver executes motor frames;
7. controller reports telemetry/faults;
8. state and useful learned data are persisted.

## 4. Teaching model

ParrotCore treats "teaching" as installing or learning an association rather than retraining a foundation model for every behavior.

Examples:

- phrase -> phrase: `"red" -> "apple"`
- phrase -> motion: `"fly" -> flap sequence`
- visual label -> response: `person:example -> greeting skill`
- touch region -> response: `back_touch -> happy chirp + wing motion`

Later versions can add imitation learning from demonstrated joint trajectories and local model fine-tuning, but the v0.1 teaching primitive remains deterministic, inspectable and safe.

## 5. Local AI path

The runtime does not require a cloud API. Perception/language adapters can be swapped independently:

- speech-to-text adapter;
- text/language policy adapter;
- text-to-speech adapter;
- object/person/pose vision adapter.

A local LLM is therefore a plugin behind the policy layer, not the motor controller.
