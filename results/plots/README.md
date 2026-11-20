# DBDAA experiment evidence

This folder contains the source data and scripts for generating the report figures. Other results
are organized under `results/tests`, `results/data`, `results/images`, and `results/outputs`.

Run the generators from the repository root:

```powershell
python -m pip install -r requirements.txt
python results\plots\generate_evidence.py
python results\plots\build_illustrated_report.py
```

`generate_evidence.py` reads `evidence_data.json`, writes CSV summaries to `results\data`, and
generates plots and flowcharts in `results\images`. The report builder reads the revised text report
from `reports\` and creates the illustrated report there.

The experiment scripts are in `results\tests`. Their captured outputs are in `results\outputs`.
To refresh the measurement logs and regenerate the figures:

```powershell
python -m results.tests.final_compare > results\outputs\results.txt
python -m results.tests.workload_tests > results\outputs\workload_results.txt
python -m results.tests.runtime_benchmarks > results\outputs\runtime_results.txt
python results\plots\generate_evidence.py
python results\plots\build_illustrated_report.py
```

If the source code or benchmark settings change, rerun the tests, verify the output logs, then update
`evidence_data.json` before regenerating figures. Runtime measurements depend on the machine and
Python interpreter.
