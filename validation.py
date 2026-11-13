from __future__ import annotations

from models import Process


def validate_input(processes: list[Process], totals: list[int]) -> None:
    if not processes:
        raise ValueError("Add at least one process.")
    if not totals or any(not isinstance(value, int) or value < 0 for value in totals):
        raise ValueError("Total resources must be non-negative integers.")
    dimensions = len(totals)
    allocated = [0] * dimensions
    ids: set[str] = set()
    for process in processes:
        if process.pid in ids:
            raise ValueError(f"Duplicate process ID: {process.pid}.")
        ids.add(process.pid)
        if len(process.maximum) != dimensions or len(process.allocation) != dimensions:
            raise ValueError(f"{process.pid}: matrix dimensions must match resource types.")
        if process.arrival_time < 0 or process.burst_time <= 0:
            raise ValueError(f"{process.pid}: arrival must be >= 0 and burst must be > 0.")
        if any(value < 0 for value in process.maximum + process.allocation):
            raise ValueError(f"{process.pid}: resource values cannot be negative.")
        if any(allocated_value > maximum for allocated_value, maximum in zip(process.allocation, process.maximum)):
            raise ValueError(f"{process.pid}: allocation cannot exceed maximum.")
        for index, value in enumerate(process.allocation):
            allocated[index] += value
    if any(value > totals[index] for index, value in enumerate(allocated)):
        raise ValueError("Total allocation exceeds system capacity.")


def initial_available(processes: list[Process], totals: list[int]) -> list[int]:
    validate_input(processes, totals)
    return [
        total - sum(process.allocation[index] for process in processes)
        for index, total in enumerate(totals)
    ]
