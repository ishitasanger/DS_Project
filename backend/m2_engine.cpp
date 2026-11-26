#include "storage.h"

// Checks the request. Returns "OK" if it is fine,
// otherwise returns the reason it is wrong.
string Storage::validate(string pid, int size) {
    // 1. size must be positive
    if (size <= 0) {
        return "INVALID_SIZE";
    }
    // 2. size cannot be bigger than the whole storage
    if (size > n) {
        return "NO_SPACE";
    }
    // 3. the process id must not already exist
    if (table.count(pid) > 0) {
        return "DUPLICATE_PID";
    }
    // everything is fine
    return "OK";
}

// TEMPORARY: returns the first hole that is big enough.
// M3 will replace this with First/Next/Best/Worst Fit.
FreeNode* Storage::find_first_fit(int size) {
    FreeNode* cur = free_head;
    while (cur != nullptr) {
        if (cur->size >= size) {
            return cur;
        }
        cur = cur->next;
    }
    return nullptr;   // no hole is big enough
}

// Adds up the sizes of all holes = total free blocks.
int Storage::count_free() {
    int total = 0;
    FreeNode* cur = free_head;
    while (cur != nullptr) {
        total += cur->size;
        cur = cur->next;
    }
    return total;
}

AllocResult Storage::allocate(string pid, int size, string strategy) {
    // 1. validate
    string check = validate(pid, size);
    if (check != "OK") {
        return {false, -1, check};
    }
    // 2. find a hole
    FreeNode* hole = find_first_fit(size);
    // 3. no hole: find out why
    if (hole == nullptr) {
        if (size > count_free()) {
            return {false, -1, "NO_SPACE"};
        }
        return {false, -1, "FRAGMENTATION"};
    }
    // 4. place the process
    int start = hole->start;          // save it BEFORE rebuilding
    for (int i = start; i < start + size; i++) {
        array[i] = pid;
    }
    table[pid] = make_pair(start, size);
    rebuild_free_list();
    return {true, start, "OK"};
}

ReleaseResult Storage::release(string pid) {
    return {false, "NOT_DONE"};   // real release comes in the next step
}
