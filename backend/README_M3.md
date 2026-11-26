# M3 – Allocation Strategies and Experiments

This module implements four memory allocation strategies, generates repeatable workloads, tests strategy placement, and compares the performance of all four strategies.

## Files and Their Purpose

### 1. m3_strategies.h
Implements the four memory allocation strategies:

- **First Fit:** Selects the first free memory block large enough for the request.
- **Next Fit:** Continues searching from the position of the previous allocation.
- **Best Fit:** Selects the smallest free block that can accommodate the request.
- **Worst Fit:** Selects the largest available free block.

Also includes a seeded workload generator that creates allocation and release operations. Using the same seed generates the same workload, ensuring fair and repeatable comparisons.

### 2. m3_tests.cpp
Contains tests for:
- T12 – Strategy placement verification.
- Next Fit search behaviour.
- Handling requests when no suitable free block exists.
- Repeatability of workloads using the same random seed.
- Different workloads using different seeds.

### 3. m3_experiments.cpp
Implements the experiment runner.

- Tests three storage sizes: 100, 1000 and 5000 blocks.
- Compares First Fit, Next Fit, Best Fit and Worst Fit.
- Uses the same seeded workload for fair comparison.
- Records successful allocations, failures, average external fragmentation, utilisation, final free segments, largest free segment and execution time.
- Generates a CSV results file named `m3_results.csv`.

## Compilation and Execution

Run the following commands from the backend directory:

**Strategy and repeatability tests:**
```bash
g++ -std=c++17 m3_tests.cpp -o m3_tests.exe
.\m3_tests.exe
```

**Experiment runner:**
```bash
g++ -std=c++17 m1_core.cpp m2_engine.cpp m3_experiments.cpp -o m3_experiments.exe
.\m3_experiments.exe
```

## M3 Contribution

This module helps evaluate how different memory allocation strategies behave under identical workloads, using repeatable experiments and measurable performance metrics.