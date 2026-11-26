"""
dummy_backend.py — Python backend mirroring the C++ M1-M4 interface.

Implements all four allocation strategies (First Fit, Next Fit,
Best Fit, Worst Fit) so that experiments produce differentiated
results.  Uses the same seed-based workload generator as M3.

Replace with ctypes bindings to the compiled C++ library for
full integration.
"""

import copy


def _pid_start_key(item):
    """Sort key returning process start index."""
    return item[1][0]


class DummyStats:
    """Mirror of the Stats struct returned by the C++ backend."""
    def __init__(self):
        self.free = 0
        self.occupied = 0
        self.segments = 0
        self.largest = 0
        self.ext_frag = 0.0
        self.utilisation = 0.0
        self.avg_hole = 0.0


class DummyAllocResult:
    def __init__(self, ok, start, reason):
        self.ok = ok
        self.start = start
        self.reason = reason


class DummyReleaseResult:
    def __init__(self, ok, reason):
        self.ok = ok
        self.reason = reason


class DummyFailureAnalysis:
    def __init__(self):
        self.reason = ""
        self.explanation = ""
        self.total_free = 0
        self.largest_hole = 0


class DummyCompactionReport:
    def __init__(self):
        self.before = DummyStats()
        self.after = DummyStats()
        self.segments_before = 0
        self.segments_after = 0
        self.moved_blocks = 0


class DummyLogEntry:
    def __init__(self, step, op, pid, size, result, reason):
        self.step = step
        self.op = op
        self.pid = pid
        self.size = size
        self.result = result
        self.reason = reason


# ---- Sample state builder (100 blocks, blueprint screenshot) -----

def _build_sample():
    """Create a sample state: 100 blocks, 93 occupied, 7 free,
    4 free segments, largest free segment 3, ext frag 57.1%."""
    arr = [""] * 100
    table = {}
    # Place processes with specific gaps to match blueprint
    plist = [
        ("P1", 0, 20),
        ("P2", 22, 18),   # gap at 20-21 (2 free)
        ("P3", 40, 15),
        ("P4", 56, 10),   # gap at 55 (1 free)
        ("P5", 66, 10),
        ("P6", 77, 10),   # gap at 76 (1 free)
        ("P7", 87, 10),   # gap at 97-99 (3 free) => largest = 3
    ]
    for pid, start, size in plist:
        for i in range(start, start + size):
            arr[i] = pid
        table[pid] = (start, size)
    return arr, table

_SAMPLE_ARRAY, _SAMPLE_TABLE = _build_sample()


class DummyBackend:
    """
    Drop-in Python replacement for the C++ Storage class.
    Implements all four allocation strategies.
    """

    def __init__(self, total_blocks=100):
        self.n = total_blocks
        if total_blocks == 100:
            self.array = copy.deepcopy(_SAMPLE_ARRAY)
            self.table = copy.deepcopy(_SAMPLE_TABLE)
            self.log = [
                DummyLogEntry(1, "ALLOCATE", "P1", 20, "OK", "OK"),
                DummyLogEntry(2, "ALLOCATE", "P2", 18, "OK", "OK"),
                DummyLogEntry(3, "ALLOCATE", "P3", 15, "OK", "OK"),
                DummyLogEntry(4, "ALLOCATE", "P4", 10, "OK", "OK"),
                DummyLogEntry(5, "ALLOCATE", "P5", 10, "OK", "OK"),
                DummyLogEntry(6, "ALLOCATE", "P6", 10, "OK", "OK"),
                DummyLogEntry(7, "ALLOCATE", "P7", 10, "OK", "OK"),
            ]
            self._next_step = 8
        else:
            self.array = [""] * self.n
            self.table = {}
            self.log = []
            self._next_step = 1
        self._last_pos = 0       # for Next Fit
        self._frag_history = []
        # Record initial fragmentation
        st = self._compute_stats()
        self._frag_history.append(st.ext_frag)

    # ---- Statistics ----------------------------------------------

    def stats(self):
        """Compute live stats from the array."""
        return self._compute_stats()

    def _compute_stats(self):
        """Internal stats computation, safe for any array state."""
        s = DummyStats()
        n = self.n
        free_count = 0
        for i in range(n):
            if self.array[i] == "":
                free_count += 1
        s.free = free_count
        s.occupied = n - free_count
        # Count free segments and find the largest
        segments = []
        i = 0
        while i < n:
            if self.array[i] == "":
                seg_start = i
                while i < n and self.array[i] == "":
                    i += 1
                segments.append(i - seg_start)
            else:
                i += 1
        s.segments = len(segments)
        s.largest = max(segments) if segments else 0
        # External fragmentation
        if s.free > 0:
            s.ext_frag = (1.0 - s.largest / s.free) * 100.0
        else:
            s.ext_frag = 0.0
        # Utilisation
        if n > 0:
            s.utilisation = 100.0 * s.occupied / n
        else:
            s.utilisation = 0.0
        # Average hole size
        if s.segments > 0:
            s.avg_hole = s.free / s.segments
        else:
            s.avg_hole = 0.0
        return s

    # ---- Core operations -----------------------------------------

    def allocate(self, pid, size, strategy):
        """Allocate 'size' blocks for process 'pid'."""
        if size <= 0:
            self._add_log("ALLOCATE", pid, size, "FAIL", "INVALID_SIZE")
            return DummyAllocResult(False, -1, "INVALID_SIZE")
        if size > self.n:
            self._add_log("ALLOCATE", pid, size, "FAIL", "NO_SPACE")
            return DummyAllocResult(False, -1, "NO_SPACE")
        if pid in self.table:
            self._add_log("ALLOCATE", pid, size, "FAIL", "DUPLICATE_PID")
            return DummyAllocResult(False, -1, "DUPLICATE_PID")
        # Find a hole using the chosen strategy
        start = self._find_hole(size, strategy)
        if start is None:
            free_total = self._count_free()
            if free_total >= size:
                reason = "FRAGMENTATION"
            else:
                reason = "NO_SPACE"
            self._add_log("ALLOCATE", pid, size, "FAIL", reason)
            return DummyAllocResult(False, -1, reason)
        # Place the process
        for i in range(start, start + size):
            self.array[i] = pid
        self.table[pid] = (start, size)
        # Update next-fit pointer
        self._last_pos = start + size
        if self._last_pos >= self.n:
            self._last_pos = 0
        self._add_log("ALLOCATE", pid, size, "OK", "OK")
        st = self._compute_stats()
        self._frag_history.append(st.ext_frag)
        return DummyAllocResult(True, start, "OK")

    def release(self, pid):
        """Release process 'pid'."""
        if pid not in self.table:
            self._add_log("RELEASE", pid, 0, "FAIL", "UNKNOWN_PID")
            return DummyReleaseResult(False, "UNKNOWN_PID")
        start, size = self.table[pid]
        for i in range(start, start + size):
            self.array[i] = ""
        del self.table[pid]
        self._add_log("RELEASE", pid, size, "OK", "OK")
        st = self._compute_stats()
        self._frag_history.append(st.ext_frag)
        return DummyReleaseResult(True, "OK")

    def compact(self):
        """Slide all processes to the left, merging free space."""
        report = DummyCompactionReport()
        report.before = self._compute_stats()
        report.segments_before = report.before.segments
        # Collect processes in order of their start position
        ordered = sorted(self.table.items(), key=_pid_start_key)
        write = 0
        moved = 0
        for pid, (old_start, size) in ordered:
            if old_start != write:
                moved += size
            for k in range(size):
                self.array[write + k] = pid
            self.table[pid] = (write, size)
            write += size
        # Clear remaining blocks
        for i in range(write, self.n):
            self.array[i] = ""
        report.after = self._compute_stats()
        report.segments_after = report.after.segments
        report.moved_blocks = moved
        self._add_log("COMPACT", "", moved, "OK", "COMPACTED")
        return report

    def analyze_failure(self, request_size):
        """Classify why a request of given size would fail."""
        fa = DummyFailureAnalysis()
        st = self._compute_stats()
        fa.total_free = st.free
        fa.largest_hole = st.largest
        if request_size <= 0:
            fa.reason = "INVALID_SIZE"
            fa.explanation = (
                "The requested block count must be positive."
            )
        elif st.free < request_size:
            fa.reason = "NO_SPACE"
            fa.explanation = (
                "The total free space is smaller than the "
                "request.\n"
                "Free blocks available: {}.\n"
                "Blocks requested: {}.\n"
                "Compaction cannot create additional free space."
            ).format(st.free, request_size)
        elif st.largest < request_size:
            fa.reason = "FRAGMENTATION"
            fa.explanation = (
                "Enough free blocks exist in total, but they "
                "are split into holes.\n"
                "Total free blocks: {}.\n"
                "Largest continuous hole: {}.\n"
                "Compaction can merge the holes into one larger "
                "free segment."
            ).format(st.free, st.largest)
        else:
            fa.reason = "ALLOCATABLE"
            fa.explanation = "The request should succeed."
        return fa

    def allocate_with_compaction(self, pid, size, strategy):
        """Try allocation, compact on fragmentation, retry once."""
        first = self.allocate(pid, size, strategy)
        if first.ok or first.reason != "FRAGMENTATION":
            return first
        self.compact()
        return self.allocate(pid, size, strategy)

    def free_segments(self):
        """Return list of (start, size) for every free segment."""
        result = []
        i = 0
        while i < self.n:
            if self.array[i] == "":
                seg_start = i
                while i < self.n and self.array[i] == "":
                    i += 1
                result.append((seg_start, i - seg_start))
            else:
                i += 1
        return result

    def get_log(self):
        """Return the event log as a list."""
        return list(self.log)

    def export_log_csv(self, filename):
        """Write the log to a CSV file."""
        try:
            with open(filename, "w") as f:
                f.write("step,operation,pid,size,result,reason\n")
                for e in self.log:
                    f.write("{},{},{},{},{},{}\n".format(
                        e.step, e.op, e.pid, e.size,
                        e.result, e.reason
                    ))
            return True
        except Exception:
            return False

    def reset(self, total_blocks=None):
        """Reset to an empty storage."""
        if total_blocks is not None:
            self.n = total_blocks
        self.array = [""] * self.n
        self.table = {}
        self.log = []
        self._next_step = 1
        self._last_pos = 0
        self._frag_history = []

    def get_frag_history(self):
        """Return the fragmentation history list."""
        return list(self._frag_history)

    # ---- Strategy implementations (mirror m3_strategies.h) -------

    def _count_free(self):
        """Count total free blocks."""
        count = 0
        for i in range(self.n):
            if self.array[i] == "":
                count += 1
        return count

    def _find_hole(self, size, strategy):
        """Dispatch to the correct strategy."""
        key = strategy.lower().replace(" ", "_")
        if key == "first_fit":
            return self._first_fit(size)
        if key == "next_fit":
            return self._next_fit(size)
        if key == "best_fit":
            return self._best_fit(size)
        if key == "worst_fit":
            return self._worst_fit(size)
        # Default to first fit
        return self._first_fit(size)

    def _first_fit(self, size):
        """First Fit: take the first hole big enough."""
        segs = self._get_free_segments()
        for start, seg_size in segs:
            if seg_size >= size:
                return start
        return None

    def _best_fit(self, size):
        """Best Fit: take the smallest hole big enough."""
        segs = self._get_free_segments()
        chosen = None
        chosen_size = None
        for start, seg_size in segs:
            if seg_size >= size:
                if chosen is None or seg_size < chosen_size:
                    chosen = start
                    chosen_size = seg_size
        return chosen

    def _worst_fit(self, size):
        """Worst Fit: take the largest hole big enough."""
        segs = self._get_free_segments()
        chosen = None
        chosen_size = None
        for start, seg_size in segs:
            if seg_size >= size:
                if chosen is None or seg_size > chosen_size:
                    chosen = start
                    chosen_size = seg_size
        return chosen

    def _next_fit(self, size):
        """Next Fit: start from where the last allocation ended."""
        segs = self._get_free_segments()
        # Pass 1: segments at or after last_pos
        for start, seg_size in segs:
            if start >= self._last_pos and seg_size >= size:
                return start
        # Pass 2: wrap around, segments before last_pos
        for start, seg_size in segs:
            if start < self._last_pos and seg_size >= size:
                return start
        return None

    def _get_free_segments(self):
        """Return list of (start, size) for all free segments."""
        result = []
        i = 0
        n = self.n
        while i < n:
            if self.array[i] == "":
                seg_start = i
                while i < n and self.array[i] == "":
                    i += 1
                result.append((seg_start, i - seg_start))
            else:
                i += 1
        return result

    def _add_log(self, op, pid, size, result, reason):
        """Append a log entry."""
        entry = DummyLogEntry(
            self._next_step, op, pid, size, result, reason
        )
        self.log.append(entry)
        self._next_step += 1
