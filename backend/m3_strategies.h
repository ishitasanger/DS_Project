// m3_strategies.h  -  M3: allocation strategies + seeded workload generator
#ifndef M3_STRATEGIES_H
#define M3_STRATEGIES_H

#include <string>
#include <vector>
#include <random>
#include "storage.h"   // gives us FreeNode {start, size, next}

// ---------- A1: four strategies (same loop, different rule) ----------

// First Fit: take the FIRST hole that is big enough
inline FreeNode* find_first_fit(FreeNode* head, int size) {
    for (FreeNode* cur = head; cur != nullptr; cur = cur->next) {
        if (cur->size >= size) return cur;
    }
    return nullptr;
}

// Best Fit: take the SMALLEST hole that is big enough
inline FreeNode* find_best_fit(FreeNode* head, int size) {
    FreeNode* chosen = nullptr;
    for (FreeNode* cur = head; cur != nullptr; cur = cur->next) {
        if (cur->size >= size && (chosen == nullptr || cur->size < chosen->size))
            chosen = cur;
    }
    return chosen;
}

// Worst Fit: take the LARGEST hole that is big enough
inline FreeNode* find_worst_fit(FreeNode* head, int size) {
    FreeNode* chosen = nullptr;
    for (FreeNode* cur = head; cur != nullptr; cur = cur->next) {
        if (cur->size >= size && (chosen == nullptr || cur->size > chosen->size))
            chosen = cur;
    }
    return chosen;
}

// Next Fit: like First Fit, but start searching where the LAST allocation ended.
// last_pos = block index where the previous allocation ended (caller keeps it).
inline FreeNode* find_next_fit(FreeNode* head, int size, int last_pos) {
    for (FreeNode* cur = head; cur != nullptr; cur = cur->next)       // pass 1: from last_pos to end
        if (cur->start >= last_pos && cur->size >= size) return cur;
    for (FreeNode* cur = head; cur != nullptr; cur = cur->next)       // pass 2: wrap around to start
        if (cur->start < last_pos && cur->size >= size) return cur;
    return nullptr;
}

// One function that picks the right strategy. Returns nullptr if no hole fits.
inline FreeNode* find_hole(FreeNode* head, int size, const std::string& strategy, int last_pos = 0) {
    if (strategy == "first") return find_first_fit(head, size);
    if (strategy == "best")  return find_best_fit(head, size);
    if (strategy == "worst") return find_worst_fit(head, size);
    if (strategy == "next")  return find_next_fit(head, size, last_pos);
    return nullptr;
}

// ---------- A6: seeded workload generator ----------

struct Op {
    bool is_alloc;      // true = allocate, false = release
    std::string pid;    // e.g. "P1"
    int size;           // only used for allocate
};

// Same seed -> exactly the same list of operations (that's why comparisons are fair).
inline std::vector<Op> generate_workload(int n_blocks, int n_ops, unsigned seed) {
    std::mt19937 rng(seed);                         // seeded random generator
    int max_size = n_blocks / 10;                   // request size: 1 to 10% of N
    if (max_size < 1) max_size = 1;

    std::vector<Op> ops;
    std::vector<std::string> issued;                // pids allocated so far, not yet released
    int next_id = 1;

    for (int i = 0; i < n_ops; i++) {
        bool do_alloc = (rng() % 2 == 0) || issued.empty();   // 50/50 mix
        if (do_alloc) {
            std::string pid = "P" + std::to_string(next_id++);
            int size = 1 + (int)(rng() % max_size);
            ops.push_back({true, pid, size});
            issued.push_back(pid);
        } else {
            int idx = (int)(rng() % issued.size());
            ops.push_back({false, issued[idx], 0});
            issued.erase(issued.begin() + idx);
        }
    }
    return ops;
}

#endif