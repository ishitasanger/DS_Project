#include "storage.h"

// Checks the request. Returns "OK" if it is fine,
// otherwise returns the reason it is wrong.
string Storage::validate(string pid, int size) {
    // 1. size must be positive
    if (size <= 0) {
        return "INVALID_SIZE";
    }
    // 2. size cannot be bigger than the whole storage
    if (size > n) {
        return "NO_SPACE";
    }
    // 3. the process id must not already exist
    if (table.count(pid) > 0) {
        return "DUPLICATE_PID";
    }
    // everything is fine
    return "OK";
}

AllocResult Storage::allocate(string pid, int size, string strategy) {
    string check = validate(pid, size);
    if (check != "OK") {
        return {false, -1, check};
    }
    return {false, -1, "NOT_DONE"};   // real placing comes in Step 3
}

ReleaseResult Storage::release(string pid) {
    return {false, "NOT_DONE"};
}
