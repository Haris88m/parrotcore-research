from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatherBusCodec:
    seq: int = 0
    version: int = 0

    def encode(self, message_type: str, **payload: Any) -> bytes:
        self.seq += 1
        obj = {"v": self.version, "seq": self.seq, "type": message_type, **payload}
        return (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")

    def decode(self, line: bytes | str) -> dict[str, Any]:
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        obj = json.loads(line)
        if obj.get("v") != self.version:
            raise ValueError(f"unsupported FeatherBus version: {obj.get('v')}")
        if "type" not in obj or "seq" not in obj:
            raise ValueError("invalid FeatherBus message")
        return obj
