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

def benchmark_cython_intersection():
    """
    Measures Intersection Performance:
    - Flat Set (Python Native) vs. Trie (Cython Optimized)
    """
    print("--- 🚀 Cython Trie vs Flat Set Intersection Benchmark ---")
    
    # Setup
    N_values = [1000, 5000, 10000, 50000]
    depth = 3
    
    print(f"{'N':<10} | {'Flat (ms)':<15} | {'Cython Trie (ms)':<18} | {'Speedup':<10}")
    print("-" * 65)

    results = []

    for N in N_values:
        policy_a = generate_policies(N, depth)
        policy_b = generate_policies(N, depth)
        
        # Build Engines
        trie_a = hierarchical_policy_engine_cython.HierarchicalPolicyEngine()
        for p in policy_a:
            trie_a.allow_path(p)
            
        trie_b = hierarchical_policy_engine_cython.HierarchicalPolicyEngine()
        for p in policy_b:
            trie_b.allow_path(p)
            
        flat_a = set(policy_a)
        flat_b = set(policy_b)
        
        # Measure Trie Intersection
        start = time.perf_counter()
        _ = trie_a.intersection(trie_b)
        trie_time = (time.perf_counter() - start) * 1000 # ms
        
        # Measure Flat Intersection
        start = time.perf_counter()
        _ = flat_a.intersection(flat_b)
        flat_time = (time.perf_counter() - start) * 1000 # ms
        
        speedup = flat_time / trie_time if trie_time > 0 else 0
        
        print(f"{N:<10} | {flat_time:.6f}        | {trie_time:.6f}           | {speedup:.2f}x")
        results.append((N, flat_time, trie_time, speedup))

    return results

if __name__ == "__main__":
    benchmark_cython_intersection()
