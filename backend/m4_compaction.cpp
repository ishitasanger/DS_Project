#include "storage.h"
#include <algorithm>
#include <sstream>

FailureAnalysis Storage::analyze_failure(int request_size) {
    FailureAnalysis result{};
    result.total_free = count_free();
    Stats current = stats();
    result.largest_hole = current.largest;

    if (request_size <= 0) {
        result.reason = "INVALID_SIZE";
        result.explanation =
            "The requested block count must be positive.\n"
            "A zero or negative request is not a valid allocation.\n"
            "No storage was changed.\n"
            "Please enter a positive size.";
    } else if (request_size > n || result.total_free < request_size) {
        result.reason = "NO_SPACE";
        result.explanation =
            "The total free space is smaller than the request.\n"
            "Free blocks available: " + std::to_string(result.total_free) + ".\n"
            "Blocks requested: " + std::to_string(request_size) + ".\n"
            "Compaction cannot create additional free space.";
    } else if (result.largest_hole < request_size) {
        result.reason = "FRAGMENTATION";
        result.explanation =
            "Enough free blocks exist in total, but they are split into holes.\n"
            "Total free blocks: " + std::to_string(result.total_free) + ".\n"
            "Largest continuous hole: " + std::to_string(result.largest_hole) + ".\n"
            "Compaction can merge the holes into one larger free segment.";
    } else {
        result.reason = "ALLOCATABLE";
        result.explanation =
            "A continuous free segment is large enough for this request.\n"
            "Total free blocks: " + std::to_string(result.total_free) + ".\n"
            "Largest continuous hole: " + std::to_string(result.largest_hole) + ".\n"
            "The request should be allocatable with a suitable strategy.";
    }
    return result;
}

CompactionReport Storage::compact() {
    CompactionReport report{};
    report.before = stats();
    report.segments_before = static_cast<int>(free_segments().size());
    report.moved_blocks = 0;

    // Scan the original layout from left to right, preserving process order.
    int read_pos = 0;
    int write_pos = 0;

    while (read_pos < n) {
        if (array[read_pos].empty()) {
            ++read_pos;
            continue;
        }

        const string pid = array[read_pos];
        auto table_it = table.find(pid);

        // The table is the authoritative process-size record.
        // If inconsistent, avoid out-of-bounds writes and stop safely.
        if (table_it == table.end() || table_it->second.second <= 0) {
            break;
        }

        const int process_size = table_it->second.second;
        const int old_start = read_pos;

        if (old_start != write_pos) {
            // Destination is always to the left, so writing forward is safe.
            for (int k = 0; k < process_size; ++k) {
                array[write_pos + k] = pid;
            }

            // Clear only the old portion not covered by the new destination.
            int clear_start = max(old_start, write_pos + process_size);
            for (int k = clear_start; k < old_start + process_size; ++k) {
                array[k].clear();
            }

            table_it->second.first = write_pos;
            report.moved_blocks += process_size;
        }

        write_pos += process_size;
        read_pos = old_start + process_size;
    }

    // Everything after the packed processes is one continuous free area.
    for (int i = write_pos; i < n; ++i) {
        array[i].clear();
    }

    rebuild_free_list();
    report.after = stats();
    report.segments_after = static_cast<int>(free_segments().size());

    add_log("COMPACT", "", report.moved_blocks, "OK", "COMPACTED");
    return report;
}

AllocResult Storage::allocate_with_compaction(string pid, int size, string strategy) {
    AllocResult first = allocate(pid, size, strategy);
    if (first.ok || first.reason != "FRAGMENTATION") {
        return first;
    }

    compact();

    // Retry exactly once after compaction.
    return allocate(pid, size, strategy);
}
