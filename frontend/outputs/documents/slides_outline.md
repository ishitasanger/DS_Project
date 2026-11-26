# Project 10 — Presentation Slides Outline

## Slide 1: Title
**Title:** Virtual Storage Allocation and Fragmentation Simulator  
**Subtitle:** Project 10 — Data Structures  
**Visual:** Dashboard screenshot (`Sample data` / `Live`)  
**Notes:** Introduce team M1–M5 and project scope.

## Slide 2: Problem Statement
**Title:** The External Fragmentation Problem  
**Content:**
- Contiguous requests leave scattered free holes over allocate/release cycles
- Requests can fail with plenty of total free space remaining
- High fragmentation defined across code, UI, and report as `>= 40%`

## Slide 3: Data Structures
**Title:** Array + Singly Linked Free List  
**Content:**
- **Array (`vector<string>`):** O(1) block ownership lookup, direct 1-to-1 BlockGrid mapping
- **Free List (`FreeNode*`):** O(S) search over holes only (`start, size, next`)
- Adjacent holes merge automatically in O(N) via `rebuild_free_list()`
**Visual:** Light-theme Fig 1 (`architecture_audit_and_diagrams.md`)

## Slide 4: Architecture & C++ ↔ Python Integration
**Title:** Modular 5-Package Design Connected via C++ Bridge  
**Content:**
- M1 Core · M2 Engine · M3 Strategies · M4 Compaction (all compiled in C++17)
- `backend_adapter.py` + `cpp_bridge.exe` communicate over JSON stdin/stdout pipes
- Zero Tkinter in backend; zero core logic duplicated in UI
**Visual:** Light-theme Fig 2 allocation flow

## Slide 5: Live Demo Flow
**Title:** Interactive Workflow (`python main.py`)  
**Content:**
1. Launch on 100-block sample state (`93` occupied, `7` free, `57.1%` High)
2. Attempt `allocate("P8", 5)` -> triggers `FRAGMENTATION`, opens Failure Analysis
3. Inspect fit table + 4-line explanation -> click **Run Compaction and Retry**
4. Compare all 4 strategies side-by-side and run 3-size C++ experiments

## Slide 6: Advancements A1–A2
**Title:** Four Strategies & Live Analytics  
**Content:**
- **A1:** First Fit, Next Fit, Best Fit, Worst Fit in selector & 2×2 comparison tiles (with free-segment size bars)
- **A2:** External fragmentation %, utilisation (+ occupied/free counts), largest hole, free segments + `dashboard_analytics.py` rules (`<20` Low, `20–<40` Moderate, `>=40` High)
**Visual:** Strategy comparison screenshot + metric cards

## Slide 7: Advancements A3–A4
**Title:** Failure Classification & Compaction  
**Content:**
- **A3:** `NO_SPACE` vs. `FRAGMENTATION` classifier with segment fit checks and 4-line explanation
- **A4:** One-click left-shift compaction with before/after grids and automatic retry (`allocate_with_compaction`)
**Visual:** Failure analysis & Compaction before/after screenshots

## Slide 8: Advancements A5–A6
**Title:** Light Bento Dashboard & Seeded C++ Workloads  
**Content:**
- **A5:** Light Executive Dashboard (`#FBF8CC` canvas, `#FFFFFF` rounded tiles, `#001219`→`#005F73` hero gradient, accessibility swatches & arrow-key grid navigation)
- **A6:** M3 `std::mt19937` workload generator (`seed=7`), same workload for all strategies

## Slide 9: Advancements A7–A8
**Title:** Matplotlib Charts & Event Log CSV  
**Content:**
- **A7:** 9 Matplotlib chart types + heat maps embedded in Results tab and saved at 200 dpi PNG
- **A8:** Every operation logged with step, op, PID, size, result, reason + C++ CSV export

## Slide 10: Experimental Charts
**Title:** Strategy Comparison Visuals (`seed=7`)  
**Content:**
- Grouped bars cleanly separate Best Fit (`15.4% / 39.8% / 58.8%`) from Worst Fit (`33.3% / 56.5% / 73.0%`)
- Heat maps colour-code project thresholds across `N = 100, 1000, 5000`
**Visual:** `1_avg_ext_fragmentation.png`, `7_heatmap_avg_frag.png`

## Slide 11: Measured Results & Time Growth
**Title:** Experimental Findings (Own C++ Runs)  
**Content:**
- Best Fit wins on fragmentation & utilisation at every size, at the cost of higher `NO_SPACE` rejections (`167` at N=5000)
- Worst Fit fragments fastest (`73.0%` at N=5000) despite only `6` `NO_SPACE` failures
- Runtime growth (`0.28ms -> 6.40ms -> 54.43ms`) grows sub-linearly vs `N×Ops` (`23.3×` vs `100×`, `8.5×` vs `16.7×`) due to sub-ms startup overhead at N=100 and higher early rejection skipping O(N) list rebuilds at N=5000

## Slide 12: Verification & Tests
**Title:** All Assigned & Cross-Module Tests Pass  
**Content:**
- C++ M1–M4 unit tests (`T1–T14`, `S9-1..4`): 23 / 23 PASS
- Analytics (`44`), Charts (`20`), UI Smoke (`26`), Python↔C++ Integration (`25`): 115 / 115 PASS

## Slide 13: Member Contributions
**Title:** Five-Member Division  
**Content:**
| Member | Focus |
|---|---|
| M1 | Array, linked free list, stats |
| M2 | Validate, allocate, release, event log & CSV |
| M3 | 4 strategies, seeded workload, experiment runner |
| M4 | Failure classifier, compaction, auto-retry |
| M5 | Light Tkinter dashboard, analytics, 9 charts, C++ bridge, docs |

## Slide 14: Q&A
**Title:** Questions?  
**Content:** Live application demo & viva walkthrough ready.
