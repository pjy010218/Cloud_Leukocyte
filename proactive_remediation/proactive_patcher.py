# -*- coding: utf-8 -*-
#
# Phase 23: Proactive Patcher (Immune Surveillance Component 3)
# Applies Epigenetic Suppression tags to services identified as susceptible by the Cluster Scanner.

from typing import Dict, Tuple, List, Optional, Any
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine

# ----------------------------------------------------------------------
# 1. CORE COMPONENT: ProactivePatcher
# ----------------------------------------------------------------------

class ProactivePatcher:
    """
    Applies immediate prophylactic hardening measures (Epigenetic Suppression) 
    to vulnerable containers identified during Immune Surveillance.
    """
    def __init__(self):
        pass

    def _simulate_network_isolation(self, service_id: str):
        """
        Mock: Simulates the immediate modification of the Istio NetworkPolicy 
        to isolate the vulnerable service, preventing further lateral movement.
        """
        print(f"   [NETWORK ISOLATION]: Service {service_id} is temporarily isolated (NetworkPolicy applied).")

    def apply_prophylactic_patch(self, 
                                 vulnerable_list: List[Dict[str, Any]], 
                                 engine_map: Dict[str, HierarchicalPolicyEngine]
                                 ) -> List[str]:
        """
        Applies Epigenetic Suppression tags to the identified vulnerable services.
        
        Args:
            vulnerable_list: List of dicts identifying services to harden (from ClusterScanner).
            engine_map: Map of all active HierarchicalPolicyEngine instances (the SSoT of policies).
            
        Returns:
            List of service IDs that were successfully hardened.
        """
        hardened_services: List[str] = []
        
        for container in vulnerable_list:
            service_id = container["service_id"]
            target_path = container["path_match"]
            
            if service_id not in engine_map:
                print(f"[ERROR] Engine for service {service_id} not found in map. Skipping.")
                continue

            engine = engine_map[service_id]
            
            # Phase 1: Epigenetic Suppression (Fastest defense mechanism)
            engine.suppress_path(target_path)
            
            print(f"✅ [SUPPRESSION APPLIED]: {service_id} hardened path '{target_path}' ({container['vulnerable_lib']}).")
            
            # Phase 2: Network Isolation (Additional containment)
            self._simulate_network_isolation(service_id)
            
            hardened_services.append(service_id)
            
        return hardened_services

# ----------------------------------------------------------------------
# 2. SIMULATION EXAMPLE
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- 🛠️ Proactive Patcher Test ---")

    # 1. Initialize Engines (Mock Environment)
    # Assume these services are running and have their own Trie policies
    billing_engine = HierarchicalPolicyEngine()
    log_engine = HierarchicalPolicyEngine()
    
    # Simulate: Billing and Log services initially allow the attack path
    billing_engine.allow_path("payload.content")
    log_engine.allow_path("payload.content")
    
    # Store engines in the map for Patcher to access
    engine_ssot_map = {
        "BillingService": billing_engine,
        "LogService": log_engine
    }

    # 2. Simulate Scanner Results (Input)
    # These services were found to be susceptible to the Log4Shell path
    mock_scanner_results = [
        {
            "service_id": "BillingService", 
            "reason": "PROPHYLACTIC_RISK", 
            "path_match": "payload.content", 
            "vulnerable_lib": "log4j 2.16.0",
            "hardening_needed": True
        },
        {
            "service_id": "LogService", 
            "reason": "PROPHYLACTIC_RISK", 
            "path_match": "payload.content", 
            "vulnerable_lib": "log4j 2.12.0",
            "hardening_needed": True
        }
    ]

    patcher = ProactivePatcher()
    
    # 3. Verify Initial State
    print("\n[Initial Verification]")
    print(f"BillingService access before patch: {billing_engine.check_access('payload.content')}")
    
    # 4. Apply Patches
    print("\n[Applying Prophylactic Patches]")
    hardened_list = patcher.apply_prophylactic_patch(mock_scanner_results, engine_ssot_map)

    # 5. Final Verification (Check Epigenetic Suppression Tag)
    print("\n[Final Verification]")
    
    final_status_billing = billing_engine.check_access('payload.content')
    final_status_log = log_engine.check_access('payload.content')
    
    print(f"BillingService access AFTER patch: {final_status_billing}")
    print(f"LogService access AFTER patch: {final_status_log}")

    if final_status_billing == "BLOCKED_SUPPRESSED" and final_status_log == "BLOCKED_SUPPRESSED":
        print("\n✅ SUCCESS: Proactive Patcher successfully applied Epigenetic Suppression to susceptible targets.")
    else:
        print("\n❌ FAIL: Suppression tag was not correctly applied or maintained.")