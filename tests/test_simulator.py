from algorithms import run_all, run_bankers, run_dbdaa
from analytics import complexity_curve
from datasets import average_case, best_case, worst_case


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
