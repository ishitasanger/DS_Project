# Screenshot Shot List — Project 10

Capture each screenshot from the running application (`python main.py`).
Use seed = 7 and the default 100-block storage unless noted.

---

## Shot 1: Main Dashboard with Sample Data
**Tab:** Dashboard
**Setup:** Launch the application (sample data loads automatically)
**Visible:** Hero frag card (57.1%), utilisation card, largest segment card, segments card, block grid with 7 processes colour-coded, process table, event log, fragmentation trend, donut chart, insight tile
**Filename:** `01_dashboard_sample.png`

## Shot 2: Input Error — Empty PID
**Tab:** Dashboard
**Setup:** Clear the PID field, enter size = 5, click Allocate
**Visible:** Orange "INPUT ERROR: Please enter a Process ID." message in the controls panel
**Filename:** `02_input_error_empty_pid.png`

## Shot 3: Input Error — Non-Numeric Size
**Tab:** Dashboard
**Setup:** Enter PID = "Test", size = "abc", click Allocate
**Visible:** Orange "INPUT ERROR: Size must be a whole number." message
**Filename:** `03_input_error_non_numeric.png`

## Shot 4: Successful Allocation
**Tab:** Dashboard
**Setup:** Reset storage, then allocate PID = "P1", size = 20, First Fit
**Visible:** Green "SUCCESS: Allocated P1 (20 blocks at 0)." message, grid shows P1 in first 20 blocks
**Filename:** `04_successful_allocation.png`

## Shot 5: Failed Allocation — FRAGMENTATION
**Tab:** Dashboard
**Setup:** From sample data, try to allocate PID = "P8", size = 5 (largest hole is 3)
**Visible:** Red "FAILED: Allocation failed: FRAGMENTATION" message
**Filename:** `05_failed_fragmentation.png`

## Shot 6: Failure Analysis Tab
**Tab:** Failure Analysis
**Setup:** After the FRAGMENTATION failure in Shot 5 (auto-navigates)
**Visible:** "FRAGMENTATION" banner in red, block grid with outlined free segments, segment list with Fits Request? column (all "No"), four-line explanation, action buttons
**Filename:** `06_failure_analysis.png`

## Shot 7: Compaction — Before
**Tab:** Compaction
**Setup:** From sample data, click "Run Compaction"
**Visible:** Before panel: grid with scattered free blocks, "Segments: 4 | Largest: 3 | Frag: 57.1%"
**Filename:** `07_compaction_before.png`

## Shot 8: Compaction — After
**Tab:** Compaction
**Setup:** Same as Shot 7 (after compaction completes)
**Visible:** After panel: processes shifted left, all free space at end, "Segments: 1 | Largest: 7 | Frag: 0.0% | Moved: X blocks"
**Filename:** `08_compaction_after.png`

## Shot 9: Strategy Comparison
**Tab:** Compare Strategies
**Setup:** Set Operations = 300, Seed = 7, click "Compare Strategies" on Dashboard
**Visible:** 2×2 tiles with First Fit, Next Fit, Best Fit, Worst Fit — each showing mini grid, OK count, frag fails, segments, avg frag, avg util. Best strategy banner at top
**Filename:** `09_compare_strategies.png`

## Shot 10: Result Table
**Tab:** Results & Charts
**Setup:** Click "Save All Charts as PNG" on Results tab, or trigger from run_experiments.py data
**Visible:** 12-row result table (3 sizes × 4 strategies), lowest fragmentation per size highlighted green, experiment info line, best strategy banner
**Filename:** `10_result_table.png`

## Shot 11: Chart — Average External Fragmentation
**Source:** `outputs/charts/1_avg_ext_fragmentation.png`
**Visible:** Grouped bars with 4 strategies × 3 sizes, values on bars, legend, title, axis labels
**Filename:** `11_chart_avg_frag.png`

## Shot 12: Chart — Fragmentation Failure Rate
**Source:** `outputs/charts/2_frag_failure_rate.png`
**Filename:** `12_chart_frag_fail_rate.png`

## Shot 13: Chart — Average Utilisation
**Source:** `outputs/charts/3_avg_utilisation.png`
**Filename:** `13_chart_avg_util.png`

## Shot 14: Chart — Simulation Time (Log Scale)
**Source:** `outputs/charts/4_simulation_time_log.png`
**Filename:** `14_chart_sim_time.png`

## Shot 15: Chart — Stacked Failures
**Source:** `outputs/charts/5_stacked_failures.png`
**Visible:** Three panels (N=100, N=1000, N=5000), FRAGMENTATION (red) + NO_SPACE (blue) stacked bars
**Filename:** `15_chart_stacked_failures.png`

## Shot 16: Chart — Fragmentation Timeline
**Source:** `outputs/charts/6_frag_timeline.png`
**Visible:** Line chart with 4 strategies per panel, different line styles and markers
**Filename:** `16_chart_frag_timeline.png`

## Shot 17: Heatmap — Average Fragmentation
**Source:** `outputs/charts/7_heatmap_avg_frag.png`
**Visible:** Strategy × size grid with printed values and colour bands
**Filename:** `17_heatmap_avg_frag.png`

## Shot 18: Heatmap — Failure Rate
**Source:** `outputs/charts/8_heatmap_frag_fail_rate.png`
**Filename:** `18_heatmap_fail_rate.png`

## Shot 19: Heatmap — Average Utilisation
**Source:** `outputs/charts/9_heatmap_avg_utilisation.png`
**Filename:** `19_heatmap_avg_util.png`

## Shot 20: Analytics Insight Tile
**Tab:** Dashboard
**Setup:** From sample data (fragmentation is 57.1%, which is High)
**Visible:** Insight tile with green background showing "External Fragmentation: 57.1% | Status: HIGH", trend, and any alert
**Filename:** `20_insight_tile.png`

## Shot 21: Event Log
**Tab:** Dashboard
**Setup:** After several operations (allocate, release, compact)
**Visible:** Event log Treeview with OK entries in teal and FAIL entries in red, columns: Step, Op, Pid, Size, Result, Reason
**Filename:** `21_event_log.png`

## Shot 22: Test Results
**Source:** Terminal
**Setup:** Run all test suites (`analytics`, `charts`, `ui_smoke`, `integration`)
**Command:** `cd d:\Projects\DS_Project\frontend; python -m tests.test_analytics; python -m tests.test_charts; python -m tests.test_ui_smoke; python -m tests.test_integration`
**Visible:** All 115 PASS lines and four "All ... tests PASSED" summaries
**Filename:** `22_test_results.png`
