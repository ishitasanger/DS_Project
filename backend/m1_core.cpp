
#include "storage.h"
#include <iostream>
#include <iomanip>

using namespace std;

Storage::Storage(int total_blocks) {
    n = total_blocks;
    array.assign(n > 0 ? n : 0, "");
    free_head = nullptr;
    rebuild_free_list();
}

Storage::~Storage() {
    clear_free_list();
}

void Storage::clear_free_list() {
    while (free_head != nullptr) {
        FreeNode* next_node = free_head->next;
        delete free_head;
        free_head = next_node;
    }
}

void Storage::rebuild_free_list() {
    clear_free_list();

    FreeNode* tail = nullptr;
    int i = 0;

    while (i < n) {
        if (array[i] != "") {
            i++;
            continue;
        }

        int hole_start = i;

        while (i < n && array[i] == "") {
            i++;
        }

        FreeNode* node = new FreeNode;
        node->start = hole_start;
        node->size = i - hole_start;
        node->next = nullptr;

        if (tail == nullptr) {
            free_head = node;
        } else {
            tail->next = node;
        }

        tail = node;
    }
}

void Storage::display_layout() {
    for (int i = 0; i < n; i++) {
        if (i % 20 == 0) {
            cout << "\n" << setw(4) << i << " | ";
        }

        if (array[i] == "") {
            cout << setw(5) << "." << " ";
        } else {
            cout << setw(5) << array[i] << " ";
        }
    }

    cout << "\n";
}

Stats Storage::stats() {
    Stats s{};

    FreeNode* cur = free_head;

    while (cur != nullptr) {
        s.free += cur->size;
        s.segments++;

        if (cur->size > s.largest) {
            s.largest = cur->size;
        }

        cur = cur->next;
    }

    s.occupied = n - s.free;

    if (s.free > 0) {
        s.ext_frag = (1.0 - static_cast<double>(s.largest) / s.free) * 100.0;
    }

    if (n > 0) {
        s.utilisation = 100.0 * s.occupied / n;
    }

    if (s.segments > 0) {
        s.avg_hole = static_cast<double>(s.free) / s.segments;
    }

    return s;
}

vector<pair<int,int>> Storage::free_segments() {
    vector<pair<int,int>> result;

    FreeNode* cur = free_head;

    while (cur != nullptr) {
        result.push_back(make_pair(cur->start, cur->size));
        cur = cur->next;
    }

    return result;
}
