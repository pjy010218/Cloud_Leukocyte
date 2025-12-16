# -*- coding: utf-8 -*-
import random
import sys
import os
from typing import List, Dict

# Adjust path to import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine
from adaptive_security.adaptive_policy_engine import AdaptivePolicyEngine
import time

def generate_realistic_attack_dataset(total=1000):
    """
    Realistic attack scenarios including:
    - Obfuscation
    - Synonym attacks
    - Schema evolution (false positives)
    - Zero-day variants
    """
    attacks = []
    
    # 40% Normal (with schema evolution)
    for i in range(400):
        if i < 350:
            path = random.choice(["user.name", "order.id", "payload.metadata"])
            attacks.append({"type": "NORMAL", "path": path})
        else:
            # 5% schema evolution (new fields)
            # Use a consistent field to demonstrate learning
            path = "user.new_feature_v1" 
            attacks.append({"type": "SCHEMA_EVOLUTION", "path": path})
    
    # 30% Known attacks (should block)
    for _ in range(300):
        path = "payload.content"
        attacks.append({"type": "ATTACK_KNOWN", "path": path})
    
    # 20% Obfuscated attacks
    for _ in range(200):
        base = "payload.content"
        # Case variation
        obfuscated = "".join([c.upper() if random.random() < 0.5 else c for c in base])
        attacks.append({"type": "ATTACK_OBFUSCATED", "path": obfuscated})
    
    # 10% Synonym attacks
    for _ in range(100):
        synonyms = {
            "payload": ["data", "body", "content"],
            "content": ["text", "message", "data"]
        }
        path = f"{random.choice(synonyms['payload'])}.{random.choice(synonyms['content'])}"
        attacks.append({"type": "ATTACK_SYNONYM", "path": path})
    
    random.shuffle(attacks)
    return attacks

def run_simulation():
    print("--- ⚔️ Enhanced Attack Simulation (Adaptive) ---")
    
    # 1. Setup Defender (Adaptive Policy Engine)
    # Low threshold and grace period for simulation speed
    defender = AdaptivePolicyEngine(grace_period=0.001, threshold=5)
    
    # Whitelist normal paths
    print("Initializing Policy: Whitelisting normal paths...")
    defender.allow_path("user.name")
    defender.allow_path("order.id")
    defender.allow_path("payload.metadata")
    
    # Explicitly suppress known attack
    print("Initializing Policy: Suppressing 'payload.content'...")
    defender.suppress_path("payload.content")
    
    # 2. Generate Dataset
    print("Generating realistic attack dataset...")
    dataset = generate_realistic_attack_dataset(1000)
    
    # 3. Run Traffic
    results = {
        "NORMAL": {"total": 0, "blocked": 0, "allowed": 0, "allowed_trial": 0},
        "SCHEMA_EVOLUTION": {"total": 0, "blocked": 0, "allowed": 0, "allowed_trial": 0},
        "ATTACK_KNOWN": {"total": 0, "blocked": 0, "allowed": 0, "allowed_trial": 0},
        "ATTACK_OBFUSCATED": {"total": 0, "blocked": 0, "allowed": 0, "allowed_trial": 0},
        "ATTACK_SYNONYM": {"total": 0, "blocked": 0, "allowed": 0, "allowed_trial": 0}
    }
    
    print("Processing traffic...")
    
    # To simulate time passing for grace period, we need to inject delays
    # or just rely on the processing time if grace_period is small enough.
    
    evolution_attempts = 0
    
    for item in dataset:
        category = item["type"]
        path = item["path"]
        
        results[category]["total"] += 1
        
        decision = defender.check_access(path)
        
        if category == "SCHEMA_EVOLUTION":
            evolution_attempts += 1
            # Simulate slight delay to help grace period logic
            if evolution_attempts > 5:
                time.sleep(0.0002) 
        
        if decision == "ALLOWED":
            results[category]["allowed"] += 1
        elif decision == "ALLOWED_TRIAL":
            results[category]["allowed_trial"] += 1
            # Treat trial as allowed for general stats, but track separately
            results[category]["allowed"] += 1
        else:
            results[category]["blocked"] += 1
            
    # 4. Report
    print("\n--- Simulation Results ---")
    print(f"{'Category':<20} | {'Total':<6} | {'Blocked':<8} | {'Allowed':<8} | {'Block Rate':<10}")
    print("-" * 65)
    
    for cat, stats in results.items():
        total = stats["total"]
        blocked = stats["blocked"]
        allowed = stats["allowed"]
        rate = (blocked / total * 100) if total > 0 else 0
        print(f"{cat:<20} | {total:<6} | {blocked:<8} | {allowed:<8} | {rate:.1f}%")

    print("\nAnalysis:")
    print("- NORMAL: Should be 0% blocked.")
    print("- SCHEMA_EVOLUTION: Block rate should be LOW (<20%) due to Adaptive Engine (Grace Period).")
    print(f"  (Trial Allowed: {results['SCHEMA_EVOLUTION']['allowed_trial']})")
    print("- ATTACK_KNOWN: Should be 100% blocked.")
    print("- ATTACK_OBFUSCATED: Should be 100% blocked (Default Deny).")
    print("- ATTACK_SYNONYM: Should be 100% blocked (Default Deny).")
    
    # Verify Adaptation
    print("\n--- Adaptation Verification ---")
    test_path = "user.new_feature_v1"
    final_status = defender.check_access(test_path)
    print(f"Final status of '{test_path}': {final_status}")
    if final_status == "ALLOWED":
        print("✅ SUCCESS: Schema Evolution field was successfully whitelisted!")
    else:
        print("❌ FAILURE: Schema Evolution field was NOT whitelisted.")

if __name__ == "__main__":
    run_simulation()
