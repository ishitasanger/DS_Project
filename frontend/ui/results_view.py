"""
ui/results_view.py — Results & Charts tab.

Shows:
  - Experiment trigger button and PNG export button
  - Full 12-row experiment result table with lowest fragmentation highlighted & labelled
  - All 9 chart types from charts.py with concise plain-English text summaries
"""

import os
import tkinter as tk
from tkinter import ttk
from ui.theme import (
    CANVAS_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, DANGER_COLOR, INSIGHT_BG, FONT_FAMILY,
    FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
)

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class ResultsView(ttk.Frame):
    """Results & Charts tab."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ctrl = controller
        self._chart_figs = []
        self._build_ui()

    def _build_ui(self):
        """Build scrollable area containing result table and charts."""
        self._outer = tk.Canvas(self, bg=CANVAS_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._outer.yview)
        self._scroll_frame = ttk.Frame(self._outer, style="Dashboard.TFrame")
        self._scroll_frame.bind("<Configure>", self._on_scroll_configure)
        self._scroll_window = self._outer.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw"
        )
        self._outer.bind("<Configure>", self._on_canvas_resize)
        self._outer.configure(yscrollcommand=scrollbar.set)
        self._outer.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._outer.bind("<Enter>", self._on_canvas_enter)
        self._outer.bind("<Leave>", self._on_canvas_leave)
        self._populate_layout(self._scroll_frame, 16)

    def _populate_layout(self, container, pad):
        self._build_header(container, pad)
        self._build_result_table(container, pad)
        self._chart_frame = tk.Frame(container, bg=CANVAS_BG)
        self._chart_frame.pack(fill="both", expand=True, padx=pad, pady=(0, pad))

    def _build_header(self, container, pad):
        """Add title, best-strategy banner, info line, and action buttons."""
        top = tk.Frame(container, bg=CANVAS_BG)
        top.pack(fill="x", padx=pad, pady=(pad, 4))
        tk.Label(
            top, text="Experiment Results & Charts",
            font=(FONT_FAMILY, 14, "bold"), bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(side="left")
        ttk.Button(
            top, text="Save All Charts as PNG", command=self._on_save_charts,
        ).pack(side="right", padx=(8, 0))
        ttk.Button(
            top, text="Run Experiments", command=self._on_run_experiments,
        ).pack(side="right")

        self._best_var = tk.StringVar(value="Run experiments first.")
        tk.Label(
            container, textvariable=self._best_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), bg=CANVAS_BG, fg=ACTION_COLOR,
        ).pack(anchor="w", padx=pad, pady=(0, 4))

        self._info_var = tk.StringVar(
            value="Click 'Run Experiments' to run 3 sizes x 4 strategies with C++ M3 runner."
        )
        tk.Label(
            container, textvariable=self._info_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=CANVAS_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w", padx=pad, pady=(0, 8))

    def _build_result_table(self, container, pad):
        """Build the 11-column result Treeview with green highlight tag."""
        tk.Label(
            container,
            text="Result Table  (Green ★ = lowest AvgFrag% for that storage size)",
            font=(FONT_FAMILY, 10, "bold"), bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", padx=pad, pady=(0, 4))

        cols = (
            "N", "Ops", "Strategy", "OK", "FailFrag", "FailNoSp",
            "AvgFrag%", "AvgUtil%", "Segments", "Largest", "Time(ms)",
        )
        self._result_tree = ttk.Treeview(
            container, columns=cols, show="headings", height=13,
        )
        widths = {
            "N": 48, "Ops": 56, "Strategy": 100, "OK": 52,
            "FailFrag": 64, "FailNoSp": 68, "AvgFrag%": 70,
            "AvgUtil%": 70, "Segments": 66, "Largest": 60, "Time(ms)": 66,
        }
        for c in cols:
            self._result_tree.heading(c, text=c)
            anc = "w" if c == "Strategy" else "e"
            self._result_tree.column(c, width=widths[c], anchor=anc, stretch=True)
        self._result_tree.pack(anchor="w", padx=pad, pady=(0, 12), fill="x")
        self._result_tree.tag_configure("best_frag", background=INSIGHT_BG)

    def _on_scroll_configure(self, _event):
        self._outer.configure(scrollregion=self._outer.bbox("all"))

    def _on_canvas_resize(self, event):
        """Stretch the results content to the available window width."""
        self._outer.itemconfigure(self._scroll_window, width=max(1, event.width))

    def _on_canvas_enter(self, _event):
        self._outer.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_leave(self, _event):
        self._outer.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._outer.yview_scroll(-1 * (event.delta // 120), "units")

    # ---- Public display ------------------------------------------

    def show_results(self, table_rows, chart_data, sizes, seed, ops_list):
        """Populate result table, best-strategy banner, and all 9 charts."""
        self._info_var.set(
            "Seed: {}  |  Sizes: {}  |  Operations: {}".format(
                seed,
                ", ".join(str(s) for s in sizes),
                ", ".join(str(o) for o in ops_list),
            )
        )
        self._populate_table(table_rows)
        self._update_best_banner(table_rows)
        self._generate_charts(chart_data, sizes)

    def _populate_table(self, table_rows):
        """Fill Treeview rows and highlight/label lowest AvgFrag% per size."""
        self._result_tree.delete(*self._result_tree.get_children())
        best_per_size = {}
        for row in table_rows:
            n, frag = row["N"], row["AvgFrag%"]
            if n not in best_per_size or frag < best_per_size[n]:
                best_per_size[n] = frag
        for row in table_rows:
            is_best = row["AvgFrag%"] == best_per_size[row["N"]]
            strat_label = row["Strategy"] + (" ★" if is_best else "")
            vals = (
                row["N"], row["Ops"], strat_label,
                row["OK"], row["FailFrag"], row["FailNoSp"],
                "{:.1f}".format(row["AvgFrag%"]),
                "{:.1f}".format(row["AvgUtil%"]),
                row["Segments"], row["Largest"],
                "{:.1f}".format(row["Time(ms)"]),
            )
            tag = ("best_frag",) if is_best else ()
            self._result_tree.insert("", "end", values=vals, tags=tag)

    def _update_best_banner(self, table_rows):
        """Compute best overall strategy using dashboard_analytics."""
        frag_map = {}
        for row in table_rows:
            strat = row["Strategy"].lower().split()[0]
            frag_map.setdefault(strat, []).append(row["AvgFrag%"])
        avg_map = {s: sum(v) / len(v) for s, v in frag_map.items()}
        best = analytics_best(avg_map)
        if best["tied"]:
            self._best_var.set(
                "Tied: {} ({:.1f}% avg frag across sizes)".format(
                    best["best"], best["value"]
                )
            )
        elif best["value"] is not None:
            self._best_var.set(
                "Best observed: {} ({:.1f}% avg frag across sizes)".format(
                    best["best"], best["value"]
                )
            )

    def _generate_charts(self, data, sizes):
        """Render all 9 charts from charts.py along with text summaries."""
        import charts as ch
        for widget in self._chart_frame.winfo_children():
            widget.destroy()
        self._chart_figs.clear()
        if not HAS_MPL:
            tk.Label(
                self._chart_frame,
                text="Matplotlib not available — charts cannot be shown.",
                bg=CANVAS_BG, fg=TEXT_SECONDARY,
            ).pack()
            return
        for fname, title, func, args, summary in self._chart_specs(ch, data, sizes):
            self._embed_one_chart(fname, title, func, args, summary)

    def _chart_specs(self, ch, data, sizes):
        """Return (filename, title, func, args, summary) tuples for all 9 charts."""
        max_sz = sizes[-1]
        return [
            ("1_avg_ext_fragmentation.png", "1. Avg External Fragmentation",
             ch.chart_avg_frag, [data["avg_frag"], sizes],
             self._summarize_min(data["avg_frag"][max_sz], "lowest avg frag at N={}".format(max_sz), "%")),
            ("2_frag_failure_rate.png", "2. Fragmentation Failure Rate",
             ch.chart_frag_fail_rate, [data["frag_fail_rate"], sizes],
             self._summarize_min(data["frag_fail_rate"][max_sz], "lowest frag-failure rate at N={}".format(max_sz), "%")),
            ("3_avg_utilisation.png", "3. Avg Utilisation",
             ch.chart_avg_util, [data["avg_util"], sizes],
             self._summarize_max(data["avg_util"][max_sz], "highest utilisation at N={}".format(max_sz), "%")),
            ("4_simulation_time_log.png", "4. Simulation Time (log scale)",
             ch.chart_sim_time, [data["sim_time"], sizes],
             "Simulation time scales with storage size N and operation count across all strategies."),
            ("5_stacked_failures.png", "5. Stacked Failures (FRAGMENTATION vs NO_SPACE)",
             ch.chart_stacked_failures, [data["stacked_fail"], sizes],
             "Compares fragmentation-caused failures against true capacity NO_SPACE failures per size."),
            ("6_frag_timeline.png", "6. Fragmentation Over Operations",
             ch.chart_frag_timeline, [data["frag_history"], sizes],
             "Tracks how external fragmentation builds up over sequential workload operations."),
            ("7_heatmap_avg_frag.png", "7. Heat Map: Avg External Fragmentation",
             ch.chart_heatmap_frag, [data["avg_frag"], sizes],
             "Band thresholds: <20% Low, 20-<40% Moderate, >=40% High."),
            ("8_heatmap_frag_fail_rate.png", "8. Heat Map: Frag Failure Rate",
             ch.chart_heatmap_frag_fail, [data["frag_fail_rate"], sizes],
             "Share of allocation requests rejected specifically because free holes were fragmented."),
            ("9_heatmap_avg_utilisation.png", "9. Heat Map: Avg Utilisation",
             ch.chart_heatmap_util, [data["avg_util"], sizes],
             "Band thresholds: <50% Underutilised, 50-<85% Efficient, >=85% Highly utilised."),
        ]

    def _embed_one_chart(self, fname, title, func, args, summary):
        tk.Label(
            self._chart_frame, text=title, font=(FONT_FAMILY, 11, "bold"),
            bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(12, 2))
        try:
            fig = func(*args)
            self._chart_figs.append((fname, fig))
            canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(anchor="w", pady=(0, 2))
            tk.Label(
                self._chart_frame, text="Summary: " + summary,
                font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=CANVAS_BG, fg=TEXT_SECONDARY,
            ).pack(anchor="w", pady=(0, 6))
        except Exception as err:
            tk.Label(
                self._chart_frame, text="Chart error: {}".format(err),
                bg=CANVAS_BG, fg=DANGER_COLOR,
            ).pack(anchor="w")

    def _summarize_min(self, metric_map, desc, unit):
        key = min(metric_map, key=metric_map.get)
        return "{} achieved {} ({:.1f}{}).".format(key.title() + " Fit", desc, metric_map[key], unit)

    def _summarize_max(self, metric_map, desc, unit):
        key = max(metric_map, key=metric_map.get)
        return "{} achieved {} ({:.1f}{}).".format(key.title() + " Fit", desc, metric_map[key], unit)

    # ---- Button handlers -----------------------------------------

    def _on_run_experiments(self):
        """Trigger the 3-size experiment suite from Results & Charts tab."""
        self.ctrl.main_view._on_run_experiments()

    def _on_save_charts(self):
        """Save all generated figures as 200 dpi PNG files."""
        import charts as ch
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "outputs", "charts",
        )
        os.makedirs(out_dir, exist_ok=True)
        for fname, fig in self._chart_figs:
            ch.save_chart(fig, os.path.join(out_dir, fname))
        self._info_var.set(
            self._info_var.get() + "  |  {} charts saved to outputs/charts/".format(len(self._chart_figs))
        )


def analytics_best(avg_map):
    """Import and invoke dashboard_analytics.best_strategy cleanly."""
    import dashboard_analytics as analytics
    return analytics.best_strategy(avg_map)
