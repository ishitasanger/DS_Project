"""
backend_adapter.py — sole bridge between the M5 UI and the M1–M4 C++ backend.

This is the ONLY frontend module that communicates with the C++ backend.
It launches the compiled C++ bridge (cpp_bridge.exe) as a persistent
offline subprocess and exchanges single-line JSON messages over stdin/stdout.
No other frontend file imports backend modules directly.
"""

import atexit
import json
import os
import subprocess
import weakref
import random

_FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_BRIDGE = os.path.join(_FRONTEND_DIR, "cpp_bridge.exe")
_LIVE_BRIDGES = weakref.WeakSet()


class BackendStats:
    """Python mirror of the C++ Stats struct."""

    def __init__(self, data=None):
        d = data or {}
        self.free = int(d.get("free", 0))
        self.occupied = int(d.get("occupied", 0))
        self.segments = int(d.get("segments", 0))
        self.largest = int(d.get("largest", 0))
        self.ext_frag = float(d.get("ext_frag", 0.0))
        self.utilisation = float(d.get("utilisation", 0.0))
        self.avg_hole = float(d.get("avg_hole", 0.0))


class AllocResult:
    """Python mirror of the C++ AllocResult struct."""

    def __init__(self, ok, start, reason):
        self.ok = bool(ok)
        self.start = int(start)
        self.reason = str(reason)


class ReleaseResult:
    """Python mirror of the C++ ReleaseResult struct."""

    def __init__(self, ok, reason):
        self.ok = bool(ok)
        self.reason = str(reason)


class FailureAnalysis:
    """Python mirror of the C++ FailureAnalysis struct."""

    def __init__(self, data=None):
        d = data or {}
        self.reason = str(d.get("reason", ""))
        self.explanation = str(d.get("explanation", ""))
        self.total_free = int(d.get("total_free", 0))
        self.largest_hole = int(d.get("largest_hole", 0))


class CompactionReport:
    """Python mirror of the C++ CompactionReport struct."""

    def __init__(self, data=None):
        d = data or {}
        self.before = BackendStats(d.get("before"))
        self.after = BackendStats(d.get("after"))
        self.segments_before = int(d.get("segments_before", 0))
        self.segments_after = int(d.get("segments_after", 0))
        self.moved_blocks = int(d.get("moved_blocks", 0))


class LogEntry:
    """Python mirror of the C++ LogEntry struct."""

    def __init__(self, data=None):
        d = data or {}
        self.step = int(d.get("step", 0))
        self.op = str(d.get("op", ""))
        self.pid = str(d.get("pid", ""))
        self.size = int(d.get("size", 0))
        self.result = str(d.get("result", ""))
        self.reason = str(d.get("reason", ""))


def _shutdown_all_bridges():
    """Close any open C++ bridge processes when Python exits."""
    for adapter in list(_LIVE_BRIDGES):
        adapter.close()


atexit.register(_shutdown_all_bridges)


class BackendAdapter:
    """
    Thin bridge between M5's Python frontend and M1–M4's C++ backend.

    Every method calls the compiled C++ M1–M4 implementation through
    cpp_bridge.exe and converts the JSON response to Python objects.
    """

    def __init__(self, total_blocks=100, load_sample=None, bridge_path=None):
        self._n = int(total_blocks)
        self._bridge_path = bridge_path or _DEFAULT_BRIDGE
        self._proc = None
        self._frag_history = []
        self._is_sample = False

        self._start_bridge()
        self._send({"cmd": "init", "n": self._n})

        use_sample = True if load_sample is None else load_sample

        if use_sample:
            if self._n == 100:
                self._load_sample_state()
            else:
                self._load_random_sample_state()
        else:
            st = self.stats()
            self._frag_history = [st.ext_frag]

    # ---- Process lifecycle ---------------------------------------

    def _start_bridge(self):
        """Launch cpp_bridge.exe and wait for its ready handshake."""
        if not os.path.exists(self._bridge_path):
            raise FileNotFoundError(
                "Compiled C++ bridge not found: {}".format(self._bridge_path)
            )
        self._proc = subprocess.Popen(
            [self._bridge_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        _LIVE_BRIDGES.add(self)
        ready_line = self._proc.stdout.readline()
        if not ready_line:
            raise RuntimeError("C++ backend bridge failed to start.")
        resp = json.loads(ready_line)
        if not resp.get("ready"):
            raise RuntimeError("Unexpected C++ bridge handshake: {}".format(resp))

    def _send(self, payload):
        """Send one JSON command to C++ and parse one JSON response line."""
        if self._proc is None or self._proc.poll() is not None:
            raise RuntimeError("C++ backend process is not running.")
        line = json.dumps(payload, separators=(",", ":"))
        self._proc.stdin.write(line + "\n")
        self._proc.stdin.flush()
        reply = self._proc.stdout.readline()
        if not reply:
            err = self._proc.stderr.read().strip()
            raise RuntimeError("No response from C++ bridge: {}".format(err))
        return json.loads(reply)

    def close(self):
        """Terminate the C++ bridge process cleanly."""
        if self._proc is None:
            return
        try:
            if self._proc.poll() is None:
                self._proc.stdin.write('{"cmd":"quit"}\n')
                self._proc.stdin.flush()
                self._proc.wait(timeout=2)
        except Exception:
            self._proc.kill()
        finally:
            self._proc = None

    def __del__(self):
        self.close()

    # ---- Sample setup --------------------------------------------

    def _load_sample_state(self):
        """Populate the 100-block sample layout using real C++ calls."""
        steps = [
            ("alloc", "P1", 20),
            ("alloc", "_gap1", 2),
            ("alloc", "P2", 18),
            ("alloc", "P3", 15),
            ("alloc", "_gap2", 1),
            ("alloc", "P4", 10),
            ("alloc", "P5", 10),
            ("alloc", "_gap3", 1),
            ("alloc", "P6", 10),
            ("alloc", "P7", 10),
            ("release", "_gap1", 0),
            ("release", "_gap2", 0),
            ("release", "_gap3", 0),
        ]

        def _load_random_sample_state(self):
          rng = random.Random(self._n)

          free_target = max(1, round(self._n * 0.07))
          occupied_target = self._n - free_target

          def make_chunks(total):
            chunks = []
            while total > 0:
                size = rng.randint(1, min(10, total))
                chunks.append(size)
                total -= size
            return chunks

          segments = (
            [(False, size) for size in make_chunks(occupied_target)]
            + [(True, size) for size in make_chunks(free_target)]
          )

          rng.shuffle(segments)
          gap_pids = []

          for index, (is_gap, size) in enumerate(segments):
            pid = "R{}".format(index + 1)

            self._send({
                "cmd": "allocate",
                "pid": pid,
                "size": size,
                "strategy": "first"
            })

            if is_gap:
                gap_pids.append(pid)

          for pid in gap_pids:
            self._send({"cmd": "release", "pid": pid})

          st = self.stats()
          self._frag_history = [st.ext_frag]
          self._is_sample = True   
        
        for op, pid, size in steps:
            if op == "alloc":
                self._send({"cmd": "allocate", "pid": pid, "size": size, "strategy": "first"})
            else:
                self._send({"cmd": "release", "pid": pid})
        st = self.stats()
        self._frag_history = [st.ext_frag]
        self._is_sample = True

    # ---- Properties ----------------------------------------------

    @property
    def n(self):
        return self._n

    @property
    def is_sample(self):
        return self._is_sample

    @property
    def backend_mode(self):
        return "C++ (M1–M4)"

    @property
    def array(self):
        resp = self._send({"cmd": "array"})
        return list(resp.get("array", []))

    @property
    def table(self):
        resp = self._send({"cmd": "table"})
        raw = resp.get("table", {})
        return {pid: (int(v[0]), int(v[1])) for pid, v in raw.items()}

    # ---- Core operations -----------------------------------------

    def allocate(self, pid, size, strategy):
        """Allocate 'size' blocks for process 'pid' via C++ M2/M3."""
        resp = self._send({
            "cmd": "allocate",
            "pid": str(pid),
            "size": int(size),
            "strategy": str(strategy),
        })
        self._is_sample = False
        self._record_frag_if_changed()
        return AllocResult(resp["ok"], resp["start"], resp["reason"])

    def release(self, pid):
        """Release process 'pid' via C++ M2."""
        resp = self._send({"cmd": "release", "pid": str(pid)})
        self._is_sample = False
        self._record_frag_if_changed()
        return ReleaseResult(resp["ok"], resp["reason"])

    def compact(self):
        """Run compaction via C++ M4 and return a CompactionReport."""
        resp = self._send({"cmd": "compact"})
        self._is_sample = False
        self._frag_history.append(float(resp["after"]["ext_frag"]))
        return CompactionReport(resp)

    def allocate_with_compaction(self, pid, size, strategy):
        """Try allocation, compact on fragmentation, retry once via C++ M4."""
        resp = self._send({
            "cmd": "allocate_with_compaction",
            "pid": str(pid),
            "size": int(size),
            "strategy": str(strategy),
        })
        self._is_sample = False
        self._record_frag_if_changed()
        return AllocResult(resp["ok"], resp["start"], resp["reason"])

    def _record_frag_if_changed(self):
        """Append live external fragmentation after a storage operation."""
        st = self.stats()
        self._frag_history.append(st.ext_frag)

    # ---- Query ---------------------------------------------------

    def stats(self):
        """Return current statistics from C++ M1."""
        return BackendStats(self._send({"cmd": "stats"}))

    def free_segments(self):
        """Return list of (start, size) for free segments from C++ M1."""
        resp = self._send({"cmd": "free_segments"})
        return [(int(s[0]), int(s[1])) for s in resp.get("segments", [])]

    def analyze_failure(self, request_size):
        """Classify failure reason via C++ M4."""
        resp = self._send({"cmd": "analyze_failure", "size": int(request_size)})
        return FailureAnalysis(resp)

    # ---- Event log -----------------------------------------------

    def get_log(self):
        """Return the full event log from C++ M2."""
        resp = self._send({"cmd": "log"})
        return [LogEntry(item) for item in resp.get("log", [])]

    def export_log_csv(self, filename):
        """Export the event log to CSV via C++ M2."""
        resp = self._send({"cmd": "export_log", "filename": str(filename)})
        return bool(resp.get("ok", False))

    # ---- History & Experiments -----------------------------------

    def get_frag_history(self):
        """Return recorded external fragmentation values."""
        return list(self._frag_history)

    def generate_workload(self, n_blocks, n_ops, seed):
        """Call M3's C++ seeded workload generator."""
        resp = self._send({
            "cmd": "workload",
            "n": int(n_blocks),
            "ops": int(n_ops),
            "seed": int(seed),
        })
        ops = []
        for is_alloc, pid, size in resp.get("ops", []):
            kind = "alloc" if is_alloc else "release"
            ops.append((kind, str(pid), int(size)))
        return ops

    def run_experiment(self, n_blocks, n_ops, seed, strategy, include_layout=False):
        """Run one complete M3 C++ experiment and return metrics + history."""
        return self._send({
            "cmd": "experiment",
            "n": int(n_blocks),
            "ops": int(n_ops),
            "seed": int(seed),
            "strategy": str(strategy),
            "include_layout": bool(include_layout),
        })

    # ---- Reset ---------------------------------------------------

    def reset(self, total_blocks=None):
        """Reset C++ storage to empty."""
        target = self._n if total_blocks is None else int(total_blocks)
        resp = self._send({"cmd": "reset", "n": target})
        self._n = int(resp["n"])
        self._is_sample = False
        self._frag_history = [self.stats().ext_frag]
