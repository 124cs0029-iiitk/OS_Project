from __future__ import annotations

from collections.abc import Callable

from models import AlgorithmResult, Event, Process
from validation import initial_available


def _result(
    name: str,
    sequence: list[str],
    primary: list[str],
    unsafe: list[str],
    available: list[int],
    comparisons: int,
    retries: int,
    events: list[Event],
    simulated_time: int,
    metadata: dict[str, str | int] | None = None,
) -> AlgorithmResult:
    return AlgorithmResult(
        algorithm=name,
        safe=not primary and not unsafe,
        safe_sequence=sequence,
        primary_unsafe_sequence=primary,
        unsafe_sequence=unsafe,
        final_available=available,
        comparisons=comparisons,
        retries=retries,
        events=events,
        simulated_time=simulated_time,
        metadata=metadata or {},
    )


def run_bankers(processes: list[Process], totals: list[int]) -> AlgorithmResult:
    work = initial_available(processes, totals)
    remaining = {process.pid: process for process in processes}
    sequence: list[str] = []
    events: list[Event] = []
    comparisons = 0
    time = 0

    while remaining:
        progress = False
        for process in list(remaining.values()):
            checks = 0
            eligible = True
            for required, available in zip(process.need, work):
                checks += 1
                comparisons += 1
                if required > available:
                    eligible = False
                    break
            events.append(Event(
                time, 0, "Traditional Banker", "safety_check", process.pid,
                work.copy(), list(process.need), "SAFE" if eligible else "UNSAFE",
                checks, "Need <= Work" if eligible else "Need exceeds Work",
                list(remaining),
            ))
            time += 1
            if eligible:
                work = [available + allocated for available, allocated in zip(work, process.allocation)]
                sequence.append(process.pid)
                del remaining[process.pid]
                progress = True
                events.append(Event(
                    time, 0, "Traditional Banker", "complete", process.pid,
                    work.copy(), list(process.need), "COMPLETED", 0,
                    "Allocation released.",
                ))
                time += process.burst_time
        if not progress:
            break

    unsafe = list(remaining)
    return _result(
        "Traditional Banker", sequence, [], unsafe, work, comparisons, 0,
        events, time, {"variant": "traditional safety scan"},
    )


def dbdaa_check(need: tuple[int, ...] | list[int], available: list[int]) -> tuple[bool, int, str]:
    """Paper DBDAA check: compare the largest need with the smallest availability."""
    marked = [False] * len(available)
    comparisons = 0
    rounds = 0
    while rounds < len(available) // 2:
        indexes = [index for index, value in enumerate(marked) if not value]
        if not indexes:
            break
        largest = max(indexes, key=lambda index: need[index])
        smallest = min(indexes, key=lambda index: available[index])
        comparisons += 1
        if need[largest] <= available[smallest]:
            return True, comparisons, f"Max_Need {need[largest]} <= Min_A {available[smallest]}"
        comparisons += 1
        if need[largest] > available[largest]:
            return False, comparisons, f"Need exceeds Available at R{largest + 1}"
        comparisons += 1
        if need[smallest] > available[smallest]:
            return False, comparisons, f"Need exceeds Available at R{smallest + 1}"
        marked[largest] = True
        marked[smallest] = True
        rounds += 1
    for index, value in enumerate(marked):
        if not value:
            comparisons += 1
            if need[index] > available[index]:
                return False, comparisons, f"Need exceeds Available at R{index + 1}"
    return True, comparisons, "All remaining resource positions are available"


def _plain_check(need: list[int], available: list[int]) -> tuple[bool, int, str]:
    comparisons = 0
    for required, value in zip(need, available):
        comparisons += 1
        if required > value:
            return False, comparisons, "Plain check found an unavailable resource"
    return True, comparisons, "Plain resource check passed"


class _AdaptiveChecker:
    def __init__(self) -> None:
        self.mode = "paper"
        self.streak = 0
        self.since_probe = 0

    def check(self, need: list[int], available: list[int]) -> tuple[bool, int, str]:
        dimensions = len(available)
        if self.mode == "paper":
            result = dbdaa_check(need, available)
            if result[1] > dimensions:
                self.streak += 1
            else:
                self.streak = 0
            if self.streak >= 2:
                self.mode = "plain"
                self.since_probe = 0
            return result
        self.since_probe += 1
        if self.since_probe >= 4:
            self.since_probe = 0
            if max(need, default=0) <= min(available, default=0):
                self.mode = "paper"
                self.streak = 0
                return True, 1, "Adaptive quick probe passed"
            ok, comparisons, reason = _plain_check(need, available)
            return ok, comparisons + 1, f"Adaptive probe: {reason}"
        return _plain_check(need, available)


def _run_dynamic(
    processes: list[Process],
    totals: list[int],
    cycle_duration: int,
    algorithm_name: str,
    checker: Callable[[list[int], list[int]], tuple[bool, int, str]],
    enhanced: bool = False,
) -> AlgorithmResult:
    pending = sorted(processes, key=lambda item: (item.arrival_time, item.pid))
    available = totals.copy()
    ready: list[Process] = []
    primary: list[Process] = []
    primary_history: list[str] = []
    sequence: list[str] = []
    unsafe: list[str] = []
    events: list[Event] = []
    comparisons = 0
    retries = 0
    clock = 0
    cycle = 1
    timer = cycle_duration
    progress = True
    overtaken = {process.pid: 0 for process in processes}
    decisions = 0
    next_probe = 0
    probe_gap = 5
    backoff = probe_gap

    def admit() -> None:
        nonlocal progress
        while pending and pending[0].arrival_time <= clock:
            process = pending.pop(0)
            progress = True
            if any(required > total for required, total in zip(process.maximum, totals)):
                unsafe.append(process.pid)
                events.append(Event(
                    clock, cycle, algorithm_name, "capacity_reject", process.pid,
                    available.copy(), list(process.need), "UNSAFE", 0,
                    "Maximum need exceeds system capacity.",
                ))
                continue
            available[:] = [
                current - allocated
                for current, allocated in zip(available, process.allocation)
            ]
            ready.append(process)

    while pending or ready or primary:
        admit()
        if ready:
            decisions += 1
            probe_cost = 0
            chosen: Process | None = None
            ready.sort(key=lambda item: (item.max_need, item.arrival_time, item.pid))
            if enhanced and len(ready) > 1 and decisions >= next_probe:
                candidate = max(
                    ready,
                    key=lambda item: (overtaken[item.pid], -item.arrival_time, item.pid),
                )
                if candidate is not ready[0] and overtaken[candidate.pid] >= 5:
                    probe_cost = 1
                    if max(candidate.need, default=0) <= min(available, default=0):
                        chosen = candidate
                        backoff = probe_gap
                    else:
                        next_probe = decisions + backoff
                        backoff = min(backoff * 2, 160)
            process = chosen or ready[0]
            ready.remove(process)
            check_need = list(process.need)
            eligible, count, reason = checker(check_need, available)
            count += probe_cost
            comparisons += count
            events.append(Event(
                clock, cycle, algorithm_name, "safety_check", process.pid,
                available.copy(), check_need,
                "SAFE" if eligible else "PRIMARY_UNSAFE",
                count, reason, [item.pid for item in ready],
            ))
            clock += 1
            if eligible:
                if enhanced:
                    for waiting in ready:
                        if waiting.arrival_time < process.arrival_time:
                            overtaken[waiting.pid] += 1
                available[:] = [
                    current + allocated
                    for current, allocated in zip(available, process.allocation)
                ]
                sequence.append(process.pid)
                events.append(Event(
                    clock, cycle, algorithm_name, "complete", process.pid,
                    available.copy(), check_need, "COMPLETED", 0,
                    "Allocation released.",
                ))
                clock += process.burst_time
                progress = True
            else:
                primary.append(process)
                primary_history.append(process.pid)
                retries += 1
            if clock >= timer:
                cycle += 1
                timer = clock + cycle_duration
                if primary:
                    ready.extend(primary)
                    primary.clear()
            continue

        if primary:
            if not progress and not pending:
                unsafe.extend(process.pid for process in primary)
                for process in primary:
                    events.append(Event(
                        clock, cycle, algorithm_name, "stuck", process.pid,
                        available.copy(), list(process.need), "UNSAFE", 0,
                        "No resource release can make this process safe.",
                    ))
                primary.clear()
                break
            progress = False
            clock = max(clock, timer)
            cycle += 1
            timer = clock + cycle_duration
            ready.extend(primary)
            primary.clear()
            continue

        if pending:
            clock = max(clock, pending[0].arrival_time)

    return _result(
        algorithm_name, sequence, primary_history, unsafe,
        available, comparisons, retries, events, clock,
        {"cycle_duration": cycle_duration, "variant": "enhanced" if enhanced else "paper DBDAA"},
    )


def run_dbdaa(
    processes: list[Process], totals: list[int], cycle_duration: int = 30,
) -> AlgorithmResult:
    return _run_dynamic(
        processes, totals, cycle_duration, "Original DBDAA",
        lambda need, available: dbdaa_check(need, available),
    )


def run_enhanced(
    processes: list[Process], totals: list[int], cycle_duration: int = 30,
) -> AlgorithmResult:
    adaptive = _AdaptiveChecker()
    return _run_dynamic(
        processes, totals, cycle_duration, "Enhanced DBDAA",
        adaptive.check, enhanced=True,
    )


def run_all(
    processes: list[Process], totals: list[int], cycle_duration: int = 30,
) -> list[AlgorithmResult]:
    return [
        run_bankers(processes, totals),
        run_dbdaa(processes, totals, cycle_duration),
        run_enhanced(processes, totals, cycle_duration),
    ]
