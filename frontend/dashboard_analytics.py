"""
dashboard_analytics.py — M5 Dashboard Analytics Engine.

Converts raw simulator statistics into concise status labels,
trend descriptions, comparison insights and dashboard alerts.

This module has NO Tkinter imports and NEVER modifies the storage
array or linked list.  It returns plain strings, dictionaries or
simple result objects.

Thresholds are named constants documented here and described in the
project report as "project settings".
"""

# ---- Thresholds (project settings — one place) -------------------

FRAG_LOW_UPPER       = 20.0    # <20   → Low
FRAG_MODERATE_UPPER  = 40.0    # 20–<40 → Moderate;  ≥40 → High
UTIL_LOW_UPPER       = 50.0    # <50   → Underutilised
UTIL_EFFICIENT_UPPER = 85.0    # 50–<85 → Efficient;  ≥85 → Highly utilised
TREND_STABLE_DELTA   = 1.0     # change < 1 point → Stable
ALERT_RISE_THRESHOLD = 10.0    # rise ≥ 10 points → alert


# ---- Fragmentation status ----------------------------------------

def fragmentation_status(value):
    """
    Classify an external-fragmentation percentage.

    Returns "Low", "Moderate" or "High".
    Returns "Not enough data" if value is None.
    """
    if value is None:
        return "Not enough data"
    if value < FRAG_LOW_UPPER:
        return "Low"
    if value < FRAG_MODERATE_UPPER:
        return "Moderate"
    return "High"


# ---- Utilisation status ------------------------------------------

def utilisation_status(value):
    """
    Classify a utilisation percentage.

    Returns "Underutilised", "Efficient" or "Highly utilised".
    Returns "Not enough data" if value is None.
    """
    if value is None:
        return "Not enough data"
    if value < UTIL_LOW_UPPER:
        return "Underutilised"
    if value < UTIL_EFFICIENT_UPPER:
        return "Efficient"
    return "Highly utilised"


# ---- Fragmentation trend -----------------------------------------

def fragmentation_trend(prev, cur):
    """
    Compare two successive fragmentation values.

    Returns "Increasing", "Decreasing" or "Stable".
    Returns "Not enough data" if either value is None.
    """
    if prev is None or cur is None:
        return "Not enough data"
    delta = cur - prev
    if abs(delta) < TREND_STABLE_DELTA:
        return "Stable"
    if delta > 0:
        return "Increasing"
    return "Decreasing"


# ---- History alert -----------------------------------------------

def history_alert(history):
    """
    Inspect a list of successive fragmentation values.

    Returns a warning string if any consecutive rise is
    >= ALERT_RISE_THRESHOLD points, otherwise returns None.
    Returns None for empty or single-element history.
    """
    if history is None or len(history) < 2:
        return None
    for i in range(1, len(history)):
        rise = history[i] - history[i - 1]
        if rise >= ALERT_RISE_THRESHOLD:
            msg = (
                "Fragmentation rose by {:.1f} points "
                "(from {:.1f}% to {:.1f}%) at step {}."
            )
            return msg.format(rise, history[i - 1], history[i], i + 1)
    return None


# ---- Best strategy -----------------------------------------------

def best_strategy(results):
    """
    Given a dict  {strategy_name: avg_ext_frag, ...}  pick the one
    with the lowest average external fragmentation.

    Returns a dict:
      {"best": name_or_list, "value": float, "tied": bool}
    Returns {"best": "Not enough data", ...} when input is empty/None.
    """
    if not results:
        return {"best": "Not enough data", "value": None, "tied": False}

    min_val = min(results.values())
    winners = [k for k, v in results.items() if v == min_val]
    tied = len(winners) > 1
    best_name = ", ".join(sorted(winners))
    return {"best": best_name, "value": min_val, "tied": tied}


# ---- Insight sentence --------------------------------------------

def _format_insight_text(frag_value, status, trend, alert, suggestion):
    """Assemble multi-line plain-English insight text from parts."""
    if frag_value is not None:
        header = "External Fragmentation: {:.1f}% | Status: {}".format(
            frag_value, status.upper()
        )
    else:
        header = "External Fragmentation: — | Status: —"
    parts = [header, "Trend: {}".format(trend)]
    if alert:
        parts.append("Alert: {}".format(alert))
    if suggestion:
        parts.append(suggestion)
    return "\n".join(parts)


def build_insight(frag_value, prev_frag, history, last_failure_reason=None):
    """Build a multi-line insight dict for the dashboard tile."""
    status = fragmentation_status(frag_value)
    trend = fragmentation_trend(prev_frag, frag_value)
    alert = history_alert(history)
    suggestion = None
    if last_failure_reason == "FRAGMENTATION":
        suggestion = (
            "Consider compaction: no single free segment is "
            "large enough for the last request."
        )
    text = _format_insight_text(frag_value, status, trend, alert, suggestion)
    return {
        "status": status, "trend": trend,
        "alert": alert, "suggestion": suggestion, "text": text,
    }


# ---- Delta description for metric cards --------------------------

def metric_delta(prev, cur, higher_is_good=False):
    """
    Return ("▲ X.X", good) or ("▼ X.X", good) or ("—", None).

    'good' is True when the direction is favourable.
    For fragmentation higher_is_good=False (lower is better).
    For utilisation higher_is_good=True (higher is better).
    """
    if prev is None or cur is None:
        return ("—", None)
    delta = cur - prev
    if abs(delta) < 0.05:
        return ("—", None)
    arrow = "▲" if delta > 0 else "▼"
    label = "{} {:.1f}".format(arrow, abs(delta))
    if higher_is_good:
        good = delta > 0
    else:
        good = delta < 0
    return (label, good)
