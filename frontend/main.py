"""
main.py — M5 entry point for the Virtual Storage Allocation Simulator.

Run offline with:
    cd d:\\Projects\\DS_Project\\frontend
    python main.py

Assembles the Tkinter window, builds ttk.Notebook tabs, and connects all
views to M1–M4's compiled C++ backend through BackendAdapter.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend_adapter import BackendAdapter
from ui.theme import (
    CANVAS_BG, TILE_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, FOCUS_HIGHLIGHT_COLOR,
    FONT_FAMILY, FONT_SIZE_NORMAL,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
)
from ui.main_view import MainView
from ui.failure_view import FailureView
from ui.compaction_view import CompactionView
from ui.compare_view import CompareView
from ui.results_view import ResultsView

# Hover colour for Ocean Sunset theme buttons.
ACTION_HOVER = "#0A9396"


class SimulatorApp:
    """Application controller owning BackendAdapter and all five UI tabs."""

    def __init__(self, root):
        self.root = root
        self.root.title("Project 10 — Virtual Storage Allocation Simulator")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.configure(bg=CANVAS_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        style = ttk.Style()
        style.theme_use("clam")
        self._configure_styles(style)

        self.backend = BackendAdapter(total_blocks=100)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)
        self._init_tabs()
        self.main_view.refresh()

    def _init_tabs(self):
        """Instantiate and register all five notebook tabs."""
        self.main_view = MainView(self.notebook, controller=self)
        self.failure_view = FailureView(self.notebook, controller=self)
        self.compaction_view = CompactionView(self.notebook, controller=self)
        self.compare_view = CompareView(self.notebook, controller=self)
        self.results_view = ResultsView(self.notebook, controller=self)

        self.notebook.add(self.main_view, text="Dashboard")
        self.notebook.add(self.failure_view, text="Failure Analysis")
        self.notebook.add(self.compaction_view, text="Compaction")
        self.notebook.add(self.compare_view, text="Compare Strategies")
        self.notebook.add(self.results_view, text="Results & Charts")

    def _configure_styles(self, style):
        """Configure light-theme ttk styles and 3 px focus rings."""
        style.configure(
            ".", background=CANVAS_BG, foreground=TEXT_PRIMARY,
            focuscolor=FOCUS_HIGHLIGHT_COLOR, focusthickness=3,
        )
        style.configure("Dashboard.TFrame", background=CANVAS_BG)
        style.configure(
            "TButton", background=ACTION_COLOR, foreground="#FFFFFF",
            padding=(12, 7), font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            borderwidth=0, focusthickness=2,
        )
        style.map(
            "TButton",
            background=[("active", ACTION_HOVER), ("pressed", "#003B46"),
                        ("disabled", "#D8E0EA")],
            foreground=[("disabled", "#667085")],
        )
        self._configure_input_and_tab_styles(style)

    def _configure_input_and_tab_styles(self, style):
        """Configure entry, notebook, and treeview ttk styles."""
        style.configure("TEntry", fieldbackground="#FFFFFF", foreground=TEXT_PRIMARY, padding=4)
        style.configure("TCombobox", fieldbackground="#FFFFFF", foreground=TEXT_PRIMARY)
        style.configure("TNotebook", background=CANVAS_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab", background="#E5EFED", foreground=TEXT_PRIMARY,
            padding=(16, 9), font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", ACTION_COLOR), ("active", "#D8ECE7")],
            foreground=[("selected", "#FFFFFF"), ("active", TEXT_PRIMARY)],
        )
        style.configure(
            "Treeview", background=TILE_BG, foreground=TEXT_PRIMARY,
            fieldbackground=TILE_BG, rowheight=29, font=(FONT_FAMILY, 10),
        )
        style.configure(
            "Treeview.Heading", background="#E5EFED",
            foreground=TEXT_PRIMARY, font=(FONT_FAMILY, 10, "bold"),
            padding=(7, 7),
        )
        style.map(
            "Treeview",
            foreground=[("selected", "#000000")],
            background=[("selected", "#D7ECE7")],
        )

    # ---- Controller actions --------------------------------------

    def allocate(self, pid, size, strategy):
        """Call C++ backend allocate."""
        return self.backend.allocate(pid, size, strategy)

    def release(self, pid):
        """Call C++ backend release."""
        return self.backend.release(pid)

    def compact(self):
        """Run C++ compaction and populate before/after views."""
        self.compaction_view.show_before()
        report = self.backend.compact()
        self.compaction_view.show_after(report)
        self.main_view.refresh()
        return report

    def reset(self):
        """Reset C++ storage to 100 empty blocks."""
        self.backend.reset(total_blocks=self.backend.n)

    def export_csv(self, path):
        """Export C++ event log to CSV."""
        return self.backend.export_log_csv(path)

    def show_failure(self, request_size, strategy, pid=""):
        """Switch to Failure Analysis tab and display C++ analysis."""
        self.failure_view.show_failure(request_size, strategy, pid)
        self.notebook.select(1)

    def run_workload(self, ops, seed, strategy="First Fit"):
        """Execute M3's C++ seeded workload on the live storage."""
        workload = self.backend.generate_workload(self.backend.n, ops, seed)
        for op_type, pid, size in workload:
            if op_type == "alloc":
                self.backend.allocate(pid, size, strategy)
            else:
                self.backend.release(pid)

    def compare_strategies(self, ops, seed):
        """Run identical C++ M3 workload across all 4 strategies."""
        results = {}
        for strat_key in ["first", "next", "best", "worst"]:
            res = self.backend.run_experiment(
                self.backend.n, ops, seed, strat_key, include_layout=True,
            )
            results[strat_key] = {
                "array": res["array"],
                "free_segments": [(int(s[0]), int(s[1])) for s in res["free_segments"]],
                "ok": res["ok"],
                "frag_fail": res["frag_fail"],
                "nospace_fail": res["nospace_fail"],
                "segments": res["segments"],
                "largest": res["largest"],
                "ext_frag": res["avg_frag"],
                "avg_util": res["avg_util"],
            }
        self.compare_view.show_comparison(results)
        self.notebook.select(3)

    def run_experiments(self, sizes, ops_list, seed):
        """Run C++ M3 experiments for Results & Charts tab."""
        chart_data = _init_chart_data()
        table_rows = []
        for n_blocks, n_ops in zip(sizes, ops_list):
            self._run_size_group(n_blocks, n_ops, seed, table_rows, chart_data)
        self.results_view.show_results(table_rows, chart_data, sizes, seed, ops_list)
        self.notebook.select(4)

    def _run_size_group(self, n_blocks, n_ops, seed, table_rows, chart_data):
        """Run all four strategies for one (N, ops) configuration."""
        names = [("First Fit", "first"), ("Next Fit", "next"),
                 ("Best Fit", "best"), ("Worst Fit", "worst")]
        for key in chart_data:
            chart_data[key][n_blocks] = {}
        for strat_name, strat_key in names:
            res = self.backend.run_experiment(n_blocks, n_ops, seed, strat_key)
            _record_experiment_row(
                n_blocks, n_ops, strat_name, strat_key, res, table_rows, chart_data
            )

    def close(self):
        """Shut down the C++ bridge subprocess and destroy Tk window."""
        self.backend.close()
        self.root.destroy()


def _init_chart_data():
    return {
        "avg_frag": {}, "frag_fail_rate": {}, "avg_util": {},
        "sim_time": {}, "stacked_fail": {}, "frag_history": {},
    }


def _record_experiment_row(n_blocks, n_ops, strat_name, strat_key, res, rows, data):
    """Append one C++ experiment result into table_rows and chart_data."""
    alloc_reqs = res["ok"] + res["frag_fail"] + res["nospace_fail"]
    ffr = (res["frag_fail"] / max(alloc_reqs, 1)) * 100.0
    rows.append({
        "N": n_blocks, "Ops": n_ops, "Strategy": strat_name,
        "OK": res["ok"], "FailFrag": res["frag_fail"],
        "FailNoSp": res["nospace_fail"], "AvgFrag%": res["avg_frag"],
        "AvgUtil%": res["avg_util"], "Segments": res["segments"],
        "Largest": res["largest"], "Time(ms)": res["time_ms"],
    })
    data["avg_frag"][n_blocks][strat_key] = res["avg_frag"]
    data["frag_fail_rate"][n_blocks][strat_key] = ffr
    data["avg_util"][n_blocks][strat_key] = res["avg_util"]
    data["sim_time"][n_blocks][strat_key] = res["time_ms"]
    data["stacked_fail"][n_blocks][strat_key] = {
        "frag": res["frag_fail"], "nospace": res["nospace_fail"],
    }
    data["frag_history"][n_blocks][strat_key] = res["frag_history"]


def main():
    """Launch the Tkinter dashboard application."""
    root = tk.Tk()
    root.geometry("1280x850")
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = SimulatorApp(root)
    status_bar = tk.Label(
        root,
        text="Virtual Storage Allocation Simulator — Project 10 | Backend: C++ (M1–M4)",
        font=(FONT_FAMILY, 9), bg="#F1C0E8", fg=TEXT_PRIMARY, anchor="w", padx=8,
    )
    status_bar.pack(side="bottom", fill="x")
    root.mainloop()


if __name__ == "__main__":
    main()
