from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from algorithms import run_all, run_bankers, run_dbdaa, run_enhanced
from analytics import benchmark, comparison_trace_frame, complexity_curve, event_frame, gantt_frame
from datasets import DATASETS, PAPER_CYCLE
from models import Process

st.set_page_config(page_title="DBDAA Simulator", page_icon="⚙", layout="wide")
st.markdown("""
<style>
:root { color-scheme: light; }
.stApp { background:#f7f9fc; color:#17212b; }
[data-testid="stAppViewContainer"] .main { background:#f7f9fc; }
[data-testid="stAppViewContainer"] .block-container { max-width:1440px; padding:2.5rem 3.5rem 4.5rem; }
[data-testid="stSidebar"] { background:#111827 !important; border-right:1px solid #263449; }
[data-testid="stSidebar"] * { color:#e5e7eb !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stCaption"] { color:#dbe4ef !important; }
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input {
    background:#1f2937 !important;
    color:#f7fafc !important;
    border:1px solid #3b4c5d !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label { padding:10px 12px; margin:3px 0; border-radius:9px; transition:.2s; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#1f2937; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#263b57; }
[data-testid="stSidebar"] button { min-height:2.65rem; font-weight:700; background:#f8fafc !important; color:#17212b !important; border:1px solid #cbd5e1 !important; border-radius:8px !important; }
[data-testid="stSidebar"] button:hover { background:#dbeafe !important; border-color:#60a5fa !important; color:#1e3a8a !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] section { background:#1a2332 !important; border:1px dashed #64748b !important; border-radius:12px !important; padding:16px !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] section * { color:#dbe4ef !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] label,
[data-testid="stSidebar"] [data-testid="stFileUploader"] label *,
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] * {
    color:#f8fafc !important;
    opacity:1 !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button,
[data-testid="stSidebar"] [data-testid="stFileUploader"] button * {
    background:#f8fafc !important;
    color:#17212b !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"],
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] *,
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] button,
[data-testid="stSidebar"] [data-testid="stFileUploaderFileName"] button * {
    color:#dbe4ef !important;
    opacity:1 !important;
}
[data-testid="stSidebar"] button,
[data-testid="stSidebar"] button * {
    color:#17212b !important;
}
header[data-testid="stHeader"] { background:#111827 !important; }
header[data-testid="stHeader"] * { color:#e7edf2 !important; }
header[data-testid="stHeader"] button {
    background:#243342 !important;
    color:#f7fafc !important;
    border:1px solid #3b4c5d !important;
}
header[data-testid="stHeader"] button:hover { background:#314456 !important; color:#ffffff !important; }
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] small,
[data-testid="stAppViewContainer"] [data-testid="stCaption"],
[data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] { color:#17212b; }
[data-testid="stAppViewContainer"] h1 { font-size:2.8rem; letter-spacing:-.05em; line-height:1.05; }
[data-testid="stAppViewContainer"] h2 { margin-top:2.2rem; letter-spacing:-.03em; }
[data-testid="stAppViewContainer"] h3 { margin-top:1.5rem; letter-spacing:-.02em; }
.hero { border-bottom:1px solid #dbe5f0; padding:0 0 1.65rem; margin-bottom:2rem; }
[data-testid="stAppViewContainer"] .hero h1 { color:#17212b !important; margin:.35rem 0 .75rem; }
[data-testid="stAppViewContainer"] .hero p { color:#586979 !important; font-size:1.06rem; max-width:700px; }
.small-label { color:#387567 !important; font-size:.72rem; text-transform:uppercase; letter-spacing:.14em; font-weight:800; }
.card { background:#ffffff; border:1px solid #e1e8f0; border-top:4px solid #387567; border-radius:12px; padding:16px 18px; box-shadow:0 6px 18px rgba(15,23,42,.05); min-height:92px; }
.dashboard-stat { border-top:3px solid #3b82f6; border-bottom:1px solid #dbe5f0; padding:12px 12px 14px; min-height:72px; }
.dashboard-stat span { display:block; color:#64748b; font-size:.75rem; text-transform:uppercase; letter-spacing:.1em; }
.dashboard-stat strong { display:block; color:#0f172a; font-size:2rem; line-height:1.15; margin-top:8px; }
.blue-head, .green-head { background:transparent; color:#17212b !important; border-bottom:1px solid #cbd4dc; padding:0 0 10px; border-radius:0; font-weight:750; letter-spacing:.01em; }
.blue-head { border-bottom-color:#315a7d; }
.green-head { border-bottom-color:#387567; }
[data-testid="stMetric"] { background:transparent; border:0; border-bottom:1px solid #dbe5f0; border-radius:0; padding:8px 0 12px; box-shadow:none; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color:#687887 !important; font-size:.78rem; text-transform:uppercase; letter-spacing:.06em; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] div { color:#17212b !important; font-weight:750; }
[data-testid="stMetricDelta"] { color:#526170 !important; }
[data-testid="stAppViewContainer"] input,
[data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] button { background:#fff !important; color:#17212b !important; border-color:#b9c5d2 !important; border-radius:5px !important; }
[data-testid="stAppViewContainer"] button:hover { border-color:#3b82f6 !important; color:#1d4ed8 !important; box-shadow:0 3px 10px rgba(59,130,246,.12); }
[data-testid="stAppViewContainer"] [data-testid="stAlert"] { background:#edf4f2 !important; border:0 !important; border-left:3px solid #387567 !important; border-radius:0 !important; }
[data-testid="stAppViewContainer"] [data-testid="stAlert"] * { color:#17212b !important; }
[data-testid="stAppViewContainer"] [data-testid="stDataFrame"],
[data-testid="stAppViewContainer"] [data-testid="stTable"] { border-top:1px solid #cbd4dc; border-bottom:1px solid #cbd4dc; border-radius:0; }
[data-testid="stAppViewContainer"] [data-testid="stDataFrame"] *,
[data-testid="stAppViewContainer"] [data-testid="stTable"] * { color:#17212b !important; }
[data-testid="stAppViewContainer"] [data-baseweb="popover"] *,
[data-testid="stAppViewContainer"] [data-baseweb="menu"] * { color:#17212b !important; }
[data-testid="stAppViewContainer"] [data-testid="stFileUploader"] *,
[data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"] * { color:#17212b !important; }
.section-note { color:#64748b !important; font-size:.92rem; line-height:1.55; }
[data-testid="stExpander"] { border:1px solid #dbe5f0 !important; border-radius:12px !important; background:#ffffff !important; }
[data-testid="stDataFrame"], [data-testid="stTable"] { box-shadow:none; }
@media (max-width: 760px) {
    [data-testid="stAppViewContainer"] .block-container { padding:5rem 1.25rem 3rem; }
    [data-testid="stAppViewContainer"] h1 { font-size:2.2rem; }
    .hero { padding-bottom:1.5rem; margin-bottom:1.5rem; }
}
</style>
""", unsafe_allow_html=True)

CHART_COLORS = {
    "Traditional Banker": "#315a7d",
    "Original DBDAA": "#387567",
    "Enhanced DBDAA": "#a65d3b",
}
CHART_TEMPLATE = "plotly_white"


def input_to_frame(processes: list[Process]) -> pd.DataFrame:
    return pd.DataFrame([
        {"Process": p.pid, "Arrival": p.arrival_time, "Burst": p.burst_time,
         "Maximum": " ".join(map(str, p.maximum)), "Allocation": " ".join(map(str, p.allocation)),
         "Need": " ".join(map(str, p.need)), "Max_Need": p.max_need}
        for p in processes
    ])


def load_dataset(name: str) -> tuple[list[Process], list[int]]:
    return DATASETS[name]()


def flowchart_image_html(filename: str, width: int = 760) -> str:
    image_path = Path(__file__).with_name(filename)
    if not image_path.exists():
        candidates = sorted(image_path.parent.glob("Traditional Banker*Algorithm Flowchart.png"))
        if candidates:
            image_path = candidates[0]
        else:
            raise FileNotFoundError(f"Flowchart image not found: {filename}")
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return (
        f'<div style="overflow:auto;text-align:center;background:#fff;">'
        f'<img src="data:image/png;base64,{encoded}" width="{width}" '
        f'alt="{filename}" style="display:inline-block;max-width:100%;height:auto;">'
        "</div>"
    )


def result_summary(result, processes: list[Process], totals: list[int]) -> dict[str, float | int | str]:
    capacity = sum(totals)
    allocated = sum(sum(process.allocation) for process in processes)
    completed = len(result.safe_sequence)
    return {
        "Algorithm": result.algorithm,
        "Completed": completed,
        "Completion %": round(100 * completed / len(processes), 1) if processes else 0,
        "Primary unsafe": len(result.primary_unsafe_sequence),
        "Unsafe": len(result.unsafe_sequence),
        "Comparisons": result.comparisons,
        "Retries": result.retries,
        "Resource utilization %": round(100 * allocated / capacity, 1) if capacity else 0,
        "Simulated time": result.simulated_time,
    }


def plot_layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        font={"family": "Arial, sans-serif", "color": "#17212b", "size": 13},
        title={"font": {"color": "#17212b", "size": 18}},
        xaxis={
            "title": {"font": {"color": "#17212b", "size": 13}},
            "tickfont": {"color": "#17212b", "size": 12},
            "linecolor": "#526170",
            "gridcolor": "#d9e0e7",
        },
        yaxis={
            "title": {"font": {"color": "#17212b", "size": 13}},
            "tickfont": {"color": "#17212b", "size": 12},
            "linecolor": "#526170",
            "gridcolor": "#d9e0e7",
        },
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin={"l": 45, "r": 25, "t": 55, "b": 45},
        legend={
            "bgcolor": "#ffffff",
            "bordercolor": "#cbd6e1",
            "borderwidth": 1,
            "font": {"color": "#17212b", "size": 12},
            "title": {"font": {"color": "#17212b", "size": 12}},
        },
    )
    return fig


def result_frame(processes: list[Process], totals: list[int], cycle_duration: int) -> pd.DataFrame:
    return pd.DataFrame([
        result_summary(result, processes, totals)
        for result in run_all(processes, totals, cycle_duration)
    ])


def parse_csv_processes(frame: pd.DataFrame, totals: list[int]) -> list[Process]:
    required = {"pid", "arrival_time", "burst_time", "maximum", "allocation"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")
    processes = []
    for row in frame.to_dict("records"):
        maximum = tuple(int(value.strip()) for value in str(row["maximum"]).split(","))
        allocation = tuple(int(value.strip()) for value in str(row["allocation"]).split(","))
        processes.append(Process(str(row["pid"]), int(row["arrival_time"]), int(row["burst_time"]), maximum, allocation))
    from validation import validate_input
    validate_input(processes, totals)
    return processes


def main() -> None:
    st.markdown('<div class="hero"><div class="small-label">OPERATING SYSTEMS RESEARCH SIMULATOR</div><h1>DBDAA: Dynamic Banker\'s Deadlock Avoidance</h1><p>Transparent execution, algorithm comparisons, and virtual process visualization.</p></div>', unsafe_allow_html=True)
    page = st.sidebar.radio("Simulation pages", ["Dashboard", "Input & I/O", "Flow & Gantt", "Info"])
    dataset_name = st.sidebar.selectbox("Scenario dataset", list(DATASETS), index=0)
    cycle_duration = st.sidebar.number_input("Cycle duration (m)", min_value=1, value=PAPER_CYCLE)
    processes, totals = load_dataset(dataset_name)
    st.sidebar.divider()
    st.sidebar.caption("Use a custom CSV across every simulator page")
    upload_key = f"sidebar_process_csv_{st.session_state.get('upload_version', 0)}"
    sidebar_upload = st.sidebar.file_uploader(
        "Upload process CSV",
        type="csv",
        help="Required columns: pid, arrival_time, burst_time, maximum, allocation",
        key=upload_key,
    )
    if sidebar_upload is not None:
        try:
            st.session_state["custom_processes"] = parse_csv_processes(
                pd.read_csv(sidebar_upload), totals
            )
            st.session_state.pop("custom_csv_error", None)
        except ValueError as error:
            st.session_state.pop("custom_processes", None)
            st.session_state["custom_csv_error"] = str(error)
    if st.session_state.get("custom_csv_error"):
        st.sidebar.error(st.session_state["custom_csv_error"])
    clear_col, _status_col = st.sidebar.columns([1, 1])
    with clear_col:
        clear_uploaded = st.button("Clear Uploaded", use_container_width=True)
    if clear_uploaded:
        st.session_state.pop("custom_processes", None)
        st.session_state.pop("custom_csv_error", None)
        st.session_state["upload_version"] = st.session_state.get("upload_version", 0) + 1
        st.rerun()
    if st.session_state.get("custom_processes"):
        processes = st.session_state["custom_processes"]
        active_dataset = "Custom CSV"
    else:
        active_dataset = dataset_name
    st.sidebar.caption(f"{active_dataset}: {len(processes)} processes, {len(totals)} resources")

    if page == "Dashboard":
        st.subheader("System overview")
        st.markdown('<div class="section-note">All figures below are calculated from the selected input by running all three implementations; no comparison values are hardcoded.</div>', unsafe_allow_html=True)
        cols = st.columns(5)
        values = [len(processes), len(totals), sum(totals), sum(totals) - sum(sum(p.allocation) for p in processes), cycle_duration]
        labels = ["Processes", "Resource types", "Capacity", "Initial allocated", "Cycle m"]
        for col, label, value in zip(cols, labels, values):
            with col:
                st.markdown(
                    f'<div class="dashboard-stat"><span>{label}</span><strong>{value}</strong></div>',
                    unsafe_allow_html=True,
                )
        summary = result_frame(processes, totals, cycle_duration)
        st.subheader("Execution health")
        health_cols = st.columns(3)
        for col, row in zip(health_cols, summary.to_dict("records")):
            with col:
                st.markdown(f'<div class="card"><h4>{row["Algorithm"]}</h4>'
                            f'<b>{row["Completion %"]}%</b> completed · '
                            f'<b>{row["Resource utilization %"]}%</b> resource utilization · '
                            f'<b>{row["Comparisons"]}</b> comparisons<br>'
                            f'<span class="section-note">Primary unsafe: {row["Primary unsafe"]} · '
                            f'Final unsafe: {row["Unsafe"]} · Retries: {row["Retries"]}</span></div>',
                            unsafe_allow_html=True)
        health_chart = px.bar(summary, x="Algorithm", y=["Completion %", "Resource utilization %"],
                              barmode="group", title="Completion and resource utilization (%)",
                              color_discrete_sequence=["#315a7d", "#b07a3f"])
        st.plotly_chart(plot_layout(health_chart), use_container_width=True)
        st.subheader("Time-complexity comparison")
        st.markdown(
            '<div class="section-note">Analytical comparison workload as the number of processes grows. '
            'The resource dimension is fixed, so the chart shows the expected scaling of safety comparisons, '
            'not machine-dependent wall-clock time. Select a case to inspect it clearly.</div>',
            unsafe_allow_html=True,
        )
        complexity = complexity_curve(len(totals), max_processes=1000, step=25)
        case_name = st.selectbox(
            "Complexity scenario",
            ["Best case", "Average case", "Worst case"],
            key="dashboard_complexity_case",
        )
        case_frame = complexity[["Processes (n)", "Algorithm", case_name]].rename(
            columns={case_name: "Comparisons"}
        )
        figure = px.line(
            case_frame,
            x="Processes (n)",
            y="Comparisons",
            color="Algorithm",
            markers=True,
            color_discrete_map=CHART_COLORS,
            title=f"{case_name} comparison workload",
        )
        current_n = len(processes)
        current_values = case_frame[case_frame["Processes (n)"] == min(
            complexity["Processes (n)"], key=lambda value: abs(value - current_n)
        )]
        figure.add_vline(
            x=current_values["Processes (n)"].iloc[0],
            line_dash="dash",
            line_color="#64748b",
            annotation_text=f"Current input: {current_n} processes",
            annotation_position="top left",
        )
        st.plotly_chart(
            plot_layout(figure, 430),
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": False},
        )
        st.dataframe(case_frame, use_container_width=True, hide_index=True)
        st.download_button(
            "Download complexity curve CSV",
            complexity.to_csv(index=False),
            "dbdaa-complexity-curves.csv",
            "text/csv",
        )
        st.subheader("Input matrix")
        st.dataframe(input_to_frame(processes), use_container_width=True, hide_index=True)
        st.info("Use Input & I/O for the complete trace and comparison report, and Flow & Gantt for the algorithm diagrams and virtual timeline.")

    elif page == "Input & I/O":
        st.subheader("Input and output workspace")
        st.write("Upload your CSV using the sidebar. After validation, it becomes active across every simulator page.")
        if active_dataset == "Custom CSV":
            st.success(f"CSV validated successfully: {len(processes)} processes are active.")
            custom_result = run_dbdaa(processes, totals, cycle_duration)
            st.write(f"DBDAA safe sequence: {' -> '.join(custom_result.safe_sequence) or 'No complete safe sequence'}")
            st.download_button("Download custom DBDAA trace", event_frame(custom_result).to_csv(index=False), "custom-dbdaa-trace.csv", "text/csv")
        else:
            st.info("No custom CSV is active. Select a scenario dataset or upload a CSV from the sidebar.")
        st.write("Current calculated Need matrix")
        st.dataframe(input_to_frame(processes), use_container_width=True, hide_index=True)
        st.download_button("Download current input CSV", input_to_frame(processes).to_csv(index=False), "dbdaa-input.csv", "text/csv")
        st.subheader("Virtual execution trace")
        banker = run_bankers(processes, totals)
        dbdaa = run_dbdaa(processes, totals, cycle_duration)
        enhanced = run_enhanced(processes, totals, cycle_duration)
        st.markdown('<div class="section-note">Each row is a real safety check or completion event emitted by the selected algorithm.</div>', unsafe_allow_html=True)
        columns = st.columns(3)
        with columns[0]:
            st.markdown('<div class="blue-head">Traditional Banker</div>', unsafe_allow_html=True)
            st.write(" → ".join(banker.safe_sequence) or "No safe sequence")
            st.dataframe(event_frame(banker), use_container_width=True, hide_index=True)
        with columns[1]:
            st.markdown('<div class="green-head">Original DBDAA</div>', unsafe_allow_html=True)
            st.write(" → ".join(dbdaa.safe_sequence) or "No safe sequence")
            st.dataframe(event_frame(dbdaa), use_container_width=True, hide_index=True)
        with columns[2]:
            st.markdown('<div class="blue-head">Enhanced DBDAA</div>', unsafe_allow_html=True)
            st.write(" → ".join(enhanced.safe_sequence) or "No safe sequence")
            st.dataframe(event_frame(enhanced), use_container_width=True, hide_index=True)
        st.download_button("Download DBDAA event log", event_frame(dbdaa).to_csv(index=False), "dbdaa-events.csv", "text/csv")
        st.subheader("Traditional Banker vs DBDAA variants")
        frame, results = benchmark(processes, totals, cycle_duration)
        detailed = result_frame(processes, totals, cycle_duration)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        banker_comparisons = int(detailed.loc[detailed["Algorithm"] == "Traditional Banker", "Comparisons"].iloc[0])
        dbdaa_comparisons = int(detailed.loc[detailed["Algorithm"] == "Original DBDAA", "Comparisons"].iloc[0])
        reduction = round(100 * (banker_comparisons - dbdaa_comparisons) / banker_comparisons, 1) if banker_comparisons else 0
        metric_cols = st.columns(4)
        metric_cols[0].metric("DBDAA comparison reduction", f"{reduction}%")
        metric_cols[1].metric("DBDAA completion", f'{detailed.loc[detailed["Algorithm"] == "Original DBDAA", "Completion %"].iloc[0]}%')
        metric_cols[2].metric("Enhanced completion", f'{detailed.loc[detailed["Algorithm"] == "Enhanced DBDAA", "Completion %"].iloc[0]}%')
        metric_cols[3].metric("Enhanced retries", int(detailed.loc[detailed["Algorithm"] == "Enhanced DBDAA", "Retries"].iloc[0]))
        charts = st.columns(2)
        with charts[0]:
            st.plotly_chart(plot_layout(px.bar(frame, x="Algorithm", y="Comparisons", color="Algorithm",
                                               color_discrete_map=CHART_COLORS, title="Safety comparisons")), use_container_width=True)
        with charts[1]:
            st.plotly_chart(plot_layout(px.bar(frame, x="Algorithm", y="Wall-clock ms", color="Algorithm",
                                               color_discrete_map=CHART_COLORS, title="Measured runtime (ms)")), use_container_width=True)
        st.subheader("Virtual comparison execution")
        st.markdown(
            '<div class="section-note">Each point shows the running total of resource comparisons as the selected algorithm processes safety checks. '
            'A flatter line means fewer comparisons are being used.</div>',
            unsafe_allow_html=True,
        )
        comparison_frames = []
        for result in results:
            trace = comparison_trace_frame(result)
            trace["Algorithm"] = result.algorithm
            comparison_frames.append(trace)
        comparison_trace = pd.concat(comparison_frames, ignore_index=True)
        comparison_chart = px.line(
            comparison_trace,
            x="Step",
            y="Cumulative comparisons",
            color="Algorithm",
            markers=True,
            hover_data=["Time", "Process", "Action", "Step comparisons"],
            color_discrete_map=CHART_COLORS,
            title="Comparisons accumulated during execution",
        )
        comparison_chart.update_layout(
            xaxis_title="Execution event",
            yaxis_title="Cumulative resource comparisons",
            hovermode="x unified",
        )
        st.plotly_chart(
            plot_layout(comparison_chart, 430),
            use_container_width=True,
            config={"displaylogo": False, "scrollZoom": True},
        )
        st.dataframe(
            comparison_trace[
                ["Algorithm", "Step", "Time", "Process", "Action",
                 "Step comparisons", "Cumulative comparisons"]
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.download_button("Download comparison CSV", frame.to_csv(index=False), "dbdaa-comparison.csv", "text/csv")

    elif page == "Flow & Gantt":
        st.subheader("Algorithm flowchart")
        st.markdown(
            '<div class="section-note">Reference flowchart for the selected implementation.</div>',
            unsafe_allow_html=True,
        )
        flow_algorithm = st.selectbox(
            "Choose algorithm flowchart",
            ["Traditional Banker", "Original DBDAA", "Enhanced DBDAA"],
            key="flow_algorithm",
        )
        flowchart_images = {
            "Traditional Banker": "Traditional Banker’s Algorithm Flowchart.png",
            "Original DBDAA": "DBDAA Deadlock Avoidance Flowchart.png",
            "Enhanced DBDAA": "Enhanced DBDAA Algorithm Flowchart.png",
        }
        st.markdown(
            flowchart_image_html(flowchart_images[flow_algorithm]),
            unsafe_allow_html=True,
        )

        st.subheader("Execution timeline")
        st.markdown(
            '<div class="section-note">Choose one algorithm to inspect its complete process-by-process execution timeline.</div>',
            unsafe_allow_html=True,
        )
        timeline_results = [
            run_bankers(processes, totals),
            run_dbdaa(processes, totals, cycle_duration),
            run_enhanced(processes, totals, cycle_duration),
        ]
        timeline_algorithm = st.selectbox(
            "Choose algorithm timeline",
            [result.algorithm for result in timeline_results],
            key="timeline_algorithm",
        )
        result = next(item for item in timeline_results if item.algorithm == timeline_algorithm)
        gantt = gantt_frame(result, processes)
        if gantt.empty:
            st.info("No completed processes to display.")
        else:
            gantt_chart = px.bar(
                gantt, x="Duration", base="Start", y="Process",
                color="Process", orientation="h", text="Duration",
                labels={"Duration": "Burst duration", "Start": "Simulation time"},
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            gantt_chart.update_traces(
                textposition="inside", insidetextanchor="middle",
                marker_line_color="#ffffff", marker_line_width=1,
            )
            gantt_chart.update_layout(
                title={"text": f"{result.algorithm} · finish time: {result.simulated_time}"},
                height=max(560, 36 * len(gantt) + 150),
                yaxis={"categoryorder": "array", "categoryarray": gantt["Process"].tolist()},
                xaxis={"type": "linear", "title": "Simulation time"},
                showlegend=False,
            )
            st.plotly_chart(
                plot_layout(gantt_chart, max(560, 36 * len(gantt) + 150)),
                use_container_width=True,
                config={"displaylogo": False, "scrollZoom": True},
            )
        st.caption("Each bar represents the simulated burst interval after the process passes its algorithm-specific safety check.")
        st.subheader("Time complexity")
        st.dataframe(pd.DataFrame([
            {
                "Algorithm": "Traditional Banker",
                "Safety check": "O(d) per process",
                "Overall": "O(n²d) worst case",
                "Why": "Repeatedly scans unfinished processes and checks every resource.",
            },
            {
                "Algorithm": "Original DBDAA",
                "Safety check": "O(d²) bounded marking check",
                "Overall": "O(nd²) per checking round; retries add work",
                "Why": "Max_Need / Min_A shortcut reduces comparisons when resources are balanced.",
            },
            {
                "Algorithm": "Enhanced DBDAA",
                "Safety check": "Adaptive O(d) to O(d²)",
                "Overall": "O(n log n + nd²) typical, plus retries",
                "Why": "Adaptive checks, aging queue ordering, gated probes, and back-off.",
            },
        ]), use_container_width=True, hide_index=True)

    else:
        st.subheader("Algorithm guide")
        st.markdown("""
### Traditional Banker’s algorithm

Banker’s algorithm tests whether each process can finish with the currently available resources. It calculates `Need = Maximum - Allocation`, finds a process whose need fits in `Work`, simulates completion, releases its allocation, and repeats.

**Limitations:** it repeatedly scans the unfinished process list, checks every resource dimension, and can perform many comparisons before finding a safe order. In dynamic workloads, processes that cannot pass immediately are repeatedly reconsidered, which increases checking overhead and can delay decisions.

### Original DBDAA

DBDAA keeps the safety guarantee but uses a `Max_Need / Min_A` shortcut. It sorts the ready queue by maximum remaining need, checks the most demanding and least available resource positions first, and parks primary-unsafe processes until a later cycle.

**How it improves Banker’s:** fewer resource comparisons in favorable cases, an explicit dynamic ready queue, cycle-based retries, and separate handling for processes whose maximum request exceeds total capacity.

### Enhanced DBDAA

Enhanced DBDAA builds on DBDAA with three changes:

1. **Adaptive safety checks:** switches between the DBDAA check and a plain scan when the system is tight.
2. **Gated aging:** gives a long-waiting process a chance to run only when a quick availability probe says it can pass.
3. **Back-off and idle retry:** failed aging probes are spaced out, while parked processes are retried when the processor would otherwise be idle.

These changes target DBDAA’s remaining issues: repeated failed checks, possible starvation in continuously arriving workloads, and unnecessary idle time while a retry is pending. All results shown in this application are calculated from the selected dataset.
        """)


if __name__ == "__main__":
    main()
