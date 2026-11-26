// m3_experiments.cpp - M3: experiment runner (3 input sizes x 4 strategies)
#include <iostream>
#include <iomanip>
#include <fstream>
#include <chrono>
#include <vector>
#include <string>
#include "storage.h"
#include "m3_strategies.h"
using namespace std;

// Same steps as M2's allocate(), but it really uses the chosen strategy.
// last_pos is only needed by Next Fit (where the last allocation ended).
AllocResult alloc_with_strategy(Storage& s, const string& pid, int size,
                                const string& strategy, int& last_pos) {
    string check = s.validate(pid, size);                 // 1. validate
    if (check != "OK") return {false, -1, check};

    FreeNode* hole = find_hole(s.free_head, size, strategy, last_pos);   // 2. find hole
    if (hole == nullptr) {                                // 3. classify failure
        string why = (size > s.count_free()) ? "NO_SPACE" : "FRAGMENTATION";
        return {false, -1, why};
    }
    int start = hole->start;                              // 4. place (save start BEFORE rebuild)
    for (int i = start; i < start + size; i++) s.array[i] = pid;
    s.table[pid] = make_pair(start, size);
    s.rebuild_free_list();
    last_pos = start + size;                              // remember for Next Fit
    if (last_pos >= s.n) last_pos = 0;
    return {true, start, "OK"};
}

struct Result {
    int n, ops;
    string strategy;
    int ok, frag_fail, nospace_fail;
    double avg_frag, avg_util;
    int final_segments, final_largest;
    double time_ms;
};

Result run_one(int n, int n_ops, unsigned seed, const string& strategy) {
    vector<Op> ops = generate_workload(n, n_ops, seed);   // same seed -> same ops
    Storage s(n);
    Result r = {n, n_ops, strategy, 0, 0, 0, 0.0, 0.0, 0, 0, 0.0};
    int last_pos = 0;
    double sum_frag = 0, sum_util = 0;

    auto t0 = chrono::steady_clock::now();
    for (size_t i = 0; i < ops.size(); i++) {
        if (ops[i].is_alloc) {
            AllocResult a = alloc_with_strategy(s, ops[i].pid, ops[i].size, strategy, last_pos);
            if (a.ok) r.ok++;
            else if (a.reason == "FRAGMENTATION") r.frag_fail++;
            else if (a.reason == "NO_SPACE") r.nospace_fail++;
        } else {
            s.release(ops[i].pid);   // if that alloc had failed earlier, this is just ignored
        }
        // metrics after every operation
        Stats st = s.stats();
        double frag = (st.free == 0) ? 0.0 : (1.0 - (double)st.largest / st.free) * 100.0;
        double util = (double)st.occupied / n * 100.0;
        sum_frag += frag;
        sum_util += util;
    }
    auto t1 = chrono::steady_clock::now();

    Stats fin = s.stats();
    r.avg_frag = sum_frag / ops.size();
    r.avg_util = sum_util / ops.size();
    r.final_segments = fin.segments;
    r.final_largest = fin.largest;
    r.time_ms = chrono::duration<double, milli>(t1 - t0).count();
    return r;
}

int main() {
    int sizes[3]  = {100, 1000, 5000};
    int opsn[3]   = {300, 3000, 10000};
    string strategies[4] = {"first", "next", "best", "worst"};
    unsigned seed = 7;

    ofstream csv("m3_results.csv");
    csv << "N,Ops,Strategy,AllocOK,FailFrag,FailNoSpace,AvgExtFrag%,AvgUtil%,FinalSegments,FinalLargest,TimeMs\n";

    cout << left << setw(6) << "N" << setw(7) << "Ops" << setw(8) << "Strat"
         << setw(8) << "OK" << setw(9) << "FailFrag" << setw(9) << "FailNoSp"
         << setw(10) << "AvgFrag%" << setw(9) << "AvgUtil%"
         << setw(6) << "Seg" << setw(8) << "Largest" << "Time(ms)\n";

    for (int k = 0; k < 3; k++) {
        for (int j = 0; j < 4; j++) {
            Result r = run_one(sizes[k], opsn[k], seed, strategies[j]);
            cout << left << fixed << setprecision(1)
                 << setw(6) << r.n << setw(7) << r.ops << setw(8) << r.strategy
                 << setw(8) << r.ok << setw(9) << r.frag_fail << setw(9) << r.nospace_fail
                 << setw(10) << r.avg_frag << setw(9) << r.avg_util
                 << setw(6) << r.final_segments << setw(8) << r.final_largest
                 << r.time_ms << "\n";
            csv << r.n << "," << r.ops << "," << r.strategy << "," << r.ok << ","
                << r.frag_fail << "," << r.nospace_fail << "," << r.avg_frag << ","
                << r.avg_util << "," << r.final_segments << "," << r.final_largest << ","
                << r.time_ms << "\n";
        }
        cout << "\n";
    }

    // Repeatability: same seed twice must give identical numbers
    Result a = run_one(100, 300, seed, "best");
    Result b = run_one(100, 300, seed, "best");
    bool same = a.ok == b.ok && a.frag_fail == b.frag_fail && a.nospace_fail == b.nospace_fail
             && a.final_segments == b.final_segments && a.final_largest == b.final_largest;
    cout << "Repeatability (same seed, same result): " << (same ? "PASS" : "FAIL") << endl;
    cout << "Results also saved to m3_results.csv" << endl;
    return 0;
}