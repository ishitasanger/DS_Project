#pragma once
#include <string>
#include <map>
#include <vector>
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

// M1: one node of the free list = one hole
struct FreeNode {
    int start;
    int size;
    FreeNode* next;
};

// M1: result of stats()
struct Stats {
    int free;
    int occupied;
    int segments;
    int largest;
    double ext_frag;
    double utilisation;
    double avg_hole;
};

class Storage {
public:
    int n;                               // M2
    map<string, pair<int,int>> table;    // M2

    // M1
    vector<string> array;                // "" = free, otherwise pid
    FreeNode* free_head;

    Storage(int total_blocks);
    ~Storage();
    Storage(const Storage&) = delete;
    Storage& operator=(const Storage&) = delete;

    void rebuild_free_list();
    void clear_free_list();
    void display_layout();
    Stats stats();
    vector<pair<int,int>> free_segments();

    // M2
    string validate(string pid, int size);
    AllocResult allocate(string pid, int size, string strategy);
    ReleaseResult release(string pid);
};