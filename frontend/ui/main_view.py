"""
ui/main_view.py — Dashboard tab (the primary screen).

Layout (4 columns, 16 px gap):
  Header:  Title · operation count · Sample/Live badge · Reduce motion · Export CSV
  Row 1:   External fragmentation (hero) · Utilisation · Largest segment · Free segments
  Row 2:   Controls + Legend (1 col) · Storage layout BlockGrid (3 cols)
  Row 3:   Fragmentation trend (2) · Donut (1) · Analytics insight (1)
  Row 4:   Process table (2) · Event log (2)
"""

import tkinter as tk
from tkinter import ttk, filedialog
from ui.theme import (
    CANVAS_BG, TILE_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, DANGER_COLOR, INSIGHT_BG, FREE_FILL, FREE_OUTLINE,
    HERO_DARK, HERO_TEXT,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    TREND_BAND_LOW, TREND_BAND_MOD, TREND_BAND_HIGH,
    TREND_LINE_CLR, DONUT_OCCUPIED, DONUT_FREE,
)
from ui.widgets import (
    RoundedTile, MetricCard, HeroCard, BlockGrid,
)
import dashboard_analytics as analytics

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class MainView(ttk.Frame):
    """The primary Dashboard tab."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ctrl = controller
        self._prev_stats = None
        self._reduce_motion = tk.BooleanVar(value=False)
        self._data_badge_var = tk.StringVar(value="Sample data")
        self._last_failure_seen = False
        self._last_failed_size = 0
        self._last_failed_strategy = "First Fit"
        self._trend_fig = None
        self._trend_canvas = None
        self._donut_fig = None
        self._donut_canvas = None
        self._build_ui()

    # ---- Layout assembly -----------------------------------------

    def _build_ui(self):
        """Assemble scrollable container and dashboard rows."""
        self.configure(style="Dashboard.TFrame")
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
        self._populate_rows(self._scroll_frame, 16)

    def _populate_rows(self, container, pad):
        self._build_header(container, pad)
        self._build_metric_row(container, pad)
        self._build_controls_and_grid(container, pad)
        self._build_analytics_row(container, pad)
        self._build_tables_row(container, pad)

    def _on_scroll_configure(self, _event):
        self._outer.configure(scrollregion=self._outer.bbox("all"))

    def _on_canvas_resize(self, event):
        """Keep the embedded dashboard frame as wide as the visible canvas."""
        self._outer.itemconfigure(self._scroll_window, width=max(1, event.width))

    def _on_canvas_enter(self, _event):
        self._outer.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_canvas_leave(self, _event):
        self._outer.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self._outer.yview_scroll(-1 * (event.delta // 120), "units")

    # ---- Header --------------------------------------------------

    def _build_header(self, parent, pad):
        """Title bar with op count, data badge, and Export CSV."""
        frame = tk.Frame(parent, bg=HERO_DARK)
        frame.pack(fill="x", padx=pad, pady=(pad, 8))
        tk.Label(
            frame, text="VIRTUAL STORAGE ALLOCATION SIMULATOR",
            font=(FONT_FAMILY, 16, "bold"), bg=HERO_DARK, fg=HERO_TEXT,
            padx=14, pady=11,
        ).pack(side="left")
        self._op_count_var = tk.StringVar(value="0 operations")
        tk.Label(
            frame, textvariable=self._op_count_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), bg=HERO_DARK, fg=HERO_TEXT,
        ).pack(side="left", padx=(18, 0))
        tk.Label(
            frame, textvariable=self._data_badge_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg="#005F73", fg="#FFFFFF", padx=9, pady=4,
        ).pack(side="left", padx=(12, 0))
        ttk.Button(
            frame, text="Export Log (CSV)", command=self._on_export_csv,
        ).pack(side="right")
        ttk.Checkbutton(
            frame, text="Reduce motion", variable=self._reduce_motion,
        ).pack(side="right", padx=(0, 12))

    # ---- Row 1: metric cards -------------------------------------

    def _build_metric_row(self, parent, pad):
        """Create the four summary metric tiles in Row 1."""
        frame = tk.Frame(parent, bg=CANVAS_BG)
        frame.pack(fill="x", padx=pad, pady=(4, 4))
        self._hero = HeroCard(
            frame, label="Scattered Free Space", value="—",
            status="", width=280, height=140, command=self._on_hero_click,
        )
        self._hero.pack(side="left", padx=(0, pad))
        self._util_card = MetricCard(
            frame, label="Utilisation", value="—", width=230, height=140,
        )
        self._util_card.pack(side="left", padx=(0, pad))
        self._largest_card = MetricCard(
            frame, label="Largest Free Area", value="—", width=230, height=140,
        )
        self._largest_card.pack(side="left", padx=(0, pad))
        self._segments_card = MetricCard(
            frame, label="Separate Free Areas", value="—", width=230, height=140,
        )
        self._segments_card.pack(side="left")

    # ---- Row 2: controls + block grid ----------------------------

    def _build_controls_and_grid(self, parent, pad):
        """Controls + Legend tile on left, storage layout grid on right."""
        frame = tk.Frame(parent, bg=CANVAS_BG)
        frame.pack(fill="both", expand=True, padx=pad, pady=(4, 4))

        ctrl_tile = RoundedTile(frame, width=320, height=1000, bg_color=TILE_BG)
        ctrl_tile.pack(side="left", anchor="nw", padx=(0, pad))
        self._build_controls(ctrl_tile.inner)

        right = tk.Frame(frame, bg=CANVAS_BG)
        right.pack(side="left", fill="both", expand=True)
        grid_tile = RoundedTile(right, width=820, height=620, bg_color=TILE_BG)
        grid_tile.pack(fill="both", expand=True)
        tk.Label(
            grid_tile.inner, text="MEMORY BLOCK MAP",
            font=(FONT_FAMILY, 14, "bold"), bg=TILE_BG, fg=ACTION_COLOR,
        ).pack(anchor="w", padx=12, pady=(10, 2))
        tk.Label(
            grid_tile.inner,
            text="Each box represents one memory block. Coloured boxes are assigned to a process; pale outlined boxes are free. The numbers on the left show block positions.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=TILE_BG, fg=TEXT_SECONDARY,
            wraplength=760, justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 8))
        grid_area = tk.Frame(grid_tile.inner, bg=TILE_BG)
        grid_area.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self._grid = BlockGrid(
            grid_area, status_callback=self._on_grid_status
        )

        grid_scrollbar = ttk.Scrollbar(
            grid_area, orient="vertical", command=self._grid.yview
        )
        self._grid.configure(yscrollcommand=grid_scrollbar.set)

        self._grid.pack(side="left", fill="both", expand=True)
        grid_scrollbar.pack(side="right", fill="y")

        self._status_var = tk.StringVar(value="Ready — Backend: C++ (M1–M4)")
        tk.Label(
            right, textvariable=self._status_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=CANVAS_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

    def _build_controls(self, parent):
        """Assemble controls panel in concise grouped sections."""
        parent.configure(bg=TILE_BG)
        self._build_request_inputs(parent)
        self._build_primary_buttons(parent)
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=6)
        self._build_workload_inputs(parent)
        self._build_legend(parent)
        self._build_msg_area(parent)

    def _build_request_inputs(self, parent):
        """Show simple, student-friendly labels for the memory operations."""
        tk.Label(
            parent, text="MEMORY CONTROLS", font=(FONT_FAMILY, 12, "bold"),
            bg=TILE_BG, fg=ACTION_COLOR,
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            parent,
            text="Add a process by giving it a short name and the number of memory blocks it needs. Then choose how free space should be searched.",
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=TILE_BG,
            fg=TEXT_SECONDARY, wraplength=270, justify="left",
        ).pack(anchor="w", pady=(0, 9))
        self._pid_var = self._add_labeled_entry(parent, "Process name (e.g. P1):")
        self._size_var = self._add_labeled_entry(parent, "Memory blocks needed:")
        tk.Label(
            parent, text="How to find free space:", font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w")
        self._strategy_var = tk.StringVar(value="First Fit")
        ttk.Combobox(
            parent, textvariable=self._strategy_var, width=25,
            values=["First Fit", "Next Fit", "Best Fit", "Worst Fit"],
            state="readonly",
        ).pack(anchor="w", pady=(0, 2))
        tk.Label(
            parent,
            text="First: first space that fits. Next: continue searching from the last position. Best: smallest space that fits. Worst: largest free space.",
            font=(FONT_FAMILY, 8), bg=TILE_BG, fg=TEXT_SECONDARY,
            wraplength=270, justify="left",
        ).pack(anchor="w", pady=(0, 6))

    def _add_labeled_entry(self, parent, label_text, default=""):
        """Helper to pack a readable label + entry pair."""
        tk.Label(
            parent, text=label_text, font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w")
        var = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=var, width=27).pack(anchor="w", pady=(0, 4))
        return var

    def _build_primary_buttons(self, parent):
        """Buttons for adding, removing, rearranging and clearing memory."""
        row1 = tk.Frame(parent, bg=TILE_BG)
        row1.pack(fill="x", pady=2)
        ttk.Button(row1, text="Add Process", command=self._on_allocate).pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        ttk.Button(row1, text="Remove Process", command=self._on_release).pack(
            side="left", fill="x", expand=True, padx=(3, 0)
        )
        row2 = tk.Frame(parent, bg=TILE_BG)
        row2.pack(fill="x", pady=2)
        ttk.Button(row2, text="Arrange Free Space", command=self._on_compact).pack(
            side="left", fill="x", expand=True, padx=(0, 3)
        )
        ttk.Button(row2, text="Clear Memory", command=self._on_reset).pack(
            side="left", fill="x", expand=True, padx=(3, 0)
        )
        tk.Label(
            parent,
            text="Add = place a process   •   Remove = free its blocks\nArrange = move used blocks together   •   Clear = start again",
            font=(FONT_FAMILY, 8), bg=TILE_BG, fg=TEXT_SECONDARY,
            wraplength=275, justify="left",
        ).pack(anchor="w", pady=(3, 5))

    def _build_workload_inputs(self, parent):
        """Inputs for repeatable sample activity and method comparison."""
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=5)
        self._ops_var = self._add_labeled_entry(parent, "Number of automatic steps:", "300")
        self._seed_var = self._add_labeled_entry(parent, "Repeat number (seed):", "7")
        tk.Label(
            parent,
            text="Steps = how many automatic add/remove actions to simulate. The same repeat number generates the same activity sequence for a fair comparison.",
            font=(FONT_FAMILY, 8), bg=TILE_BG, fg=TEXT_SECONDARY,
            wraplength=270, justify="left",
        ).pack(anchor="w", pady=(0, 4))
        ttk.Button(
            parent, text="Run Sample Activity", command=self._on_run_workload,
        ).pack(fill="x", pady=2)
        ttk.Button(
            parent, text="Compare Placement Methods", command=self._on_compare,
        ).pack(fill="x", pady=2)
        ttk.Button(
            parent, text="Run Tests & Show Charts", command=self._on_run_experiments,
        ).pack(fill="x", pady=2)

    def _build_legend(self, parent):
        """Compact block-grid legend matching blueprint specification."""
        tk.Label(
            parent, text="Legend:", font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold"),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(6, 2))
        self._add_legend_item(parent, FREE_FILL, FREE_OUTLINE, "Free memory")
        self._add_legend_item(parent, ACTION_COLOR, TEXT_PRIMARY, "Used by a process")

    def _add_legend_item(self, parent, fill, outline, text):
        row = tk.Frame(parent, bg=TILE_BG)
        row.pack(anchor="w", pady=1)
        swatch = tk.Canvas(row, width=14, height=14, bg=TILE_BG, highlightthickness=0)
        swatch.create_rectangle(2, 2, 12, 12, fill=fill, outline=outline, width=2)
        swatch.pack(side="left", padx=(0, 6))
        tk.Label(
            row, text=text, font=(FONT_FAMILY, 8), bg=TILE_BG, fg=TEXT_SECONDARY,
        ).pack(side="left")

    def _build_msg_area(self, parent):
        self._msg_var = tk.StringVar(value="")
        self._msg_label = tk.Label(
            parent, textvariable=self._msg_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=TILE_BG,
            fg=TEXT_SECONDARY, wraplength=270, justify="left",
        )
        self._msg_label.pack(anchor="w", pady=(6, 0))

    # ---- Row 3: trend + donut + insight --------------------------

    def _build_analytics_row(self, parent, pad):
        """Fragmentation trend, donut chart, and analytics insight tile."""
        frame = tk.Frame(parent, bg=CANVAS_BG)
        frame.pack(fill="x", padx=pad, pady=(4, 4))
        self._build_trend_tile(frame, pad)
        self._build_donut_tile(frame, pad)
        self._build_insight_tile(frame)

    def _build_trend_tile(self, parent, pad):
        tile = RoundedTile(parent, width=540, height=250, bg_color=TILE_BG)
        tile.pack(side="left", padx=(0, pad))
        self._trend_frame = tile.inner
        if HAS_MPL:
            self._trend_fig = Figure(figsize=(5.1, 2.1), dpi=100)
            self._trend_fig.patch.set_facecolor(TILE_BG)
            self._trend_canvas = FigureCanvasTkAgg(self._trend_fig, master=self._trend_frame)
            self._trend_canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(
                self._trend_frame, text="Matplotlib not available",
                bg=TILE_BG, fg=TEXT_SECONDARY,
            ).pack()

    def _build_donut_tile(self, parent, pad):
        tile = RoundedTile(parent, width=250, height=250, bg_color=TILE_BG)
        tile.pack(side="left", padx=(0, pad))
        self._donut_frame = tile.inner
        if HAS_MPL:
            self._donut_fig = Figure(figsize=(2.3, 2.1), dpi=100)
            self._donut_fig.patch.set_facecolor(TILE_BG)
            self._donut_canvas = FigureCanvasTkAgg(self._donut_fig, master=self._donut_frame)
            self._donut_canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(self._donut_frame, text="—", bg=TILE_BG, fg=TEXT_SECONDARY).pack()

    def _build_insight_tile(self, parent):
        tile = RoundedTile(parent, width=260, height=250, bg_color=INSIGHT_BG)
        tile.pack(side="left")
        self._insight_var = tk.StringVar(value="Data pending")
        tk.Label(
            tile.inner, text="Analytics Insight",
            font=(FONT_FAMILY, 10, "bold"), bg=INSIGHT_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 4))
        tk.Label(
            tile.inner, textvariable=self._insight_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL), bg=INSIGHT_BG,
            fg=TEXT_PRIMARY, wraplength=185, justify="left",
        ).pack(anchor="w")

    # ---- Row 4: process table + event log ------------------------

    def _build_tables_row(self, parent, pad):
        """Process table and event log tiles side by side."""
        frame = tk.Frame(parent, bg=CANVAS_BG)
        frame.pack(fill="both", expand=True, padx=pad, pady=(4, pad))
        self._build_process_table_tile(frame, pad)
        self._build_event_log_tile(frame)

    def _build_process_table_tile(self, parent, pad):
        ptile = RoundedTile(parent, width=520, height=260, bg_color=TILE_BG)
        ptile.pack(side="left", fill="both", expand=True, padx=(0, pad))
        tk.Label(
            ptile.inner, text="Process Table",
            font=(FONT_FAMILY, 10, "bold"), bg=TILE_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 4))
        cols = ("pid", "start", "size", "end")

        proc_area = tk.Frame(ptile.inner, bg=TILE_BG)
        proc_area.pack(fill="both", expand=True)

        self._proc_tree = ttk.Treeview(
            proc_area, columns=cols, show="tree headings", height=7,
        )

        proc_scrollbar = ttk.Scrollbar(
            proc_area, orient="vertical",
            command=self._proc_tree.yview
        )
        self._proc_tree.configure(yscrollcommand=proc_scrollbar.set)

        self._proc_tree.heading("#0", text="")
        self._proc_tree.column("#0", width=28, anchor="center", stretch=False)

        for c, label, anc in [
            ("pid", "Process", "w"), ("start", "Start", "e"),
            ("size", "Size", "e"), ("end", "End", "e"),
        ]:
            self._proc_tree.heading(c, text=label)
            self._proc_tree.column(c, width=85, anchor=anc)

        self._proc_tree.pack(side="left", fill="both", expand=True)
        proc_scrollbar.pack(side="right", fill="y")

        self._proc_tree.bind(
            "<<TreeviewSelect>>", self._on_process_select
        )

    def _build_event_log_tile(self, parent):
        ltile = RoundedTile(parent, width=520, height=260, bg_color=TILE_BG)
        ltile.pack(side="left", fill="both", expand=True)
        tk.Label(
            ltile.inner, text="Event Log",
            font=(FONT_FAMILY, 10, "bold"), bg=TILE_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 4))
        cols = ("step", "op", "pid", "size", "result", "reason")

        # Frame to hold the event log and its scrollbar
        log_area = tk.Frame(ltile.inner, bg=TILE_BG)
        log_area.pack(fill="both", expand=True)

        self._log_tree = ttk.Treeview(
            log_area, columns=cols, show="headings", height=7,
        )

        # Configure column headings and widths
        for c in cols:
            self._log_tree.heading(c, text=c.capitalize())
            w = 50 if c in ("step", "size") else 80
            anc = "e" if c in ("step", "size") else "center"
            self._log_tree.column(c, width=w, anchor=anc)

        # Add vertical scrollbar
        log_scrollbar = ttk.Scrollbar(
            log_area,
            orient="vertical",
            command=self._log_tree.yview
        )
        self._log_tree.configure(yscrollcommand=log_scrollbar.set)

        # Display table and scrollbar side by side
        self._log_tree.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")

    # ---- Named event handlers ------------------------------------

    def _on_allocate(self):
        """Validate PID and numeric size before calling backend allocate."""
        pid = self._pid_var.get().strip()
        size_str = self._size_var.get().strip()
        strategy = self._strategy_var.get()
        if not pid:
            self._show_msg("Please enter a Process ID.", "invalid")
            return
        if not size_str:
            self._show_msg("Please enter a size.", "invalid")
            return
        try:
            size = int(size_str)
        except ValueError:
            self._show_msg("Size must be a whole number.", "invalid")
            return
        self._finish_allocate(pid, size, strategy, self.ctrl.allocate(pid, size, strategy))

    def _finish_allocate(self, pid, size, strategy, result):
        """Handle backend allocation outcome and refresh views."""
        if result.ok:
            msg = "Allocated {} ({} blocks at {}).".format(pid, size, result.start)
            self._show_msg(msg, "success")
        else:
            self._show_msg("Allocation failed: {}".format(result.reason), "fail")
            if result.reason in ("FRAGMENTATION", "NO_SPACE"):
                self._last_failure_seen = True
                self._last_failed_size = size
                self._last_failed_strategy = strategy
                self.ctrl.show_failure(size, strategy, pid)
        self.refresh()

    def _on_release(self):
        """Release process entered in PID field."""
        pid = self._pid_var.get().strip()
        if not pid:
            self._show_msg("Please enter a Process ID.", "invalid")
            return
        result = self.ctrl.release(pid)
        if result.ok:
            self._show_msg("Released {}.".format(pid), "success")
        else:
            self._show_msg("Release failed: {}".format(result.reason), "fail")
        self.refresh()

    def _on_compact(self):
        """Run storage compaction and refresh dashboard."""
        self.ctrl.compact()
        self.ctrl.notebook.select(2)
        self._show_msg("Compaction complete.", "success")
        self.refresh()

    def _on_reset(self):
        """Reset storage to empty 100 blocks."""
        self.ctrl.reset()
        self._grid.reset_colors()
        self._last_failure_seen = False
        self._show_msg("Storage reset.", "success")
        self.refresh()

    def _on_run_workload(self):
        """Run C++ seeded workload and refresh dashboard."""
        parsed = self._parse_ops_seed()
        if parsed is None:
            return
        ops, seed = parsed
        self._set_busy(True, "Running workload...")
        self.ctrl.run_workload(ops, seed, self._strategy_var.get())
        self._set_busy(False, "Ready — Backend: {}".format(self.ctrl.backend.backend_mode))
        self._show_msg("Workload complete ({} ops, seed {}).".format(ops, seed), "success")
        self.refresh()

    def _on_compare(self):
        """Run strategy comparison across all 4 strategies."""
        parsed = self._parse_ops_seed()
        if parsed is None:
            return
        ops, seed = parsed
        self._set_busy(True, "Running strategy comparison...")
        self.ctrl.compare_strategies(ops, seed)
        self._set_busy(False, "Ready — Backend: {}".format(self.ctrl.backend.backend_mode))

    def _on_run_experiments(self):
        """Run 3-size x 4-strategy C++ experiment suite."""
        parsed = self._parse_ops_seed()
        seed = parsed[1] if parsed is not None else 7
        self._set_busy(True, "Running experiments across 3 sizes x 4 strategies...")
        self.ctrl.run_experiments([100, 1000, 5000], [300, 3000, 10000], seed)
        self._set_busy(False, "Ready — Backend: {}".format(self.ctrl.backend.backend_mode))

    def _parse_ops_seed(self):
        """Validate numeric Operations and Seed fields."""
        try:
            ops = int(self._ops_var.get().strip())
            seed = int(self._seed_var.get().strip())
        except ValueError:
            self._show_msg("Operations and seed must be whole numbers.", "invalid")
            return None
        if ops <= 0:
            self._show_msg("Operations must be positive.", "invalid")
            return None
        return ops, seed

    def _on_export_csv(self):
        """Open file dialog and export C++ event log to CSV."""
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            title="Export Event Log",
        )
        if not path:
            return
        if self.ctrl.export_csv(path):
            self._show_msg("Log exported to {}".format(path), "success")
        else:
            self._show_msg("Export failed.", "fail")

    def _on_process_select(self, _event):
        """Highlight blocks of selected process in the BlockGrid."""
        sel = self._proc_tree.selection()
        if sel:
            vals = self._proc_tree.item(sel[0]).get("values", [])
            if vals:
                self._grid.highlight_process(str(vals[0]))

    def _on_hero_click(self):
        """Open Failure Analysis if a failure occurred, else show trend status."""
        if self._last_failure_seen:
            self.ctrl.notebook.select(1)
        else:
            self._show_msg(
                "No allocation failure yet — view Fragmentation Trend below.", "info"
            )

    def _on_grid_status(self, text):
        """Update visible status line when hovering or stepping grid cells."""
        self._status_var.set(text)

    def _set_busy(self, busy, status_text):
        """Show busy cursor and status line cleanly without threads."""
        self._status_var.set(status_text)
        try:
            self.ctrl.root.configure(cursor="watch" if busy else "")
        except tk.TclError:
            pass
        self.update_idletasks()

    # ---- Refresh -------------------------------------------------

    def refresh(self):
        """Redraw all dashboard widgets from current C++ backend state."""
        backend = self.ctrl.backend
        st = backend.stats()
        arr = backend.array
        table = backend.table
        log = backend.get_log()
        history = backend.get_frag_history()

        self._refresh_cards(st)
        self._grid.draw(arr, table)
        self._op_count_var.set("{} operations".format(len(log)))
        self._data_badge_var.set("Sample data" if backend.is_sample else "Live")
        self._refresh_process_table(table)
        self._refresh_event_log(log)
        self._refresh_insight(st, history, log)
        self._refresh_charts(history, st)
        if not self._reduce_motion.get():
            self._flash_hero()

    def _refresh_cards(self, st):
        """Update all four metric tiles and deltas."""
        prev = self._prev_stats
        self._hero.update_hero(
            "{:.1f}%".format(st.ext_frag),
            analytics.fragmentation_status(st.ext_frag).upper(),
        )
        util_delta, util_good = analytics.metric_delta(
            prev.utilisation if prev else None, st.utilisation, higher_is_good=True,
        )
        self._util_card.update_value(
            "{:.1f}%".format(st.utilisation),
            delta=util_delta, delta_good=util_good,
            subtitle="Occupied: {} | Free: {}".format(st.occupied, st.free),
        )
        lg_delta, lg_good = analytics.metric_delta(
            prev.largest if prev else None, st.largest, higher_is_good=True,
        )
        self._largest_card.update_value(str(st.largest), delta=lg_delta, delta_good=lg_good)
        self._segments_card.update_value(
            str(st.segments), delta="Avg hole: {:.1f}".format(st.avg_hole),
        )
        self._prev_stats = st

    def _refresh_process_table(self, table):
        """Reload the Process Table with colour swatches and right-aligned sizes."""
        self._proc_tree.delete(*self._proc_tree.get_children())
        for pid in sorted(table.keys()):
            start, size = table[pid]
            bg, fg = self._grid.get_process_color(pid)
            tag = "swatch_{}".format(pid)
            self._proc_tree.tag_configure(tag, background=bg, foreground=fg)
            self._proc_tree.insert(
                "", "end", text="■", values=(pid, start, size, start + size - 1),
                tags=(tag,),
            )

    def _refresh_event_log(self, log):
        """Reload the Event Log with coloured OK/FAIL markers."""
        self._log_tree.delete(*self._log_tree.get_children())
        for entry in reversed(log):
            is_ok = (entry.result == "OK")
            marker = "● OK" if is_ok else "▲ FAIL"
            tag = "ok" if is_ok else "fail"
            self._log_tree.insert(
                "", "end",
                values=(entry.step, entry.op, entry.pid, entry.size, marker, entry.reason),
                tags=(tag,),
            )
        self._log_tree.tag_configure("ok", foreground="#000000")
        self._log_tree.tag_configure("fail", foreground="#000000")

    def _refresh_insight(self, st, history, log):
        """Update the Analytics Insight tile text."""
        prev_frag = history[-2] if len(history) >= 2 else None
        last_reason = None
        if log and log[-1].result == "FAIL":
            last_reason = log[-1].reason
        insight = analytics.build_insight(st.ext_frag, prev_frag, history, last_reason)
        self._insight_var.set(insight["text"])

    def _refresh_charts(self, history, st):
        if HAS_MPL:
            self._refresh_trend_chart(history)
            self._refresh_donut(st.occupied, st.free)

    def _refresh_trend_chart(self, history):
        """Redraw embedded fragmentation trend chart."""
        if not self._trend_fig:
            return
        self._trend_fig.clear()
        ax = self._trend_fig.add_subplot(111)
        ax.set_facecolor(TILE_BG)
        if len(history) > 1:
            ax.axhspan(0, 20, color=TREND_BAND_LOW, alpha=0.3)
            ax.axhspan(20, 40, color=TREND_BAND_MOD, alpha=0.3)
            ax.axhspan(40, 100, color=TREND_BAND_HIGH, alpha=0.3)
            ax.plot(list(range(len(history))), history, color=TREND_LINE_CLR, linewidth=1.5)
            ax.set_ylabel("Frag %", fontsize=8, color=TEXT_SECONDARY)
            ax.set_xlabel("Operation", fontsize=8, color=TEXT_SECONDARY)
            ax.tick_params(labelsize=7, colors=TEXT_SECONDARY)
        else:
            ax.text(
                0.5, 0.5, "Not enough data", ha="center", va="center",
                transform=ax.transAxes, fontsize=10, color=TEXT_SECONDARY,
            )
        ax.set_title("Fragmentation Trend", fontsize=10, fontweight="bold", color=TEXT_PRIMARY)
        self._trend_fig.tight_layout()
        self._trend_canvas.draw()

    def _refresh_donut(self, occupied, free):
        """Redraw embedded free/occupied donut chart."""
        if not self._donut_fig:
            return
        self._donut_fig.clear()
        ax = self._donut_fig.add_subplot(111)
        if occupied + free == 0:
            ax.text(0.5, 0.5, "Empty", ha="center", va="center", transform=ax.transAxes)
        else:
            _, _, autotexts = ax.pie(
                [occupied, free], labels=["Occupied", "Free"],
                colors=[DONUT_OCCUPIED, DONUT_FREE], autopct="%1.0f%%",
                startangle=90, pctdistance=0.75,
                wedgeprops=dict(width=0.35, edgecolor="white"), textprops={"fontsize": 7},
            )
            autotexts[0].set_color("#FFFFFF")
            autotexts[1].set_color(TEXT_PRIMARY)
        ax.set_title("Free vs Occupied", fontsize=9, fontweight="bold", color=TEXT_PRIMARY)
        self._donut_fig.tight_layout()
        self._donut_canvas.draw()

    def _show_msg(self, text, kind="info"):
        """Display distinctly styled feedback for success, failure, and invalid input."""
        colors = {"success": TEXT_PRIMARY, "fail": DANGER_COLOR, "invalid": "#9B2226", "info": TEXT_SECONDARY}
        prefix = {"success": "SUCCESS: ", "fail": "FAILED: ", "invalid": "INPUT ERROR: ", "info": ""}
        self._msg_var.set(prefix.get(kind, "") + text)
        self._msg_label.configure(fg=colors.get(kind, TEXT_SECONDARY))

    def _flash_hero(self):
        """Briefly highlight hero KPI value after refresh."""
        original = self._hero.itemcget(self._hero._val_id, "fill")
        self._hero.itemconfigure(self._hero._val_id, fill="#94D2BD")
        self._hero.after(300, self._restore_hero_color)
        self._hero_orig_color = original

    def _restore_hero_color(self):
        color = getattr(self, "_hero_orig_color", "#FFFFFF")
        self._hero.itemconfigure(self._hero._val_id, fill=color)
