# DBDAA: Dynamic Banker's Deadlock Avoidance Algorithm

OS course project: a Python implementation of DBDAA, validated against the reference paper,
with additional algorithm changes and reproducible experiments.

Paper: Zohora M. F., Farhin F., and Kaiser M. S. (2024), "DBDAA: A real-time approach to Dynamic
Banker's Deadlock Avoidance Algorithm with optimized time complexity," PLOS ONE 19(9), e0310807.
https://doi.org/10.1371/journal.pone.0310807

## Authors

- Poojith Kumar
- Navadeep

## Project layout

- Core application and algorithm modules remain in the repository root.
- `reports/` contains the revised text and illustrated reports.
- `results/tests/` contains the paper comparisons, correctness tests, workload tests, runtime
  benchmarks, and the simulator's pytest tests.
- `results/plots/` contains the plot and report generators and their source data.
- `results/data/` contains the CSV data used by the plots.
- `results/images/` contains the paper flowcharts and generated plots.
- `results/outputs/` contains captured experiment outputs and the evidence ZIP.

## Run

Use Python 3.8 or newer. Install dependencies with:

```powershell
python -m pip install -r requirements.txt
```

Run the app with `streamlit run app.py`. Run the project validation and experiments from the
repository root:

```powershell
python -m pytest
python -m results.tests.stress_tests
python -m results.tests.edge_tests
python -m results.tests.final_compare
python -m results.tests.workload_tests
python -m results.tests.runtime_benchmarks
python results\plots\generate_evidence.py
python results\plots\build_illustrated_report.py
```

The report builder writes `reports/DBDAA_Enhancement_Study_Illustrated_Revised.docx`.

## Paper validation

For Data 1/2/3 (Best/Average/Worst cases), the traditional algorithm uses 85/100/125 comparisons,
and DBDAA uses 10/36/70 comparisons in its first round, matching the paper's Table 8. The safe
sequences and timelines match the paper's Tables 5-7 and Figs. 3-5.

## Our modifications

1. Adaptive check: switch to a plain check after repeated expensive DBDAA checks.
2. Gated aging: a process overtaken at least five times may go first, but only if it can run now.
3. Idle retry: retry parked processes when the processor would otherwise be idle. This flowchart
   interpretation applies to DBDAA as well.
4. Ordered insertion: maintain the same queue order without sorting the whole queue after each
   change.

## Results in brief

- Safety-check comparisons fall 26.2% on the paper's Worst case (Data 3). Generated systems range
  from about 4% fewer under low resource headroom to a few more under high resource headroom.
- Total counted work, including queue ordering, is 14% to 51% lower in the tested scenarios.
- Heavy-process waiting falls 82% in the stream starvation test.
- Idle retry removes fixed-cycle idle time and benefits the DBDAA baseline too.

Safety checks, ordering work, fairness, and elapsed time are reported separately because the paper
does not count queue-ordering work.

## Limitations

The simulator does not model processes requesting additional resources while running, multiple
processors, or preemption.
