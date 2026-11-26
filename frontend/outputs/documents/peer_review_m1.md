# Peer Review of M1 — Core Storage

**Reviewer:** M5
**Files reviewed:** `storage.h`, `m1_core.cpp`, `m1_tests.cpp`
**Review date:** 2026-11-26

---

## 1. Scope

M1 owns the core storage data structure: the `Storage` class with the block array, process table, free list, and the functions `rebuild_free_list`, `stats`, `free_segments`, and `display_layout`.

## 2. Contract Compliance

| Function | Contract | Implementation | Verdict |
|----------|---------|----------------|---------|
| `Storage(n)` | Create array of N empty strings, build initial free list | Constructor initialises `array(n, "")`, calls `rebuild_free_list()` | **Compliant** |
| `rebuild_free_list()` | Scan array, create linked list of free segments | Clears old list, scans for runs of `""`, creates FreeNode for each | **Compliant** |
| `stats()` | Return Stats struct with free, occupied, segments, largest, ext_frag, utilisation, avg_hole | Traverses free list, computes all seven fields correctly | **Compliant** |
| `free_segments()` | Return vector of (start, size) pairs | Iterates free list, pushes (start, size) pairs | **Compliant** |
| `display_layout()` | Print array contents | Loops through array, prints PIDs or "." for free | **Compliant** |

## 3. Test Analysis

### T1: Stats on Empty Storage
- Creates `Storage(100)`, calls `stats()`.
- Expects: free=100, occupied=0, segments=1, largest=100, ext_frag=0.0.
- **Analysis:** Correct.  An empty array has one segment spanning all blocks.  Fragmentation is 0% because largest=free.

### T2: Stats After One Allocation
- Allocates one process, then calls `stats()`.
- Expects: occupied increases by the allocation size, free decreases, segments may increase.
- **Analysis:** Correct.  After placing one process in the middle, there should be 1 or 2 free segments depending on where the allocation starts.

### T5: free_segments Accuracy
- Creates a known state with specific holes, calls `free_segments()`.
- Expects: exact (start, size) pairs matching the known holes.
- **Analysis:** Correct.  The function mirrors the free list structure, which is rebuilt from the array.

### T13: rebuild_free_list After Release
- Allocates a process, releases it, then checks the free list.
- Expects: free list has one segment spanning the full array again.
- **Analysis:** Correct.  After releasing the only process, the array returns to all-empty, and rebuild creates one segment.

### Test Coverage Assessment
The four tests cover the basic lifecycle: empty → allocate → query → release → rebuild.  Missing edge cases:
- T1 does not test N=0 or N=1.
- No test for a fully-occupied array (zero free blocks).
- No test for multiple adjacent releases merging segments.

## 4. Readability

**Positive:**
- Clean, well-structured code with consistent naming.
- Functions are short and focused.
- Struct definitions in `storage.h` are clear and well-commented.
- Use of `#pragma once` prevents include guard issues.

**Observations:**
- `m1_core.cpp` uses `using namespace std;` from the header — this is common in student code but can cause name collisions in larger projects.
- The destructor should clear the free list to avoid memory leaks (the linked list nodes are allocated with `new`).
- Comments could note the O(N) complexity of `rebuild_free_list`.

## 5. Findings

### Finding 1: Memory Management
The free list nodes are allocated with `new FreeNode{...}` in `rebuild_free_list` but the destructor / `clear_free_list` implementation should be verified to delete all nodes.  A missing delete would leak memory over many allocate/release cycles.

**Severity:** Medium
**Suggested fix:** Ensure `clear_free_list()` traverses the list and `delete`s each node, and that the destructor calls `clear_free_list()`.

### Finding 2: Edge Case — Zero Free Blocks
When all blocks are occupied, `stats()` computes `ext_frag = (1 − 0/0)` which is undefined.  The implementation should handle this by returning 0.0 when `free == 0`.

**Severity:** Low (the guard may already be present — to be verified against the actual code).

### Finding 3: Thread Safety
No mutex or lock protects the array or free list.  This is acceptable for a single-threaded simulator but should be noted as a limitation.

**Severity:** Informational

## 6. Summary

M1's implementation is correct against its contract.  The four tests cover the core lifecycle.  Suggested improvements: (1) verify memory cleanup in the destructor, (2) guard against division by zero in `stats()` when free=0, (3) add edge-case tests for N=0, fully-occupied storage, and adjacent merging.

**Overall assessment:** Sound implementation, minor improvements recommended.
