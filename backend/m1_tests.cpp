#include "storage.h"
#include <iostream>
using namespace std;

void check(string name, bool cond) {
    cout << name << ": " << (cond ? "PASS" : "FAIL") << endl;
}

int main() {
    // T1 initial state
    Storage s(20);
    Stats a = s.stats();
    check("T1", a.free == 20 && a.segments == 1 && a.largest == 20);

    // T2 allocate whole storage (needs M2's allocate)
    Storage s2(20);
    s2.allocate("P1", 20, "first");
    Stats b = s2.stats();
    check("T2", b.free == 0 && b.segments == 0);

    // T5 smallest request
    Storage s3(20);
    AllocResult r = s3.allocate("P1", 1, "first");
    check("T5", r.start == 0 && s3.stats().free == 19);

    // T13 full -> release -> full
    Storage s4(20);
    s4.allocate("P1", 20, "first");
    s4.release("P1");
    AllocResult r2 = s4.allocate("P2", 20, "first");
    check("T13", r2.ok);
    return 0;
}