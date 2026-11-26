#include "storage.h"
#include <iostream>
using namespace std;

static void check_m4(const string& name, bool pass) {
    cout << name << ": " << (pass ? "PASS" : "FAIL") << endl;
}

// T9: total free >= request, but largest hole < request => FRAGMENTATION.
void test_T9_failure_classification() {
    Storage s(12);
    s.allocate("P1", 2, "First Fit");
    s.allocate("P2", 2, "First Fit");
    s.allocate("P3", 2, "First Fit");
    s.allocate("P4", 2, "First Fit");
    s.release("P1");
    s.release("P3");
    FailureAnalysis f = s.analyze_failure(5); // 8 free, largest hole 4
    check_m4("T9", f.reason == "FRAGMENTATION" &&
             f.total_free >= 5 && f.largest_hole < 5);
}

// T10: compaction packs allocated blocks and leaves one free segment.
void test_T10_compaction() {
    Storage s(12);
    s.allocate("P1", 3, "First Fit");
    s.allocate("P2", 2, "First Fit");
    s.allocate("P3", 2, "First Fit");
    s.release("P2");
    CompactionReport r = s.compact();
    auto segments = s.free_segments();
    bool one_hole = segments.size() == 1 && segments[0].second == 7;
    bool table_ok = s.table["P1"].first == 0 && s.table["P3"].first == 3;
    check_m4("T10", one_hole && table_ok &&
             r.segments_after == 1 && r.after.largest == 7);
}

// T11: fragmentation triggers compaction and automatic retry.
void test_T11_auto_retry() {
    Storage s(12);
    s.allocate("P1", 3, "First Fit");
    s.allocate("P2", 2, "First Fit");
    s.allocate("P3", 3, "First Fit");
    s.allocate("P4", 4, "First Fit");
    s.release("P2");
    s.release("P4");
    // 6 free blocks total, largest hole is 4; request 5 is fragmented.
    FailureAnalysis before = s.analyze_failure(5);
    AllocResult r = s.allocate_with_compaction("P5", 5, "First Fit");
    check_m4("T11", before.reason == "FRAGMENTATION" &&
             r.ok && s.table.count("P5") == 1);
}

int main() {
    test_T9_failure_classification();
    test_T10_compaction();
    test_T11_auto_retry();
    return 0;
}
