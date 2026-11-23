#include "storage.h"

AllocResult Storage::allocate(string pid, int size, string strategy) {
    return {false, -1, "NOT_DONE"};
}

ReleaseResult Storage::release(string pid) {
    return {false, "NOT_DONE"};
}
