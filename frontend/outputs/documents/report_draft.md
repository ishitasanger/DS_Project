# Project 10: Virtual Storage Allocation and Fragmentation Simulator — Final Report

## 1. Title Page

**Project 10: Virtual Storage Allocation and Fragmentation Simulator**

Course: Data Structures  
Team: M1, M2, M3, M4, M5

---

## 2. Problem Statement

Operating systems allocate contiguous ranges of storage blocks to concurrent processes. As processes arrive and finish over time, free blocks become split into scattered, non-contiguous holes. Even when enough total free blocks remain, a large request can fail because no single continuous hole is big enough. This problem is **external fragmentation**.

This project implements a simulator with an array-and-linked-list storage engine in C++ (M1–M4), four allocation strategies (First Fit, Next Fit, Best Fit, Worst Fit), failure classification, compaction with automatic retry, and a light-theme Python Tkinter desktop dashboard with Matplotlib analytics and charts (M5).

## 3. Data Structure Choice: Array + Linked List

### Why an Array (`std::vector<std::string>`)?

- **O(1) random lookup** by block index (`array[i]` stores `""` when free or a PID string when occupied).
- Direct 1-to-1 visual mapping to the Tkinter `BlockGrid` canvas.
- Contiguous placement simply writes a PID across `start .. start + size - 1`.

### Why a Singly Linked List (`FreeNode* free_head`)?

- Tracks only contiguous free holes `(start, size, next)`.
- **O(S) hole search** where `S` is the number of free segments, without scanning occupied blocks.
- Supports all four placement strategies using one list traversal loop.
- Adjacent holes merge automatically whenever `rebuild_free_list()` scans the array after an allocation, release, or compaction.

## 4. Architecture and Backend Integration

### Module Breakdown

| Module | Owner | Language / File | Responsibility |
|---|---|---|---|
| M1 — Core Storage | M1 | `backend/storage.h`, `backend/m1_core.cpp` | `Storage(n)`, `rebuild_free_list`, `clear_free_list`, `stats`, `free_segments`, `display_layout` |
| M2 — Allocate / Release Engine | M2 | `backend/m2_engine.cpp` | `validate`, `allocate`, `release`, `add_log`, `export_log_csv`, `last_pos` |
| M3 — Strategies & Experiments | M3 | `backend/m3_strategies.h`, `backend/m3_experiments.cpp` | `find_first_fit`, `find_best_fit`, `find_worst_fit`, `find_next_fit`, `find_hole`, `generate_workload`, experiment runner |
| M4 — Failure Analysis & Compaction | M4 | `backend/m4_compaction.cpp` | `analyze_failure`, `compact`, `allocate_with_compaction` |
| M5 — UI, Charts, Analytics & Bridge | M5 | `frontend/` | Light Tkinter dashboard (5 views), Matplotlib charts (`charts.py`), `dashboard_analytics.py`, C++ JSON bridge (`cpp_bridge.cpp`), `backend_adapter.py`, docs |

### C++ ↔ Python Bridge (`backend_adapter.py` + `cpp_bridge.cpp`)

M1–M4 C++ files are never modified. `backend/m1_core.cpp`, `backend/m2_engine.cpp`, `backend/m4_compaction.cpp`, and `backend/m3_strategies.h` are compiled offline with `g++ -O2 -std=c++17` into `frontend/cpp_bridge.exe`. `backend_adapter.py` is the sole Python module that communicates with `cpp_bridge.exe` over persistent single-line JSON stdin/stdout pipes:

```
Tkinter UI views -> main.py controller -> backend_adapter.py -> cpp_bridge.exe (C++ M1–M4)
```

See `outputs/documents/architecture_audit_and_diagrams.md` for the full 15-row interface mapping table, 8-item contract mismatch log, and light-theme Architecture/Flow diagrams (Figs. 1 & 2).

## 5. Advancements (A1–A8)

| ID | Advancement | Owners | Delivered in UI & Backend |
|---|---|---|---|
| **A1** | Four allocation strategies | M3 (logic), M5 (UI) | Strategy dropdown (`First Fit`, `Next Fit`, `Best Fit`, `Worst Fit`) and 2×2 **Compare Strategies** tab with grids, metrics, and free-segment bars. |
| **A2** | Fragmentation analytics | M1 (metrics), M5 (UI + analytics) | Live cards (`External Fragmentation`, `Utilisation` with occupied/free counts, `Largest Free Segment`, `Free Segments` with average hole size) plus `dashboard_analytics.py` status, trend, and alerts. |
| **A3** | Failure classifier | M4 (logic), M5 (UI) | Automatically opens **Failure Analysis** tab on `NO_SPACE` or `FRAGMENTATION`, showing outlined holes, fit-check table, 4-line explanation, and retry buttons. |
| **A4** | Compaction | M4 (logic), M5 (UI) | `Compact` button slides processes left and displays **Compaction Before/After** grids and moved block counts; `allocate_with_compaction` retries once on `FRAGMENTATION`. |
| **A5** | Light Tkinter dashboard | M5 | Light-theme Executive Dashboard + Bento Box grid (`Ocean Sunset` + `Soft Rainbow` palettes in `ui/theme.py`), 5 `ttk.Notebook` tabs, interactive `BlockGrid` with tooltips and arrow-key stepping, process colour swatches, event markers. |
| **A6** | Seeded workloads | M3 (C++ generator), M5 (UI) | `Operations` and `Seed` controls call M3's `std::mt19937` generator (`generate_workload`) and M3's experiment runner across 3 sizes × 4 strategies. |
| **A7** | Matplotlib charts | M5 | 9 experiment charts + heat maps in `charts.py` (plus sample donut) embedded in **Results & Charts** tab with text summaries and exported as 200 dpi PNGs. |
| **A8** | Event log & CSV export | M2 (C++ log), M5 (UI) | Live **Event Log** Treeview (most recent 50 steps, `● OK` / `▲ FAIL`) and one-click `Export Log (CSV)` calling C++ `Storage::export_log_csv()`. |

### Dashboard Analytics Rules (`dashboard_analytics.py`, Project Settings)

| Function | Rule / Thresholds | Missing Input Return |
|---|---|---|
| `fragmentation_status(v)` | `< 20%` Low · `20% to < 40%` Moderate · `>= 40%` High | `"Not enough data"` |
| `utilisation_status(v)` | `< 50%` Underutilised · `50% to < 85%` Efficient · `>= 85%` Highly utilised | `"Not enough data"` |
| `fragmentation_trend(prev, cur)` | `|cur - prev| < 1.0` Stable · `> 0` Increasing · `< 0` Decreasing | `"Not enough data"` |
| `history_alert(history)` | Any consecutive step jump `>= 10.0` points triggers warning | `None` |
| `best_strategy(results)` | Minimum average external fragmentation; reports ties | `"Not enough data"` |

## 6. Key Pseudocode

### Allocate (M2 + M3)

```
function ALLOCATE(pid, size, strategy):
    check = VALIDATE(pid, size)
    if check != "OK":
        ADD_LOG("ALLOCATE", pid, size, "FAIL", check)
        return AllocResult(false, -1, check)

    hole = FIND_HOLE(free_head, size, strategy_key(strategy), last_pos)
    if hole == null:
        reason = "NO_SPACE" if size > COUNT_FREE() else "FRAGMENTATION"
        ADD_LOG("ALLOCATE", pid, size, "FAIL", reason)
        return AllocResult(false, -1, reason)

    for i from hole.start to hole.start + size - 1:
        array[i] = pid
    table[pid] = (hole.start, size)
    REBUILD_FREE_LIST()
    last_pos = (hole.start + size) % N (or 0 if >= N)
    ADD_LOG("ALLOCATE", pid, size, "OK", "OK")
    return AllocResult(true, hole.start, "OK")
```

### Release (M2)

```
function RELEASE(pid):
    if pid not in table:
        ADD_LOG("RELEASE", pid, 0, "FAIL", "UNKNOWN_PID")
        return ReleaseResult(false, "UNKNOWN_PID")
    (start, size) = table[pid]
    for i from start to start + size - 1:
        array[i] = ""
    erase pid from table
    REBUILD_FREE_LIST()   // merges adjacent holes in one scan
    ADD_LOG("RELEASE", pid, size, "OK", "OK")
    return ReleaseResult(true, "OK")
```

### Strategy Hole Selection (M3)

```
FIRST_FIT: return first node in free_head with node.size >= size
BEST_FIT:  scan all nodes; return node with minimum node.size >= size
WORST_FIT: scan all nodes; return node with maximum node.size >= size
NEXT_FIT:  pass 1 scans node.start >= last_pos; pass 2 wraps node.start < last_pos
```

### Compaction (M4)

```
function COMPACT():
    before = STATS()
    write_pos = 0, moved = 0
    for read_pos from 0 to N - 1:
        if array[read_pos] != "":
            pid = array[read_pos], size = table[pid].size
            if read_pos != write_pos:
                shift pid blocks left to write_pos .. write_pos + size - 1
                clear old tail blocks; table[pid].start = write_pos; moved += size
            write_pos += size
            read_pos += size - 1
    clear remaining blocks write_pos .. N - 1
    REBUILD_FREE_LIST()
    after = STATS()
    ADD_LOG("COMPACT", "", moved, "OK", "COMPACTED")
    return CompactionReport(before, after, moved)
```

## 7. Time & Space Complexity (`N` = blocks, `S` = free segments, `k` = request size, `P` = active processes)

| Operation | Time Complexity | Space Complexity | Reason |
|---|---|---|---|
| `Storage(N)` | O(N) | O(N) | Initialise `array` of N empty strings and initial free node |
| `rebuild_free_list()` | O(N) | O(S) | Linear scan of N blocks creating S `FreeNode` entries |
| `stats()` / `free_segments()` | O(S) | O(1) / O(S) | Single traversal over S nodes in `free_head` |
| `find_hole(...)` | O(S) | O(1) | First/Next Fit stop early; Best/Worst Fit scan all S nodes |
| `allocate(...)` | O(S + k + N) = O(N) | O(1) | Search list, write `k` blocks, rebuild free list |
| `release(...)` | O(k + N) = O(N) | O(1) | Clear `k` blocks, rebuild list (merges adjacent holes) |
| `analyze_failure(...)` | O(S) | O(1) | Reads `count_free()` and `stats()` over free list |
| `compact()` | O(N) | O(1) extra | Scans left-to-right shifting processes and rebuilding free list |
| `generate_workload()` | O(ops) | O(ops) | Generates `ops` allocate/release operations with `mt19937` |
| `run_experiments` | O(sizes × strats × ops × N) | O(N + ops) | Executes full workload benchmark suite |

## 8. Test Cases and Results

### Blueprint Tests T1–T14 (Verified in Both C++ Unit Suites and Live Python → C++ Integration)

| ID | Description | Owner | Expected Outcome | Observed Result |
|---|---|---|---|---|
| T1 | Initial state (`N=20`) | M1 | `free=20, segments=1, largest=20` | PASS |
| T2 | Allocate whole storage | M1 | `free=0, segments=0` | PASS |
| T3 | Request larger than N | M2 | Rejected: `NO_SPACE` | PASS |
| T4 | Zero and negative size | M2 | Rejected: `INVALID_SIZE` | PASS |
| T5 | Smallest request (1 block) | M1 | `start=0, free=19` | PASS |
| T6 | Release unknown PID | M2 | Rejected: `UNKNOWN_PID` | PASS |
| T7 | Double release | M2 | Second release rejected | PASS |
| T8 | Duplicate PID | M2 | Rejected: `DUPLICATE_PID` | PASS |
| T9 | Fragmentation failure (`free=10, largest=5, req=8`) | M4 | Classified `FRAGMENTATION` | PASS |
| T10 | Compaction fixes failure | M4 | `segments_after=1`, req `8` succeeds | PASS |
| T11 | Adjacent holes merge on release | M1/M4 | Merged hole `segments=1, largest=10` | PASS |
| T12 | Strategy placement differs (`holes 4 & 8, req=3`) | M3 | `best=0, worst=6, first=0` | PASS |
| T13 | Full → release → full | M1 | Full reallocation succeeds | PASS |
| T14 | Request on full storage | M2 | Rejected: `NO_SPACE` | PASS |

### Complete Test Execution Summary

- **C++ Backend Unit Tests (`m1_tests`, `m2_tests`, `m3_tests`, `m3_section9_tests`, `m4_tests`):** 23 / 23 PASS (compiled and executed with `g++ -O2 -std=c++17`).
- **M5 Analytics Tests (`tests/test_analytics.py`):** 44 / 44 PASS (all boundaries: 19.9, 20.0, 39.9, 40.0, 49.9, 50.0, 84.9, 85.0, all trends, alerts at 9.9 vs 10.0, ties, empty/None).
- **M5 Chart Tests (`tests/test_charts.py`):** 20 / 20 PASS (all 9 experiment charts + donut generate valid Figures and 200 dpi PNGs).
- **M5 UI Smoke Tests (`tests/test_ui_smoke.py`):** 26 / 26 PASS (all 5 tabs, controls, empty/non-numeric validation, live C++ allocate/release/compact/reset refresh).
- **M5 C++ ↔ Python Integration Tests (`tests/test_integration.py`):** 25 / 25 PASS (T1–T14 through Python → C++ bridge, C++ CSV export, C++ repeatability, Failure/Compaction/Compare/Results UI tabs).

## 9. Experimental Results (Measured from C++ M3 Engine, Seed = 7)

Configuration: `seed = 7`, `mt19937` workload generator (`50%` allocate / `50%` release mix, request sizes `1` to `N/10`), sizes `[100, 1000, 5000]`, operations `[300, 3000, 10000]`.

| N | Ops | Strategy | OK | FailFrag | FailNoSp | AvgFrag% | AvgUtil% | Segments | Largest | Time(ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 300 | First Fit | 152 | 0 | 0 | 16.4 | 24.7 | 4 | 54 | 0.2 |
| 100 | 300 | Next Fit | 152 | 0 | 0 | 24.9 | 24.7 | 3 | 40 | 0.2 |
| 100 | 300 | **Best Fit ★** | 152 | 0 | 0 | **15.4** | 24.7 | 3 | 54 | 0.4 |
| 100 | 300 | Worst Fit | 152 | 0 | 0 | 33.3 | 24.7 | 4 | 27 | 0.3 |
| 1000 | 3000 | First Fit | 1304 | 198 | 12 | 40.4 | 51.5 | 8 | 22 | 5.8 |
| 1000 | 3000 | Next Fit | 1299 | 210 | 5 | 50.1 | 50.5 | 7 | 46 | 6.6 |
| 1000 | 3000 | **Best Fit ★** | 1307 | 189 | 18 | **39.8** | 51.8 | 8 | 46 | 6.8 |
| 1000 | 3000 | Worst Fit | 1277 | 237 | 0 | 56.5 | 48.1 | 9 | 27 | 6.4 |
| 5000 | 10000 | First Fit | 3278 | 1706 | 48 | 62.2 | 70.1 | 16 | 163 | 52.3 |
| 5000 | 10000 | Next Fit | 3263 | 1744 | 25 | 66.2 | 69.2 | 15 | 300 | 53.9 |
| 5000 | 10000 | **Best Fit ★** | 3285 | 1580 | 167 | **58.8** | 72.0 | 17 | 287 | 55.1 |
| 5000 | 10000 | Worst Fit | 3191 | 1835 | 6 | 73.0 | 64.7 | 13 | 262 | 56.4 |

Repeatability check (`N=100, Ops=300, Seed=7, Best Fit` run twice in C++): identical counts and fragmentation — **PASS**. Results exported to `outputs/charts/experiment_results.csv`.

## 10. Comparison and Observations

### Best Observed Strategy (Best Fit)

Best Fit recorded the lowest average external fragmentation at every tested size (`15.4%` at N=100, `39.8%` at N=1000, `58.8%` at N=5000), the fewest fragmentation failures (`0`, `189`, `1580`), and the highest average utilisation (`24.7%`, `51.8%`, `72.0%`). Because it selects the tightest-fitting hole, larger holes remain intact for subsequent larger requests. That tight packing creates tiny unusable leftovers, causing more `NO_SPACE` failures when free capacity shrinks (`18` at N=1000; `167` at N=5000).

### Worst Observed Strategy (Worst Fit)

Worst Fit produced the highest fragmentation at every size (`33.3%`, `56.5%`, `73.0%`) and the most fragmentation failures (`237` at N=1000; `1835` at N=5000). Repeatedly splitting the largest available hole rapidly eliminates large contiguous regions. Paradoxically, it suffered the fewest `NO_SPACE` failures (`0` at N=1000; `6` at N=5000) because overall utilisation stayed lower (`48.1%` / `64.7%`).

### Next Fit vs. First Fit

Next Fit dispersed allocations across the array instead of packing near index 0, producing higher fragmentation than First Fit at all three sizes (`24.9%` vs. `16.4%`; `50.1%` vs. `40.4%`; `66.2%` vs. `62.2%`) and slightly more fragmentation failures (`210` vs. `198`; `1744` vs. `1706`). However, Next Fit incurred fewer `NO_SPACE` failures (`5` vs. `12`; `25` vs. `48`).

### Running-Time Observation (From Measured C++ Timings)

| Transition | N × Ops Growth | Measured Time Growth (First Fit) | Mean Time Growth (4 Strategies) |
|---|---|---|---|
| `N=100, Ops=300` → `N=1000, Ops=3000` | `30,000 → 3,000,000` (**100.0×**) | `0.2 ms → 5.8 ms` (**29.0×**) | `0.28 ms → 6.40 ms` (**23.3×**) |
| `N=1000, Ops=3000` → `N=5000, Ops=10000` | `3,000,000 → 50,000,000` (**16.7×**) | `5.8 ms → 52.3 ms` (**9.0×**) | `6.40 ms → 54.43 ms` (**8.5×**) |

Measured runtime grows substantially slower than the raw `N × Ops` product in both intervals (`23.3×` mean time vs. `100×` product; `8.5×` mean time vs. `16.7×` product). Two measured factors explain this: (1) at `N=100`, total simulation time is sub-millisecond (`0.2–0.4 ms`) so constant loop and timer overhead dominates the baseline; (2) at `N=5000`, `~35%` of allocation attempts fail (`1,754 / 5,032` for First Fit vs. `210 / 1,514` at `N=1000` and `0` at `N=100`), skipping both block placement and the O(N) `rebuild_free_list()` scan. Across all four strategies at a fixed `N`, runtime remains nearly identical (`52.3–56.4 ms` at `N=5000`).

### Fragmentation Threshold Crossing

With the project rule classifying external fragmentation **40% or above as High**, all strategies stay Low/Moderate at `N=100` (`15.4%–33.3%`), First/Next/Worst Fit cross the 40% High threshold at `N=1000` (`40.4%–56.5%`, while Best Fit sits at `39.8%`), and all four strategies exceed High at `N=5000` (`58.8%–73.0%`). Compaction eliminates external fragmentation (`0.0%`, `1` segment) when triggered.

## 11. Screenshots and Charts

- 10 Matplotlib PNG figures generated at 200 dpi in `outputs/charts/` (`1_avg_ext_fragmentation.png` through `10_donut_sample.png`), visually checked for legibility and overlap.
- Window screenshots / shot list: see `outputs/documents/screenshot_shot_list.md` and `outputs/screenshots/`.

## 12. Limitations

1. **Single-machine synchronous execution:** GUI runs offline on one workstation; long workloads use `update_idletasks()` and a busy cursor instead of threads per design rules.
2. **Untested screen reader:** High-contrast light colours, keyboard focus rings, arrow-key cell stepping, chart summaries, and pattern+label redundancy are implemented, but screen-reader software compatibility has not been tested.
3. **Subprocess pipe bridge overhead per interactive call:** Bulk experiments execute natively inside C++ (`cpp_bridge.exe`), while interactive single actions incur sub-millisecond JSON line serialization.

## 13. Member Contributions

| Member | Module | Key Deliverables |
|---|---|---|
| M1 | Core Storage | `Storage` constructor, `rebuild_free_list`, `stats`, `free_segments`, `display_layout`, tests T1/T2/T5/T13 |
| M2 | Engine | `validate`, `allocate`, `release`, event log, CSV export, tests T3/T4/T6/T7/T8/T14 |
| M3 | Strategies & Experiments | First/Next/Best/Worst Fit, `mt19937` workload generator, experiment runner, T12 & repeatability |
| M4 | Compaction & Failure | `analyze_failure`, `compact`, `allocate_with_compaction`, tests T9/T10/T11 |
| M5 | UI, Charts, Analytics & Integration | 5 Tkinter light-theme views, 9 Matplotlib charts, `dashboard_analytics.py`, `cpp_bridge.cpp`, `backend_adapter.py`, integration/analytics/chart/smoke tests, documentation |
