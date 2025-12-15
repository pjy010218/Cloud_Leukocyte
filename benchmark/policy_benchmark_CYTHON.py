# -*- coding: utf-8 -*-
import sys
import os
import time
import random
import string
import numpy as np
from typing import List

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Cython Engine
try:
    import hierarchical_policy_engine_cython
except ImportError:
    print("Error: Could not import hierarchical_policy_engine_cython. Make sure it is built.")
    sys.exit(1)

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_policies(num_fields: int, depth: int) -> List[str]:
    policies = []
    for _ in range(num_fields):
        parts = [generate_random_string() for _ in range(depth)]
        policies.append(".".join(parts))
    return policies

def benchmark_cython_vs_flat():
    """
    Measures Data Plane Lookup Performance:
    - Flat Set (Python Native) vs. Trie (Cython Optimized)
    """
    print("--- 🚀 Cython Trie vs Flat Set Benchmark ---")
    
    # Setup
    N_values = [1000, 10000, 50000]
    depth = 3
    
    print(f"{'N':<10} | {'Flat (ms)':<15} | {'Cython Trie (ms)':<18} | {'Speedup':<10}")
    print("-" * 65)

    results = []

    for N in N_values:
        policies = generate_policies(N, depth)
        
        # Build Engines
        trie_engine = hierarchical_policy_engine_cython.HierarchicalPolicyEngine()
        for p in policies:
            trie_engine.allow_path(p)
            
        flat_set = set(policies)
        
        # Generate test paths
        test_paths = []
        for _ in range(500):
            test_paths.append(random.choice(policies))
        for _ in range(500):
            parts = [generate_random_string() for _ in range(depth)]
            test_paths.append(".".join(parts))
            
        random.shuffle(test_paths)
        
        # Measure Trie
        times_trie = []
        for path in test_paths:
            start = time.perf_counter()
            _ = trie_engine.check_access(path)
            times_trie.append(time.perf_counter() - start)
        
        # Measure Flat
        times_flat = []
        for path in test_paths:
            start = time.perf_counter()
            _ = path in flat_set
            times_flat.append(time.perf_counter() - start)
        
        avg_trie = np.mean(times_trie) * 1000 # ms
        avg_flat = np.mean(times_flat) * 1000 # ms
        
        speedup = avg_flat / avg_trie if avg_trie > 0 else 0
        
        print(f"{N:<10} | {avg_flat:.6f}        | {avg_trie:.6f}           | {speedup:.2f}x")
        results.append((N, avg_flat, avg_trie, speedup))

    return results

if __name__ == "__main__":
    benchmark_cython_vs_flat()
