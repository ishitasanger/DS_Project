"""
ui/failure_view.py — Failure Analysis tab.

Shown when an allocation returns NO_SPACE or FRAGMENTATION.
Displays:
  - Banner with failure type
  - Block grid with outlined free segments
  - Segment list with fit check for the failed request size
  - 4-line explanation from M4's analyze_failure()
  - Buttons: Run Compaction and Retry, Try Another Strategy
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import (
    CANVAS_BG, TILE_BG, TEXT_PRIMARY, ACTION_COLOR, DANGER_COLOR,
    FAIL_FRAG_COLOR, FONT_FAMILY, FONT_SIZE_NORMAL,
)
from ui.widgets import RoundedTile, BlockGrid


class FailureView(ttk.Frame):
    """Failure analysis tab content."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ctrl = controller
        self._last_size = 0
        self._last_strategy = "First Fit"
        self._last_pid = ""
        self._build_ui()

    def _build_ui(self):
        """Assemble the failure analysis layout."""
        container = tk.Frame(self, bg=CANVAS_BG)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        self._banner_var = tk.StringVar(value="No failure to analyse")
        self._banner = tk.Label(
            container, textvariable=self._banner_var,
            font=(FONT_FAMILY, 14, "bold"), bg="#EAF2F1", fg=TEXT_PRIMARY,
            padx=12, pady=9,
        )
        self._banner.pack(anchor="w", fill="x", pady=(0, 12))

        content = tk.Frame(container, bg=CANVAS_BG)
        content.pack(fill="both", expand=True)
        self._build_grid_panel(content)
        self._build_detail_panel(content)

    def _build_grid_panel(self, parent):
        """Create the left block grid showing outlined free segments."""
        grid_tile = RoundedTile(
            parent, width=580, height=390, bg_color=TILE_BG,
        )
        grid_tile.pack(side="left", anchor="nw", padx=(0, 16))
        self._grid = BlockGrid(grid_tile.inner)
        self._grid.pack(fill="both", expand=True)

    def _build_detail_panel(self, parent):
        """Create right-hand segment fit table, explanation, and buttons."""
        detail = tk.Frame(parent, bg=CANVAS_BG)
        detail.pack(side="left", fill="both", expand=True)
        self._build_segment_table(detail)
        self._build_explanation(detail)
        self._build_action_buttons(detail)

    def _build_segment_table(self, parent):
        """Add treeview listing every free hole and whether it fits."""
        tk.Label(
            parent, text="Free Segments", font=(FONT_FAMILY, 11, "bold"),
            bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        cols = ("start", "size", "fits")
        self._seg_tree = ttk.Treeview(
            parent, columns=cols, show="headings", height=6,
        )
        self._seg_tree.heading("start", text="Start")
        self._seg_tree.heading("size", text="Size")
        self._seg_tree.heading("fits", text="Fits Request?")
        for col in cols:
            anchor = "e" if col in ("start", "size") else "center"
            self._seg_tree.column(col, width=95, anchor=anchor)
        self._seg_tree.pack(anchor="w", pady=(0, 12))

    def _build_explanation(self, parent):
        """Add 4-line failure explanation label."""
        tk.Label(
            parent, text="Explanation", font=(FONT_FAMILY, 11, "bold"),
            bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        self._explanation_var = tk.StringVar(value="Data pending")
        tk.Label(
            parent, textvariable=self._explanation_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL), bg=CANVAS_BG,
            fg=TEXT_PRIMARY, wraplength=380, justify="left",
        ).pack(anchor="w", pady=(0, 12))

    def _build_action_buttons(self, parent):
        """Add compaction-retry and strategy-switch buttons."""
        btn_frame = tk.Frame(parent, bg=CANVAS_BG)
        btn_frame.pack(anchor="w")
        ttk.Button(
            btn_frame, text="Run Compaction and Retry",
            command=self._on_compact_retry,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_frame, text="Try Another Strategy",
            command=self._on_try_strategy,
        ).pack(side="left")

        self._result_var = tk.StringVar(value="")
        self._result_label = tk.Label(
            parent, textvariable=self._result_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=CANVAS_BG, fg=TEXT_PRIMARY,
        )
        self._result_label.pack(anchor="w", pady=(12, 0))

    # ---- Public methods ------------------------------------------

    def show_failure(self, request_size, strategy, pid=""):
        """Populate the tab using M4's analyze_failure() classification."""
        self._last_size = request_size
        self._last_strategy = strategy
        self._last_pid = pid
        backend = self.ctrl.backend
        fa = backend.analyze_failure(request_size)
        self._update_banner(fa.reason, request_size)
        self._grid.draw(backend.array, backend.table)
        self._populate_segments(backend.free_segments(), request_size)
        self._explanation_var.set(fa.explanation)
        self._result_var.set("")

    def _update_banner(self, reason, request_size):
        if reason == "FRAGMENTATION":
            self._banner_var.set(
                "FRAGMENTATION — Request of {} blocks failed".format(request_size)
            )
            self._banner.configure(fg=FAIL_FRAG_COLOR, bg="#FCE8E5")
        elif reason == "NO_SPACE":
            self._banner_var.set(
                "NO SPACE — Request of {} blocks failed".format(request_size)
            )
            self._banner.configure(fg="#704300", bg="#FFF2D5")
        else:
            self._banner_var.set(
                "Analysis for request of {} blocks".format(request_size)
            )
            self._banner.configure(fg=TEXT_PRIMARY, bg="#EAF2F1")

    def _populate_segments(self, segments, request_size):
        self._seg_tree.delete(*self._seg_tree.get_children())
        for start, size in segments:
            fits = "Yes" if size >= request_size else "No"
            tag = "fits" if fits == "Yes" else "nope"
            self._seg_tree.insert("", "end", values=(start, size, fits), tags=(tag,))
        self._seg_tree.tag_configure("fits", foreground=TEXT_PRIMARY)
        self._seg_tree.tag_configure("nope", foreground="#202020")

    # ---- Button handlers -----------------------------------------

    def _on_compact_retry(self):
        """Compact storage and retry the failed allocation once via M4."""
        pid = self._last_pid or self.ctrl.main_view._pid_var.get().strip() or "P_retry"
        self.ctrl.compaction_view.show_before()
        result = self.ctrl.backend.allocate_with_compaction(
            pid, self._last_size, self._last_strategy,
        )
        if result.ok:
            self._result_var.set(
                "SUCCESS: {} placed at block {} after compaction.".format(
                    pid, result.start
                )
            )
            self._result_label.configure(fg=TEXT_PRIMARY)
        else:
            self._result_var.set("STILL FAILED: {} — {}".format(pid, result.reason))
            self._result_label.configure(fg=DANGER_COLOR)
        self._grid.draw(self.ctrl.backend.array, self.ctrl.backend.table)
        self.ctrl.main_view.refresh()

    def _on_try_strategy(self):
        """Switch back to Dashboard so the user can pick another strategy."""
        self._result_var.set(
            "Select a different strategy on the Dashboard and try allocating again."
        )
        self._result_label.configure(fg=ACTION_COLOR)
        self.ctrl.notebook.select(0)
