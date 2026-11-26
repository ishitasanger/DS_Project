"""
ui/compare_view.py — Compare Strategies tab.

Displays a 2x2 grid of tiles for First Fit, Next Fit, Best Fit, and Worst Fit,
each showing a mini block grid, success/failure counts, segments, largest
hole, average fragmentation, utilisation, and proportional free-segment size
bars. Also highlights the best observed strategy.
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import (
    CANVAS_BG, TILE_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, FREE_OUTLINE, FONT_FAMILY,
    FONT_SIZE_NORMAL, FONT_SIZE_SMALL, STRATEGY_COLORS,
)
from ui.widgets import RoundedTile, BlockGrid
import dashboard_analytics as analytics


class CompareView(ttk.Frame):
    """Strategy Comparison tab showing 2x2 strategy result tiles."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.ctrl = controller
        self._tiles = {}
        self._build_ui()

    def _build_ui(self):
        """Assemble the header and 2x2 comparison grid."""
        container = tk.Frame(self, bg=CANVAS_BG)
        container.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(
            container, text="Strategy Comparison",
            font=(FONT_FAMILY, 14, "bold"),
            bg=CANVAS_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))

        self._best_var = tk.StringVar(value="Run a comparison first.")
        tk.Label(
            container, textvariable=self._best_var,
            font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
            bg=CANVAS_BG, fg=ACTION_COLOR,
        ).pack(anchor="w", pady=(0, 12))

        grid_frame = tk.Frame(container, bg=CANVAS_BG)
        grid_frame.pack(fill="both", expand=True)
        self._build_strategy_tiles(grid_frame)

    def _build_strategy_tiles(self, grid_frame):
        """Create the four strategy tiles in a 2x2 layout."""
        labels = {
            "first": "First Fit",
            "next": "Next Fit",
            "best": "Best Fit",
            "worst": "Worst Fit",
        }
        for i, strat in enumerate(["first", "next", "best", "worst"]):
            row, col = i // 2, i % 2
            grid_frame.grid_columnconfigure(col, weight=1)
            grid_frame.grid_rowconfigure(row, weight=1)
            self._tiles[strat] = self._build_one_tile(
                grid_frame, row, col, strat, labels[strat]
            )

    def _build_one_tile(self, parent, row, col, strat, title):
        """Build a single rounded tile for one allocation strategy."""
        frame = tk.Frame(parent, bg=CANVAS_BG)
        frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        tk.Frame(frame, bg=STRATEGY_COLORS[strat], height=4).pack(fill="x")

        tile = RoundedTile(frame, width=480, height=330, bg_color=TILE_BG)
        tile.pack(fill="both", expand=True)
        inner = tile.inner
        inner.configure(bg=TILE_BG)

        tk.Label(
            inner, text=title, font=(FONT_FAMILY, 11, "bold"),
            bg=TILE_BG, fg=STRATEGY_COLORS[strat],
        ).pack(anchor="w", pady=(0, 2))

        mini_grid = BlockGrid(inner, height=112, compact=True)
        mini_grid.pack(fill="x")

        stats_var = tk.StringVar(value="Data pending")
        tk.Label(
            inner, textvariable=stats_var, font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=TILE_BG, fg=TEXT_SECONDARY, justify="left", wraplength=390,
        ).pack(anchor="w", pady=(2, 2))

        seg_canvas = tk.Canvas(
            inner, height=44, bg=TILE_BG, highlightthickness=0,
        )
        seg_canvas.pack(fill="x")
        return {"grid": mini_grid, "stats_var": stats_var, "seg_canvas": seg_canvas}

    # ---- Public update -------------------------------------------

    def show_comparison(self, results):
        """Populate all four tiles from C++ experiment comparison data."""
        frag_map = {}
        for strat, data in results.items():
            tile = self._tiles.get(strat)
            if not tile:
                continue
            self._populate_tile(tile, data)
            frag_map[strat] = data["ext_frag"]
        self._update_best_banner(frag_map)

    def _populate_tile(self, tile, data):
        """Draw grid, summary metrics, and free-segment bars for one tile."""
        tile["grid"].reset_colors()
        tile["grid"].draw(data["array"])
        info = (
            "OK: {}  |  Frag fails: {}  |  NoSpace: {}\n"
            "Segments: {}  |  Largest: {}  |  "
            "Frag: {:.1f}%  |  Util: {:.1f}%"
        ).format(
            data["ok"], data["frag_fail"], data["nospace_fail"],
            data["segments"], data["largest"],
            data["ext_frag"], data["avg_util"],
        )
        tile["stats_var"].set(info)
        self._draw_segment_bars(tile["seg_canvas"], data.get("free_segments", []))

    def _draw_segment_bars(self, canvas, free_segs):
        """Draw proportional amber bars representing free segment sizes."""
        canvas.delete("all")
        canvas.create_text(
            2, 16, text="Free segments:", anchor="w",
            fill=TEXT_SECONDARY, font=(FONT_FAMILY, 8),
        )
        if not free_segs:
            canvas.create_text(
                96, 16, text="None (full)", anchor="w",
                fill=TEXT_SECONDARY, font=(FONT_FAMILY, 8),
            )
            return
        max_sz = max(sz for _, sz in free_segs) or 1
        x = 98
        for _, sz in free_segs[:12]:
            bar_h = max(6, int(20 * sz / max_sz))
            canvas.create_rectangle(
                x, 26 - bar_h, x + 14, 26,
                fill=FREE_OUTLINE, outline=TEXT_PRIMARY, width=1,
            )
            canvas.create_text(
                x + 7, 36, text=str(sz),
                fill=TEXT_SECONDARY, font=(FONT_FAMILY, 7),
            )
            x += 22

    def _update_best_banner(self, frag_map):
        best = analytics.best_strategy(frag_map)
        if best["tied"]:
            self._best_var.set(
                "Tied for lowest fragmentation: {} ({:.1f}%)".format(
                    best["best"], best["value"]
                )
            )
        elif best["value"] is not None:
            self._best_var.set(
                "Best observed strategy: {} ({:.1f}% avg frag)".format(
                    best["best"], best["value"]
                )
            )
