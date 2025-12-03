# -*- coding: utf-8 -*-
#
# Phase 13: Systems Evaluation (Benchmark)
# Compares performance of Flat Set (policy_engine) vs. Trie (hierarchical_policy_engine)

import sys
import os
import timeit
import tracemalloc
import random
import string
import csv
from typing import List, Set, Tuple

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import policy_engine
import hierarchical_policy_engine

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_synthetic_policy(num_fields: int, max_depth: int, overlap_ratio: float) -> Tuple[Set[str], Set[str], List[str], List[str]]:
    """
    Generates synthetic policy data (fields) for benchmarking.
    Returns two sets of fields with a specified overlap ratio.
    """
    base_fields = []
    
    # Generate base pool of fields
    for _ in range(int(num_fields * (2 - overlap_ratio))):
        depth = random.randint(1, max_depth)
        parts = [generate_random_string() for _ in range(depth)]
        base_fields.append(".".join(parts))
        
    # Split into two sets with overlap
    # Set A: First N fields
    # Set B: Overlapping fields + Unique fields
    
    # Simple approach:
    # Common: N * overlap_ratio
    # Unique A: N * (1 - overlap_ratio)
    # Unique B: N * (1 - overlap_ratio)
    
    num_common = int(num_fields * overlap_ratio)
    num_unique = int(num_fields * (1 - overlap_ratio))
    
    common = [generate_random_string() for _ in range(num_common)] # Use simple random strings for common base to ensure exact match? 
    # Actually, let's use the generated paths.
    
    all_pool = base_fields
    random.shuffle(all_pool)
    
    set_a_list = all_pool[:num_fields]
    # For Set B, we want some overlap.
    # Let's pick 'num_common' from set_a_list, and fill the rest with new randoms or from the pool.
    
    # Better approach for controlled overlap:
    common_part = set_a_list[:num_common]
    unique_part_b = [generate_random_string() for _ in range(num_unique)] # Simplified unique generation
    
    set_b_list = common_part + unique_part_b
    
    return set(set_a_list), set(set_b_list), set_a_list, set_b_list

def measure_flat_set_intersection(set_a: Set[str], set_b: Set[str]):
    return policy_engine.calculate_minimum_set(set_a, set_b)

def measure_trie_intersection(list_a: List[str], list_b: List[str]):
    trie_a = hierarchical_policy_engine.PolicyTrie()
    for f in list_a: trie_a.insert(f)
        
    trie_b = hierarchical_policy_engine.PolicyTrie()
    for f in list_b: trie_b.insert(f)
        
    return hierarchical_policy_engine.calculate_hierarchical_intersection(trie_a, trie_b)

def run_benchmark_suite():
    print("--- 📊 Symbiosis Policy Engine Benchmark ---")
    print(f"{'Scenario':<20} | {'N (Fields)':<10} | {'Depth':<5} | {'Engine':<10} | {'Time (ms)':<10} | {'Memory (KB)':<10}")
    print("-" * 85)
    
    results = []
    
    # Scenarios
    scenarios = [
        # Scale-up (Fixed Depth=3)
        {"N": 100, "D": 3},
        {"N": 1000, "D": 3},
        {"N": 10000, "D": 3},
        {"N": 50000, "D": 3},
        
        # Depth Sensitivity (Fixed N=1000)
        {"N": 1000, "D": 1},
        {"N": 1000, "D": 5},
        {"N": 1000, "D": 10},
    ]
    
    for sc in scenarios:
        N = sc["N"]
        D = sc["D"]
        overlap = 0.5
        
        set_a, set_b, list_a, list_b = generate_synthetic_policy(N, D, overlap)
        
        # 1. Benchmark Flat Set
        tracemalloc.start()
        start_time = timeit.default_timer()
        measure_flat_set_intersection(set_a, set_b)
        flat_time = (timeit.default_timer() - start_time) * 1000 # ms
        current, peak = tracemalloc.get_traced_memory()
        flat_mem = peak / 1024 # KB
        tracemalloc.stop()
        
        print(f"{'Scale-up' if D==3 else 'Depth-Sens':<20} | {N:<10} | {D:<5} | {'Flat Set':<10} | {flat_time:<10.4f} | {flat_mem:<10.2f}")
        results.append(["Flat Set", N, D, flat_time, flat_mem])

        # 2. Benchmark Trie
        # Note: Trie building time is included? Usually we benchmark the operation itself.
        # But for fairness, data structure construction might be relevant if it's per-request.
        # However, usually policies are pre-loaded.
        # Let's measure Intersection ONLY to be fair to the algorithm comparison.
        # So we build Tries outside the timer.
        
        trie_a = hierarchical_policy_engine.PolicyTrie()
        for f in list_a: trie_a.insert(f)
        trie_b = hierarchical_policy_engine.PolicyTrie()
        for f in list_b: trie_b.insert(f)
        
        tracemalloc.start()
        start_time = timeit.default_timer()
        hierarchical_policy_engine.calculate_hierarchical_intersection(trie_a, trie_b)
        trie_time = (timeit.default_timer() - start_time) * 1000 # ms
        current, peak = tracemalloc.get_traced_memory()
        trie_mem = peak / 1024 # KB
        tracemalloc.stop()
        
        print(f"{'Scale-up' if D==3 else 'Depth-Sens':<20} | {N:<10} | {D:<5} | {'Trie':<10} | {trie_time:<10.4f} | {trie_mem:<10.2f}")
        results.append(["Trie", N, D, trie_time, trie_mem])

    # Save to CSV
    with open("benchmark_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Engine", "N", "Depth", "Time_ms", "Memory_KB"])
        writer.writerows(results)
        
    print("\nBenchmark completed. Results saved to benchmark_results.csv")

if __name__ == "__main__":
    run_benchmark_suite()
