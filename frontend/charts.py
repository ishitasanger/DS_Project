"""
charts.py — M5 chart generation using Matplotlib.

Reads theme colours from ui/theme.py. Every function returns a Figure used
in the Results & Charts tab and for 200 dpi PNG export on white.

Chart list (Section 7 of M5 Execution Guidelines):
  1. Grouped bars: avg external fragmentation per size
  2. Grouped bars: frag-failure rate (% of alloc requests) per size
  3. Grouped bars: avg utilisation per size
  4. Grouped bars: total simulation time (ms, log scale)
  5. Stacked bars: FRAGMENTATION + NO_SPACE failures per strategy/size
  6. Line chart: fragmentation over operations per size
  7. Heat map: avg ext frag (strategy x size)
  8. Heat map: frag-failure rate (strategy x size)
  9. Heat map: avg utilisation (strategy x size)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ui.theme import (
    STRATEGY_COLORS, STRATEGY_LINES, STRATEGY_MARKERS,
    STRATEGY_HATCHES, FRAG_HEATMAP, UTIL_HEATMAP,
    FAIL_FRAG_COLOR, FAIL_NOSPACE_CLR,
    DONUT_OCCUPIED, DONUT_FREE,
    TEXT_PRIMARY, TEXT_SECONDARY,
)

STRATEGIES = ["first", "next", "best", "worst"]
STRATEGY_LABELS = {
    "first": "First Fit",
    "next": "Next Fit",
    "best": "Best Fit",
    "worst": "Worst Fit",
}


def _style_ax(ax, title, xlabel, ylabel):
    """Apply consistent light-theme styling to an axis."""
    ax.set_title(title, fontsize=12, fontweight="bold", color=TEXT_PRIMARY, pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color=TEXT_SECONDARY)
    ax.set_ylabel(ylabel, fontsize=10, color=TEXT_SECONDARY)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.set_facecolor("#FFFFFF")


def _new_fig(figsize=(8, 5)):
    """Create a styled Matplotlib figure on white background."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FFFFFF")
    return fig, ax


def _draw_grouped_bars(results, sizes, title, ylabel, log_scale=False):
    """Shared builder for grouped strategy bars across storage sizes."""
    fig, ax = _new_fig()
    x = np.arange(len(sizes))
    width = 0.18
    for i, strat in enumerate(STRATEGIES):
        raw_vals = [results[s][strat] for s in sizes]
        plot_vals = [max(v, 0.05) if log_scale else v for v in raw_vals]
        bars = ax.bar(
            x + i * width, plot_vals, width, label=STRATEGY_LABELS[strat],
            color=STRATEGY_COLORS[strat], hatch=STRATEGY_HATCHES[strat],
            edgecolor=TEXT_PRIMARY, linewidth=0.5,
        )
        _annotate_bars(ax, bars, raw_vals, log_scale)
    if log_scale:
        ax.set_yscale("log")
        ax.set_ylim(0.1, None)
    else:
        max_v = max((results[s][st] for s in sizes for st in STRATEGIES), default=1.0)
        ax.set_ylim(0, max(5.0, max_v * 1.15))
    ax.set_xticks(x + 1.5 * width)
    ax.set_xticklabels(["N = {}".format(s) for s in sizes])
    _style_ax(ax, title, "Storage Size", ylabel)
    ax.legend(fontsize=9)
    fig.tight_layout()
    return fig


def _annotate_bars(ax, bars, raw_vals, log_scale):
    """Print crisp numeric labels above each bar."""
    for bar, v in zip(bars, raw_vals):
        y = bar.get_height() * 1.08 if log_scale else bar.get_height() + 0.4
        txt = "{:.1f}".format(v) if (log_scale and v < 10) else (
            "{:.0f}".format(v) if log_scale else "{:.1f}".format(v)
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2, y, txt,
            ha="center", va="bottom", fontsize=7,
        )


def chart_avg_frag(results, sizes):
    """1. Grouped bars: average external fragmentation per size."""
    return _draw_grouped_bars(
        results, sizes,
        "Average External Fragmentation by Strategy",
        "Avg External Fragmentation (%)",
    )


def chart_frag_fail_rate(results, sizes):
    """2. Grouped bars: fragmentation failure rate per size."""
    return _draw_grouped_bars(
        results, sizes,
        "Fragmentation Failure Rate by Strategy",
        "Frag Failures (% of alloc requests)",
    )


def chart_avg_util(results, sizes):
    """3. Grouped bars: average utilisation per size."""
    return _draw_grouped_bars(
        results, sizes,
        "Average Utilisation by Strategy",
        "Avg Utilisation (%)",
    )


def chart_sim_time(results, sizes):
    """4. Grouped bars: total simulation time on log scale."""
    return _draw_grouped_bars(
        results, sizes,
        "Total Simulation Time by Strategy (log scale)",
        "Time (ms)", log_scale=True,
    )


def chart_stacked_failures(results, sizes):
    """5. Stacked bars: FRAGMENTATION and NO_SPACE counts per size."""
    n_panels = len(sizes)
    fig, axes = plt.subplots(1, n_panels, figsize=(5 * n_panels, 5))
    fig.patch.set_facecolor("#FFFFFF")
    if n_panels == 1:
        axes = [axes]
    for idx, (ax, sz) in enumerate(zip(axes, sizes)):
        _draw_stacked_panel(ax, results[sz], sz, show_legend=(idx == 0))
    fig.tight_layout()
    return fig


def _draw_stacked_panel(ax, size_data, sz, show_legend):
    """Draw one subplot of stacked failure counts."""
    frags = [size_data[st]["frag"] for st in STRATEGIES]
    nospaces = [size_data[st]["nospace"] for st in STRATEGIES]
    x = np.arange(len(STRATEGIES))
    ax.bar(x, frags, 0.5, label="FRAGMENTATION",
           color=FAIL_FRAG_COLOR, edgecolor=TEXT_PRIMARY, linewidth=0.5)
    ax.bar(x, nospaces, 0.5, bottom=frags, label="NO_SPACE",
           color=FAIL_NOSPACE_CLR, edgecolor=TEXT_PRIMARY, linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_LABELS[st] for st in STRATEGIES], fontsize=8, rotation=20)
    _style_ax(ax, "Failures — N = {}".format(sz), "", "Count")
    if show_legend:
        ax.legend(fontsize=8)


def chart_frag_timeline(histories, sizes):
    """6. Line chart: external fragmentation over operations."""
    n_panels = len(sizes)
    fig, axes = plt.subplots(1, n_panels, figsize=(6 * n_panels, 5))
    fig.patch.set_facecolor("#FFFFFF")
    if n_panels == 1:
        axes = [axes]
    for ax, sz in zip(axes, sizes):
        _draw_timeline_panel(ax, histories[sz], sz)
    fig.tight_layout()
    return fig


def _draw_timeline_panel(ax, size_hist, sz):
    """Draw raw fragmentation trajectory for each strategy."""
    for strat in STRATEGIES:
        vals = size_hist[strat]
        ax.plot(
            list(range(len(vals))), vals,
            color=STRATEGY_COLORS[strat], linestyle=STRATEGY_LINES[strat],
            marker=STRATEGY_MARKERS[strat], markevery=max(1, len(vals) // 15),
            markersize=4, linewidth=1.2, label=STRATEGY_LABELS[strat],
        )
    _style_ax(ax, "Fragmentation Over Time — N = {}".format(sz),
              "Operation", "External Fragmentation (%)")
    ax.legend(fontsize=8)


def _heatmap_cell_color(value, bands):
    """Return (bg, fg) band colours matching dashboard thresholds."""
    for upper, bg, fg in bands:
        if value < upper:
            return bg, fg
    return bands[-1][1], bands[-1][2]


def _draw_heatmap(results, sizes, title, bands):
    """Shared heat-map renderer with printed percentages in every cell."""
    fig, ax = _new_fig(figsize=(6, 4))
    ax.set_xticks(np.arange(len(STRATEGIES)))
    ax.set_xticklabels([STRATEGY_LABELS[s] for s in STRATEGIES], fontsize=9)
    ax.set_yticks(np.arange(len(sizes)))
    ax.set_yticklabels(["N = {}".format(s) for s in sizes], fontsize=9)
    for i, sz in enumerate(sizes):
        for j, st in enumerate(STRATEGIES):
            val = results[sz][st]
            bg, fg = _heatmap_cell_color(val, bands)
            ax.add_patch(plt.Rectangle(
                (j - 0.5, i - 0.5), 1, 1, facecolor=bg, edgecolor="white", linewidth=2,
            ))
            ax.text(j, i, "{:.1f}%".format(val), ha="center", va="center",
                    fontsize=10, fontweight="bold", color=fg)
    ax.set_xlim(-0.5, len(STRATEGIES) - 0.5)
    ax.set_ylim(len(sizes) - 0.5, -0.5)
    _style_ax(ax, title, "Strategy", "Storage Size")
    fig.tight_layout()
    return fig


def chart_heatmap_frag(results, sizes):
    """7. Heat map: average external fragmentation (strategy x size)."""
    return _draw_heatmap(results, sizes, "Heat Map: Avg External Fragmentation", FRAG_HEATMAP)


def chart_heatmap_frag_fail(results, sizes):
    """8. Heat map: fragmentation failure rate (strategy x size)."""
    return _draw_heatmap(results, sizes, "Heat Map: Fragmentation Failure Rate", FRAG_HEATMAP)


def chart_heatmap_util(results, sizes):
    """9. Heat map: average utilisation (strategy x size)."""
    return _draw_heatmap(results, sizes, "Heat Map: Average Utilisation", UTIL_HEATMAP)


def chart_donut(free, occupied):
    """Small free vs occupied donut chart."""
    fig, ax = plt.subplots(figsize=(3, 3))
    fig.patch.set_facecolor("#FFFFFF")
    _, texts, autotexts = ax.pie(
        [occupied, free], labels=["Occupied", "Free"],
        colors=[DONUT_OCCUPIED, DONUT_FREE], autopct="%1.0f%%",
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.35, edgecolor="white"),
    )
    autotexts[0].set_color(TEXT_PRIMARY)
    autotexts[1].set_color(TEXT_PRIMARY)
    for t in autotexts:
        t.set_fontsize(9)
        t.set_fontweight("bold")
    for t in texts:
        t.set_fontsize(8)
    ax.set_title("Free vs Occupied", fontsize=10, fontweight="bold", color=TEXT_PRIMARY)
    fig.tight_layout()
    return fig


def save_chart(fig, path, dpi=200):
    """Save figure as PNG at 200 dpi on white background and close it."""
    fig.savefig(path, dpi=dpi, facecolor="#FFFFFF", bbox_inches="tight")
    plt.close(fig)
