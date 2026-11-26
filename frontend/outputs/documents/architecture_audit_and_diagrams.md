# Architecture Audit, Interface Mapping & Light-Theme Diagrams — Project 10

## 1. Stage 1 Interface Audit & Mapping Table

Every frontend data need maps strictly to M1–M4's C++ `Storage` contract via `backend_adapter.py` and `cpp_bridge.exe`.

| UI Need | Frontend Call (`backend_adapter.py`) | C++ Backend Target (M1–M4) | Return Type |
|---|---|---|---|
| Initialise storage | `BackendAdapter(total_blocks)` | `Storage::Storage(int total_blocks)` (M1) | `BackendAdapter` |
| Read block array | `backend.array` | `Storage::array` (`vector<string>`) (M1) | `list[str]` |
| Read process table | `backend.table` | `Storage::table` (`map<string, pair<int,int>>`) (M2) | `dict[str, (int, int)]` |
| Live statistics | `backend.stats()` | `Storage::stats()` (`Stats`) (M1) | `BackendStats` |
| Free segments | `backend.free_segments()` | `Storage::free_segments()` (M1) | `list[(int, int)]` |
| Allocate blocks | `backend.allocate(pid, size, strategy)` | `Storage::allocate(pid, size, strategy)` (M2 + M3) | `AllocResult` |
| Release process | `backend.release(pid)` | `Storage::release(pid)` (M2) | `ReleaseResult` |
| Event log read | `backend.get_log()` | `Storage::log` (`vector<LogEntry>`) (M2) | `list[LogEntry]` |
| Event log export | `backend.export_log_csv(filename)` | `Storage::export_log_csv(filename)` (M2) | `bool` |
| Strategy lookup | (called inside `Storage::allocate`) | `find_hole(...)` in `m3_strategies.h` (M3) | `FreeNode*` |
| Seeded workload | `backend.generate_workload(n, ops, seed)` | `generate_workload(n, ops, seed)` (M3) | `list[(op, pid, size)]` |
| Experiment suite | `backend.run_experiment(n, ops, seed, strat)` | M3 `generate_workload` + `alloc_with_strategy` + `stats` | `dict` |
| Failure classifier | `backend.analyze_failure(request_size)` | `Storage::analyze_failure(request_size)` (M4) | `FailureAnalysis` |
| Defragmentation | `backend.compact()` | `Storage::compact()` (M4) | `CompactionReport` |
| Auto-retry | `backend.allocate_with_compaction(pid, sz, st)` | `Storage::allocate_with_compaction(...)` (M4) | `AllocResult` |

---

## 2. Contract vs. Code Mismatch Log (M1–M4 Untouched)

Per M5 boundaries, M1–M4 files were **never edited**. All mismatches between the blueprint prototype specification and actual M1–M4 C++ code are bridged cleanly in `cpp_bridge.cpp` and `backend_adapter.py`:

| # | Owner | Blueprint Contract | Actual M1–M4 C++ Implementation | Resolution in Bridge |
|---|---|---|---|---|
| 1 | M1 | `stats()` returns Python `dict` | Returns C++ `Stats` struct with 7 fields (`free`, `occupied`, `segments`, `largest`, `ext_frag`, `utilisation`, `avg_hole`) | `cpp_bridge.cpp` serialises all 7 fields as JSON; `backend_adapter.py` exposes `BackendStats` attributes |
| 2 | M1 | `Storage(n)` array of zeros | `vector<string> array(n, "")` (`""` = free, PID string = occupied) | UI & bridge treat `""` as free block and non-empty string as PID |
| 3 | M1/M5 | Main screen starts on sample snapshot (100 blocks, 7 free, 4 segments) | `Storage(100)` starts empty (`free=100, occupied=0`) | `BackendAdapter(100)` replays real C++ `allocate`/`release` calls to build the 7-process sample state inside C++ (`is_sample=True` until first live user action) |
| 4 | M2 | `validate()` rejects empty PID | `Storage::validate(pid, size)` checks `size <= 0`, `size > n`, and `table.count(pid) > 0`; does not reject empty `pid` | `MainView` checks empty PID and non-numeric size before calling backend |
| 5 | M3 | `find_hole` takes `"first"`..`"worst"` | `m2_engine.cpp` normalises UI names (`"First Fit"` → `"first"`), whereas `m3_strategies.h`'s `find_hole` requires lowercase short keys | `cpp_bridge.cpp` calls `normalize_strategy()` before `find_hole` in experiments |
| 6 | M3 | C++ experiments standalone (`m3_experiments.cpp`) | `m3_experiments.cpp` has its own `main()` and writes `m3_results.csv` rather than a callable library | `cpp_bridge.cpp` exposes `workload` and `experiment` JSON commands calling M3's exact `m3_strategies.h` functions |
| 7 | M4/M1 | Frag history timeline for UI trend card | `Storage` holds current snapshot only, not historical `ext_frag` series | `BackendAdapter` appends `stats().ext_frag` after each operation; `run_experiment` records full `frag_history` per op |
| 8 | M5/M1–M4 | Cross-language invocation | Backend is compiled C++17; UI is Python/Tkinter | Persistent `cpp_bridge.exe` subprocess with single-line JSON stdin/stdout protocol |

---

## 3. Diagrams (Blueprint Figs 1 & 2, Light Theme)

### Figure 1 — Array (Ownership) and Linked List (Free Holes) Describe the Same Storage

Light-theme styling: `#FBF8CC` cream backdrop, `#FFFFFF` free cells with `#CA6702` amber border, process cells using `#005F73` / `#FFCFD2` / `#EE9B00`.

```mermaid
flowchart LR
    subgraph ARR["1D Array (array[0..19]) — O(1) Block Ownership Lookup"]
        direction LR
        B0["0-2: P1 (occupied)"]
        B3["3-4: Free (2)"]
        B5["5-8: P2 (occupied)"]
        B9["9-10: Free (2)"]
        B11["11-13: P3 (occupied)"]
        B14["14-19: Free (6)"]
        B0 --- B3 --- B5 --- B9 --- B11 --- B14
    end

    subgraph LL["Singly Linked List (free_head) — O(S) Free-Hole Search"]
        direction LR
        N1["FreeNode 1\nstart = 3, size = 2"] --> N2["FreeNode 2\nstart = 9, size = 2"]
        N2 --> N3["FreeNode 3\nstart = 14, size = 6"]
        N3 --> NULL["nullptr"]
    end

    B3 -.-> N1
    B9 -.-> N2
    B14 -.-> N3

    style ARR fill:#FFFFFF,stroke:#005F73,stroke-width:2px,color:#001219
    style LL fill:#FFFFFF,stroke:#CA6702,stroke-width:2px,color:#001219
    style B0 fill:#005F73,stroke:#001219,color:#FFFFFF
    style B5 fill:#FFCFD2,stroke:#001219,color:#001219
    style B11 fill:#EE9B00,stroke:#001219,color:#001219
    style B3 fill:#FFFFFF,stroke:#CA6702,stroke-width:2px,stroke-dasharray: 4 3,color:#001219
    style B9 fill:#FFFFFF,stroke:#CA6702,stroke-width:2px,stroke-dasharray: 4 3,color:#001219
    style B14 fill:#FFFFFF,stroke:#CA6702,stroke-width:2px,stroke-dasharray: 4 3,color:#001219
    style N1 fill:#FDE4CF,stroke:#CA6702,color:#001219
    style N2 fill:#FDE4CF,stroke:#CA6702,color:#001219
    style N3 fill:#FDE4CF,stroke:#CA6702,color:#001219
    style NULL fill:#E9D8A6,stroke:#475459,color:#001219
```

### Figure 2 — Linear Flow of One Allocation Request

```mermaid
flowchart TD
    S1["1. UI Input Check\nMainView validates non-empty PID\nand numeric integer size"] --> S2["2. Bridge Call (JSON over pipe)\nBackendAdapter -> cpp_bridge.exe -> Storage::allocate"]
    S2 --> S3["3. M2 Validate\nsize > 0? size <= N? PID unique?"]
    S3 -->|Invalid| RFAIL["Return FAIL\nINVALID_SIZE / NO_SPACE / DUPLICATE_PID\nAppend M2 Event Log"]
    S3 -->|Valid| S4["4. M3 Strategy Search (O(S))\nWalk free_head using First / Next / Best / Worst Fit"]
    S4 -->|hole == nullptr| S5{"count_free() < size?"}
    S5 -->|Yes| NOSP["Classify: NO_SPACE\nAppend FAIL log -> UI opens Failure Analysis"]
    S5 -->|No| FRAG["Classify: FRAGMENTATION\nAppend FAIL log -> UI opens Failure Analysis"]
    S4 -->|hole found| S6["5. Place & Rebuild (O(N))\nWrite pid to array[start..start+size-1]\nUpdate table[pid], last_pos\nrebuild_free_list() + add_log(OK)"]
    S6 --> S7["6. UI Refresh\nRedraw BlockGrid, Metric Cards,\nAnalytics Insight, Trend, Donut, Process Table, Log"]

    style S1 fill:#FFFFFF,stroke:#005F73,color:#001219
    style S2 fill:#90DBF4,stroke:#005F73,color:#001219
    style S3 fill:#FFFFFF,stroke:#005F73,color:#001219
    style S4 fill:#E9D8A6,stroke:#001219,color:#001219
    style S5 fill:#FDE4CF,stroke:#CA6702,color:#001219
    style S6 fill:#B9FBC0,stroke:#2E7D32,color:#001219
    style S7 fill:#FFFFFF,stroke:#005F73,color:#001219
    style RFAIL fill:#FFCFD2,stroke:#AE2012,color:#001219
    style NOSP fill:#A3C4F3,stroke:#005F73,color:#001219
    style FRAG fill:#FFCFD2,stroke:#AE2012,color:#001219
```
