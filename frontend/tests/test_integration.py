"""
tests/test_integration.py — C++ <-> Python integration & blueprint T1–T14 tests.

Verifies:
  - BackendAdapter runs against the compiled C++ M1–M4 bridge
  - All 14 blueprint tests (T1–T14) pass through Python -> C++
  - M2 CSV export works from C++
  - M3 seeded workload and experiment runner match C++ m3_experiments
  - End-to-end UI controller flows (compare_strategies, run_experiments,
    compaction view, failure view) populate views accurately from C++ data.

Run with:
    cd d:\\Projects\\DS_Project\\frontend
    python -m tests.test_integration
"""

import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_adapter import BackendAdapter


def check(name, condition):
    """Print one PASS/FAIL line per test case."""
    print("{}: {}".format(name, "PASS" if condition else "FAIL"))
    return bool(condition)


def run_t1_to_t14():
    """Run all 14 blueprint test cases through BackendAdapter -> C++ M1–M4."""
    ok = True
    b = BackendAdapter(total_blocks=20, load_sample=False)
    try:
        # T1: Initial state
        st = b.stats()
        ok &= check("T1 Initial state (free=20, seg=1, largest=20)",
                    st.free == 20 and st.segments == 1 and st.largest == 20)

        # T2: Allocate whole storage
        r2 = b.allocate("P1", 20, "First Fit")
        st2 = b.stats()
        ok &= check("T2 Allocate whole storage (free=0, seg=0)",
                    r2.ok and st2.free == 0 and st2.segments == 0)

        # T3: Request larger than storage -> NO_SPACE
        b.reset(20)
        r3 = b.allocate("P1", 25, "First Fit")
        ok &= check("T3 Request > N rejected as NO_SPACE",
                    not r3.ok and r3.reason == "NO_SPACE")

        # T4: Zero and negative size -> INVALID_SIZE
        r4a = b.allocate("P1", 0, "First Fit")
        r4b = b.allocate("P2", -3, "First Fit")
        ok &= check("T4 Zero/negative size -> INVALID_SIZE",
                    r4a.reason == "INVALID_SIZE" and r4b.reason == "INVALID_SIZE")

        # T5: Smallest request (1 block)
        r5 = b.allocate("P1", 1, "First Fit")
        ok &= check("T5 Smallest request 1 block (start=0, free=19)",
                    r5.ok and r5.start == 0 and b.stats().free == 19)

        # T6: Release unknown PID -> UNKNOWN_PID
        r6 = b.release("P99")
        ok &= check("T6 Release unknown PID -> UNKNOWN_PID",
                    not r6.ok and r6.reason == "UNKNOWN_PID")

        # T7: Double release -> second rejected
        rel1 = b.release("P1")
        rel2 = b.release("P1")
        ok &= check("T7 Double release rejected", rel1.ok and not rel2.ok)

        # T8: Duplicate PID -> DUPLICATE_PID
        b.allocate("P1", 5, "First Fit")
        r8 = b.allocate("P1", 2, "First Fit")
        ok &= check("T8 Duplicate PID -> DUPLICATE_PID",
                    not r8.ok and r8.reason == "DUPLICATE_PID")

        # T9: Fragmentation failure (free=10, largest=5, request=8)
        b.reset(20)
        b.allocate("A", 5, "First Fit")
        b.allocate("B", 5, "First Fit")
        b.allocate("C", 5, "First Fit")
        b.allocate("D", 5, "First Fit")
        b.release("A")
        b.release("C")
        fa = b.analyze_failure(8)
        r9 = b.allocate("E", 8, "First Fit")
        ok &= check("T9 Fragmentation failure (free=10, largest=5)",
                    fa.reason == "FRAGMENTATION" and not r9.ok and r9.reason == "FRAGMENTATION")

        # T10: Compaction merges holes so request 8 succeeds
        rep = b.compact()
        r10 = b.allocate("E", 8, "First Fit")
        ok &= check("T10 Compaction merges holes (seg_after=1) and request 8 fits",
                    rep.segments_after == 1 and r10.ok)

        # T11: Adjacent holes merge automatically on release
        b.reset(10)
        b.allocate("P1", 5, "First Fit")
        b.allocate("P2", 5, "First Fit")
        b.release("P1")
        b.release("P2")
        ok &= check("T11 Adjacent holes merge (largest=10, seg=1)",
                    b.stats().segments == 1 and b.stats().largest == 10)

        # T12: Strategy placement differs (holes at 0 size 4, 6 size 8; req=3)
        b.reset(14)
        b.allocate("H1", 4, "First Fit")
        b.allocate("X1", 2, "First Fit")
        b.allocate("H2", 8, "First Fit")
        b.release("H1")
        b.release("H2")
        r_best = b.allocate("Q", 3, "Best Fit")
        b.release("Q")
        r_worst = b.allocate("Q", 3, "Worst Fit")
        b.release("Q")
        r_first = b.allocate("Q", 3, "First Fit")
        ok &= check("T12 Strategy placement differs (best=0, worst=6, first=0)",
                    r_best.start == 0 and r_worst.start == 6 and r_first.start == 0)

        # T13: Full -> release -> full
        b.reset(20)
        b.allocate("P1", 20, "First Fit")
        b.release("P1")
        r13 = b.allocate("P2", 20, "First Fit")
        ok &= check("T13 Full -> release -> full succeeds", r13.ok)

        # T14: Request on full storage -> NO_SPACE
        r14 = b.allocate("P3", 1, "First Fit")
        ok &= check("T14 Request on full storage -> NO_SPACE",
                    not r14.ok and r14.reason == "NO_SPACE")

        # M2 CSV export check
        tmpdir = tempfile.mkdtemp()
        csv_path = os.path.join(tmpdir, "cpp_log.csv")
        csv_ok = b.export_log_csv(csv_path)
        ok &= check("M2 C++ CSV log export succeeds",
                    csv_ok and os.path.exists(csv_path) and os.path.getsize(csv_path) > 0)

        # M3 repeatability check via C++ bridge
        e1 = b.run_experiment(100, 300, 7, "best")
        e2 = b.run_experiment(100, 300, 7, "best")
        ok &= check("M3 C++ repeatability (same seed=7 identical)",
                    e1["ok"] == e2["ok"] and e1["frag_fail"] == e2["frag_fail"]
                    and abs(e1["avg_frag"] - e2["avg_frag"]) < 1e-6)
    finally:
        b.close()
    return ok


def run_ui_integration():
    """Verify UI views reflect live C++ backend operations."""
    ok = True
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        print("SKIPPED UI integration: No display available.")
        return ok

    from main import SimulatorApp
    app = SimulatorApp(root)
    try:
        ok &= check("Backend mode is C++ (M1–M4)", "C++" in app.backend.backend_mode)
        ok &= check("Initial badge is Sample data",
                    app.main_view._data_badge_var.get() == "Sample data")
        ok &= check("Sample hero fragmentation is 57.1%",
                    app.main_view._hero._val_var.get() == "57.1%")

        # Trigger fragmentation failure -> Failure Analysis tab
        app.main_view._pid_var.set("P8")
        app.main_view._size_var.set("5")
        app.main_view._strategy_var.set("Best Fit")
        app.main_view._on_allocate()
        ok &= check("Live badge switches after allocate",
                    app.main_view._data_badge_var.get() == "Live")
        ok &= check("Failure tab shows FRAGMENTATION",
                    "FRAGMENTATION" in app.failure_view._banner_var.get())

        # Compaction tab before/after
        app.compact()
        ok &= check("CompactionView after shows 0.0% frag and 1 segment",
                    "1 free segments" in app.compaction_view._after_var.get()
                    and "0.0%" in app.compaction_view._after_var.get())

        # Strategy comparison
        app.compare_strategies(300, 7)
        best_banner = app.compare_view._best_var.get()
        ok &= check("CompareView displays best strategy from C++",
                    "Best observed" in best_banner or "Tied" in best_banner)

        # Experiments + ResultsView
        app.run_experiments([100], [300], 7)
        rows = app.results_view._result_tree.get_children()
        ok &= check("ResultsView populated 4 rows for N=100", len(rows) == 4)
        ok &= check("ResultsView rendered 9 Matplotlib charts",
                    len(app.results_view._chart_figs) == 9)
    finally:
        app.close()
    return ok


def run_all():
    ok = run_t1_to_t14()
    ok &= run_ui_integration()
    return ok


if __name__ == "__main__":
    passed = run_all()
    print("\n{} integration tests {}".format(
        "All" if passed else "Some", "PASSED" if passed else "FAILED"
    ))
    sys.exit(0 if passed else 1)
