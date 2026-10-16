from __future__ import annotations

from enum import IntEnum


class FeetechInstruction(IntEnum):
    PING = 0x01
    READ = 0x02
    WRITE = 0x03
    REG_WRITE = 0x04
    ACTION = 0x05
    RECOVERY = 0x06
    RESET = 0x0A
    SYNC_READ = 0x82
    SYNC_WRITE = 0x83


BROADCAST_ID = 0xFE
GOAL_POSITION_ADDRESS = 0x2A


def _checksum(payload_from_id: bytes) -> int:
    return (~sum(payload_from_id)) & 0xFF


def instruction_packet(servo_id: int, instruction: int | FeetechInstruction, parameters: bytes = b"") -> bytes:
    if not 0 <= servo_id <= 0xFE:
        raise ValueError("servo id must be 0..254")
    if len(parameters) > 253:
        raise ValueError("parameter payload too long")
    length = len(parameters) + 2
    body = bytes((servo_id, length, int(instruction))) + parameters
    return b"\xFF\xFF" + body + bytes((_checksum(body),))


def ping_packet(servo_id: int) -> bytes:
    return instruction_packet(servo_id, FeetechInstruction.PING)


def read_packet(servo_id: int, address: int, length: int) -> bytes:
    if not 0 <= address <= 255 or not 1 <= length <= 255:
        raise ValueError("invalid address/read length")
    return instruction_packet(servo_id, FeetechInstruction.READ, bytes((address, length)))


def write_packet(servo_id: int, address: int, data: bytes) -> bytes:
    if not 0 <= address <= 255:
        raise ValueError("invalid address")
    if not data:
        raise ValueError("write payload cannot be empty")
    return instruction_packet(servo_id, FeetechInstruction.WRITE, bytes((address,)) + data)


def goal_position_packet(servo_id: int, position_tick: int, speed_tick_s: int, time_tick: int = 0) -> bytes:
    """Build the Feetech magnetic-encoder goal-position WRITE packet.

    This accepts *raw servo ticks only*. ParrotCore deliberately does not convert
    logical joint degrees to raw ticks until physical center/direction/linkage
    calibration has been performed for that individual actuator and mechanism.
    """
    for label, value in (("position_tick", position_tick), ("speed_tick_s", speed_tick_s), ("time_tick", time_tick)):
        if not 0 <= value <= 0xFFFF:
            raise ValueError(f"{label} must be 0..65535")
    data = bytes((
        position_tick & 0xFF, (position_tick >> 8) & 0xFF,
        time_tick & 0xFF, (time_tick >> 8) & 0xFF,
        speed_tick_s & 0xFF, (speed_tick_s >> 8) & 0xFF,
    ))
    return write_packet(servo_id, GOAL_POSITION_ADDRESS, data)
