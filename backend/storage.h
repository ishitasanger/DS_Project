
#pragma once
#include <string>
#include <map>
#include <vector>
#include <utility>
#include <fstream>
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
// M2: one record of the event log
struct LogEntry {
    int step;
    string op;
    string pid;
    int size;
    string result;
    string reason;
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
    FreeNode* find_first_fit(int size);   // M2 temporary, M3 will replace
    int count_free();    
    vector<LogEntry> log;                                                          // M2
    void add_log(string op, string pid, int size, string result, string reason);   // M2
    bool export_log_csv(string filename);                                          // M2
};
