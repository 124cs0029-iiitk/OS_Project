# workload_tests.py - seven kinds of workload that differ in STRUCTURE (not just in tightness)
# Run:  python workload_tests.py        (a few seconds)
#
# For every workload: DBDAA (cycle), DBDAA (idle retry) and Enhanced + idle on 200 random systems that
# are safe by construction. Reported: safety-check comparisons ("checks"), comparisons spent on ordering
# the ready queue ("order"), their sum ("work"), average and longest waiting time, finish time, and a paired
# comparison  Enhanced + idle  versus  DBDAA (idle retry)  with a 95% confidence interval.
import math
import random
import sys

from data import DATASETS, TOTAL_RESOURCES
from dbdaa import dbdaa_run
from enhanced import enhanced_final_idle
from stress_tests import CountingList, load_counting

counting = load_counting("dbdaa.py", "dbdaa_counting")


def mean(values):
    return sum(values) / len(values)


# ---------------------------------------------------------------- building safe systems
def build(rng, n, d, alloc_fn, need_fn, burst_fn, arrival_fn, avail0=None):
    """A system that can finish: processes get a random 'finishing order' and every need is chosen
    so that it fits into what is free at its turn in that order."""
    allocation = [alloc_fn(rng, i, d) for i in range(n)]
    avail = avail0[:] if avail0 else [rng.randint(1, 3) for _ in range(d)]
    total = [avail[j] + sum(allocation[i][j] for i in range(n)) for j in range(d)]
    order = list(range(n))
    rng.shuffle(order)
    work = avail[:]
    need = [None] * n
    for i in order:
        need[i] = [max(0, min(work[j], v)) for j, v in enumerate(need_fn(rng, i, work, d))]
        for j in range(d):
            work[j] += allocation[i][j]
    maximum = [[allocation[i][j] + need[i][j] for j in range(d)] for i in range(n)]
    burst = [burst_fn(rng, i) for i in range(n)]
    arrival = [arrival_fn(rng, i, n) for i in range(n)]
    return total, maximum, allocation, burst, arrival


def small_alloc(rng, i, d):
    return [rng.randint(0, 2) for _ in range(d)]


def uniform_burst(rng, i):
    return rng.randint(1, 6)


def spread_arrival(latest):
    return lambda rng, i, n: 0 if i < n // 3 else rng.randint(0, latest)


# ---------------------------------------------------------------- the seven workloads
def w1_paper_data(rng):
    name = rng.choice(list(DATASETS))
    maximum, allocation, burst = DATASETS[name]
    arrival = [rng.randint(0, 40) for _ in maximum]          # only the arrival times are random
    return TOTAL_RESOURCES, maximum, allocation, burst, arrival


def w2_heavy_tailed_needs(rng):
    def need(rng, i, work, d):
        out = []
        for j in range(d):
            if rng.random() < 0.10:
                out.append(work[j] - rng.randint(0, 2))               # a rare huge need
            else:
                out.append(int(work[j] * rng.random() ** 4))          # most needs are tiny
        return out
    return build(rng, 40, 5, small_alloc, need, uniform_burst, spread_arrival(60))


def w3_specialised(rng):
    def need(rng, i, work, d):
        dominant = i % d                                              # each process wants one resource type
        return [work[j] - rng.randint(0, 2) if j == dominant else rng.randint(0, 1) for j in range(d)]
    return build(rng, 40, 5, small_alloc, need, uniform_burst, spread_arrival(60))


def w4_bursty_waves(rng):
    def need(rng, i, work, d):
        return [work[j] - rng.randint(0, 6) for j in range(d)]
    return build(rng, 48, 5, small_alloc, need, uniform_burst, lambda rng, i, n: (i // 8) * 60)   # 6 waves, gaps of ~60


def w5_late_heavy(rng):
    """60 small processes arrive steadily until t = 118 and hold nothing. Four heavy processes arrive LATE
    (t = 40..55). They always fit (10 of each resource are free) but have a bigger Max_Need than the small
    ones, so the sorted queue always serves newcomers first: starvation by overtaking, not by resources."""
    d = 5
    small = 60
    n = small + 4
    allocation = [[0] * d for _ in range(n)]
    maximum = [[rng.randint(0, 2) for _ in range(d)] for _ in range(small)]
    maximum += [[rng.randint(6, 9) for _ in range(d)] for _ in range(4)]
    burst = [rng.randint(2, 3) for _ in range(n)]
    arrival = [2 * i for i in range(small)] + [40, 45, 50, 55]
    return [10] * d, maximum, allocation, burst, arrival


def w6_heavy_tailed_runtimes(rng):
    def need(rng, i, work, d):
        return [work[j] - rng.randint(0, 4) for j in range(d)]
    def burst(rng, i):
        return min(100, int(1 + 2 * rng.paretovariate(1.2)))          # most jobs are short, a few run very long
    return build(rng, 40, 5, small_alloc, need, burst, spread_arrival(80))


def w7_abundant(rng):
    """Control: resources are abundant and needs tiny, so nothing is ever tight."""
    def need(rng, i, work, d):
        return [rng.randint(0, 2) for _ in range(d)]
    return build(rng, 40, 5, small_alloc, need, uniform_burst, spread_arrival(60), avail0=[30] * 5)


WORKLOADS = [
    ("W1", "the paper's own data (Data 1-3) with random arrival times",
     "hand-built data, not generated", w1_paper_data, None),
    ("W2", "heavy-tailed needs: mostly tiny, a few huge",
     "needs follow a very skewed distribution", w2_heavy_tailed_needs, None),
    ("W3", "specialised processes: each wants one resource type",
     "every quick test fails on the dominant resource", w3_specialised, None),
    ("W4", "bursty waves: 6 waves of 8 simultaneous arrivals, quiet gaps of ~60",
     "batches of arrivals, long idle stretches", w4_bursty_waves, None),
    ("W5", "late heavy arrivals into a busy system (heavy processes always fit)",
     "starvation purely by being overtaken", w5_late_heavy, [60, 61, 62, 63]),
    ("W6", "heavy-tailed run times: mostly short, a few very long jobs",
     "long non-preemptive runs", w6_heavy_tailed_runtimes, None),
    ("W7", "control: abundant resources, tiny needs",
     "nothing is tight, so we expect no gain on safety checks", w7_abundant, None),
]


# ---------------------------------------------------------------- measuring
def measure_one(kind, system):
    if kind == "dbdaa_cycle" or kind == "dbdaa_idle":
        CountingList.comparisons = 0
        r = counting.dbdaa_run(*system, wait_for_cycle=(kind == "dbdaa_cycle"))
        order = CountingList.comparisons
    else:
        r = enhanced_final_idle(*system)
        order = r["sort_comparisons"]
    return r, order


def summarise(r, order, system, heavy):
    arrival = system[4]
    n = len(arrival)
    waits = [r["first_start"][i] - arrival[i] for i in range(n)]
    out = {"checks": r["comparisons"], "order": order, "work": r["comparisons"] + order,
           "avg": mean(waits), "max": max(waits), "finish": r["end_time"]}
    if heavy:
        out["heavy"] = mean([waits[i] for i in heavy])
    return out


def paired(values_new, values_base):
    diffs = [a - b for a, b in zip(values_new, values_base)]
    m = mean(diffs)
    sd = math.sqrt(sum((x - m) ** 2 for x in diffs) / (len(diffs) - 1)) if len(diffs) > 1 else 0.0
    better = sum(1 for x in diffs if x < 0)
    worse = sum(1 for x in diffs if x > 0)
    return m, 1.96 * sd / math.sqrt(len(diffs)), better, worse, len(diffs) - better - worse


def run_workload(code, text, structure, generator, heavy, runs=200, seed=0):
    rng = random.Random(1000 + seed)
    kinds = [("DBDAA (cycle)", "dbdaa_cycle"), ("DBDAA (idle retry)", "dbdaa_idle"), ("Enhanced + idle", "enhanced")]
    rows = {name: [] for name, _ in kinds}
    skipped = 0
    while len(rows["Enhanced + idle"]) < runs:
        system = generator(rng)
        n = len(system[1])
        results = []
        for name, kind in kinds:
            r, order = measure_one(kind, system)
            results.append((name, r, order))
        if any(len(r["safe_sequence"]) != n for _, r, _ in results):
            skipped += 1
            continue
        for name, r, order in results:
            rows[name].append(summarise(r, order, system, heavy))
    print("\n%s  %s" % (code, text))
    print("    (%s; %d systems, %d discarded as not finishable)" % (structure, runs, skipped))
    columns = ["checks", "order", "work", "avg", "max", "finish"] + (["heavy"] if heavy else [])
    header = {"checks": "checks", "order": "order", "work": "work", "avg": "avg wait", "max": "max wait",
              "finish": "finish", "heavy": "heavy wait"}
    print("    %-20s" % "" + "".join("%11s" % header[c] for c in columns))
    for name, _ in kinds:
        print("    %-20s" % name + "".join("%11.1f" % mean([row[c] for row in rows[name]]) for c in columns))
    base = rows["DBDAA (idle retry)"]
    new = rows["Enhanced + idle"]
    for c, label in (("checks", "safety checks"), ("work", "total work"), ("max", "longest wait")):
        m, ci, b, w, e = paired([row[c] for row in new], [row[c] for row in base])
        print("    Enhanced + idle minus DBDAA (idle retry), %-13s %+8.1f +- %-6.1f (better %3d, worse %3d, equal %3d)"
              % (label + ":", m, ci, b, w, e))
    if heavy:
        m, ci, b, w, e = paired([row["heavy"] for row in new], [row["heavy"] for row in base])
        print("    Enhanced + idle minus DBDAA (idle retry), %-13s %+8.1f +- %-6.1f (better %3d, worse %3d, equal %3d)"
              % ("heavy wait:", m, ci, b, w, e))
    return rows


if __name__ == "__main__":
    print("Seven workloads; waits are measured from arrival; 'work' = safety checks + ordering comparisons")
    for k, (code, text, structure, generator, heavy) in enumerate(WORKLOADS):
        run_workload(code, text, structure, generator, heavy, seed=k)