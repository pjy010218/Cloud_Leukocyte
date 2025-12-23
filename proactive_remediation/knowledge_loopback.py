# -*- coding: utf-8 -*-
import sys
import os
import numpy as np
from neo4j import GraphDatabase
from typing import Dict, Any

# Adjust sys.path to include project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from adaptive_security.evolutionary_agent import EvolutionaryAgent, ACTION_SUPPRESS
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine

class KnowledgeLoopback:
    """
    Phase 25: Knowledge Loopback
    Converts RL Agent's ephemeral experience (Q-Table) into permanent wisdom (Neo4j Graph & SSoT Policy).
    """
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", auth: tuple = ("neo4j", "cve_password")):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=auth)

    def close(self):
        self.driver.close()

    def enrich_vulnerability_knowledge(self, path: str, cwe_id: str, rl_agent: EvolutionaryAgent, threshold: float = 100.0) -> bool:
        """
        If the RL agent has a high confidence (Q-Value) for suppressing a path, 
        record this as a DYNAMICALLY_TRIGGERED_BY relationship in the Knowledge Graph.
        """
        # 1. Check RL Confidence
        # Use a mock features dict to lookup state (In real system, we'd scan all states matching path)
        # For simplicity in this loopback, we assume we know the state or we iterate.
        # Here we iterate the Q-Table to find the max suppression value for this path.
        
        max_suppress_q = -float('inf')
        
        for state, q_values in rl_agent.q_table.items():
            # state is a tuple, index 0 is usually path (depending on implementation)
            # EvolutionaryAgent.get_state returns (path, q_anomaly, q_entropy, q_freq)
            if state[0] == path:
                q_val = q_values[ACTION_SUPPRESS]
                if q_val > max_suppress_q:
                    max_suppress_q = q_val
        
        if max_suppress_q < threshold:
            print(f"[LOOPBACK] Low confidence (Q={max_suppress_q:.2f} < {threshold}). Skipping graph enrichment.")
            return False

        print(f"[LOOPBACK] High confidence (Q={max_suppress_q:.2f}). Enriching Knowledge Graph...")

        # 2. Enrich Neo4j
        query = """
        MERGE (w:Weakness {id: $cwe_id})
        MERGE (vp:VulnerablePath {path: $path})
        MERGE (w)-[r:DYNAMICALLY_TRIGGERED_BY]->(vp)
        ON CREATE SET r.confidence = 1, r.created_at = timestamp()
        ON MATCH SET r.confidence = r.confidence + 1, r.updated_at = timestamp()
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, cwe_id=cwe_id, path=path)
            print(f"[LOOPBACK] SUCCESS: Mapped {cwe_id} -> {path} in Neo4j.")
            return True
        except Exception as e:
            print(f"[LOOPBACK ERROR] Neo4j Enrichment Failed: {e}")
            return False

    def sync_to_ssot(self, service_id: str, path: str, global_ssot: Dict[str, HierarchicalPolicyEngine]):
        """
        Persists the decision to the Single Source of Truth (Policy Engine), 
        ensuring the path is permanently suppressed for this service.
        """
        if service_id in global_ssot:
            engine = global_ssot[service_id]
            engine.suppress_path(path)
            print(f"[SSoT SYNC] Permanently suppressed '{path}' for {service_id}.")
        else:
            print(f"[SSoT ERROR] Service {service_id} not found in global map.")

# ----------------------------------------------------------------------
# Simulation / Verification
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- 🧠 Knowledge Loopback Module Verification ---")
    
    # 1. Setup Mock RL Agent
    mock_engine = HierarchicalPolicyEngine()
    agent = EvolutionaryAgent(mock_engine)
    
    # Train it to suppress 'payload.content'
    test_path = "payload.content"
    # Create a state tuple manually matching get_state format: (path, anomaly, entropy, freq)
    # Using the same quantization logic assumption
    test_state = (test_path, 2, 2, 0) # High anomaly/entropy, low freq
    agent.q_table[test_state] = [-50.0, 150.0] # Suppress Q=150.0
    
    # 2. Initialize Loopback
    loopback = KnowledgeLoopback()
    
    # 3. Test Enrichment (Neo4j)
    # Assume we identified this as CWE-502 from previous analysis
    cwe_target = "CWE-502"
    
    print("\n[TEST] 1. Enriching Vulnerability Knowledge...")
    success = loopback.enrich_vulnerability_knowledge(test_path, cwe_target, agent, threshold=100.0)
    
    if success:
        print("✅ Graph Enrichment Verification Passed.")
    else:
        print("❌ Graph Enrichment Failed.")
        sys.exit(1)
        
    # 4. Test SSoT Sync
    print("\n[TEST] 2. Syncing to SSoT...")
    ssot_map = {"LogService": mock_engine}
    loopback.sync_to_ssot("LogService", test_path, ssot_map)
    
    if mock_engine.check_access(test_path) == "BLOCKED_SUPPRESSED":
        print("✅ SSoT Persistence Verification Passed.")
    else:
        print("❌ SSoT Persistence Failed.")
        
    loopback.close()
