#pragma once
#include <string>
#include <map>
#include <utility>
using namespace std;

struct AllocResult {
    bool ok;
    int start;
    string reason;
};

struct ReleaseResult {
    bool ok;
    string reason;
};

class Storage {
public:
    int n;                               // total blocks
    map<string, pair<int,int>> table;    // pid -> (start, size)

    Storage(int n);                                               // M1 fills this
    string validate(string pid, int size);                        // M2
    AllocResult allocate(string pid, int size, string strategy);  // M2
    ReleaseResult release(string pid);                            // M2
};
