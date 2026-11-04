# DBDAA: Dynamic Banker's Deadlock Avoidance Algorithm

OS course project: a from-scratch Python reimplementation of DBDAA, validated against the paper,
plus our own modifications and the experiments that compare them.

Paper: Zohora M.F., Farhin F., Kaiser M.S. (2024), "DBDAA: A real-time approach to Dynamic Banker's
Deadlock Avoidance Algorithm with optimized time complexity", PLOS ONE 19(9): e0310807.
https://doi.org/10.1371/journal.pone.0310807

## Files

| File | What it does |
|---|---|
| `data.py` | The paper's three datasets (Tables 2, 3, 4 = Data 1, 2, 3) |
| `bankers.py` | Traditional Banker's safety algorithm |
| `dbdaa.py` | DBDAA (arrivals, sorted queue, optimized safety check, timer cycle, retries) |
| `enhanced.py` | Our version: adaptive safety check, gated aging, optional idle retry |
| `compare.py`, `compare2.py` | Early comparison scripts |
| `final_compare.py` | All final experiments |
| `results.txt` | Output of `final_compare.py` |

## Run

Python 3.8+ and the standard library only.

    python bankers.py
    python dbdaa.py
    python enhanced.py
    python final_compare.py

## Validation

On the paper's data the traditional algorithm needs 85 / 100 / 125 comparisons and DBDAA needs
10 / 36 / 70 in its first round, matching the paper's Table 8. The safe sequences and timelines
match the paper's Tables 5-7 and Figs 3-5.

## Our modifications

1. Adaptive check: switch to a plain check when DBDAA's shortcut keeps failing (tight systems).
2. Gated aging: a long-waiting process may go first, but only if it can run right now.
3. Idle retry: retry parked processes as soon as the processor would be idle, instead of waiting
   for the 30-unit cycle (this is the second reading of the paper's flowchart).

## Status and known issues

Work in progress. At this commit:
- `enhanced.py` re-sorts the ready queue before every pick. The paper does not count sorting, but
  this adds hidden cost; it will be changed to sort only when the queue changes.
- The aging trigger is being revised (an "overtaken N times" trigger tests better).
- Not modelled: processes requesting more resources while running, multiple processors, preemption.
