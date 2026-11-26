/*
 * cpp_bridge.cpp — Persistent JSON stdin/stdout bridge for M1–M4 C++.
 *
 * Reads single-line JSON commands from stdin and writes single-line
 * JSON responses to stdout. Calls M1, M2, M3, and M4 directly without
 * modifying any M1–M4 source files.
 *
 * Compile from frontend/:
 *   g++ -O2 -std=c++17 -o cpp_bridge.exe cpp_bridge.cpp
 *       ../backend/m1_core.cpp ../backend/m2_engine.cpp
 *       ../backend/m4_compaction.cpp -I../backend
 */

#include <iostream>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <cstdlib>
#include <cctype>

#include "storage.h"
#include "m3_strategies.h"

using namespace std;

// Global live Storage instance managed over the pipe.
static Storage* storage = nullptr;

// Escape special characters for safe JSON string output.
string json_escape(const string& s) {
    string out;
    out.reserve(s.size() + 4);
    for (char c : s) {
        if (c == '"')       out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else                out += c;
    }
    return out;
}

// Find the start of the value token for a given JSON object key.
size_t json_find_value(const string& json, const string& key) {
    string needle = "\"" + key + "\"";
    size_t pos = 0;
    while ((pos = json.find(needle, pos)) != string::npos) {
        bool left_ok = (pos == 0 || json[pos - 1] == '{' ||
                        json[pos - 1] == ',' || json[pos - 1] == ' ');
        size_t after = pos + needle.size();
        while (after < json.size() && (json[after] == ' ' || json[after] == '\t'))
            after++;
        if (left_ok && after < json.size() && json[after] == ':') {
            after++;
            while (after < json.size() && (json[after] == ' ' || json[after] == '\t'))
                after++;
            return after;
        }
        pos += needle.size();
    }
    return string::npos;
}

// Extract a string or primitive value for a given key.
string json_get_str(const string& json, const string& key) {
    size_t pos = json_find_value(json, key);
    if (pos == string::npos || pos >= json.size()) return "";
    if (json[pos] == '"') {
        pos++;
        string result;
        while (pos < json.size() && json[pos] != '"') {
            if (json[pos] == '\\' && pos + 1 < json.size()) {
                pos++;
                if (json[pos] == 'n') result += '\n';
                else if (json[pos] == 'r') result += '\r';
                else if (json[pos] == 't') result += '\t';
                else result += json[pos];
            } else {
                result += json[pos];
            }
            pos++;
        }
        return result;
    }
    string result;
    while (pos < json.size() && json[pos] != ',' &&
           json[pos] != '}' && json[pos] != ' ') {
        result += json[pos];
        pos++;
    }
    return result;
}

int json_get_int(const string& json, const string& key, int def = 0) {
    string val = json_get_str(json, key);
    return val.empty() ? def : atoi(val.c_str());
}

unsigned json_get_uint(const string& json, const string& key, unsigned def = 0) {
    string val = json_get_str(json, key);
    return val.empty() ? def : (unsigned)strtoul(val.c_str(), nullptr, 10);
}

bool json_get_bool(const string& json, const string& key, bool def = false) {
    string val = json_get_str(json, key);
    if (val == "true" || val == "1") return true;
    if (val == "false" || val == "0") return false;
    return def;
}

// Normalize UI or short strategy names to M3 keys.
string normalize_strategy(const string& name) {
    string s;
    for (char c : name) s += (char)tolower((unsigned char)c);
    if (s.find("first") == 0) return "first";
    if (s.find("next") == 0)  return "next";
    if (s.find("best") == 0)  return "best";
    if (s.find("worst") == 0) return "worst";
    return "first";
}

void write_stats_json(const Stats& s) {
    cout << "{\"free\":" << s.free
         << ",\"occupied\":" << s.occupied
         << ",\"segments\":" << s.segments
         << ",\"largest\":" << s.largest
         << ",\"ext_frag\":" << s.ext_frag
         << ",\"utilisation\":" << s.utilisation
         << ",\"avg_hole\":" << s.avg_hole << "}";
}

void write_segments_json(const vector<pair<int, int>>& segs) {
    cout << "[";
    for (size_t i = 0; i < segs.size(); i++) {
        if (i > 0) cout << ",";
        cout << "[" << segs[i].first << "," << segs[i].second << "]";
    }
    cout << "]";
}

void write_array_json(const vector<string>& arr) {
    cout << "[";
    for (size_t i = 0; i < arr.size(); i++) {
        if (i > 0) cout << ",";
        cout << "\"" << json_escape(arr[i]) << "\"";
    }
    cout << "]";
}

void send_error(const string& msg) {
    cout << "{\"ok\":false,\"error\":\"" << json_escape(msg) << "\"}\n" << flush;
}

void handle_init_or_reset(const string& line) {
    int def_n = storage ? storage->n : 100;
    int n = json_get_int(line, "n", def_n);
    if (storage != nullptr) delete storage;
    storage = new Storage(n);
    cout << "{\"ok\":true,\"n\":" << storage->n << "}\n" << flush;
}

void handle_allocate(const string& line) {
    if (!storage) { send_error("not_initialized"); return; }
    string pid = json_get_str(line, "pid");
    int size = json_get_int(line, "size");
    string strategy = json_get_str(line, "strategy");
    AllocResult r = storage->allocate(pid, size, strategy);
    cout << "{\"ok\":" << (r.ok ? "true" : "false")
         << ",\"start\":" << r.start
         << ",\"reason\":\"" << json_escape(r.reason) << "\"}\n" << flush;
}

void handle_release(const string& line) {
    if (!storage) { send_error("not_initialized"); return; }
    string pid = json_get_str(line, "pid");
    ReleaseResult r = storage->release(pid);
    cout << "{\"ok\":" << (r.ok ? "true" : "false")
         << ",\"reason\":\"" << json_escape(r.reason) << "\"}\n" << flush;
}

void handle_stats() {
    if (!storage) { send_error("not_initialized"); return; }
    write_stats_json(storage->stats());
    cout << "\n" << flush;
}

void handle_free_segments() {
    if (!storage) { send_error("not_initialized"); return; }
    cout << "{\"segments\":";
    write_segments_json(storage->free_segments());
    cout << "}\n" << flush;
}

void handle_compact() {
    if (!storage) { send_error("not_initialized"); return; }
    CompactionReport r = storage->compact();
    cout << "{\"before\":";
    write_stats_json(r.before);
    cout << ",\"after\":";
    write_stats_json(r.after);
    cout << ",\"segments_before\":" << r.segments_before
         << ",\"segments_after\":" << r.segments_after
         << ",\"moved_blocks\":" << r.moved_blocks << "}\n" << flush;
}

void handle_analyze_failure(const string& line) {
    if (!storage) { send_error("not_initialized"); return; }
    int size = json_get_int(line, "size");
    FailureAnalysis fa = storage->analyze_failure(size);
    cout << "{\"reason\":\"" << json_escape(fa.reason)
         << "\",\"explanation\":\"" << json_escape(fa.explanation)
         << "\",\"total_free\":" << fa.total_free
         << ",\"largest_hole\":" << fa.largest_hole << "}\n" << flush;
}

void handle_allocate_with_compaction(const string& line) {
    if (!storage) { send_error("not_initialized"); return; }
    string pid = json_get_str(line, "pid");
    int size = json_get_int(line, "size");
    string strategy = json_get_str(line, "strategy");
    AllocResult r = storage->allocate_with_compaction(pid, size, strategy);
    cout << "{\"ok\":" << (r.ok ? "true" : "false")
         << ",\"start\":" << r.start
         << ",\"reason\":\"" << json_escape(r.reason) << "\"}\n" << flush;
}

void handle_log() {
    if (!storage) { send_error("not_initialized"); return; }
    cout << "{\"log\":[";
    for (size_t i = 0; i < storage->log.size(); i++) {
        if (i > 0) cout << ",";
        const LogEntry& e = storage->log[i];
        cout << "{\"step\":" << e.step
             << ",\"op\":\"" << json_escape(e.op)
             << "\",\"pid\":\"" << json_escape(e.pid)
             << "\",\"size\":" << e.size
             << ",\"result\":\"" << json_escape(e.result)
             << "\",\"reason\":\"" << json_escape(e.reason) << "\"}";
    }
    cout << "]}\n" << flush;
}

void handle_export_log(const string& line) {
    if (!storage) { send_error("not_initialized"); return; }
    string filename = json_get_str(line, "filename");
    bool ok = storage->export_log_csv(filename);
    cout << "{\"ok\":" << (ok ? "true" : "false") << "}\n" << flush;
}

void handle_array() {
    if (!storage) { send_error("not_initialized"); return; }
    cout << "{\"array\":";
    write_array_json(storage->array);
    cout << "}\n" << flush;
}

void handle_table() {
    if (!storage) { send_error("not_initialized"); return; }
    cout << "{\"table\":{";
    bool first = true;
    for (const auto& kv : storage->table) {
        if (!first) cout << ",";
        first = false;
        cout << "\"" << json_escape(kv.first) << "\":["
             << kv.second.first << "," << kv.second.second << "]";
    }
    cout << "}}\n" << flush;
}

void handle_workload(const string& line) {
    int n = json_get_int(line, "n", 100);
    int n_ops = json_get_int(line, "ops", 300);
    unsigned seed = json_get_uint(line, "seed", 7);
    vector<Op> ops = generate_workload(n, n_ops, seed);
    cout << "{\"ops\":[";
    for (size_t i = 0; i < ops.size(); i++) {
        if (i > 0) cout << ",";
        cout << "[" << (ops[i].is_alloc ? 1 : 0) << ",\""
             << json_escape(ops[i].pid) << "\"," << ops[i].size << "]";
    }
    cout << "]}\n" << flush;
}

void handle_experiment(const string& line) {
    int n = json_get_int(line, "n", 100);
    int n_ops = json_get_int(line, "ops", 300);
    unsigned seed = json_get_uint(line, "seed", 7);
    string strategy = normalize_strategy(json_get_str(line, "strategy"));
    bool include_layout = json_get_bool(line, "include_layout", false);

    vector<Op> ops = generate_workload(n, n_ops, seed);
    Storage s(n);
    int last_pos = 0;
    int ok_count = 0, frag_fail = 0, nospace_fail = 0;
    double sum_frag = 0.0, sum_util = 0.0;
    vector<double> frag_hist(ops.size(), 0.0);

    auto t0 = chrono::steady_clock::now();
    for (size_t i = 0; i < ops.size(); i++) {
        if (ops[i].is_alloc) {
            string check = s.validate(ops[i].pid, ops[i].size);
            if (check != "OK") {
                if (check == "NO_SPACE") nospace_fail++;
            } else {
                FreeNode* hole = find_hole(s.free_head, ops[i].size, strategy, last_pos);
                if (hole == nullptr) {
                    if (ops[i].size > s.count_free()) nospace_fail++;
                    else frag_fail++;
                } else {
                    int start = hole->start;
                    for (int k = start; k < start + ops[i].size; k++)
                        s.array[k] = ops[i].pid;
                    s.table[ops[i].pid] = make_pair(start, ops[i].size);
                    s.rebuild_free_list();
                    last_pos = start + ops[i].size;
                    if (last_pos >= s.n) last_pos = 0;
                    ok_count++;
                }
            }
        } else {
            s.release(ops[i].pid);
        }
        Stats st = s.stats();
        double frag = (st.free == 0) ? 0.0 : (1.0 - (double)st.largest / st.free) * 100.0;
        double util = (n > 0) ? ((double)st.occupied / n * 100.0) : 0.0;
        sum_frag += frag;
        sum_util += util;
        frag_hist[i] = frag;
    }
    auto t1 = chrono::steady_clock::now();

    Stats fin = s.stats();
    double denom = ops.empty() ? 1.0 : (double)ops.size();
    double time_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "{\"n\":" << n
         << ",\"ops\":" << n_ops
         << ",\"strategy\":\"" << json_escape(strategy) << "\""
         << ",\"ok\":" << ok_count
         << ",\"frag_fail\":" << frag_fail
         << ",\"nospace_fail\":" << nospace_fail
         << ",\"avg_frag\":" << (sum_frag / denom)
         << ",\"avg_util\":" << (sum_util / denom)
         << ",\"segments\":" << fin.segments
         << ",\"largest\":" << fin.largest
         << ",\"time_ms\":" << time_ms
         << ",\"frag_history\":[";
    for (size_t i = 0; i < frag_hist.size(); i++) {
        if (i > 0) cout << ",";
        cout << frag_hist[i];
    }
    cout << "]";
    if (include_layout) {
        cout << ",\"array\":";
        write_array_json(s.array);
        cout << ",\"free_segments\":";
        write_segments_json(s.free_segments());
    }
    cout << "}\n" << flush;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    cout << "{\"ready\":true}\n" << flush;

    string line;
    while (getline(cin, line)) {
        if (line.empty()) continue;
        string cmd = json_get_str(line, "cmd");
        if (cmd == "init" || cmd == "reset") handle_init_or_reset(line);
        else if (cmd == "allocate") handle_allocate(line);
        else if (cmd == "release") handle_release(line);
        else if (cmd == "stats") handle_stats();
        else if (cmd == "free_segments") handle_free_segments();
        else if (cmd == "compact") handle_compact();
        else if (cmd == "analyze_failure") handle_analyze_failure(line);
        else if (cmd == "allocate_with_compaction") handle_allocate_with_compaction(line);
        else if (cmd == "log") handle_log();
        else if (cmd == "export_log") handle_export_log(line);
        else if (cmd == "array") handle_array();
        else if (cmd == "table") handle_table();
        else if (cmd == "workload") handle_workload(line);
        else if (cmd == "experiment") handle_experiment(line);
        else if (cmd == "quit") break;
        else send_error("unknown_command: " + cmd);
    }

    if (storage) delete storage;
    return 0;
}
