from __future__ import annotations

import time
import pandas as pd

from algorithms import run_all
from models import AlgorithmResult, Process


def metrics(result: AlgorithmResult, totals: list[int], elapsed_ms: float = 0.0) -> dict[str, float | int | str]:
    capacity = sum(totals)
    used = capacity - sum(result.final_available)
    return {
        "Algorithm": result.algorithm,
        "Comparisons": result.comparisons,
        "Wall-clock ms": round(elapsed_ms, 4),
        "Throughput": round(len(result.safe_sequence) / max(result.simulated_time, 1), 4),
        "Utilization %": round(100 * used / capacity, 2) if capacity else 0,
        "Retries": result.retries,
        "Completed": len(result.safe_sequence),
        "Unsafe": len(result.unsafe_sequence),
    }


def benchmark(processes: list[Process], totals: list[int], cycle_duration: int = 30) -> tuple[pd.DataFrame, list[AlgorithmResult]]:
    rows = []
    results = []
    started = time.perf_counter()
    run_results = run_all(processes, totals, cycle_duration)
    elapsed = (time.perf_counter() - started) * 1000
    per_result = elapsed / max(len(run_results), 1)
    results.extend(run_results)
    rows.extend(metrics(result, totals, per_result) for result in run_results)
    return pd.DataFrame(rows), results


def event_frame(result: AlgorithmResult) -> pd.DataFrame:
    frame = pd.DataFrame([
        {
            "Time": event.time,
            "Cycle": event.cycle,
            "Process": str(event.pid or "-"),
            "Action": str(event.action),
            "Decision": str(event.decision),
            "Available": " ".join(str(value) for value in event.available),
            "Need": " ".join(str(value) for value in (event.need or [])),
            "Comparisons": event.comparisons,
            "Reason": str(event.reason),
            "Queue": " -> ".join(str(pid) for pid in event.queue),
        }
        for event in result.events
    ])
    return frame.reset_index(drop=True)


def comparison_trace_frame(result: AlgorithmResult) -> pd.DataFrame:
    """Build the cumulative comparison count used by the virtual comparison chart."""
    total = 0
    rows = []
    for index, event in enumerate(result.events, start=1):
        total += event.comparisons
        rows.append({
            "Step": index,
            "Time": event.time,
            "Process": str(event.pid or "-"),
            "Action": event.action,
            "Step comparisons": event.comparisons,
            "Cumulative comparisons": total,
        })
    if not rows:
        rows.append({
            "Step": 0,
            "Time": 0,
            "Process": "-",
            "Action": "No events",
            "Step comparisons": 0,
            "Cumulative comparisons": 0,
        })
    return pd.DataFrame(rows)


def complexity_curve(
    resource_types: int,
    max_processes: int = 1000,
    step: int = 25,
) -> pd.DataFrame:
    """Return the analytical comparison workload for fixed resource dimensions.

    The curves describe the number of resource comparisons as process count grows.
    They are intentionally separate from wall-clock timing, which varies by machine.
    """
    if resource_types < 1:
        raise ValueError("resource_types must be positive")
    if max_processes < 1:
        raise ValueError("max_processes must be positive")
    if step < 1:
        raise ValueError("step must be positive")

    process_counts = list(range(step, max_processes + 1, step))
    if not process_counts or process_counts[-1] != max_processes:
        process_counts.append(max_processes)
    rows = []
    for n in process_counts:
        dimensions = resource_types
        rows.extend([
            {
                "Processes (n)": n,
                "Algorithm": "Traditional Banker",
                "Best case": n * dimensions,
                "Average case": round(n * (n + 1) * dimensions / 4),
                "Worst case": n * (n + 1) * dimensions // 2,
            },
            {
                "Processes (n)": n,
                "Algorithm": "Original DBDAA",
                "Best case": n,
                "Average case": round(n * (dimensions / 2 + 1)),
                "Worst case": n * (dimensions + 1),
            },
            {
                "Processes (n)": n,
                "Algorithm": "Enhanced DBDAA",
                "Best case": n,
                "Average case": round(n * (dimensions / 3 + 1)),
                "Worst case": round(n * (dimensions / 2 + 1)),
            },
        ])
    return pd.DataFrame(rows)


def gantt_frame(result: AlgorithmResult, processes: list[Process]) -> pd.DataFrame:
    rows = []
    for event in result.events:
        if event.action == "complete" and event.pid is not None:
            process = next(item for item in processes if item.pid == event.pid)
            start = event.time
            finish = start + process.burst_time
            rows.append({
                "Process": event.pid,
                "Start": start,
                "Finish": finish,
                "Duration": process.burst_time,
                "Type": "Safety completion",
            })
    return pd.DataFrame(rows)
