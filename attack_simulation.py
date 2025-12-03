# -*- coding: utf-8 -*-
#
# Phase 15: Security Evaluation (Attack Simulation)
# Demonstrates the efficacy of Epigenetic Symbiosis (Suppression & Transduction)
# against Zero-day attacks (e.g., Log4Shell).

import random
import time
from typing import List, Dict
from hierarchical_policy_engine import HierarchicalPolicyEngine

# ----------------------------------------------------------------------
# 1. Dataset Generation
# ----------------------------------------------------------------------

def generate_traffic_dataset(total_requests: int = 1000, attack_ratio: float = 0.2) -> List[Dict[str, str]]:
    """
    Generates a mixed dataset of Normal and Attack traffic.
    """
    dataset = []
    num_attacks = int(total_requests * attack_ratio)
    num_normal = total_requests - num_attacks
    
    # Normal Paths (Whitelisted)
    normal_paths = [
        "user.name", "user.id", "order.id", "order.amount", 
        "payload.metadata", "payload.timestamp"
    ]
    
    # Attack Paths (Vulnerability Targets)
    # 'payload.content' is the target of Log4Shell-like injection
    attack_paths = ["payload.content"] 
    
    # Unknown Paths (Not in whitelist, should be denied by default)
    unknown_paths = ["admin.debug", "system.env", "hidden.api"]

    # Generate Normal Traffic
    for _ in range(num_normal):
        path = random.choice(normal_paths)
        dataset.append({"type": "NORMAL", "path": path})
        
    # Generate Attack Traffic
    for _ in range(num_attacks):
        path = random.choice(attack_paths)
        dataset.append({"type": "ATTACK", "path": path})
        
    random.shuffle(dataset)
    return dataset

# ----------------------------------------------------------------------
# 2. Simulation Logic
# ----------------------------------------------------------------------

def run_attack_simulation():
    print("--- 🛡️ Phase 15: Security Evaluation (Attack Simulation) ---")
    
    # Initialize Engines
    # Both nodes start with the same policy (Allowing payload.content for business logic)
    node_a = HierarchicalPolicyEngine()
    node_b = HierarchicalPolicyEngine()
    
    initial_whitelist = [
        "user.name", "user.id", "order.id", "order.amount", 
        "payload.metadata", "payload.timestamp", "payload.content" # Initially allowed!
    ]
    
    for path in initial_whitelist:
        node_a.allow_path(path)
        node_b.allow_path(path)
        
    print(f"\n[Init] Nodes A & B initialized. 'payload.content' is ALLOWED (Business Requirement).")

    # ------------------------------------------------------------------
    # Phase 1: Zero-day Attack on Node A
    # ------------------------------------------------------------------
    print("\n>> Phase 1: Zero-day Attack on Node A")
    target_path = "payload.content"
    
    # Check access
    result_a = node_a.check_access(target_path)
    print(f"Attacker sends payload to Node A ('{target_path}'). Result: {result_a}")
    
    if result_a == "ALLOWED":
        print("🚨 COMPROMISE DETECTED! Node A is infected via Zero-day vulnerability.")
        
        # Response: Epigenetic Suppression
        print("   -> Response: Suppressing (Methylating) 'payload.content' on Node A.")
        node_a.suppress_path(target_path)
        
        # Verify Suppression
        print(f"   -> Node A status for '{target_path}': {node_a.check_access(target_path)}")
    else:
        print("Unexpected: Attack blocked initially?")

    # ------------------------------------------------------------------
    # Phase 2: Transduction (Immunity Transfer)
    # ------------------------------------------------------------------
    print("\n>> Phase 2: Transduction (Immunity Transfer A -> B)")
    print(f"Before Transduction, Node B status for '{target_path}': {node_b.check_access(target_path)}")
    
    # Transduce
    node_b.transduce_immunity(node_a)
    print("   -> Transduction Complete.")
    
    print(f"After Transduction, Node B status for '{target_path}': {node_b.check_access(target_path)}")
    if node_b.check_access(target_path) == "BLOCKED_SUPPRESSED":
        print("✅ Node B has acquired immunity!")
    else:
        print("❌ Transduction Failed.")

    # ------------------------------------------------------------------
    # Phase 3: Massive Attack on Node B
    # ------------------------------------------------------------------
    print("\n>> Phase 3: Massive Attack Simulation on Node B (1,000 Requests)")
    dataset = generate_traffic_dataset(total_requests=1000, attack_ratio=0.2)
    
    stats = {
        "total": 0,
        "normal_allowed": 0,
        "normal_blocked": 0,
        "attack_blocked": 0,
        "attack_allowed": 0
    }
    
    start_time = time.time()
    
    for req in dataset:
        stats["total"] += 1
        res = node_b.check_access(req["path"])
        
        if req["type"] == "NORMAL":
            if res == "ALLOWED":
                stats["normal_allowed"] += 1
            else:
                stats["normal_blocked"] += 1 # False Positive (should not happen for whitelisted)
        elif req["type"] == "ATTACK":
            if res == "BLOCKED_SUPPRESSED" or res == "DENIED_NOT_FOUND":
                stats["attack_blocked"] += 1
            else:
                stats["attack_allowed"] += 1 # False Negative (Critical Failure)
                
    duration = time.time() - start_time
    
    # ------------------------------------------------------------------
    # 4. Report
    # ------------------------------------------------------------------
    print("\n" + "="*40)
    print("       SECURITY EVALUATION REPORT       ")
    print("="*40)
    print(f"Total Requests Processed: {stats['total']}")
    print(f"Execution Time: {duration:.4f}s")
    print("-" * 40)
    print(f"Normal Requests Allowed : {stats['normal_allowed']} / 800")
    print(f"Attacks Blocked         : {stats['attack_blocked']} / 200")
    print("-" * 40)
    
    fp_rate = (stats['normal_blocked'] / 800) * 100 if 800 > 0 else 0
    fn_rate = (stats['attack_allowed'] / 200) * 100 if 200 > 0 else 0
    
    print(f"False Positive Rate (Normal Blocked): {fp_rate:.1f}%")
    print(f"False Negative Rate (Attack Allowed): {fn_rate:.1f}%")
    
    if fn_rate == 0.0 and fp_rate == 0.0:
        print("\n🏆 RESULT: PERFECT DEFENSE. Epigenetic Symbiosis is effective.")
    else:
        print("\n⚠️ RESULT: DEFENSE IMPERFECT. Check logic.")

if __name__ == "__main__":
    run_attack_simulation()
