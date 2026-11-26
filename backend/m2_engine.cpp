#include "storage.h"
#include "m3_strategies.h"
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
// Turns names like "First Fit" or "Best Fit" into M3's names:
// "first", "next", "best", "worst". Unknown names become "first".
string strategy_key(string name) {
    string s = "";
    for (int i = 0; i < (int)name.size(); i++) {
        s += tolower(name[i]);
    }
    if (s.find("first") == 0) return "first";
    if (s.find("next") == 0)  return "next";
    if (s.find("best") == 0)  return "best";
    if (s.find("worst") == 0) return "worst";
    return "first";
}

AllocResult Storage::allocate(string pid, int size, string strategy) {
    // 1. validate
    string check = validate(pid, size);
    if (check != "OK") {
        add_log("ALLOCATE", pid, size, "FAIL", check);
        return {false, -1, check};
    }
    // 2. find a hole
        FreeNode* hole = find_hole(free_head, size, strategy_key(strategy), last_pos);
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
    last_pos = start + size;          // Next Fit starts from here next time
    if (last_pos >= n) {
        last_pos = 0;
    }
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
// Saves the event log to a CSV file. Returns true if it worked.
bool Storage::export_log_csv(string filename) {
    ofstream out(filename);
    if (!out.is_open()) {
        return false;   // file could not be created
    }
    // header row
    out << "step,operation,pid,size,result,reason" << endl;
    // one row per log record
    for (int i = 0; i < (int)log.size(); i++) {
        LogEntry e = log[i];
        out << e.step << "," << e.op << "," << e.pid << ","
            << e.size << "," << e.result << "," << e.reason << endl;
    }
    out.close();
    return true;
}

