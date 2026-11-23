#pragma once
#include <string>
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
    Storage(int n);                                               // M1 fills this
    AllocResult allocate(string pid, int size, string strategy);  // you (M2)
    ReleaseResult release(string pid);                            // you (M2)
};
