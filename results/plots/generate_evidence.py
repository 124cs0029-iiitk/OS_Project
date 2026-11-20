"""Generate CSV summaries, plots, and a final-version Enhanced DBDAA flowchart."""
import csv
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIGURES = ROOT / "results" / "images"
DATA_DIR = ROOT / "results" / "data"

COLORS = {
    "traditional": "#777777",
    "dbdaa": "#2C7FB8",
    "enhanced": "#E67E22",
}


def write_csv(name, rows):
    if not rows:
        return
    with (DATA_DIR / name).open("w", newline="", encoding="utf-8") as file:
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_fig(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=300, bbox_inches="tight")
    plt.close(fig)


def read_data():
    return json.loads((HERE / "evidence_data.json").read_text(encoding="utf-8"))


def export_csv(data):
    write_csv("paper_datasets.csv", data["paper_datasets"])
    scaling_rows = []
    for regime in ("low_headroom", "high_headroom"):
        for index, n in enumerate(data["scaling"]["n"]):
            scaling_rows.append({
                "regime": regime.replace("_", " "),
                "processes": n,
                "traditional_checks": data["scaling"][regime]["traditional"][index],
                "dbdaa_checks": data["scaling"][regime]["dbdaa"][index],
                "enhanced_checks": data["scaling"][regime]["enhanced"][index],
            })
    write_csv("scaling_checks.csv", scaling_rows)
    write_csv("workload_summary.csv", data["workloads"])
    write_csv("runtime_small_workloads.csv", data["runtime_small"])
    write_csv("starvation_wait.csv", data["starvation"])
    write_csv("high_dimension_runtime.csv", data["high_dimension"])
    write_csv("adaptive_sensitivity.csv", data["adaptive_sensitivity"])
    write_csv("aging_sensitivity.csv", data["aging_sensitivity"])


def plot_paper_datasets(data):
    rows = data["paper_datasets"]
    x = np.arange(len(rows))
    width = 0.24
    fig, ax = plt.subplots(figsize=(3.25, 2.2))
    for offset, key, label in [
        (-width, "traditional", "Banker"),
        (0, "dbdaa", "DBDAA"),
        (width, "enhanced", "Enhanced"),
    ]:
        bars = ax.bar(x + offset, [row[key] for row in rows], width,
                      label=label, color=COLORS[key])
        ax.bar_label(bars, padding=1, fontsize=6)
    ax.set_ylabel("Safety-check comparisons")
    ax.set_xticks(x, ["%s\n(%s)" % (row["paper_case"], row["dataset"]) for row in rows])
    ax.legend(frameon=False, ncol=3, fontsize=6, loc="upper left")
    ax.set_title("DBDAA paper cases", fontsize=9)
    save_fig(fig, "paper_dataset_checks.png")


def plot_scaling(data):
    n = data["scaling"]["n"]
    fig, ax = plt.subplots(figsize=(3.25, 2.25))
    for regime, linestyle, regime_label in [
        ("low_headroom", "-", "Low"),
        ("high_headroom", "--", "High"),
    ]:
        for alg, algorithm_label, color in [
            ("dbdaa", "DBDAA", COLORS["dbdaa"]),
            ("enhanced", "Enhanced", COLORS["enhanced"]),
        ]:
            ax.plot(n, data["scaling"][regime][alg], marker="o",
                    linestyle=linestyle, color=color,
                    label="%s, %s" % (regime_label, algorithm_label))
    ax.set_yscale("log")
    ax.set_xlabel("Number of processes")
    ax.set_ylabel("Safety-check comparisons (log)")
    ax.set_title("Generated-system scaling by resource headroom", fontsize=9)
    ax.legend(frameon=False, fontsize=5.8, ncol=2)
    save_fig(fig, "scaling_checks.png")


def plot_workloads(data):
    rows = data["workloads"]
    x = np.arange(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(3.25, 2.25))
    ax.bar(x - width / 2, [row["dbdaa_work"] for row in rows], width,
           label="DBDAA", color=COLORS["dbdaa"])
    ax.bar(x + width / 2, [row["enhanced_work"] for row in rows], width,
           label="Enhanced", color=COLORS["enhanced"])
    ax.set_xticks(x, [row["id"] for row in rows])
    ax.set_ylabel("Checks + queue-order comparisons")
    ax.set_title("Total counted work by workload", fontsize=9)
    ax.legend(frameon=False, fontsize=6)
    save_fig(fig, "workload_total_work.png")

    fig, ax = plt.subplots(figsize=(3.25, 2.25))
    ax.bar(x - width / 2, [row["dbdaa_checks"] for row in rows], width,
           label="DBDAA", color=COLORS["dbdaa"])
    ax.bar(x + width / 2, [row["enhanced_checks"] for row in rows], width,
           label="Enhanced", color=COLORS["enhanced"])
    ax.set_xticks(x, [row["id"] for row in rows])
    ax.set_ylabel("Safety-check comparisons")
    ax.set_title("Safety checks alone", fontsize=9)
    ax.legend(frameon=False, fontsize=6)
    save_fig(fig, "workload_safety_checks.png")


def plot_runtime(data):
    rows = data["runtime_small"]
    x = np.arange(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(3.25, 2.25))
    ax.bar(x - width / 2, [row["dbdaa_ms"] for row in rows], width,
           label="DBDAA", color=COLORS["dbdaa"])
    bars = ax.bar(x + width / 2, [row["enhanced_ms"] for row in rows], width,
                  label="Enhanced", color=COLORS["enhanced"])
    for bar, row in zip(bars, rows):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                "%.2fx" % (row["enhanced_ms"] / row["dbdaa_ms"]),
                ha="center", va="bottom", fontsize=5.5)
    ax.set_xticks(x, [row["workload"] for row in rows])
    ax.set_ylabel("Mean time per run (ms)")
    ax.set_title("Small-workload runtime", fontsize=9)
    ax.legend(frameon=False, fontsize=6)
    save_fig(fig, "runtime_small_workloads.png")


def plot_starvation(data):
    rows = data["starvation"]
    x = np.arange(len(rows))
    width = 0.34
    fig, ax = plt.subplots(figsize=(3.25, 2.2))
    ax.bar(x - width / 2, [row["dbdaa"] for row in rows], width,
           label="DBDAA", color=COLORS["dbdaa"])
    ax.bar(x + width / 2, [row["enhanced"] for row in rows], width,
           label="Enhanced", color=COLORS["enhanced"])
    ax.set_xticks(x, ["Stream\nheavy", "Late\nheavy", "Late\nmaximum"])
    ax.set_ylabel("Wait (time units)")
    ax.set_title("Waiting under repeated overtaking", fontsize=9)
    ax.legend(frameon=False, fontsize=6)
    save_fig(fig, "starvation_wait.png")


def plot_high_dimension(data):
    rows = data["high_dimension"]
    fig, ax = plt.subplots(figsize=(3.25, 2.25))
    for process_count, marker in [(100, "o"), (300, "s")]:
        subset = [row for row in rows if row["processes"] == process_count]
        ax.plot([row["resources"] for row in subset],
                [row["dbdaa_ms"] for row in subset], marker=marker,
                linestyle="-", color=COLORS["dbdaa"],
                label="DBDAA, n=%d" % process_count)
        ax.plot([row["resources"] for row in subset],
                [row["enhanced_ms"] for row in subset], marker=marker,
                linestyle="--", color=COLORS["enhanced"],
                label="Enhanced, n=%d" % process_count)
    ax.set_yscale("log")
    ax.set_xlabel("Number of resource types")
    ax.set_ylabel("Median runtime (ms, log)")
    ax.set_title("High-dimensional safe systems", fontsize=9)
    ax.legend(frameon=False, fontsize=5.5, ncol=2)
    save_fig(fig, "high_dimension_runtime.png")


def plot_sensitivity(data):
    rows = data["adaptive_sensitivity"]
    columns = [
        "Worst case (Data 3)", "Very low headroom", "Low headroom",
        "Moderate headroom", "High headroom",
    ]
    matrix = np.array([[row[column] for column in columns] for row in rows])
    display_columns = [
        "Data 3\n(Worst)", "Very low\nheadroom", "Low\nheadroom",
        "Moderate\nheadroom", "High\nheadroom",
    ]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    image = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=-30, vmax=10)
    ax.set_xticks(np.arange(len(columns)), display_columns)
    ax.set_yticks(np.arange(len(rows)), [row["setting"] for row in rows])
    ax.set_xlabel("Paper case or generated resource headroom")
    ax.set_ylabel("(streak limit, probe interval)")
    ax.set_title("Adaptive-check sensitivity: percent change vs DBDAA")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, "%.1f" % matrix[i, j], ha="center", va="center", fontsize=7)
    ax.add_patch(plt.Rectangle((0.5, 4.5), 1, 1, fill=False, edgecolor="black", linewidth=2))
    fig.colorbar(image, ax=ax, label="Percent change (negative is fewer checks)")
    save_fig(fig, "adaptive_sensitivity.png")

    rows = data["aging_sensitivity"]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    for gap in (1, 5, 10):
        subset = [row for row in rows if row["probe_gap"] == gap]
        ax.plot([row["overtakes"] for row in subset],
                [row["heavy_wait"] for row in subset], marker="o", label="Probe gap %d" % gap)
    ax.set_xlabel("Overtake threshold")
    ax.set_ylabel("Mean heavy-process wait")
    ax.set_title("Aging threshold sensitivity")
    ax.legend(frameon=False)
    save_fig(fig, "aging_sensitivity.png")


def add_box(ax, center, y, text, width=6.2, height=0.76, color="#eaf3f8"):
    x = center - width / 2
    box = FancyBboxPatch((x, y - height / 2), width, height,
                         boxstyle="round,pad=0.08,rounding_size=0.12",
                         facecolor=color, edgecolor="#284b63", linewidth=1.2)
    ax.add_patch(box)
    ax.text(center, y, text, ha="center", va="center", fontsize=8,
            wrap=True, color="#172b3a")
    return (center, y - height / 2), (center, y + height / 2)


def arrow(ax, start, end, label=None, color="#34495e", curve=0.0):
    patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11,
                            linewidth=1.1, color=color,
                            connectionstyle="arc3,rad=%s" % curve)
    ax.add_patch(patch)
    if label:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x + 0.12, mid_y, label, fontsize=7, color=color,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 1})


def plot_enhanced_flowchart():
    fig, ax = plt.subplots(figsize=(6.6, 9.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 15)
    ax.axis("off")
    ax.set_title("Final Enhanced DBDAA (idle-retry comparison mode)", fontsize=14, pad=12)

    nodes = []
    nodes.append(add_box(ax, 5, 14.0, "Start: read resources, process maxima, allocations,\nbursts, arrivals; set cycle m = 30", width=7.6, height=0.9))
    nodes.append(add_box(ax, 5, 12.75, "Initialize Available and Need; reject Max > total; admit arrivals\nand keep the queue stably ordered by ascending Max_Need", width=7.6, height=0.9))
    nodes.append(add_box(ax, 5, 11.35, "Select queue head; if an aging probe is due, try a process\novertaken at least 5 times only if the quick test passes", width=7.6, height=0.95, color="#fff4d6"))
    nodes.append(add_box(ax, 5, 9.95, "Adaptive check: use DBDAA quick/marking check, or plain check\nafter 2 checks costing > d; probe every 4 checks", width=7.6, height=0.95, color="#dceeff"))

    def add_diamond(center, y, width, height, text):
        shape = Polygon(
            [(center, y + height / 2), (center + width / 2, y),
             (center, y - height / 2), (center - width / 2, y)],
            closed=True, facecolor="#fff1b8", edgecolor="#725d19", linewidth=1.3
        )
        ax.add_patch(shape)
        ax.text(center, y, text, ha="center", va="center", fontsize=9, weight="bold")

    add_diamond(5, 8.25, 2.2, 1.3, "Safe now?")
    arrow(ax, nodes[0][0], nodes[1][1])
    arrow(ax, nodes[1][0], nodes[2][1])
    arrow(ax, nodes[2][0], nodes[3][1])
    arrow(ax, nodes[3][0], (5, 8.92))

    safe_box = add_box(ax, 2.5, 6.45, "Yes: run process; release allocation;\nupdate overtaking counts", width=4.2, height=0.9, color="#e3f4df")
    parked_box = add_box(ax, 7.5, 6.45, "No: park as Primary Unsafe;\nback off failed aging probes", width=4.2, height=0.9, color="#f7e5e5")
    arrow(ax, (4.05, 7.82), safe_box[1], "Yes")
    arrow(ax, (5.95, 7.82), parked_box[1], "No")

    add_diamond(5, 4.95, 2.5, 1.35, "Ready queue\nempty?")
    arrow(ax, safe_box[0], (4.45, 5.62))
    arrow(ax, parked_box[0], (5.55, 5.62))
    ax.plot([9.4, 9.4], [1.65, 11.35], color="#34495e", linewidth=1.1)
    arrow(ax, (6.25, 4.95), (9.4, 4.95), "No")
    arrow(ax, (9.4, 11.35), (8.82, 11.35))

    idle_box = add_box(ax, 5, 3.25, "Yes: retry parked processes now; wait for an arrival if needed", width=7.6, height=0.8, color="#e9e2f5")
    arrow(ax, (5, 4.27), idle_box[1], "Yes")
    add_diamond(5, 1.65, 3.2, 1.05, "All done or\nstuck?")
    arrow(ax, idle_box[0], (5, 2.18))
    stop_box = add_box(ax, 5, 0.48, "Stop", width=2.2, height=0.48, color="#eaf3f8")
    arrow(ax, (5, 1.12), stop_box[1], "Yes")
    arrow(ax, (6.6, 1.65), (9.4, 1.65), "No")

    fig.savefig(FIGURES / "enhanced_final_flowchart.png", dpi=300, bbox_inches="tight")
    svg_path = FIGURES / "enhanced_final_flowchart.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_lines) + "\n",
        encoding="utf-8",
    )
    plt.close(fig)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 7,
        "axes.titlesize": 9,
        "axes.labelsize": 7,
        "legend.fontsize": 6,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.2,
    })
    data = read_data()
    export_csv(data)
    plot_paper_datasets(data)
    plot_scaling(data)
    plot_workloads(data)
    plot_runtime(data)
    plot_starvation(data)
    plot_high_dimension(data)
    plot_sensitivity(data)
    plot_enhanced_flowchart()

    baseline = FIGURES / "DBDAA Deadlock Avoidance Flowchart.png"
    if not baseline.exists():
        raise FileNotFoundError("Missing baseline flowchart: %s" % baseline)
    shutil.copy2(baseline, FIGURES / "dbdaa_baseline_flowchart.png")
    print("Wrote evidence CSVs to:", DATA_DIR)
    print("Wrote plots and flowcharts to:", FIGURES)


if __name__ == "__main__":
    main()
