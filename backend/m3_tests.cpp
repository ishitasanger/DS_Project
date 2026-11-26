// m3_tests.cpp  -  tests for M3
#include <iostream>
#include "m3_strategies.h"
using namespace std;

int main() {
    // T12: holes -> (start 0, size 4) and (start 6, size 8), request 3 blocks
    FreeNode* h2 = new FreeNode{6, 8, nullptr};
    FreeNode* h1 = new FreeNode{0, 4, h2};

    bool t12 = find_first_fit(h1, 3)->start == 0 &&
               find_best_fit(h1, 3)->start  == 0 &&
               find_worst_fit(h1, 3)->start == 6;
    cout << "T12 strategy placement differs: " << (t12 ? "PASS" : "FAIL") << endl;

    // Next fit: last allocation ended at block 5 -> should pick hole at 6
    cout << "Next fit starts from last position: "
         << (find_next_fit(h1, 3, 5)->start == 6 ? "PASS" : "FAIL") << endl;

    // No hole big enough -> nullptr
    cout << "Request too big returns none: "
         << (find_first_fit(h1, 20) == nullptr ? "PASS" : "FAIL") << endl;

    // Repeatability: same seed -> identical workload
    vector<Op> a = generate_workload(100, 300, 7);
    vector<Op> b = generate_workload(100, 300, 7);
    vector<Op> c = generate_workload(100, 300, 8);
    bool same = a.size() == b.size();
    for (size_t i = 0; same && i < a.size(); i++)
        same = a[i].is_alloc == b[i].is_alloc && a[i].pid == b[i].pid && a[i].size == b[i].size;
    cout << "Same seed gives same workload: " << (same ? "PASS" : "FAIL") << endl;

    bool diff = false;
    for (size_t i = 0; i < a.size(); i++)
        if (a[i].size != c[i].size || a[i].pid != c[i].pid) { diff = true; break; }
    cout << "Different seed gives different workload: " << (diff ? "PASS" : "FAIL") << endl;
    return 0;
}