// m3_section9_tests.cpp - extra tests for report Section 9 (S9-1 to S9-4)
// Uses M1's storage core and M2's engine. Compile with:
//   g++ -std=c++17 m1_core.cpp m2_engine.cpp m3_section9_tests.cpp -o m3_section9_tests.exe
#include <iostream>
#include "storage.h"
using namespace std;

void check(const string& name, bool passed) {
    cout << name << ": " << (passed ? "PASS" : "FAIL") << endl;
}

int main() {
    // S9-1: valid allocation on an empty storage of 20 blocks
    {
        Storage s(20);
        AllocResult a = s.allocate("P1", 5, "first");
        bool ok = a.ok && a.start == 0
               && s.array[0] == "P1" && s.array[4] == "P1" && s.array[5] == ""
               && s.table.count("P1") == 1
               && s.table["P1"].first == 0 && s.table["P1"].second == 5
               && s.stats().free == 15;
        check("S9-1 valid allocation", ok);
    }

    // S9-2: release frees the blocks and neighbouring holes merge
    {
        Storage s(20);
        s.allocate("P1", 5, "first");           // blocks 0-4
        s.allocate("P2", 5, "first");           // blocks 5-9
        ReleaseResult r1 = s.release("P1");     // holes: 0-4 and 10-19
        bool two_holes = (s.stats().segments == 2);
        ReleaseResult r2 = s.release("P2");     // everything free again, one hole
        Stats st = s.stats();
        bool ok = r1.ok && two_holes && r2.ok
               && st.segments == 1 && st.largest == 20
               && s.table.empty() && s.array[0] == "";
        check("S9-2 release and merge", ok);
    }

    // S9-3: insufficient space -> NO_SPACE (6 requested, only 4 free in total)
    {
        Storage s(10);
        s.allocate("P1", 6, "first");           // leaves 4 free
        AllocResult a = s.allocate("P2", 6, "first");
        check("S9-3 insufficient space", !a.ok && a.reason == "NO_SPACE");
    }

    // S9-4: fragmentation failure -> FRAGMENTATION
    // holes of size 2 and 3 (5 free in total), request 4
    {
        Storage s(10);
        s.allocate("P1", 2, "first");           // 0-1
        s.allocate("P2", 2, "first");           // 2-3
        s.allocate("P3", 3, "first");           // 4-6
        s.allocate("P4", 3, "first");           // 7-9
        s.release("P1");                        // hole 0-1 (size 2)
        s.release("P3");                        // hole 4-6 (size 3)
        bool setup = (s.count_free() == 5 && s.stats().segments == 2);
        AllocResult a = s.allocate("P5", 4, "first");
        check("S9-4 fragmentation failure", setup && !a.ok && a.reason == "FRAGMENTATION");
    }

    return 0;
}