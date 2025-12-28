#!/bin/bash
set -e  # Exit on error

echo "--- 🧪 Symbiosis: Running All Experiments ---"

echo "[Phase 1] Profiling..."
if [ -f "policy_learning/policy_profiler.py" ]; then
    python3 policy_learning/policy_profiler.py
else
    echo "Skipping policy_profiler.py (not found)"
fi

echo "[Phase 2] Integration..."
if [ -f "policy_integration/policy_integrator.py" ]; then
    python3 policy_integration/policy_integrator.py
else
    echo "Skipping policy_integrator.py (not found)"
fi

echo "[Phase 3] Benchmark..."
if [ -f "performance/benchmark/policy_benchmark_FIXED.py" ]; then
    echo "Running FIXED Benchmark (Fair Comparison)..."
    python3 performance/benchmark/policy_benchmark_FIXED.py
elif [ -f "performance/benchmark/policy_benchmark.py" ]; then
    python3 performance/benchmark/policy_benchmark.py
elif [ -f "performance/wasm_benchmark_driver.py" ]; then
     # Fallback or alternative benchmark script if the specific one doesn't exist
     echo "Warning: performance/benchmark/policy_benchmark.py not found. Checking for alternatives..."
     if [ -f "performance/wasm_benchmark_driver.py" ]; then
        echo "Running wasm_benchmark_driver.py instead..."
        python3 performance/wasm_benchmark_driver.py
     fi
fi

echo "[Phase 4] Attack Simulation..."
if [ -f "attack_simulation_ENHANCED.py" ]; then
    echo "Running Enhanced Attack Simulation..."
    python3 attack_simulation_ENHANCED.py
elif [ -f "attack_simulation.py" ]; then
    python3 attack_simulation.py
else
    echo "Skipping attack_simulation.py (not found)"
fi

echo "[Phase 5] Compile-to-Flat Optimization..."
if [ -f "tests/test_policy_compiler_flattening.py" ]; then
    python3 tests/test_policy_compiler_flattening.py
fi

echo "[Phase 6] Data Plane Benchmark..."
if [ -f "benchmark/benchmark_lookup_performance.py" ]; then
    python3 benchmark/benchmark_lookup_performance.py
fi

echo "[Phase 7] Adaptive Policy Engine Test..."
if [ -f "adaptive_security/adaptive_policy_engine.py" ]; then
    python3 adaptive_security/adaptive_policy_engine.py
fi

echo "[Phase 8] Evolution..."
echo "  > Running Evolutionary Agent..."
python3 adaptive_security/evolutionary_agent.py
echo "  > Running Co-evolution Simulation..."
python3 adaptive_security/coevolution_simulation.py

echo "[Phase 9] Reporting..."
if [ -f "final_report_generator.py" ]; then
    python3 final_report_generator.py
else
    echo "Skipping final_report_generator.py (not found)"
fi

echo "--- ✅ All Experiments Completed Successfully ---"
