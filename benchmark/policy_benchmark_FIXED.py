# -*- coding: utf-8 -*-
import sys
import os
import timeit
import random
import string
import numpy as np
from scipy import stats
from typing import List, Set, Tuple

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import hierarchical_policy_engine

def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_synthetic_policy(num_fields: int, max_depth: int, overlap_ratio: float) -> Tuple[Set[str], Set[str], List[str], List[str]]:
    base_fields = []
    for _ in range(int(num_fields * (2 - overlap_ratio))):
        depth = random.randint(1, max_depth)
        parts = [generate_random_string() for _ in range(depth)]
        base_fields.append(".".join(parts))
        
    num_common = int(num_fields * overlap_ratio)
    num_unique = int(num_fields * (1 - overlap_ratio))
    
    all_pool = base_fields
    random.shuffle(all_pool)
    
    set_a_list = all_pool[:num_fields]
    common_part = set_a_list[:num_common]
    unique_part_b = [generate_random_string() for _ in range(num_unique)]
    
    set_b_list = common_part + unique_part_b
    
    return set(set_a_list), set(set_b_list), set_a_list, set_b_list

def calculate_hierarchical_intersection(engine_a, engine_b):
    """
    Calculates intersection of two HierarchicalPolicyEngines.
    Returns count of common allowed paths.
    """
    common_count = 0
    
    def traverse_pair(node_a, node_b):
        nonlocal common_count
        # If both allow this path (conceptually), count it?
        # Wait, is_allowed is on the node.
        # If both nodes have is_allowed=True, then this path is in intersection.
        if node_a.is_allowed and node_b.is_allowed:
            common_count += 1
            
        # Recurse on common children
        for key, child_a in node_a.children.items():
            if key in node_b.children:
                traverse_pair(child_a, node_b.children[key])

    traverse_pair(engine_a.root, engine_b.root)
    return common_count

def run_benchmark_suite_FIXED():
    """
    FAIR COMPARISON: 
    - Trie/Set construction is warmup (excluded from measurement)
    - Measures ONLY query performance
    """
    print("--- FIXED Benchmark (Query Performance Only) ---")
    print(f"{'N':<10} | {'Flat Mean':<15} | {'Trie Mean':<15} | {'P-Value':<10}")
    print("-" * 60)
    
    scenarios = [
        {"N": 100, "D": 3},
        {"N": 1000, "D": 3},
        {"N": 5000, "D": 3},
        {"N": 10000, "D": 3},
        {"N": 50000, "D": 3},
    ]
    # Re-structure to collect results
    results_data = []
    for sc in scenarios:
        N = sc["N"]
        D = sc["D"]
        set_a, set_b, list_a, list_b = generate_synthetic_policy(N, D, 0.5)
        
        trie_a = hierarchical_policy_engine.HierarchicalPolicyEngine()
        for f in list_a: trie_a.allow_path(f)
        trie_b = hierarchical_policy_engine.HierarchicalPolicyEngine()
        for f in list_b: trie_b.allow_path(f)
        
        flat_a = set_a
        flat_b = set_b
        
        iterations = 100 if N >= 10000 else 1000
        
        times_flat = []
        for _ in range(iterations):
            start = timeit.default_timer()
            _ = flat_a.intersection(flat_b)
            times_flat.append((timeit.default_timer() - start) * 1000)
            
        times_trie = []
        for _ in range(iterations):
            start = timeit.default_timer()
            _ = calculate_hierarchical_intersection(trie_a, trie_b)
            times_trie.append((timeit.default_timer() - start) * 1000)
            
        flat_mean = np.mean(times_flat)
        flat_std = np.std(times_flat)
        trie_mean = np.mean(times_trie)
        trie_std = np.std(times_trie)
        _, p_value = stats.ttest_ind(times_flat, times_trie)
        
        print(f"{N:<10} | {flat_mean:.4f}±{flat_std:.4f}ms | {trie_mean:.4f}±{trie_std:.4f}ms | {p_value:.4f}")
        results_data.append([N, D, flat_mean, flat_std, trie_mean, trie_std, p_value])

    import csv
    with open('benchmark_results_FIXED.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['N', 'Depth', 'Flat_Mean_ms', 'Flat_Std_ms', 'Trie_Mean_ms', 'Trie_Std_ms', 'P_Value'])
        writer.writerows(results_data)
    print("Results saved to benchmark_results_FIXED.csv")

if __name__ == "__main__":
    run_benchmark_suite_FIXED()
