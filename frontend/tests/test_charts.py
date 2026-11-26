"""
tests/test_charts.py — tests for charts.py.

Verifies that each chart function:
  - Returns a matplotlib Figure
  - The figure saves successfully to PNG

Run with:
    cd d:\\Projects\\DS_Project\\frontend
    python -m tests.test_charts
"""

import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import charts as ch


def check(name, condition):
    result = "PASS" if condition else "FAIL"
    print("{}: {}".format(name, result))
    return condition


# ---- Sample data matching the expected formats -------------------

SIZES = [100, 1000, 5000]

SAMPLE_AVG_FRAG = {
    100:  {"first": 35.0, "next": 41.5, "best": 29.5, "worst": 48.4},
    1000: {"first": 71.6, "next": 73.7, "best": 67.3, "worst": 80.1},
    5000: {"first": 72.9, "next": 75.3, "best": 69.9, "worst": 81.4},
}

SAMPLE_FRAG_FAIL_RATE = {
    100:  {"first": 4.5, "next": 3.2, "best": 3.9, "worst": 6.5},
    1000: {"first": 46.6, "next": 48.7, "best": 43.5, "worst": 49.7},
    5000: {"first": 54.9, "next": 54.4, "best": 52.3, "worst": 56.4},
}

SAMPLE_AVG_UTIL = {
    100:  {"first": 46.4, "next": 44.8, "best": 46.6, "worst": 43.3},
    1000: {"first": 79.7, "next": 78.4, "best": 81.9, "worst": 72.5},
    5000: {"first": 79.2, "next": 77.6, "best": 80.7, "worst": 72.4},
}

SAMPLE_SIM_TIME = {
    100:  {"first": 2.0, "next": 2.0, "best": 2.0, "worst": 2.0},
    1000: {"first": 98.0, "next": 95.0, "best": 93.0, "worst": 88.0},
    5000: {"first": 1012.0, "next": 1096.0, "best": 1067.0, "worst": 900.0},
}

SAMPLE_STACKED_FAIL = {
    100:  {"first": {"frag": 7, "nospace": 1},
           "next": {"frag": 5, "nospace": 1},
           "best": {"frag": 6, "nospace": 3},
           "worst": {"frag": 10, "nospace": 0}},
    1000: {"first": {"frag": 713, "nospace": 16},
           "next": {"frag": 740, "nospace": 14},
           "best": {"frag": 666, "nospace": 63},
           "worst": {"frag": 762, "nospace": 0}},
    5000: {"first": {"frag": 2773, "nospace": 57},
           "next": {"frag": 2758, "nospace": 38},
           "best": {"frag": 2639, "nospace": 167},
           "worst": {"frag": 2878, "nospace": 1}},
}

SAMPLE_FRAG_HISTORY = {
    100:  {"first": [10 + i * 0.3 for i in range(50)],
           "next": [12 + i * 0.35 for i in range(50)],
           "best": [8 + i * 0.25 for i in range(50)],
           "worst": [15 + i * 0.4 for i in range(50)]},
    1000: {"first": [20 + i * 0.1 for i in range(50)],
           "next": [22 + i * 0.12 for i in range(50)],
           "best": [18 + i * 0.08 for i in range(50)],
           "worst": [25 + i * 0.15 for i in range(50)]},
    5000: {"first": [25 + i * 0.08 for i in range(50)],
           "next": [27 + i * 0.09 for i in range(50)],
           "best": [22 + i * 0.07 for i in range(50)],
           "worst": [30 + i * 0.1 for i in range(50)]},
}


def run_all():
    """Test every chart function."""
    all_ok = True
    tmpdir = tempfile.mkdtemp()

    # 1. Avg frag bars
    fig = ch.chart_avg_frag(SAMPLE_AVG_FRAG, SIZES)
    all_ok &= check("chart_avg_frag returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "avg_frag.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_avg_frag saves PNG",
                     os.path.exists(path) and os.path.getsize(path) > 0)

    # 2. Frag failure rate bars
    fig = ch.chart_frag_fail_rate(SAMPLE_FRAG_FAIL_RATE, SIZES)
    all_ok &= check("chart_frag_fail_rate returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "frag_fail.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_frag_fail_rate saves PNG",
                     os.path.exists(path))

    # 3. Avg utilisation bars
    fig = ch.chart_avg_util(SAMPLE_AVG_UTIL, SIZES)
    all_ok &= check("chart_avg_util returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "avg_util.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_avg_util saves PNG", os.path.exists(path))

    # 4. Sim time bars (log scale)
    fig = ch.chart_sim_time(SAMPLE_SIM_TIME, SIZES)
    all_ok &= check("chart_sim_time returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "sim_time.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_sim_time saves PNG", os.path.exists(path))

    # 5. Stacked failures
    fig = ch.chart_stacked_failures(SAMPLE_STACKED_FAIL, SIZES)
    all_ok &= check("chart_stacked_failures returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "stacked.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_stacked_failures saves PNG",
                     os.path.exists(path))

    # 6. Frag timeline
    fig = ch.chart_frag_timeline(SAMPLE_FRAG_HISTORY, SIZES)
    all_ok &= check("chart_frag_timeline returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "timeline.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_frag_timeline saves PNG",
                     os.path.exists(path))

    # 7. Heatmap: avg frag
    fig = ch.chart_heatmap_frag(SAMPLE_AVG_FRAG, SIZES)
    all_ok &= check("chart_heatmap_frag returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "hm_frag.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_heatmap_frag saves PNG",
                     os.path.exists(path))

    # 8. Heatmap: frag failure rate
    fig = ch.chart_heatmap_frag_fail(SAMPLE_FRAG_FAIL_RATE, SIZES)
    all_ok &= check("chart_heatmap_frag_fail returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "hm_fail.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_heatmap_frag_fail saves PNG",
                     os.path.exists(path))

    # 9. Heatmap: avg utilisation
    fig = ch.chart_heatmap_util(SAMPLE_AVG_UTIL, SIZES)
    all_ok &= check("chart_heatmap_util returns Figure",
                     fig is not None)
    path = os.path.join(tmpdir, "hm_util.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_heatmap_util saves PNG",
                     os.path.exists(path))

    # 10. Donut chart
    fig = ch.chart_donut(7, 93)
    all_ok &= check("chart_donut returns Figure", fig is not None)
    path = os.path.join(tmpdir, "donut.png")
    ch.save_chart(fig, path)
    all_ok &= check("chart_donut saves PNG", os.path.exists(path))

    return all_ok


if __name__ == "__main__":
    ok = run_all()
    print("\n{} chart tests {}".format(
        "All" if ok else "Some", "PASSED" if ok else "FAILED"
    ))
    sys.exit(0 if ok else 1)
