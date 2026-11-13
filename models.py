from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Process:
    pid: str
    arrival_time: int
    burst_time: int
    maximum: tuple[int, ...]
    allocation: tuple[int, ...]

    @property
    def need(self) -> tuple[int, ...]:
        return tuple(maximum - allocated for maximum, allocated in zip(self.maximum, self.allocation))

    @property
    def max_need(self) -> int:
        return max(self.need, default=0)


@dataclass
class Event:
    time: int
    cycle: int
    algorithm: str
    action: str
    pid: str | None
    available: list[int]
    need: list[int] | None = None
    decision: str = ""
    comparisons: int = 0
    reason: str = ""
    queue: list[str] = field(default_factory=list)


@dataclass
class AlgorithmResult:
    algorithm: str
    safe: bool
    safe_sequence: list[str]
    primary_unsafe_sequence: list[str]
    unsafe_sequence: list[str]
    final_available: list[int]
    comparisons: int
    retries: int
    events: list[Event]
    simulated_time: int
    metadata: dict[str, str | int] = field(default_factory=dict)
