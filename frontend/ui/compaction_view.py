"""
ui/compaction_view.py — Compaction (Defragmentation) tab.

Displays before and after block grids along with free segment count,
largest hole size, external fragmentation %, and moved block count.
All data comes from the backend through the application controller.
"""

import copy
import tkinter as tk
from tkinter import ttk
from ui.theme import (
    CANVAS_BG, TILE_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, DANGER_COLOR, INSIGHT_BG,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
)
from ui.widgets import RoundedTile, BlockGrid


class CompactionView(ttk.Frame):
    """Compaction before/after comparison tab."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ctrl = controller
        self._before_var = tk.StringVar(value="BEFORE — Data pending")
        self._after_var = tk.StringVar(value="AFTER — Data pending")
        self._summary_var = tk.StringVar(
            value="Click 'Run Compaction' to merge scattered free holes."
        )
        self._build_ui()

    def _build_ui(self):
        """Assemble the before and after compaction panels."""
        container = tk.Frame(self, bg=CANVAS_BG)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_header(container)
        self._before_grid = self._build_stage_tile(
            container, self._before_var, pady=(0, 12)
        )
        self._after_grid = self._build_stage_tile(
            container, self._after_var, pady=(0, 0)
        )

    def _build_header(self, parent):
        """Build the tab title, summary line, and Run Compaction button."""
        hdr = tk.Frame(parent, bg=CANVAS_BG)
        hdr.pack(fill="x", pady=(0, 10))

        left = tk.Frame(hdr, bg=CANVAS_BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text="Compaction (Defragmentation) — Before / After",
            font=(FONT_FAMILY, 14, "bold"),
            bg=CANVAS_BG,
            fg=TEXT_PRIMARY,
        ).pack(anchor="w")

        tk.Label(
            left,
            textvariable=self._summary_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL),
            bg=CANVAS_BG,
            fg=ACTION_COLOR,
        ).pack(anchor="w", pady=(2, 0))

        ttk.Button(
            hdr,
            text="Run Compaction",
            command=self._on_run_compaction,
        ).pack(side="right", anchor="n")

    def _build_stage_tile(self, parent, label_var, pady):
        """Create one rounded tile containing a header and a BlockGrid."""
        tile = RoundedTile(parent, width=980, height=260, bg_color=TILE_BG)
        tile.pack(fill="both", expand=True, pady=pady)
        tile.inner.configure(bg=TILE_BG)

        tk.Label(
            tile.inner,
            textvariable=label_var,
            font=(FONT_FAMILY, 10, "bold"),
            bg=TILE_BG,
            fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(2, 4))

        grid = BlockGrid(tile.inner, height=150)
        grid.pack(fill="both", expand=True)
        return grid

    # ---- Public update methods -----------------------------------

    def show_before(self):
        """Capture and draw the current storage state before compaction."""
        backend = self.ctrl.backend
        before_array = copy.deepcopy(backend.array)
        st = backend.stats()
        self._before_grid.reset_colors()
        self._before_grid.draw(before_array)
        self._before_var.set(
            "BEFORE — {} free segments | Largest hole: {} | "
            "External fragmentation: {:.1f}%".format(
                st.segments, st.largest, st.ext_frag
            )
        )

    def show_after(self, report):
        """Draw the compacted storage state and summary metrics."""
        backend = self.ctrl.backend
        after_array = copy.deepcopy(backend.array)
        # Keep the exact process colours used in the 'before' grid.
        self._after_grid._color_map = dict(self._before_grid._color_map)
        self._after_grid._next_color = self._before_grid._next_color
        self._after_grid.draw(after_array)

        self._after_var.set(
            "AFTER — {} free segments | Largest hole: {} | "
            "External fragmentation: {:.1f}% | Moved: {} blocks".format(
                report.segments_after,
                report.after.largest,
                report.after.ext_frag,
                report.moved_blocks,
            )
        )
        self._summary_var.set(
            "Moved {} blocks | Segments reduced {} -> {} | "
            "Fragmentation {:.1f}% -> {:.1f}%".format(
                report.moved_blocks,
                report.segments_before,
                report.segments_after,
                report.before.ext_frag,
                report.after.ext_frag,
            )
        )

    # ---- Button handler ------------------------------------------

    def _on_run_compaction(self):
        """Trigger compaction through the application controller."""
        self.ctrl.compact()
