from algorithms import run_all, run_bankers, run_dbdaa, run_enhanced
from analytics import complexity_curve
from datasets import average_case, best_case, worst_case
from models import Process


def test_best_case_dbdaa_matches_expected_comparison_count():
    processes, totals = best_case()
    result = run_dbdaa(processes, totals)
    assert result.safe
    assert len(result.safe_sequence) == 10
    assert result.comparisons == 10


def test_all_safe_algorithms_complete_best_case():
    processes, totals = best_case()
    assert run_bankers(processes, totals).safe
    assert run_dbdaa(processes, totals).safe


def test_scenario_dimensions_and_need_recalculation():
    for loader in (best_case, average_case, worst_case):
        processes, totals = loader()
        assert totals == [20, 25, 30, 35, 30]
        assert len(processes) == 10
        assert all(len(process.maximum) == 5 for process in processes)
        assert all(len(process.need) == 5 for process in processes)


def test_worst_case_exposes_capacity_unsafe_processes_in_every_algorithm():
    processes, totals = worst_case()
    results = run_all(processes, totals)
    assert all(result.unsafe_sequence for result in results)
    assert all(not result.safe for result in results)


def test_complexity_curve_has_all_cases_and_algorithms():
    frame = complexity_curve(resource_types=5, max_processes=100, step=25)
    assert set(frame["Algorithm"]) == {
        "Traditional Banker",
        "Original DBDAA",
        "Enhanced DBDAA",
    }
    assert set(frame.columns) == {
        "Processes (n)", "Algorithm", "Best case", "Average case", "Worst case",
    }
    assert frame["Worst case"].max() > frame["Best case"].max()


def test_enhanced_reduces_checks_for_many_resource_types():
    totals = tuple(range(1, 51))
    processes = [
        Process("P%d" % i, 0, 1, totals, (0,) * len(totals))
        for i in range(10)
    ]

    dbdaa = run_dbdaa(processes, list(totals))
    enhanced = run_enhanced(processes, list(totals))

    assert enhanced.safe
    assert enhanced.safe_sequence == dbdaa.safe_sequence
    assert enhanced.comparisons < dbdaa.comparisons


def test_enhanced_aging_reduces_heavy_process_wait():
    totals = [10] * 5
    small_count = 40
    heavy_count = 4
    processes = [
        Process("S%03d" % i, i, 3, (1,) * 5, (0,) * 5)
        for i in range(small_count)
    ]
    processes.extend(
        Process("H%02d" % i, small_count // 3 + i, 1, (8,) * 5, (0,) * 5)
        for i in range(heavy_count)
    )

    dbdaa = run_dbdaa(processes, totals)
    enhanced = run_enhanced(processes, totals)

    def average_heavy_wait(result):
        first_starts = {}
        for event in result.events:
            if event.action == "safety_check" and event.decision == "SAFE":
                first_starts.setdefault(event.pid, event.time)
        return sum(
            first_starts["H%02d" % i] - (small_count // 3 + i)
            for i in range(heavy_count)
        ) / heavy_count

    assert enhanced.safe
    assert average_heavy_wait(enhanced) < average_heavy_wait(dbdaa)
