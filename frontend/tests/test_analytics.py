"""
tests/test_analytics.py — tests for dashboard_analytics.py.

Covers every boundary, all trend cases, empty history,
strategy comparison, ties, and missing input.

Run with:
    cd d:\\Projects\\DS_Project\\frontend
    python -m tests.test_analytics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dashboard_analytics as da


def check(name, condition):
    """Print one PASS/FAIL line per test case."""
    result = "PASS" if condition else "FAIL"
    print("{}: {}".format(name, result))
    return condition


def run_all():
    """Run all analytics tests. Returns True if all pass."""
    all_ok = True

    # ---- fragmentation_status boundaries ----
    all_ok &= check("frag_status None",
                     da.fragmentation_status(None) == "Not enough data")
    all_ok &= check("frag_status 0.0", da.fragmentation_status(0.0) == "Low")
    all_ok &= check("frag_status 19.9",
                     da.fragmentation_status(19.9) == "Low")
    all_ok &= check("frag_status 20.0",
                     da.fragmentation_status(20.0) == "Moderate")
    all_ok &= check("frag_status 39.9",
                     da.fragmentation_status(39.9) == "Moderate")
    all_ok &= check("frag_status 40.0",
                     da.fragmentation_status(40.0) == "High")
    all_ok &= check("frag_status 100.0",
                     da.fragmentation_status(100.0) == "High")

    # ---- utilisation_status boundaries ----
    all_ok &= check("util_status None",
                     da.utilisation_status(None) == "Not enough data")
    all_ok &= check("util_status 0.0",
                     da.utilisation_status(0.0) == "Underutilised")
    all_ok &= check("util_status 49.9",
                     da.utilisation_status(49.9) == "Underutilised")
    all_ok &= check("util_status 50.0",
                     da.utilisation_status(50.0) == "Efficient")
    all_ok &= check("util_status 84.9",
                     da.utilisation_status(84.9) == "Efficient")
    all_ok &= check("util_status 85.0",
                     da.utilisation_status(85.0) == "Highly utilised")

    # ---- fragmentation_trend ----
    all_ok &= check("trend None_None",
                     da.fragmentation_trend(None, None) == "Not enough data")
    all_ok &= check("trend None_50",
                     da.fragmentation_trend(None, 50) == "Not enough data")
    all_ok &= check("trend stable",
                     da.fragmentation_trend(30.0, 30.5) == "Stable")
    all_ok &= check("trend increasing",
                     da.fragmentation_trend(30.0, 35.0) == "Increasing")
    all_ok &= check("trend decreasing",
                     da.fragmentation_trend(40.0, 32.0) == "Decreasing")
    all_ok &= check("trend boundary (0.9 delta)",
                     da.fragmentation_trend(10.0, 10.9) == "Stable")
    all_ok &= check("trend boundary (1.0 delta)",
                     da.fragmentation_trend(10.0, 11.0) == "Increasing")

    # ---- history_alert ----
    all_ok &= check("alert None", da.history_alert(None) is None)
    all_ok &= check("alert empty", da.history_alert([]) is None)
    all_ok &= check("alert single", da.history_alert([50.0]) is None)
    all_ok &= check("alert no rise",
                     da.history_alert([10.0, 15.0, 18.0]) is None)
    alert_msg = da.history_alert([10.0, 25.0])
    all_ok &= check("alert 15pt rise", alert_msg is not None and "15.0" in alert_msg)
    all_ok &= check("alert exactly 10pt",
                     da.history_alert([20.0, 30.0]) is not None)
    all_ok &= check("alert 9.9pt no trigger",
                     da.history_alert([20.0, 29.9]) is None)

    # ---- best_strategy ----
    all_ok &= check("best_strat empty",
                     da.best_strategy({})["best"] == "Not enough data")
    all_ok &= check("best_strat None",
                     da.best_strategy(None)["best"] == "Not enough data")
    best = da.best_strategy({"first": 35.0, "best": 29.5, "worst": 48.4})
    all_ok &= check("best_strat winner",
                     best["best"] == "best" and best["value"] == 29.5)
    all_ok &= check("best_strat not tied", not best["tied"])

    tied = da.best_strategy({"first": 30.0, "best": 30.0, "worst": 50.0})
    all_ok &= check("best_strat tied", tied["tied"])
    all_ok &= check("best_strat tied names",
                     "best" in tied["best"] and "first" in tied["best"])

    # ---- build_insight ----
    insight = da.build_insight(55.0, 40.0, [40.0, 55.0], "FRAGMENTATION")
    all_ok &= check("insight status",   insight["status"] == "High")
    all_ok &= check("insight trend",    insight["trend"] == "Increasing")
    all_ok &= check("insight alert",    insight["alert"] is not None)
    all_ok &= check("insight suggestion",
                     insight["suggestion"] is not None and "compaction" in insight["suggestion"].lower())
    all_ok &= check("insight text",     "55.0%" in insight["text"])

    empty_insight = da.build_insight(None, None, [], None)
    all_ok &= check("insight empty", "—" in empty_insight["text"])

    # ---- metric_delta ----
    label, good = da.metric_delta(None, 50.0)
    all_ok &= check("delta no prev", label == "—" and good is None)
    label, good = da.metric_delta(50.0, 50.0)
    all_ok &= check("delta no change", label == "—")
    label, good = da.metric_delta(50.0, 55.0, higher_is_good=False)
    all_ok &= check("delta up bad", "▲" in label and good is False)
    label, good = da.metric_delta(50.0, 45.0, higher_is_good=False)
    all_ok &= check("delta down good", "▼" in label and good is True)
    label, good = da.metric_delta(50.0, 55.0, higher_is_good=True)
    all_ok &= check("delta up good", "▲" in label and good is True)

    return all_ok


if __name__ == "__main__":
    ok = run_all()
    print("\n{} analytics tests {}".format(
        "All" if ok else "Some", "PASSED" if ok else "FAILED"
    ))
    sys.exit(0 if ok else 1)
