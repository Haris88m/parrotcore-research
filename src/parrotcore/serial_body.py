from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import BinaryIO

from .models import MotionFrame
from .profile import BodyProfile
from .protocol import FeatherBusCodec
from .safety import SafetyGate


@dataclass
class FeatherSerialBody:
    profile: BodyProfile
    safety: SafetyGate
    stream: BinaryIO
    codec: FeatherBusCodec = field(default_factory=FeatherBusCodec)
    frames_executed: int = 0
    heartbeat_interval_s: float = 0.0
    _write_lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _stop_heartbeat: threading.Event = field(default_factory=threading.Event, init=False, repr=False)
    _heartbeat_thread: threading.Thread | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.heartbeat_interval_s > 0:
            self.start_heartbeat()

    @classmethod
    def from_port(cls, profile: BodyProfile, safety: SafetyGate, port: str, baud: int = 115200):
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install pyserial to use a physical serial port: pip install pyserial") from exc
        stream = serial.Serial(port, baudrate=baud, timeout=0.25)
        return cls(profile=profile, safety=safety, stream=stream, heartbeat_interval_s=0.25)

    def _send(self, message_type: str, **payload) -> None:
        with self._write_lock:
            self.stream.write(self.codec.encode(message_type, **payload))
            if hasattr(self.stream, "flush"):
                self.stream.flush()

    def move(self, frame: MotionFrame) -> None:
        safe = self.safety.check_motion(frame.positions)
        values = {str(self.profile.controller_ids[name]): value for name, value in safe.items()}
        self._send("pose", values=values, duration_ms=max(0, round(frame.duration_s * 1000)))
        self.frames_executed += 1

    def home(self) -> None:
        self.move(MotionFrame({name: spec.home for name, spec in self.profile.joints.items()}, 0.35))

    def estop(self, active: bool = True) -> None:
        if active:
            self.safety.latch_estop()
        else:
            self.safety.reset_estop()
        self._send("estop", active=bool(active))

    def ping(self) -> None:
        self._send("ping")

    def _heartbeat_loop(self) -> None:
        while not self._stop_heartbeat.wait(self.heartbeat_interval_s):
            try:
                self.ping()
            except Exception:
                return

    def start_heartbeat(self) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        if self.heartbeat_interval_s <= 0:
            raise ValueError("heartbeat_interval_s must be > 0")
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, name="parrotcore-heartbeat", daemon=True)
        self._heartbeat_thread.start()

    def close(self) -> None:
        self._stop_heartbeat.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=max(0.25, self.heartbeat_interval_s * 2))
        if hasattr(self.stream, "close"):
            self.stream.close()

    def status(self) -> dict[str, object]:
        return {
            "transport": "featherbus-serial",
            "estop": self.safety.estop_latched,
            "frames_executed": self.frames_executed,
            "heartbeat": bool(self._heartbeat_thread and self._heartbeat_thread.is_alive()),
        }
