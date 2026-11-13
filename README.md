@'
# DBDAA: Dynamic Banker's Deadlock Avoidance Algorithm

OS course project: a from-scratch Python reimplementation of DBDAA, validated against the paper,
plus our own modifications and the experiments that compare them.

Paper: Zohora M.F., Farhin F., Kaiser M.S. (2024), "DBDAA: A real-time approach to Dynamic Banker's
Deadlock Avoidance Algorithm with optimized time complexity", PLOS ONE 19(9): e0310807.
https://doi.org/10.1371/journal.pone.0310807

## Authors

- Poojith Kumar
- Navadeep

## Files

| File | What it does |
|---|---|
| `data.py` | The paper's three datasets (Tables 2, 3, 4 = Data 1, 2, 3) |
| `bankers.py` | Traditional Banker's safety algorithm |
| `dbdaa.py` | DBDAA (arrivals, sorted queue, optimized safety check, timer cycle, retries) |
| `enhanced.py` | Our version: adaptive safety check, gated aging, idle retry, ordered insertion |
| `compare.py`, `compare2.py` | Early comparison scripts |
| `final_compare.py` | All final experiments |
| `stress_tests.py` | Correctness tests: paper numbers, exactness of the check, independent replay, verdicts, no infinite loops, total-work measurement |
| `results.txt` | Output of `final_compare.py` |

## Run

Python 3.8+ and the standard library only.

    python bankers.py
    python dbdaa.py
    python enhanced.py
    python final_compare.py
    python stress_tests.py

## Validation

On the paper's data the traditional algorithm needs 85 / 100 / 125 comparisons and DBDAA needs
10 / 36 / 70 in its first round, matching the paper's Table 8. The safe sequences and timelines
match the paper's Tables 5-7 and Figs 3-5. `stress_tests.py` re-checks this and also tests the
code on thousands of random systems.

## Our modifications

1. Adaptive check: switch to a plain check when DBDAA's shortcut keeps failing (tight systems).
2. Gated aging: a process that has been overtaken at least 5 times by later arrivals may go first,
   but only if it can run right now (1-comparison test, with back-off after failed tries).
3. Idle retry: retry parked processes as soon as the processor would be idle, instead of waiting
   for the 30-unit cycle (this is the second reading of the paper's flowchart).

Implementation detail: processes entering the ready queue are inserted with a binary search or
merged in as a batch, instead of re-sorting the whole queue. The order, and therefore every
result, is identical to DBDAA's.

## Results in short

- Safety-check comparisons: fewer than DBDAA in tight systems (10% to 30% fewer in our tests),
  about equal when slightly tight, and a few comparisons more in loose systems.
- Total work including ordering the queue (which the paper does not count): 14% to 51% less
  than DBDAA in all tested scenarios.
- Starvation test: waiting time of heavy processes 82% lower.
- Idle retry removes the idle time of the fixed 30-unit cycle (average wait 18% to 24% lower in
  tight systems); it applies to DBDAA as well.

## Status and known issues

- The paper does not count sorting. In our measurements DBDAA's ordering costs about as much as
  its safety checks.
- Not modelled: processes requesting more resources while running, multiple processors, preemption.
'@ | Set-Content -Encoding ascii README.md