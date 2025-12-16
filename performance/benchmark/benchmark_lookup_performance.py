# -*- coding: utf-8 -*-
import sys
import os
import time
import random
import string
import numpy as np
from typing import List, Set

# Adjust sys.path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hierarchical_control import hierarchical_policy_engine

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_policies(num_fields: int, depth: int) -> List[str]:
    policies = []
    for _ in range(num_fields):
        # Generate random path of given depth
        parts = [generate_random_string() for _ in range(depth)]
        policies.append(".".join(parts))
    return policies

def benchmark_data_plane_realistic():
    """
    Measures Data Plane Lookup Performance:
    - Single Path Verification (Lookup)
    - Simulates 1,000 requests against a policy of size N
    """
    print("--- 🚀 Data Plane Lookup Benchmark (Trie vs Flat Set) ---")
    
    # Setup
    N_values = [1000, 10000, 50000]
    depth = 3
    
    print(f"{'N':<10} | {'Flat (ms)':<15} | {'Trie (ms)':<15} | {'Speedup':<10}")
    print("-" * 60)

    for N in N_values:
        policies = generate_policies(N, depth)
        
        # Build Engines
        trie_engine = hierarchical_policy_engine.HierarchicalPolicyEngine()
        for p in policies:
            trie_engine.allow_path(p)
            
        flat_set = set(policies)
        
        # Generate test paths (Mix of allowed and denied)
        # 50% existing, 50% random
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
        
        print(f"{N:<10} | {avg_flat:.6f}        | {avg_trie:.6f}        | {speedup:.2f}x")

if __name__ == "__main__":
    benchmark_data_plane_realistic()
