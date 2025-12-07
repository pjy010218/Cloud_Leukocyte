# -*- coding: utf-8 -*-
import time
from typing import Dict, Tuple, Set

class AdaptivePolicyEngine:
    """
    Adaptive Policy Engine that handles Schema Evolution using a Grace Period mechanism.
    Reduces False Positives for new, legitimate fields.
    """
    def __init__(self, grace_period=3600, threshold=100):
        self.whitelist: Set[str] = set()
        self.candidate_fields: Dict[str, Tuple[float, int]] = {}  # path -> (first_seen_timestamp, count)
        self.grace_period = grace_period  # Seconds before auto-whitelisting
        self.threshold = threshold        # Min requests before auto-whitelisting
    
    def allow_path(self, path: str):
        """Manually whitelist a path."""
        self.whitelist.add(path)

    def check_access(self, path: str) -> str:
        """
        Checks access with adaptive logic.
        Returns: "ALLOWED", "ALLOWED_TRIAL", "DENIED_UNKNOWN"
        """
        # 1. Whitelist Check
        if path in self.whitelist:
            return "ALLOWED"
        
        # 2. Candidate Check (Schema Evolution)
        current_time = time.time()
        
        if path in self.candidate_fields:
            first_seen, count = self.candidate_fields[path]
            
            # Check if criteria met for Auto-Whitelisting
            if (current_time - first_seen > self.grace_period) and (count > self.threshold):
                self.whitelist.add(path)
                del self.candidate_fields[path] # Promote to whitelist
                return "ALLOWED"
            
            # Update count
            self.candidate_fields[path] = (first_seen, count + 1)
            return "ALLOWED_TRIAL"  # Warn but allow (Grace Period)
        
        # 3. First Appearance
        self.candidate_fields[path] = (current_time, 1)
        return "DENIED_UNKNOWN" # Block first time or allow trial depending on policy. 
                                # User prompt said "ALLOWED_TRIAL" for candidates, 
                                # but usually first packet is blocked or allowed trial?
                                # User code:
                                # if path in candidate: ... return ALLOWED_TRIAL
                                # else: candidate[path] = ... return DENIED_UNKNOWN
                                # So first packet is DENIED.
        
# Test Scenario
if __name__ == "__main__":
    print("--- 🛡️ Adaptive Policy Engine Test ---")
    engine = AdaptivePolicyEngine(grace_period=0.1, threshold=5) # Fast settings for test
    
    path = "user.new_field"
    
    print(f"1. First access '{path}': {engine.check_access(path)}") 
    # Expected: DENIED_UNKNOWN (Added to candidates)
    
    print("   (Simulating traffic...)")
    for i in range(5):
        res = engine.check_access(path)
    print(f"2. 6th access '{path}': {res}")
    # Expected: ALLOWED_TRIAL
    
    print("   (Waiting for grace period...)")
    time.sleep(0.2)
    
    print(f"3. After grace period '{path}': {engine.check_access(path)}")
    # Expected: ALLOWED (Promoted)
    
    print(f"4. Verify Whitelist: {path in engine.whitelist}")
