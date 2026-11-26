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
// Adds one record to the event log.
void Storage::add_log(string op, string pid, int size, string result, string reason) {
    LogEntry e;
    e.step = log.size() + 1;   // step number = records so far + 1
    e.op = op;
    e.pid = pid;
    e.size = size;
    e.result = result;
    e.reason = reason;
    log.push_back(e);
}

AllocResult Storage::allocate(string pid, int size, string strategy) {
    // 1. validate
    string check = validate(pid, size);
    if (check != "OK") {
        add_log("ALLOCATE", pid, size, "FAIL", check);
        return {false, -1, check};
    }
    // 2. find a hole
    FreeNode* hole = find_first_fit(size);
    // 3. no hole: find out why
    if (hole == nullptr) {
        string why = "FRAGMENTATION";
        if (size > count_free()) {
            why = "NO_SPACE";
        }
        add_log("ALLOCATE", pid, size, "FAIL", why);
        return {false, -1, why};
    }
    // 4. place the process
    int start = hole->start;          // save it BEFORE rebuilding
    for (int i = start; i < start + size; i++) {
        array[i] = pid;
    }
    table[pid] = make_pair(start, size);
    rebuild_free_list();
    add_log("ALLOCATE", pid, size, "OK", "OK");
    return {true, start, "OK"};
}

ReleaseResult Storage::release(string pid) {
    // 1. the process must exist
    if (table.count(pid) == 0) {
        add_log("RELEASE", pid, 0, "FAIL", "UNKNOWN_PID");
        return {false, "UNKNOWN_PID"};
    }
    // 2. read where it is stored
    int start = table[pid].first;
    int size = table[pid].second;
    // 3. mark its blocks as free
    for (int i = start; i < start + size; i++) {
        array[i] = "";
    }
    // 4. remove it from the table
    table.erase(pid);
    // 5. rebuild the list (neighbouring holes merge)
    rebuild_free_list();
    add_log("RELEASE", pid, size, "OK", "OK");
    return {true, "OK"};
}

