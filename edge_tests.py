# edge_tests.py - edge cases and adversarial inputs
# Run:  python edge_tests.py        (about 20 seconds; PASS / FAIL for what must hold,
#                                    NOTE for limitations that we measure and report)
#
#   Part E: edge cases (empty input, one process, d = 1, ties, boundaries, odd times, bad input, size)
#   Part A: adversarial inputs that try to break our claims, including the paper's
#     A1: processes must run in the REVERSE of DBDAA's sort order (tests the paper's worst case)
#     A2: the worst repeating pattern for the adaptive check (how much worse than the paper's check?)
#     A3: aging probes while the longest-waiting process stays blocked for the whole run
#     A4: ordering cost when the queue keeps growing and the Max_Need pattern is unfavourable
import functools
import itertools
import random
import sys
import threading
import types

from bankers import bankers_safety
from dbdaa import dbdaa_run, safety_check
from enhanced import AdaptiveChecker, enhanced_run, enhanced_final, enhanced_final_idle
from stress_tests import replay_problems

VARIANTS = [
    ("DBDAA (cycle)",      lambda *s: dbdaa_run(*s)),
    ("DBDAA (idle retry)", lambda *s: dbdaa_run(*s, wait_for_cycle=False)),
    ("Enhanced (cycle)",   lambda *s: enhanced_final(*s)),
    ("Enhanced + idle",    lambda *s: enhanced_final_idle(*s)),
]
failures = 0


def report(name, ok, detail=""):
    global failures
    if not ok:
        failures += 1
    print("%-6s %s %s" % ("PASS" if ok else "FAIL", name, detail))


def note(text):
    print("NOTE   " + text)


def run_guarded(fn, args, timeout=20):
    """Run fn(*args) in a thread so that a hang is reported instead of freezing the test."""
    box = {}

    def target():
        try:
            box["result"] = fn(*args)
        except Exception as error:
            box["error"] = error
    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout)
    if "result" in box:
        return "ok", box["result"]
    if "error" in box:
        return "error", box["error"]
    return "hang", None


# =============================================================== Part E: edge cases
EDGE_CASES = [
    ("E1", "no processes (n = 0)", ([5, 5], [], [], [], []),
     lambda r: r["safe_sequence"] == [] and r["comparisons"] == 0 and r["stuck"] == []),
    ("E2", "a single safe process", ([5, 5], [[3, 3]], [[1, 1]], [2], [0]),
     lambda r: r["safe_sequence"] == [1] and r["comparisons"] == 1),
    ("E3", "a process whose maximum exceeds the total", ([5, 5], [[9, 3]], [[1, 1]], [2], [0]),
     lambda r: r["unsafe_sequence"] == [1] and r["safe_sequence"] == [] and r["comparisons"] == 0),
    ("E4", "a single resource type (d = 1)", ([10], [[6], [4], [8]], [[2], [1], [3]], [2, 2, 2], [0, 0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2, 3]),
    ("E5", "nobody needs anything more (all needs 0)", ([6, 6], [[2, 2]] * 3, [[2, 2]] * 3, [1, 1, 1], [0, 0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2, 3] and r["comparisons"] == 3),
    ("E6", "identical processes (every key is a tie; order must stay P1..P4)",
     ([8, 8], [[3, 3]] * 4, [[1, 1]] * 4, [2] * 4, [0] * 4),
     lambda r: r["safe_sequence"] == [1, 2, 3, 4]),
    ("E7", "maximum exactly equal to the total (valid, not oversized)", ([5, 5], [[5, 5]], [[0, 0]], [2], [0]),
     lambda r: r["safe_sequence"] == [1] and r["unsafe_sequence"] == []),
    ("E8", "nobody holds any resource", ([5, 5], [[3, 3], [2, 2]], [[0, 0], [0, 0]], [2, 2], [0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2]),
    ("E9", "burst time 0", ([5, 5], [[3, 3], [2, 2]], [[1, 1], [1, 1]], [0, 0], [0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2] and r["end_time"] == 0),
    ("E10", "a gap of 10^9 time units between arrivals", ([5, 5], [[3, 3], [2, 2]], [[1, 1], [1, 1]], [2, 2], [0, 10 ** 9]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2] and r["end_time"] == 10 ** 9 + 2),
    ("E11", "deadlocked from the start (nothing can ever run)", ([4, 4], [[4, 4], [4, 4]], [[2, 2], [2, 2]], [2, 2], [0, 0]),
     lambda r: r["safe_sequence"] == [] and sorted(r["stuck"]) == [1, 2]),
    ("E12", "fractional burst times", ([5, 5], [[3, 3], [2, 2]], [[1, 1], [1, 1]], [1.5, 2.5], [0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2] and abs(r["end_time"] - 4.0) < 1e-9),
    ("E13", "a process arrives exactly when a cycle ends (t = 30)",
     ([20, 20], [[3, 3], [8, 8]], [[1, 1], [1, 1]], [30, 2], [0, 30]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2] and min(s for p, s, e in r["timeline"] if p == 2) >= 30),
    ("E14", "every process is oversized", ([4, 4], [[9, 1], [1, 9]], [[0, 0], [0, 0]], [1, 1], [0, 0]),
     lambda r: sorted(r["unsafe_sequence"]) == [1, 2] and r["comparisons"] == 0),
    ("E15", "no resources at all (total 0, nobody needs any)", ([0, 0], [[0, 0], [0, 0]], [[0, 0], [0, 0]], [1, 1], [0, 0]),
     lambda r: sorted(r["safe_sequence"]) == [1, 2]),
]

BAD_INPUT = [
    ("a process holds more than its maximum", ([5, 5], [[2, 2]], [[3, 3]], [2], [0])),
    ("a negative maximum", ([5, 5], [[-1, 2]], [[0, 0]], [2], [0])),
    ("a row with the wrong number of values", ([5, 5], [[3, 3, 3]], [[1, 1]], [2], [0])),
    ("a negative arrival time", ([5, 5], [[3, 3]], [[1, 1]], [2], [-5])),
    ("a negative burst time", ([5, 5], [[3, 3]], [[1, 1]], [-2], [0])),
    ("lists of different length", ([5, 5], [[3, 3]], [[1, 1]], [2, 2], [0])),
    ("no resource types", ([], [[]], [[]], [1], [0])),
]


def part_e():
    print("\nPart E: edge cases (each must hold for every variant)")
    for code, text, args, holds in EDGE_CASES:
        bad = []
        for name, fn in VARIANTS:
            status, result = run_guarded(fn, args)
            if status != "ok" or not holds(result):
                bad.append("%s: %s" % (name, status if status != "ok" else "wrong result"))
        report("%s  %s" % (code, text), not bad, "; ".join(bad))

    # size and shape: many processes, many resource types
    n = 2000
    args = ([10 ** 6, 10 ** 6], [[3, 3]] * n, [[1, 1]] * n, [1] * n, [0] * n)
    bad = [name for name, fn in VARIANTS if run_guarded(fn, args, 60)[0] != "ok"]
    report("E16  2000 identical processes arriving together", not bad, str(bad) if bad else "")
    d = 50
    total = [100] * d
    args = (total, [[3] * d, [2] * d, [4] * d], [[1] * d, [1] * d, [1] * d], [1, 1, 1], [0, 0, 0])
    bad = []
    for name, fn in VARIANTS:
        status, r = run_guarded(fn, args)
        if status != "ok" or sorted(r["safe_sequence"]) != [1, 2, 3]:
            bad.append(name)
    report("E17  50 resource types (d = 50)", not bad, str(bad) if bad else "")

    print("\nPart E, invalid input (every variant must raise ValueError with a message)")
    for text, args in BAD_INPUT:
        bad = []
        for name, fn in VARIANTS:
            status, result = run_guarded(fn, args)
            if status != "error" or not isinstance(result, ValueError):
                bad.append(name)
        report("rejects: " + text, not bad, str(bad) if bad else "")


# =============================================================== Part A: adversarial inputs
def inversion(n):
    """d = 2. Process i needs R1 = 1000 + i (so Max_Need grows with i) and R2 = n-1-i
    (so the processes can only run in the order n-1, n-2, ..., 0): the reverse of the sort order."""
    allocation = [[0, 1] for _ in range(n)]
    need = [[1000 + i, n - 1 - i] for i in range(n)]
    maximum = [[allocation[i][j] + need[i][j] for j in range(2)] for i in range(n)]
    return [1000 + n, n], maximum, allocation, [1] * n, [0] * n


def part_a1():
    print("\nA1: processes must run in the reverse of DBDAA's sort order (d = 2)")
    print("    %5s %12s %14s %18s %16s" % ("n", "Traditional", "DBDAA (cycle)", "DBDAA (idle retry)", "Enhanced + idle"))
    growth = {}
    previous = {}
    for n in (10, 25, 50, 100, 200, 400):
        s = inversion(n)
        total, maximum, allocation = s[0], s[1], s[2]
        available = [total[j] - sum(allocation[i][j] for i in range(n)) for j in range(2)]
        safe, seq, trad = bankers_safety(available, maximum, allocation)
        results = {}
        ok = safe
        for name, fn in (("a", VARIANTS[0][1]), ("b", VARIANTS[1][1]), ("c", VARIANTS[3][1])):
            r = fn(*s)
            results[name] = r
            ok = ok and len(r["safe_sequence"]) == n and not replay_problems(*s, r)
        report("A1 n=%d: every algorithm finishes all processes with a valid run" % n, ok)
        print("    %5d %12d %14d %18d %16d" % (n, trad, results["a"]["comparisons"], results["b"]["comparisons"],
                                                results["c"]["comparisons"]))
        if n in (200, 400):
            growth[n] = (trad, results["a"]["comparisons"], results["c"]["comparisons"])
    f_trad = growth[400][0] / growth[200][0]
    f_dbdaa = growth[400][1] / growth[200][1]
    f_enh = growth[400][2] / growth[200][2]
    note("doubling n from 200 to 400 multiplies the comparisons by %.2f (traditional), %.2f (DBDAA), %.2f (Enhanced)"
         % (f_trad, f_dbdaa, f_enh))
    note("a factor near 4 means quadratic growth: DBDAA's worst case is NOT linear over all its retries;")
    note("on this input DBDAA needs %.2fx the comparisons of the traditional algorithm" % (growth[400][1] / growth[400][0]))
    report("A1 DBDAA grows about quadratically on this input (factor between 3.5 and 4.5)", 3.5 <= f_dbdaa <= 4.5)


def part_a2():
    print("\nA2: adaptive check versus the paper's check on every repeating pattern of")
    print("    hard (H, costs 7 with the paper's check) and easy (E, costs 1) checks, period 1..10")
    available = [2, 2, 7, 8, 5]
    hard = [1, 2, 3, 4, 2]
    easy = [1, 1, 1, 1, 1]
    assert safety_check(hard, available) == (True, 7) and safety_check(easy, available) == (True, 1)
    worst = (0.0, "")
    best = (99.0, "")
    for period in range(1, 11):
        for pattern in itertools.product("HE", repeat=period):
            sequence = ([hard if p == "H" else easy for p in pattern] * (200 // period + 1))[:200]
            paper = sum(safety_check(v, available)[1] for v in sequence)
            checker = AdaptiveChecker()
            ours = sum(checker.check(v, available)[1] for v in sequence)
            ratio = ours / paper
            if ratio > worst[0]:
                worst = (ratio, "".join(pattern))
            if ratio < best[0]:
                best = (ratio, "".join(pattern))
    note("worst pattern found: %s repeated -> the adaptive check uses %.2fx the comparisons of the paper's check" % (worst[1], worst[0]))
    note("best pattern found:  %s repeated -> %.2fx" % (best[1], best[0]))
    report("A2 the adaptive check never uses more than 2x the paper's comparisons (all patterns, period <= 10)", worst[0] <= 2.0)


def blocked_heavy(n_small):
    """Process 0 needs R2 = n_small units that only come back when every small process has run."""
    n = n_small + 1
    allocation = [[0, 0]] + [[0, 1]] * n_small
    need = [[1, n_small]] + [[0, 0]] * n_small
    maximum = [[allocation[i][j] + need[i][j] for j in range(2)] for i in range(n)]
    return [5, n_small], maximum, allocation, [1] * n, [0] + list(range(n_small))


def part_a3():
    print("\nA3: aging probes while the longest-waiting process stays blocked for the whole run")
    print("    %8s %14s %16s %8s" % ("small", "check only", "check + aging", "extra"))
    last_overhead = None
    for n_small in (50, 200, 1000):
        s = blocked_heavy(n_small)
        a = enhanced_run(*s, adaptive=True, wait_for_cycle=False)
        b = enhanced_run(*s, adaptive=True, overtake_limit=5, probe_gap=5, wait_for_cycle=False)
        assert len(a["safe_sequence"]) == len(b["safe_sequence"]) == len(s[1])
        print("    %8d %14d %16d %+8d" % (n_small, a["comparisons"], b["comparisons"], b["comparisons"] - a["comparisons"]))
        last_overhead = (b["comparisons"] - a["comparisons"]) / a["comparisons"]
    report("A3 aging overhead stays below 2%% when the candidate is blocked for 1000 decisions (%.1f%%)" % (100 * last_overhead),
           last_overhead < 0.02)


class CountingList(list):
    comparisons = 0

    def sort(self, key=None, reverse=False):
        keys = [key(x) if key else x for x in self]
        order = list(range(len(self)))

        def compare(a, b):
            CountingList.comparisons += 1
            return (keys[a] > keys[b]) - (keys[a] < keys[b])
        order.sort(key=functools.cmp_to_key(compare))
        self[:] = [self[i] for i in order]


def growing_queue(n, kind):
    """One process arrives per time unit and runs 3 units, so the ready queue keeps growing."""
    if kind == "equal keys":
        needs = [5] * n
    elif kind == "increasing":
        needs = [i + 1 for i in range(n)]
    elif kind == "decreasing":
        needs = [n - i for i in range(n)]
    else:
        generator = random.Random(1)
        needs = [generator.randint(1, n) for _ in range(n)]
    return [10 * n, 10 * n], [[x, 0] for x in needs], [[0, 0] for _ in range(n)], [3] * n, list(range(n))


def part_a4():
    print("\nA4: ordering comparisons when the queue keeps growing (n = 400)")
    source = open("dbdaa.py").read()
    assert "ready_queue = []" in source
    counting = types.ModuleType("dbdaa_counting")
    counting.CountingList = CountingList
    exec(compile(source.replace("ready_queue = []", "ready_queue = CountingList()"), "dbdaa.py", "exec"),
         counting.__dict__)
    print("    %-12s %14s %8s" % ("Max_Need", "DBDAA's sort", "ours"))
    for kind in ("equal keys", "increasing", "decreasing", "random"):
        s = growing_queue(400, kind)
        CountingList.comparisons = 0
        counting.dbdaa_run(*s)
        theirs = CountingList.comparisons
        ours = enhanced_final_idle(*s)["sort_comparisons"]
        print("    %-12s %14d %8d" % (kind, theirs, ours))
        report("A4 ordering is not more expensive than DBDAA's sort (%s)" % kind, ours <= theirs)


if __name__ == "__main__":
    part_e()
    print("\nPart A: adversarial inputs")
    part_a1()
    part_a2()
    part_a3()
    part_a4()
    print("\n" + ("ALL TESTS PASSED" if failures == 0 else "%d TEST(S) FAILED" % failures))
    sys.exit(1 if failures else 0)