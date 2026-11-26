# Mock Viva Plan — Project 10

Each member explains a module written by someone else.  This exercises cross-module understanding and ensures every member can speak to the full project.

---

## 1. M1 explains M3 (Strategies and Experiments)

### Files to Study
- `m3_strategies.h` — four strategy functions and `generate_workload`
- `m3_experiments.cpp` — `alloc_with_strategy`, `run_one`, experiment runner

### Questions the Examiner Might Ask
1. What makes Best Fit "best" — and when is it not?
2. Walk through a Next Fit allocation when `last_pos` is in the middle of the array.
3. How does `generate_workload` decide between allocate and release?
4. Why is the seed important for fair comparisons?
5. What data does `run_one` return, and how is it used?

### Key Talking Points
- Best Fit scans the entire free list for the smallest fitting hole; O(S) time.
- Next Fit uses a two-pass approach: first from `last_pos` onward, then wrapping.
- `generate_workload` uses a 50/50 coin flip, but forces allocate when `issued` is empty.
- Request sizes are 1 to `n_blocks / 10`, ensuring a mix of small and large.
- The experiment runner loops over sizes × strategies, calling `run_one` for each.

### Pitfalls to Avoid
- Do not confuse Best Fit (smallest fitting hole) with First Fit (first fitting hole).
- Do not say Next Fit is "better" than First Fit — it has higher fragmentation in our data.
- Remember that `generate_workload` returns a vector of Op structs, not results.

---

## 2. M2 explains M4 (Compaction and Failure Analysis)

### Files to Study
- `m4_compaction.cpp` — `analyze_failure`, `compact`, `allocate_with_compaction`
- `storage.h` — `FailureAnalysis` and `CompactionReport` structs

### Questions the Examiner Might Ask
1. What is the difference between FRAGMENTATION and NO_SPACE?
2. When should compaction NOT be run?
3. How does `compact` handle processes that are already at the left?
4. What does `allocate_with_compaction` do if the retry also fails?
5. How many blocks does compaction move in the worst case?

### Key Talking Points
- `analyze_failure` compares total free vs. request and largest hole vs. request.
- Compaction is O(N): it touches every block once to slide processes left.
- `allocate_with_compaction` retries only once; if the retry fails, it returns that failure.
- Compaction should not be run for NO_SPACE — it cannot create new free blocks.
- In the worst case, compaction moves all occupied blocks (N − free).

### Pitfalls to Avoid
- Do not say compaction "adds" free space — it only merges existing free space.
- Do not forget to mention that compaction rebuilds the free list after moving.

---

## 3. M3 explains M1 (Core Storage)

### Files to Study
- `storage.h` — `Storage` class declaration, `Stats` struct, `FreeNode` struct
- `m1_core.cpp` — constructor, `rebuild_free_list`, `stats`, `free_segments`, `display_layout`

### Questions the Examiner Might Ask
1. What happens in the `Storage(n)` constructor?
2. Why is `rebuild_free_list` called after every allocate and release?
3. How does `stats()` compute external fragmentation?
4. What is the time complexity of `free_segments()`?
5. What does the free list look like after releasing a process between two occupied ones?

### Key Talking Points
- Constructor creates an array of N empty strings and builds the initial free list (one node: start=0, size=N).
- `rebuild_free_list` is O(N): it scans the array for runs of empty blocks.
- `stats` traverses the free list (O(S)), counting segments and finding the largest.
- `free_segments` returns a vector of (start, size) pairs from the free list.
- After releasing a middle process, `rebuild_free_list` creates a new segment or merges adjacent free blocks.

### Pitfalls to Avoid
- Do not forget that `rebuild_free_list` clears the old list before building a new one.
- Do not say `stats()` scans the array — it traverses the free list.

---

## 4. M4 explains M5 (UI and Integration)

### Files to Study
- `main.py` — `SimulatorApp` controller
- `backend_adapter.py` — the bridge
- `ui/main_view.py` — Dashboard tab
- `dashboard_analytics.py` — analytics module
- `charts.py` — chart generation

### Questions the Examiner Might Ask
1. How does the UI call backend functions without importing backend files?
2. What happens when the user clicks "Allocate"?
3. How does `dashboard_analytics.py` differ from `stats()`?
4. How are charts embedded in the Tkinter window?
5. What accessibility features does the UI provide?

### Key Talking Points
- `backend_adapter.py` is the sole import bridge; all other files use the adapter.
- Click "Allocate" → `_on_allocate()` validates input → calls `self.ctrl.allocate()` → calls `backend.allocate()` → calls `refresh()` → updates grid, cards, tables, charts.
- `dashboard_analytics.py` takes raw numbers and classifies them (Low/Moderate/High); `stats()` computes the numbers.
- Matplotlib figures are embedded via `FigureCanvasTkAgg` — reused on each refresh.
- Accessibility: WCAG AA contrast, 3px focus ring, keyboard access, labels+patterns, reduce-motion option.

### Pitfalls to Avoid
- Do not say the UI "computes" statistics — it only displays them.
- Do not confuse `charts.py` (Matplotlib for PNGs) with the embedded trend/donut (also Matplotlib but via TkAgg).

---

## 5. M5 explains M2 (Engine and Event Log)

### Files to Study
- `m2_engine.cpp` — `validate`, `allocate`, `release`, `add_log`, `export_log_csv`
- `storage.h` — `AllocResult`, `ReleaseResult`, `LogEntry` structs

### Questions the Examiner Might Ask
1. What does `validate(pid, size)` check?
2. Walk through a successful allocation step by step.
3. What information does the event log capture?
4. How does `export_log_csv` format the output?
5. What happens if `release` is called with an unknown PID?

### Key Talking Points
- `validate` checks: PID not empty, size > 0, size ≤ N, PID not in table.  Returns first failure reason.
- Allocate: validate → find_hole → write PID into array → update table → rebuild free list → log → return AllocResult.
- LogEntry: step (auto-increment), op, pid, size, result, reason — six fields.
- `export_log_csv` writes a header line then one line per entry, comma-separated.
- Unknown PID release returns `ReleaseResult(false, "UNKNOWN_PID")` and logs the failure.

### Pitfalls to Avoid
- Do not forget the `rebuild_free_list` call after allocation and release.
- Do not confuse `last_pos` (Next Fit state) with the allocation start position.
