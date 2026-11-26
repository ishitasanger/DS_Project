#include <iostream>
#include "storage.h"

void check(string name, bool passed) {
    cout << name << ": " << (passed ? "PASS" : "FAIL") << endl;
}

// T3: request larger than storage -> NO_SPACE
void test_T3() {
    Storage s(20);
    AllocResult a = s.allocate("P-1", 25, "First Fit");
    check("T3", !a.ok && a.reason == "NO_SPACE");
}

// T4: zero and negative size -> INVALID_SIZE
void test_T4() {
    Storage s(20);
    AllocResult a = s.allocate("P-1", 0, "First Fit");
    AllocResult b = s.allocate("P-2", -3, "First Fit");
    check("T4", a.reason == "INVALID_SIZE" && b.reason == "INVALID_SIZE");
}

// T6: release unknown process -> UNKNOWN_PID
void test_T6() {
    Storage s(20);
    ReleaseResult r = s.release("P-9");
    check("T6", !r.ok && r.reason == "UNKNOWN_PID");
}

// T7: releasing the same process twice -> second one rejected
void test_T7() {
    Storage s(20);
    s.allocate("P-1", 5, "First Fit");
    ReleaseResult first = s.release("P-1");
    ReleaseResult second = s.release("P-1");
    check("T7", first.ok && !second.ok);
}

// T8: same process id twice -> DUPLICATE_PID
void test_T8() {
    Storage s(20);
    s.allocate("P-1", 5, "First Fit");
    AllocResult a = s.allocate("P-1", 2, "First Fit");
    check("T8", !a.ok && a.reason == "DUPLICATE_PID");
}

// T14: request on a full storage -> NO_SPACE
void test_T14() {
    Storage s(20);
    s.allocate("P-1", 20, "First Fit");
    AllocResult a = s.allocate("P-2", 1, "First Fit");
    check("T14", !a.ok && a.reason == "NO_SPACE");
}

int main() {
    test_T3();
    test_T4();
    test_T6();
    test_T7();
    test_T8();
    test_T14();
    return 0;
}