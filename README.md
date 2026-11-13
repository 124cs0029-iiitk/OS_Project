# DBDAA Simulator

Python/Streamlit simulator for:

- Traditional Banker's safety algorithm
- Original DBDAA from `dbdaa.pdf`
- Enhanced DBDAA with adaptive checks and gated aging
- Best, average, and unsafe stress scenarios
- Transparent event-by-event execution traces
- Integrated trace and comparison report on the Input & I/O page
- Queue, safe/primary-unsafe/unsafe outputs
- Plotly comparison charts
- Separate vertical flowcharts for all three algorithms
- Virtual completion Gantt chart
- CSV input/output and downloadable logs

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Open `http://localhost:8501`.

The simulator recalculates results and never hardcodes comparison outputs. The DBDAA implementation uses the Max_Need/Min_A marking procedure, while Enhanced DBDAA adds adaptive checks, gated aging, and back-off for repeated failures.
