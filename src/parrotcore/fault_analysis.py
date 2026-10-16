from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .telemetry import FaultKind, TelemetryFrame


def fault_active_frame_counts(frames: Iterable[TelemetryFrame]) -> dict[str, int]:
    """Count frames on which each fault code is active.

    This is useful for fault duration, but it must not be presented as a count
    of independent fault events.
    """
    counts: Counter[str] = Counter()
    for frame in frames:
        counts.update(f.value for f in frame.faults)
    return dict(counts)


def fault_episode_counts(frames: Iterable[TelemetryFrame]) -> dict[str, int]:
    """Count rising-edge fault episodes rather than telemetry frames.

    If one injected watchdog failure remains active for 20 frames, this returns
    one watchdog episode, not twenty faults.
    """
    counts: Counter[str] = Counter()
    previous: set[FaultKind] = set()
    for frame in frames:
        current = set(frame.faults)
        for fault in current - previous:
            counts[fault.value] += 1
        previous = current
    return dict(counts)


def has_faults(frames: Iterable[TelemetryFrame]) -> bool:
    return any(frame.faults for frame in frames)
