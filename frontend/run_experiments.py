"""
run_experiments.py — generate all PNG charts and experiment_results.csv
using the compiled M1–M4 C++ backend through BackendAdapter.

Run with:
    cd d:\\Projects\\DS_Project\\frontend
    python run_experiments.py
"""

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend_adapter import BackendAdapter
import charts as ch

SEED = 7
SIZES = [100, 1000, 5000]
OPS_LIST = [300, 3000, 10000]
STRATEGIES = [("First Fit", "first"), ("Next Fit", "next"),
              ("Best Fit", "best"), ("Worst Fit", "worst")]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "charts")


def run_one(adapter, n_blocks, n_ops, seed, strat_name, strat_key):
    """Execute one C++ experiment and return formatted row + history."""
    res = adapter.run_experiment(n_blocks, n_ops, seed, strat_key)
    alloc_reqs = res["ok"] + res["frag_fail"] + res["nospace_fail"]
    ffr = (res["frag_fail"] / max(alloc_reqs, 1)) * 100.0
    return {
        "N": n_blocks, "Ops": n_ops, "Strategy": strat_name,
        "OK": res["ok"], "FailFrag": res["frag_fail"],
        "FailNoSp": res["nospace_fail"], "AvgFrag%": res["avg_frag"],
        "AvgUtil%": res["avg_util"], "Segments": res["segments"],
        "Largest": res["largest"], "Time(ms)": res["time_ms"],
        "frag_fail_rate": ffr, "history": res["frag_history"],
    }


def collect_experiments(adapter):
    """Run all sizes x strategies and assemble rows and chart structures."""
    rows = []
    data = {
        "avg_frag": {}, "frag_fail_rate": {}, "avg_util": {},
        "sim_time": {}, "stacked_fail": {}, "frag_history": {},
    }
    for n_blocks, n_ops in zip(SIZES, OPS_LIST):
        for key in data:
            data[key][n_blocks] = {}
        for strat_name, strat_key in STRATEGIES:
            r = run_one(adapter, n_blocks, n_ops, SEED, strat_name, strat_key)
            rows.append(r)
            _store_chart_entry(data, n_blocks, strat_key, r)
    return rows, data


def _store_chart_entry(data, n_blocks, strat_key, r):
    data["avg_frag"][n_blocks][strat_key] = r["AvgFrag%"]
    data["frag_fail_rate"][n_blocks][strat_key] = r["frag_fail_rate"]
    data["avg_util"][n_blocks][strat_key] = r["AvgUtil%"]
    data["sim_time"][n_blocks][strat_key] = r["Time(ms)"]
    data["stacked_fail"][n_blocks][strat_key] = {
        "frag": r["FailFrag"], "nospace": r["FailNoSp"],
    }
    data["frag_history"][n_blocks][strat_key] = r["history"]


def save_csv(rows):
    """Write experiment results CSV to outputs/charts/experiment_results.csv."""
    os.makedirs(OUT_DIR, exist_ok=True)
    csv_path = os.path.join(OUT_DIR, "experiment_results.csv")
    cols = [
        "N", "Ops", "Strategy", "OK", "FailFrag", "FailNoSp",
        "AvgFrag%", "AvgUtil%", "Segments", "Largest", "Time(ms)",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: ("{:.1f}".format(row[k]) if isinstance(row[k], float) else row[k])
                for k in cols
            })
    return csv_path


def save_all_charts(data):
    """Render and export all 9 charts plus sample donut at 200 dpi."""
    specs = [
        ("1_avg_ext_fragmentation.png", ch.chart_avg_frag, [data["avg_frag"], SIZES]),
        ("2_frag_failure_rate.png", ch.chart_frag_fail_rate, [data["frag_fail_rate"], SIZES]),
        ("3_avg_utilisation.png", ch.chart_avg_util, [data["avg_util"], SIZES]),
        ("4_simulation_time_log.png", ch.chart_sim_time, [data["sim_time"], SIZES]),
        ("5_stacked_failures.png", ch.chart_stacked_failures, [data["stacked_fail"], SIZES]),
        ("6_frag_timeline.png", ch.chart_frag_timeline, [data["frag_history"], SIZES]),
        ("7_heatmap_avg_frag.png", ch.chart_heatmap_frag, [data["avg_frag"], SIZES]),
        ("8_heatmap_frag_fail_rate.png", ch.chart_heatmap_frag_fail, [data["frag_fail_rate"], SIZES]),
        ("9_heatmap_avg_utilisation.png", ch.chart_heatmap_util, [data["avg_util"], SIZES]),
        ("10_donut_sample.png", ch.chart_donut, [7, 93]),
    ]
    for filename, func, args in specs:
        fig = func(*args)
        ch.save_chart(fig, os.path.join(OUT_DIR, filename))
        print("  Saved: {}".format(filename))


def print_table(rows):
    """Print formatted result table to stdout."""
    print("{:<6} {:<6} {:<11} {:<6} {:<9} {:<9} {:<9} {:<9} {:<6} {:<8} {:<8}".format(
        "N", "Ops", "Strategy", "OK", "FailFrag", "FailNoSp",
        "AvgFrag%", "AvgUtil%", "Seg", "Largest", "Time(ms)",
    ))
    print("-" * 96)
    for r in rows:
        print("{:<6} {:<6} {:<11} {:<6} {:<9} {:<9} {:<9.1f} {:<9.1f} {:<6} {:<8} {:<8.1f}".format(
            r["N"], r["Ops"], r["Strategy"], r["OK"], r["FailFrag"], r["FailNoSp"],
            r["AvgFrag%"], r["AvgUtil%"], r["Segments"], r["Largest"], r["Time(ms)"],
        ))


def main():
    """Run all C++ experiments, save CSV/PNGs, and check repeatability."""
    print("Experiment parameters: Seed={}, Sizes={}, Ops={}\n".format(SEED, SIZES, OPS_LIST))
    adapter = BackendAdapter(total_blocks=100, load_sample=False)
    try:
        rows, data = collect_experiments(adapter)
        print_table(rows)
        csv_path = save_csv(rows)
        print("\nSaved CSV: {}".format(csv_path))
        print("\nGenerating charts...")
        save_all_charts(data)
        r1 = run_one(adapter, 100, 300, SEED, "Best Fit", "best")
        r2 = run_one(adapter, 100, 300, SEED, "Best Fit", "best")
        same = (
            r1["OK"] == r2["OK"] and r1["FailFrag"] == r2["FailFrag"]
            and r1["FailNoSp"] == r2["FailNoSp"]
            and abs(r1["AvgFrag%"] - r2["AvgFrag%"]) < 0.01
        )
        print("\nRepeatability check (same seed): {}".format("PASS" if same else "FAIL"))
    finally:
        adapter.close()


if __name__ == "__main__":
    main()
