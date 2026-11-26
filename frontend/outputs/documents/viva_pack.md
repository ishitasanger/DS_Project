# Viva Preparation Pack — Project 10

## 1. General Questions

### Q: What is external fragmentation? How does it differ from internal fragmentation?
**A:** External fragmentation occurs when free memory exists but is split into non-contiguous holes, so no single hole can satisfy a large request even though the total free space is sufficient.  Internal fragmentation occurs when allocated blocks are larger than the actual request, wasting space inside each allocation.  Our simulator measures external fragmentation as `(1 − largest_hole / total_free) × 100%`.

### Q: Why use an array for storage simulation?
**A:** An array provides O(1) random access to any block by index.  It maps directly to the block grid in the UI — each cell of the array corresponds to one rectangle on screen.  Writing a PID into a range of cells is a simple loop.

### Q: What is the advantage of a linked list for the free list?
**A:** The linked list allows traversal of only the free segments (O(S) where S is the number of segments) rather than scanning the entire array (O(N)).  It supports efficient insertion and deletion when segments merge after a release or split after an allocation.

### Q: Compare First Fit, Best Fit, Worst Fit, Next Fit — when is each best?
**A:**
- **First Fit:** Fast — takes the first hole that fits.  Good general-purpose choice.
- **Best Fit:** Minimises leftover fragmentation by choosing the tightest fit.  Best for reducing external fragmentation but may create many tiny unusable holes and more NO_SPACE failures.
- **Worst Fit:** Takes the largest hole, leaving the biggest remainder.  Increases overall fragmentation but rarely produces NO_SPACE failures.
- **Next Fit:** Like First Fit but resumes from the last position.  Distributes allocations across the array, useful when the beginning of storage fills quickly.

### Q: What is compaction? When should it be triggered?
**A:** Compaction slides all occupied processes towards the beginning of storage, merging all free holes into one contiguous block at the end.  It should be triggered when an allocation fails due to FRAGMENTATION — meaning enough total free space exists but no single hole is large enough.  It should not be triggered for NO_SPACE failures, where total free space is insufficient.

### Q: How does seeded workload generation ensure fair comparison?
**A:** The `generate_workload` function uses a seeded pseudo-random number generator.  The same seed always produces the same sequence of allocate and release operations.  By running the same workload under all four strategies, we eliminate random variation and isolate the effect of the strategy choice.

### Q: What is the time complexity of allocate?
**A:** O(N) in the worst case.  The strategy search is O(S) ≤ O(N), writing the PID into the array is O(size) ≤ O(N), and rebuilding the free list is O(N).  Total: O(N).

### Q: How do you calculate external fragmentation percentage?
**A:** `ext_frag = (1 − largest_free_segment / total_free_blocks) × 100`.  When all free space is in one segment, the ratio is 1 and fragmentation is 0%.  When free space is split into many equal tiny segments, the ratio approaches 0 and fragmentation approaches 100%.

---

## 2. M1 (Core Storage) Questions

### Q: How does `rebuild_free_list` work?
**A:** It scans the array from index 0 to N−1.  Whenever it encounters a free block (""), it starts a new segment, counts consecutive free blocks, creates a FreeNode with (start, size), and links it to the list.  It clears any old nodes first.

### Q: What does `stats()` compute?
**A:** It traverses the free list to count the number of free segments, the total free blocks, and the largest segment size.  Occupied = N − free.  External fragmentation = (1 − largest / free) × 100.  Utilisation = occupied / N × 100.  Average hole = free / segments.

---

## 3. M2 (Engine) Questions

### Q: How does `validate()` check inputs?
**A:** It checks: (1) PID is not empty, (2) size is positive, (3) size does not exceed N, (4) PID is not already in the table.  It returns the first failure reason found, or empty string if valid.

### Q: Explain the event log format.
**A:** Each LogEntry has six fields: step (sequential number), op (ALLOCATE/RELEASE/COMPACT), pid (process identifier), size (block count), result (OK/FAIL), reason (OK/NO_SPACE/FRAGMENTATION/UNKNOWN_PID/DUPLICATE_PID/INVALID_SIZE/COMPACTED).

---

## 4. M3 (Strategies) Questions

### Q: How does Next Fit differ from First Fit in implementation?
**A:** First Fit always starts scanning from the head of the free list.  Next Fit remembers `last_pos` (where the previous allocation ended) and scans from that point.  It makes two passes: first from `last_pos` to the end, then wrapping around from the beginning to `last_pos`.

### Q: Why does Best Fit sometimes cause more NO_SPACE failures?
**A:** Best Fit chooses the tightest-fitting hole, leaving tiny leftover fragments.  Over many operations, these fragments can become too small for any request.  While total free space may be low, the fragments are individually useless, causing more outright NO_SPACE failures than strategies that leave larger remainders.

### Q: How does `generate_workload` ensure reproducibility?
**A:** It takes a seed parameter and creates a `mt19937` random generator initialised with that seed.  Every random decision (allocate vs release, which PID to release, what size to request) comes from this generator.  Same seed = same sequence = reproducible experiment.

---

## 5. M4 (Compaction/Failure) Questions

### Q: How does `analyze_failure` classify between FRAGMENTATION and NO_SPACE?
**A:** It compares the request size against two values: total free blocks and the largest single hole.  If total free < request, it is NO_SPACE (even compaction cannot help).  If total free ≥ request but largest hole < request, it is FRAGMENTATION (compaction can merge holes to satisfy the request).

### Q: What does `compact()` do step by step?
**A:** (1) Record "before" stats.  (2) Sort processes by their start position.  (3) Walk through processes in order, sliding each one to the left so it starts right after the previous one ends.  (4) Clear all blocks after the last process.  (5) Rebuild the free list.  (6) Record "after" stats and count moved blocks.

### Q: How does `allocate_with_compaction` retry?
**A:** It first attempts a normal allocation.  If the result is OK or the failure reason is not FRAGMENTATION, it returns immediately.  If the failure is FRAGMENTATION, it calls `compact()` to merge free space, then retries the allocation once.

---

## 6. M5 (UI/Integration) Questions

### Q: How does the UI know what to draw?
**A:** The UI calls `backend.stats()` to get the current free, occupied, segments, largest, ext_frag, utilisation, and avg_hole values.  It reads `backend.array` to draw the block grid (each cell's PID determines its colour).  It reads `backend.table` to populate the process table.  It calls `backend.get_log()` to show the event log.  All data comes from the backend; the UI invents nothing.

### Q: How does the UI connect to the backend?
**A:** Through `backend_adapter.py`, which is the sole file that knows about the C++ backend. Every UI view calls methods on the `SimulatorApp` controller, which delegates to `BackendAdapter`. `BackendAdapter` launches the compiled C++17 binary `cpp_bridge.exe` (which links M1's `m1_core.cpp`, M2's `m2_engine.cpp`, M3's `m3_strategies.h`, and M4's `m4_compaction.cpp` untouched) and exchanges single-line JSON messages over stdin/stdout pipes.

### Q: What is `dashboard_analytics.py`?
**A:** A standalone module with no Tkinter imports that classifies raw statistics into human-readable labels.  Functions like `fragmentation_status(value)` return "Low", "Moderate", or "High" based on threshold constants.  `build_insight()` composes a multi-line insight string for the dashboard tile.  Thresholds are named constants defined once and documented in the report.

### Q: How are charts generated?
**A:** `charts.py` contains nine chart functions plus a donut chart, each using Matplotlib.  Each function takes pre-computed experiment data (dictionaries of averages, failure rates, histories) and returns a `Figure`.  The figure is embedded in the Results tab using `FigureCanvasTkAgg` and saved as a 200 dpi PNG using `save_chart()`.

### Q: How does the Compare Strategies view work?
**A:** The controller generates a fixed workload from the seed, then runs it under all four strategies by resetting the backend and replaying the workload for each.  It records OK count, failure counts, final stats, and average fragmentation.  The results are displayed in a 2×2 tile layout, each with a mini block grid and stats.  `best_strategy()` identifies the winner.

### Q: How do you handle long-running experiments?
**A:** Before starting, the UI sets a "Running..." status message and calls `update_idletasks()` to refresh the display.  The experiment runs synchronously (no threads) in a single call.  After completion, the status returns to "Ready" and the results are displayed.

### Q: What colour accessibility measures did you take?
**A:** All text meets WCAG AA contrast ratios against its background.  Focus highlights use a 3px ring in `#005F73`.  Every colour is paired with a label, value, pattern, or marker — colour is never the sole channel of information.  Hatch patterns distinguish bars, different line styles and markers distinguish strategies in line charts, and values are printed inside heat map cells.
