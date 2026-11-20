"""Reproducible wall-clock comparisons for DBDAA and the enhanced implementation.

Run with: python -m results.tests.runtime_benchmarks
"""
import platform
import random
import statistics
import time

from dbdaa import dbdaa_run
from enhanced import enhanced_final_idle
from results.tests.stress_tests import CountingList, load_counting
from results.tests.workload_tests import WORKLOADS


WORKLOAD_RUNS = 200
WORKLOAD_REPEATS = 5
HIGH_DIMENSION_REPEATS = 7
counting_dbdaa = load_counting("dbdaa.py", "dbdaa_runtime_counting")


def collect_workload_systems(seed, generator, count):
    rng = random.Random(1000 + seed)
    systems = []
    skipped = 0
    while len(systems) < count:
        system = generator(rng)
        process_count = len(system[1])
        dbdaa_result = dbdaa_run(*system, wait_for_cycle=False)
        enhanced_result = enhanced_final_idle(*system)
        if (len(dbdaa_result["safe_sequence"]) != process_count
                or len(enhanced_result["safe_sequence"]) != process_count):
            skipped += 1
            continue
        systems.append(system)
    return systems, skipped


def time_workload(systems):
    dbdaa_times = []
    enhanced_times = []
    dbdaa_run(*systems[0], wait_for_cycle=False)
    enhanced_final_idle(*systems[0])

    for index, system in enumerate(systems):
        for repeat in range(WORKLOAD_REPEATS):
            dbdaa_first = (index + repeat) % 2 == 0
            runners = (
                (("DBDAA", lambda: dbdaa_run(*system, wait_for_cycle=False)),
                 ("Enhanced", lambda: enhanced_final_idle(*system)))
                if dbdaa_first else
                (("Enhanced", lambda: enhanced_final_idle(*system)),
                 ("DBDAA", lambda: dbdaa_run(*system, wait_for_cycle=False)))
            )
            for name, run in runners:
                start = time.perf_counter()
                result = run()
                elapsed_ms = (time.perf_counter() - start) * 1000
                if name == "DBDAA":
                    dbdaa_times.append(elapsed_ms)
                    if len(result["safe_sequence"]) != len(system[1]):
                        raise AssertionError("DBDAA failed to finish a retained safe workload")
                else:
                    enhanced_times.append(elapsed_ms)
                    if len(result["safe_sequence"]) != len(system[1]):
                        raise AssertionError("Enhanced failed to finish a retained safe workload")

    return dbdaa_times, enhanced_times


def high_dimension_system(process_count, resource_types):
    total = list(range(1, resource_types + 1))
    maximum = [total[:] for _ in range(process_count)]
    allocation = [[0] * resource_types for _ in range(process_count)]
    burst = [1] * process_count
    arrival = [0] * process_count
    return total, maximum, allocation, burst, arrival


def time_high_dimension(system):
    dbdaa_result = dbdaa_run(*system, wait_for_cycle=False)
    enhanced_result = enhanced_final_idle(*system)
    if (dbdaa_result["safe_sequence"] != enhanced_result["safe_sequence"]
            or dbdaa_result["end_time"] != enhanced_result["end_time"]):
        raise AssertionError("High-dimension benchmark changed the execution result")

    times = {"DBDAA": [], "Enhanced": []}
    for _ in range(HIGH_DIMENSION_REPEATS + 1):
        for name, run in (("DBDAA", lambda: dbdaa_run(*system, wait_for_cycle=False)),
                          ("Enhanced", lambda: enhanced_final_idle(*system))):
            start = time.perf_counter()
            run()
            elapsed_ms = (time.perf_counter() - start) * 1000
            if _ > 0:
                times[name].append(elapsed_ms)

    CountingList.comparisons = 0
    counted_dbdaa = counting_dbdaa.dbdaa_run(*system, wait_for_cycle=False)
    dbdaa_order = CountingList.comparisons
    counted_enhanced = enhanced_final_idle(*system)

    return {
        "dbdaa_ms": statistics.median(times["DBDAA"]),
        "enhanced_ms": statistics.median(times["Enhanced"]),
        "dbdaa_checks": counted_dbdaa["comparisons"],
        "enhanced_checks": counted_enhanced["comparisons"],
        "dbdaa_work": counted_dbdaa["comparisons"] + dbdaa_order,
        "enhanced_work": counted_enhanced["comparisons"] + counted_enhanced["sort_comparisons"],
    }


def main():
    print("Runtime comparison: DBDAA idle retry vs Enhanced + idle retry")
    print("Python: %s | Platform: %s" % (platform.python_version(), platform.platform()))
    print("Wall time excludes startup and input generation; systems are warmed once.")
    print("\nSeven workload families: %d systems/family, %d timed repetitions/system" %
          (WORKLOAD_RUNS, WORKLOAD_REPEATS))
    print("Workload | systems | DBDAA mean ms | Enhanced mean ms | Enhanced/DBDAA | skipped")
    for seed, (code, _text, _structure, generator, _heavy) in enumerate(WORKLOADS):
        systems, skipped = collect_workload_systems(seed, generator, WORKLOAD_RUNS)
        dbdaa_times, enhanced_times = time_workload(systems)
        dbdaa_mean = statistics.mean(dbdaa_times)
        enhanced_mean = statistics.mean(enhanced_times)
        print("%s | %d | %.4f | %.4f | %.2fx | %d" %
              (code, len(systems), dbdaa_mean, enhanced_mean,
               enhanced_mean / dbdaa_mean, skipped))

    print("\nHigh-dimensional safe systems: all processes arrive at 0, allocation is zero,")
    print("and each process maximum equals the total resource vector.")
    print("Processes | Resources | DBDAA ms median | Enhanced ms median | DBDAA checks | Enhanced checks | DBDAA work | Enhanced work")
    for process_count in (100, 300):
        for resource_types in (50, 100, 200):
            system = high_dimension_system(process_count, resource_types)
            result = time_high_dimension(system)
            print("%10d | %9d | %15.2f | %18.2f | %12d | %15d | %10d | %13d" %
                  (process_count, resource_types, result["dbdaa_ms"], result["enhanced_ms"],
                   result["dbdaa_checks"], result["enhanced_checks"],
                   result["dbdaa_work"], result["enhanced_work"]))


if __name__ == "__main__":
    main()
