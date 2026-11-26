"""
ui/widgets.py — reusable Tkinter widgets for the M5 dashboard.

RoundedTile    — Canvas that draws a rounded rectangle with soft shadow
                 and optional click/focus activation.
MetricCard     — tile showing a large value, label, subtitle, and delta.
HeroCard       — gradient-filled clickable card for the main KPI.
BlockGrid      — Canvas that draws the storage block layout with tooltips
                 and arrow-key cell navigation.
StatusDot      — small coloured circle for status indication.
"""

import tkinter as tk
from ui.theme import (
    TILE_BG, TILE_RADIUS, TILE_BORDER, TILE_BORDER_CLR,
    SHADOW_COLOR, CANVAS_BG, TEXT_PRIMARY, TEXT_SECONDARY,
    ACTION_COLOR, DANGER_COLOR, HERO_DARK, HERO_LIGHT, HERO_TEXT,
    PROCESS_COLORS, FREE_FILL, FREE_OUTLINE,
    FONT_FAMILY, FONT_SIZE_HERO, FONT_SIZE_LARGE,
    FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    FOCUS_HIGHLIGHT_WIDTH, FOCUS_HIGHLIGHT_COLOR,
    STATUS_LOW, STATUS_MODERATE, STATUS_HIGH,
)


def _round_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a rounded rectangle on 'canvas'. Returns the item id."""
    r = radius
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedTile(tk.Canvas):
    """Canvas that draws a rounded tile with shadow and inner frame."""

    def __init__(self, parent, width=200, height=120,
                 bg_color=TILE_BG, shadow=True, command=None, **kwargs):
        super().__init__(
            parent, width=width, height=height,
            bg=CANVAS_BG, highlightthickness=0, **kwargs,
        )
        self._bg_color = bg_color
        self._width = width
        self._height = height
        self._shadow = shadow
        self._command = command
        self._border_color = TILE_BORDER_CLR
        self._border_width = TILE_BORDER
        self._draw()
        self.inner = tk.Frame(self, bg=bg_color)
        self._inner_window = self.create_window(
            TILE_RADIUS, TILE_RADIUS,
            window=self.inner, anchor="nw",
            width=width - 2 * TILE_RADIUS,
            height=height - 2 * TILE_RADIUS,
        )
        self.bind("<Configure>", self._on_tile_resize)
        if command is not None:
            self._enable_interactive()

    def _on_tile_resize(self, event):
        """Resize the tile artwork and its child frame with the parent layout."""
        width = max(80, event.width)
        height = max(60, event.height)
        if width == self._width and height == self._height:
            return
        self._width, self._height = width, height
        self._draw()
        self.coords(self._inner_window, TILE_RADIUS, TILE_RADIUS)
        self.itemconfigure(
            self._inner_window,
            width=max(1, width - 2 * TILE_RADIUS),
            height=max(1, height - 2 * TILE_RADIUS),
        )

    def _draw(self):
        """Draw drop shadow and rounded tile border."""
        self.delete("tile_bg")
        w, h, r = self._width, self._height, TILE_RADIUS
        if self._shadow:
            _round_rect(
                self, 4, 4, w, h, r,
                fill=SHADOW_COLOR, outline="", tags="tile_bg",
            )
        self._outline_id = _round_rect(
            self, 2, 2, w - 2, h - 2, r,
            fill=self._bg_color, outline=self._border_color,
            width=self._border_width, tags="tile_bg",
        )

    def _enable_interactive(self):
        """Make the tile clickable and keyboard-focusable."""
        self.configure(takefocus=1, cursor="hand2")
        self.bind("<Enter>", self._on_hover_in)
        self.bind("<Leave>", self._on_hover_out)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_activate)
        self.bind("<Return>", self._on_activate)

    def _on_hover_in(self, _event):
        self.itemconfigure(self._outline_id, outline=ACTION_COLOR, width=2)

    def _on_hover_out(self, _event):
        self.itemconfigure(
            self._outline_id, outline=self._border_color,
            width=self._border_width,
        )

    def _on_focus_in(self, _event):
        self._border_color = FOCUS_HIGHLIGHT_COLOR
        self._border_width = FOCUS_HIGHLIGHT_WIDTH
        self._on_hover_in(None)

    def _on_focus_out(self, _event):
        self._border_color = TILE_BORDER_CLR
        self._border_width = TILE_BORDER
        self._on_hover_out(None)

    def _on_activate(self, _event):
        if self._command is not None:
            self._command()


class MetricCard(RoundedTile):
    """Tile showing a primary numeric value, label, subtitle, and delta."""

    def __init__(self, parent, label="Metric", value="—",
                 delta="—", delta_good=None, width=200,
                 height=120, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self._val_var = tk.StringVar(value=value)
        self._delta_var = tk.StringVar(value=delta)
        self._sub_var = tk.StringVar(value="")
        self._build_labels(label)
        self._set_delta_color(delta_good)

    def _build_labels(self, label):
        """Create labels inside the metric card."""
        tk.Label(
            self.inner, textvariable=self._val_var,
            font=(FONT_FAMILY, FONT_SIZE_LARGE, "bold"),
            bg=TILE_BG, fg=TEXT_PRIMARY,
        ).pack(anchor="w")
        tk.Label(
            self.inner, text=label,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        ).pack(anchor="w")
        self._delta_lbl = tk.Label(
            self.inner, textvariable=self._delta_var,
            font=(FONT_FAMILY, FONT_SIZE_SMALL),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        )
        self._delta_lbl.pack(anchor="w")
        self._sub_lbl = tk.Label(
            self.inner, textvariable=self._sub_var,
            font=(FONT_FAMILY, 8),
            bg=TILE_BG, fg=TEXT_SECONDARY,
        )
        self._sub_lbl.pack(anchor="w")

    def update_value(self, value, delta="—", delta_good=None, subtitle=""):
        """Refresh displayed metric value, delta, and optional subtitle."""
        self._val_var.set(value)
        if subtitle and delta == "—":
            self._delta_var.set(subtitle)
            self._sub_var.set("")
        else:
            self._delta_var.set(delta)
            self._sub_var.set(subtitle)
        self._set_delta_color(delta_good)

    def _set_delta_color(self, good):
        if good is True:
            self._delta_lbl.configure(fg=TEXT_PRIMARY)
        elif good is False:
            self._delta_lbl.configure(fg=DANGER_COLOR)
        else:
            self._delta_lbl.configure(fg=TEXT_SECONDARY)


class HeroCard(tk.Canvas):
    """Gradient-filled clickable hero card for external fragmentation."""

    def __init__(self, parent, label="External Fragmentation",
                 value="—", status="", width=280, height=120,
                 command=None, **kwargs):
        super().__init__(
            parent, width=width, height=height,
            bg=CANVAS_BG, highlightthickness=0, **kwargs,
        )
        self._width = width
        self._height = height
        self._command = command
        self._val_var = tk.StringVar(value=value)
        self._status_var = tk.StringVar(value=status)
        self._draw_gradient()
        self._draw_text(label)
        if command is not None:
            self._enable_interactive()

    def _draw_gradient(self):
        """Draw horizontal dark-to-teal gradient clipped inside tile."""
        self.delete("grad")
        w, h, r = self._width, self._height, TILE_RADIUS
        _round_rect(self, 4, 4, w, h, r, fill=SHADOW_COLOR, outline="", tags="grad")
        _round_rect(self, 2, 2, w - 2, h - 2, r, fill=HERO_DARK, outline="", tags="grad")
        self._draw_gradient_bands(w, h)
        self._outline_id = _round_rect(
            self, 2, 2, w - 2, h - 2, r,
            fill="", outline=HERO_DARK, width=2, tags="grad",
        )

    def _draw_gradient_bands(self, w, h):
        """Paint smooth colour bands across the right side of the card."""
        dark = tuple(int(HERO_DARK[i:i + 2], 16) for i in (1, 3, 5))
        light = tuple(int(HERO_LIGHT[i:i + 2], 16) for i in (1, 3, 5))
        steps = 48
        bar_w = (w - 4) / steps
        for i in range(steps):
            frac = i / max(1, steps - 1)
            cr = int(dark[0] + (light[0] - dark[0]) * frac)
            cg = int(dark[1] + (light[1] - dark[1]) * frac)
            cb = int(dark[2] + (light[2] - dark[2]) * frac)
            colour = "#{:02x}{:02x}{:02x}".format(cr, cg, cb)
            x = 2 + i * bar_w
            self.create_rectangle(
                x, TILE_RADIUS + 2, x + bar_w + 1, h - TILE_RADIUS - 2,
                fill=colour, outline="", tags="grad",
            )

    def _draw_text(self, label):
        """Place value, caption, and status text on the hero card."""
        cx = TILE_RADIUS + 10
        self._val_id = self.create_text(
            cx, 35, text=self._val_var.get(), anchor="w",
            fill=HERO_TEXT, font=(FONT_FAMILY, FONT_SIZE_HERO, "bold"),
        )
        self.create_text(
            cx, 70, text=label, anchor="w",
            fill=HERO_TEXT, font=(FONT_FAMILY, FONT_SIZE_SMALL),
        )
        self._status_id = self.create_text(
            cx, 92, text=self._status_var.get(), anchor="w",
            fill=HERO_TEXT, font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
        )

    def _enable_interactive(self):
        """Allow keyboard and pointer click on the hero card."""
        self.configure(takefocus=1, cursor="hand2")
        self.bind("<Enter>", self._on_hover_in)
        self.bind("<Leave>", self._on_hover_out)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self.bind("<Button-1>", self._on_activate)
        self.bind("<Return>", self._on_activate)

    def _on_hover_in(self, _event):
        self.itemconfigure(self._outline_id, outline=ACTION_COLOR, width=3)

    def _on_hover_out(self, _event):
        self.itemconfigure(self._outline_id, outline=HERO_DARK, width=2)

    def _on_focus_in(self, _event):
        self.itemconfigure(
            self._outline_id, outline=FOCUS_HIGHLIGHT_COLOR,
            width=FOCUS_HIGHLIGHT_WIDTH,
        )

    def _on_focus_out(self, _event):
        self._on_hover_out(None)

    def _on_activate(self, _event):
        if self._command is not None:
            self._command()

    def update_hero(self, value, status):
        """Refresh hero value and classification status."""
        self._val_var.set(value)
        self._status_var.set(status)
        self.itemconfigure(self._val_id, text=value)
        self.itemconfigure(self._status_id, text=status)


class BlockGrid(tk.Canvas):
    """
    Draws the storage layout as a 20-column grid of coloured cells.
    Supports hover tooltips, status-line updates, and arrow-key stepping.
    """

    CELL_SIZE_DEFAULT = 26
    CELL_SIZE_MEDIUM = 18
    CELL_SIZE_MINI = 15
    CELL_SIZE_SMALL = 11
    COLS = 20

    def __init__(self, parent, status_callback=None, compact=False, **kwargs):
        super().__init__(
            parent, bg=TILE_BG, highlightthickness=FOCUS_HIGHLIGHT_WIDTH,
            highlightbackground=TILE_BG, highlightcolor=FOCUS_HIGHLIGHT_COLOR,
            takefocus=1, **kwargs,
        )
        self._color_map = {}
        self._next_color = 0
        self._last_array = []
        self._last_table = {}
        self._status_cb = status_callback
        self._compact = compact
        self._tooltip_win = None
        self._cursor_idx = 0
        self._cell_bounds = {}
        self._bind_events()

    def _bind_events(self):
        """Bind resize, pointer hover, and arrow-key events."""
        self.bind("<Configure>", self._on_resize)
        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Left>", self._on_key_left)
        self.bind("<Right>", self._on_key_right)
        self.bind("<Up>", self._on_key_up)
        self.bind("<Down>", self._on_key_down)

    def draw(self, array, table=None):
        """Redraw the block grid from 'array' and optional 'table'."""
        self._last_array = list(array)
        if table is not None:
            self._last_table = dict(table)
        self.delete("all")
        self._cell_bounds.clear()
        n = len(self._last_array)
        if n == 0:
            return
        cell_w, cell_h, left, top = self._cell_dimensions(n)
        for idx in range(n):
            self._draw_cell(idx, self._last_array[idx], cell_w, cell_h, left, top)
        total_rows = (n + self.COLS - 1) // self.COLS
        total_h = top + total_rows * (cell_h + 3) + 12
        total_w = left + self.COLS * (cell_w + 3) + 12
        self.configure(scrollregion=(0, 0, max(total_w, self.winfo_width()),
                                      max(total_h, self.winfo_height())))

    def _cell_dimensions(self, n):
        """Scale the block map to use the available white panel area."""
        if self._compact and n <= 200:
            return self.CELL_SIZE_MINI, self.CELL_SIZE_MINI, 34, 12
        rows = max(1, (n + self.COLS - 1) // self.COLS)
        available_w = max(360, self.winfo_width() - 78)
        available_h = max(180, self.winfo_height() - 28)
        cell_w = max(20, min(48, int(available_w / self.COLS) - 3))
        cell_h = max(32, min(62, int(available_h / rows) - 3))
        top = max(12, int((self.winfo_height() - rows * (cell_h + 3)) / 2))
        return cell_w, cell_h, 42, top

    def _draw_cell(self, idx, pid, cell_w, cell_h, left, top):
        """Draw one memory block, its process label, and row position."""
        row, col = idx // self.COLS, idx % self.COLS
        x1 = left + col * (cell_w + 3)
        y1 = top + row * (cell_h + 3)
        x2, y2 = x1 + cell_w, y1 + cell_h
        cell = min(cell_w, cell_h)
        self._cell_bounds[idx] = (x1, y1, x2, y2)
        if pid == "":
            dash_pat = (6, 4) if cell >= self.CELL_SIZE_MEDIUM else (3, 2)
            self.create_rectangle(
                x1, y1, x2, y2, fill=FREE_FILL, outline=FREE_OUTLINE,
                width=2, dash=dash_pat, tags=("block", "free", "b_{}".format(idx)),
            )
        else:
            bg, fg = self._get_color(pid)
            self.create_rectangle(
                x1, y1, x2, y2, fill=bg, outline=TEXT_PRIMARY, width=1,
                tags=("block", "pid_{}".format(pid), "b_{}".format(idx)),
            )
            if cell >= self.CELL_SIZE_MEDIUM:
                self.create_text(
                    (x1 + x2) // 2, (y1 + y2) // 2, text=pid, fill=fg,
                    font=(FONT_FAMILY, max(7, cell // 4)), tags=("label",),
                )
        if col == 0:
            self.create_text(
                30, (y1 + y2) // 2, text=str(idx), anchor="e",
                fill=TEXT_SECONDARY, font=(FONT_FAMILY, FONT_SIZE_SMALL),
            )

    def highlight_process(self, pid):
        """Outline all blocks belonging to 'pid'."""
        self.delete("highlight")
        for item in self.find_withtag("pid_{}".format(pid)):
            coords = self.coords(item)
            if len(coords) == 4:
                self.create_rectangle(
                    coords[0] - 2, coords[1] - 2,
                    coords[2] + 2, coords[3] + 2,
                    outline=ACTION_COLOR, width=3, tags="highlight",
                )

    def get_process_color(self, pid):
        """Expose (bg, fg) swatch colour for table alignment."""
        return self._get_color(pid)

    def _get_color(self, pid):
        if pid not in self._color_map:
            idx = self._next_color % len(PROCESS_COLORS)
            self._color_map[pid] = idx
            self._next_color += 1
        return PROCESS_COLORS[self._color_map[pid]]

    def _cell_size(self, n):
        if self._compact and n <= 200:
            return self.CELL_SIZE_MINI
        if n <= 200:
            return self.CELL_SIZE_DEFAULT
        if n <= 1000:
            return self.CELL_SIZE_MEDIUM
        return self.CELL_SIZE_SMALL

    def _cell_description(self, idx):
        """Format readable inspection string for block 'idx'."""
        if idx < 0 or idx >= len(self._last_array):
            return ""
        pid = self._last_array[idx]
        if pid == "":
            return "Block {}: Free".format(idx)
        info = self._last_table.get(pid)
        if info:
            return "Block {}: {} (start {}, size {})".format(
                idx, pid, info[0], info[1]
            )
        return "Block {}: {}".format(idx, pid)

    def _on_motion(self, event):
        """Show block details in status line and tooltip on hover."""
        cx = self.canvasx(event.x)
        cy = self.canvasy(event.y)
        items = self.find_overlapping(cx, cy, cx, cy)
        idx = self._extract_block_index(items)
        if idx is None:
            self._hide_tooltip()
            return
        desc = self._cell_description(idx)
        self._report_status(desc)
        self._show_tooltip(event.x_root + 12, event.y_root + 12, desc)

    def _extract_block_index(self, items):
        for item in items:
            for tag in self.gettags(item):
                if tag.startswith("b_"):
                    return int(tag[2:])
        return None

    def _on_leave(self, _event):
        self._hide_tooltip()

    def _show_tooltip(self, x_root, y_root, text):
        if self._tooltip_win is None:
            self._tooltip_win = tk.Toplevel(self)
            self._tooltip_win.wm_overrideredirect(True)
            lbl = tk.Label(
                self._tooltip_win, text=text, bg="#E9D8A6", fg=TEXT_PRIMARY,
                font=(FONT_FAMILY, 9), padx=6, pady=2, relief="solid", bd=1,
            )
            lbl.pack()
            self._tooltip_lbl = lbl
        else:
            self._tooltip_lbl.configure(text=text)
        self._tooltip_win.wm_geometry("+{}+{}".format(x_root, y_root))

    def _hide_tooltip(self):
        if self._tooltip_win is not None:
            self._tooltip_win.destroy()
            self._tooltip_win = None

    def _move_cursor(self, delta):
        n = len(self._last_array)
        if n == 0:
            return
        self._cursor_idx = max(0, min(n - 1, self._cursor_idx + delta))
        self.delete("cell_cursor")
        bounds = self._cell_bounds.get(self._cursor_idx)
        if bounds:
            self.create_rectangle(
                bounds[0] - 1, bounds[1] - 1, bounds[2] + 1, bounds[3] + 1,
                outline=FOCUS_HIGHLIGHT_COLOR, width=2, tags="cell_cursor",
            )
        self._report_status(self._cell_description(self._cursor_idx))

    def _report_status(self, text):
        if self._status_cb is not None and text:
            self._status_cb(text)

    def _on_key_left(self, _event):
        self._move_cursor(-1)

    def _on_key_right(self, _event):
        self._move_cursor(1)

    def _on_key_up(self, _event):
        self._move_cursor(-self.COLS)

    def _on_key_down(self, _event):
        self._move_cursor(self.COLS)

    def _on_resize(self, _event):
        if self._last_array:
            self.draw(self._last_array)

    def reset_colors(self):
        """Clear assigned process colours on storage reset."""
        self._color_map.clear()
        self._next_color = 0


class StatusDot(tk.Canvas):
    """Small coloured circle for low/moderate/high status indication."""

    def __init__(self, parent, status="low", size=12, **kwargs):
        super().__init__(
            parent, width=size, height=size,
            bg=TILE_BG, highlightthickness=0, **kwargs,
        )
        self._size = size
        self.set_status(status)

    def set_status(self, status):
        """Set dot colour to 'low', 'moderate', or 'high'."""
        self.delete("dot")
        colors = {
            "low": STATUS_LOW["dot"],
            "moderate": STATUS_MODERATE["dot"],
            "high": STATUS_HIGH["dot"],
        }
        color = colors.get(status.lower(), STATUS_LOW["dot"])
        pad = 2
        self.create_oval(
            pad, pad, self._size - pad, self._size - pad,
            fill=color, outline="", tags="dot",
        )
