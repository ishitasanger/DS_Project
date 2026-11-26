"""
tests/test_ui_smoke.py — UI smoke tests.

Verifies:
  - Application opens against C++ backend without crashing
  - All 5 tabs exist and key widgets are present
  - Input validation works (empty PID, empty size, non-numeric size)
  - Allocate, release, compact, reset refresh the display & backend stats

Run with:
    cd d:\\Projects\\DS_Project\\frontend
    python -m tests.test_ui_smoke
"""

import os
import sys
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check(name, condition):
    """Print one PASS/FAIL line per test case."""
    print("{}: {}".format(name, "PASS" if condition else "FAIL"))
    return condition


def run_all():
    """Run all UI smoke tests."""
    all_ok = True
    try:
        root = tk.Tk()
        root.withdraw()
    except tk.TclError:
        print("SKIPPED: No display available to test Tkinter window.")
        return True

    from main import SimulatorApp
    try:
        app = SimulatorApp(root)
    except Exception as exc:
        print("FAIL: Application failed to start: {}".format(exc))
        root.destroy()
        return False

    try:
        all_ok &= _check_tabs_and_widgets(app)
        all_ok &= _check_input_validation(app)
        all_ok &= _check_operations(app)
    finally:
        app.close()
    return all_ok


def _check_tabs_and_widgets(app):
    ok = check("App creates without crash", True)
    tab_count = app.notebook.index("end")
    ok &= check("5 tabs exist", tab_count == 5)
    names = [app.notebook.tab(i, "text") for i in range(tab_count)]
    for expected in [
        "Dashboard", "Failure Analysis", "Compaction",
        "Compare Strategies", "Results & Charts",
    ]:
        ok &= check("{} tab".format(expected), expected in names)

    mv = app.main_view
    for name, obj in [
        ("Hero card exists", mv._hero),
        ("Block grid exists", mv._grid),
        ("Process table exists", mv._proc_tree),
        ("Event log exists", mv._log_tree),
        ("PID entry exists", mv._pid_var),
        ("Size entry exists", mv._size_var),
        ("Strategy selector exists", mv._strategy_var),
    ]:
        ok &= check(name, obj is not None)
    return ok


def _check_input_validation(app):
    mv = app.main_view
    mv._pid_var.set("")
    mv._size_var.set("5")
    mv._on_allocate()
    ok = check("Empty PID shows message", "INPUT ERROR" in mv._msg_var.get())

    mv._pid_var.set("Test1")
    mv._size_var.set("")
    mv._on_allocate()
    ok &= check("Empty size shows message", "INPUT ERROR" in mv._msg_var.get())

    mv._pid_var.set("Test1")
    mv._size_var.set("abc")
    mv._on_allocate()
    ok &= check("Non-numeric size shows message", "INPUT ERROR" in mv._msg_var.get())
    return ok


def _check_operations(app):
    mv = app.main_view
    app.backend.reset(total_blocks=20)
    mv._grid.reset_colors()
    mv._pid_var.set("P1")
    mv._size_var.set("5")
    mv._strategy_var.set("First Fit")
    mv._on_allocate()
    st = app.backend.stats()
    ok = check("Allocation succeeds", "SUCCESS" in mv._msg_var.get())
    ok &= check("Stats after alloc: free=15", st.free == 15)
    ok &= check("Stats after alloc: occupied=5", st.occupied == 5)

    mv._pid_var.set("P1")
    mv._on_release()
    st = app.backend.stats()
    ok &= check("Release succeeds", "SUCCESS" in mv._msg_var.get())
    ok &= check("Stats after release: free=20", st.free == 20)

    mv._on_compact()
    ok &= check(
        "Compact on empty: no crash",
        "SUCCESS" in mv._msg_var.get() or "Compaction" in mv._msg_var.get(),
    )

    mv._on_reset()
    st = app.backend.stats()
    ok &= check("Reset works", st.free == 100 and st.occupied == 0)

    mv._pid_var.set("PBig")
    mv._size_var.set("200")
    mv._on_allocate()
    ok &= check("Over-size allocation fails", "FAILED" in mv._msg_var.get())

    mv._pid_var.set("PD1")
    mv._size_var.set("3")
    mv._on_allocate()
    mv._pid_var.set("PD1")
    mv._size_var.set("3")
    mv._on_allocate()
    ok &= check("Duplicate PID rejected", "DUPLICATE_PID" in mv._msg_var.get())
    return ok


if __name__ == "__main__":
    ok = run_all()
    print("\n{} UI smoke tests {}".format(
        "All" if ok else "Some", "PASSED" if ok else "FAILED"
    ))
    sys.exit(0 if ok else 1)
