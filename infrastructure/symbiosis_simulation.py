# -*- coding: utf-8 -*-
#
# Symbiosis Adaptive Security Framework: Final Integrated Simulation
# Phase 10: Full Lifecycle with Nested Field Support
# Flow: Profiler -> Engine -> Integrator -> Compiler -> L7 Enforcement

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import datetime
import logging
from typing import Set, Dict, Any, List

# Internal Module Imports
from policy_learning import policy_engine
from policy_integration import policy_integrator
from compilation import policy_compiler
from policy_learning import policy_profiler
from data_plane import l7_enforcement_simulator
from infrastructure.schemas import PolicyDraft, MergedPolicy, ExecutionArtifact

# ----------------------------------------------------------------------
# Logging Setup
# ----------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "component": getattr(record, "component", "Simulation")
        }
        return json.dumps(log_entry)

logger = logging.getLogger("SymbiosisLogger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

def log_info(message: str, component: str = "Simulation"):
    logger.info(message, extra={"component": component})

# ----------------------------------------------------------------------
# Simulation Logic
# ----------------------------------------------------------------------

def run_simulation():
    log_info("Starting Symbiosis Final Integration Simulation (Nested Fields)")

    # ----------------------------------------------------------------------
    # Step 1: Dynamic Profiling (Learning Phase)
    # ----------------------------------------------------------------------
    log_info("Step 1: Dynamic Profiling (Learning Phase)", "Profiler")
    
    profiler = policy_profiler.TrafficProfiler()
    
    # Mock Traffic Logs with Nested Fields
    traffic_logs = [
        # Legitimate Traffic
        {
            "requester_payload": {
                "order": {"id": "ORD-001", "amount": 100},
                "user": {"address": {"city": "Seoul", "zip": "12345"}}
            },
            "receiver_payload": {"status": "ok"}
        },
        {
            "requester_payload": {
                "order": {"id": "ORD-002", "amount": 200},
                "user": {"address": {"city": "Busan", "zip": "67890"}}
            },
            "receiver_payload": {"status": "ok"}
        },
        # Anomalous Traffic (Contains PII 'credit_card' and 'debug_info')
        {
            "requester_payload": {
                "order": {"id": "ORD-003", "amount": 300},
                "user": {"address": {"city": "Incheon"}, "credit_card": "4111-xxxx"},
                "debug_info": "trace_stack"
            },
            "receiver_payload": {"status": "ok"}
        }
    ]
    
    # Ingest Logs
    for log in traffic_logs:
        profiler.ingest_traffic_log(log)
        
    # Generate Dynamic Sets (Threshold 0.6 to include fields present in 2/3 logs)
    # We want to learn 'order.id', 'order.amount', 'user.address.city' etc.
    D_learned, _ = profiler.generate_field_set(threshold=0.6)
    log_info(f"Learned D Set (Requester): {sorted(list(D_learned))}", "Profiler")
    
    # ----------------------------------------------------------------------
    # Step 2: Policy Calculation (Engine Phase)
    # ----------------------------------------------------------------------
    log_info("Step 2: Policy Calculation (Engine Phase)", "Engine")
    
    # Define Receiver Schema I (Nested) - What the receiver actually needs
    # Note: Receiver might not need 'user.address.zip' strictly, but let's say it does.
    I_Receiver = {
        "order", "order.id", "order.amount", 
        "user", "user.address", "user.address.city", "user.address.zip"
    }
    
    # Calculate Minimum Set M = D \cap I
    M = policy_engine.calculate_minimum_set(D_learned, I_Receiver)
    
    # Create Policy Draft
    draft = policy_engine.generate_policy_output(M, "/api/v1/order/create", "L-AUTO")
    log_info(f"Calculated M: {draft.minimum_allowed_fields}", "Engine")

    # ----------------------------------------------------------------------
    # Step 3: Integration & Verification (Integrator Phase)
    # ----------------------------------------------------------------------
    log_info("Step 3: Integration & Verification (Integrator Phase)", "Integrator")
    
    # Merge (Single draft in this case, but logic holds)
    merged_policy = policy_integrator.merge_policies([draft])
    
    # Global Rules (Nested PII)
    GLOBAL_FORBIDDEN_FIELDS = {"user.credit_card", "debug_info"}
    
    # Verify
    # Verify
    validated_policies_map = policy_integrator.mock_formal_verification(
        merged_policy, 
        GLOBAL_FORBIDDEN_FIELDS
    )
    
    # Get the first (and only) policy
    if not validated_policies_map:
        log_info("Verification returned empty map.", "Integrator")
        return
        
    validated_policy = list(validated_policies_map.values())[0]
    
    if validated_policy.verification_status.startswith("VALIDATED"):
        log_info("Verification Passed.", "Integrator")
    else:
        log_info(f"Verification Check: {validated_policy.verification_status}", "Integrator")
    
    log_info(f"Final Validated Policy: {validated_policy.minimum_allowed_fields}", "Integrator")

    # ----------------------------------------------------------------------
    # Step 4: Compilation (Compiler Phase)
    # ----------------------------------------------------------------------
    log_info("Step 4: Compilation (Compiler Phase)", "Compiler")
    
    artifact = policy_compiler.compile_to_data_plane_artifact(validated_policy)
    log_info(f"Compiled Artifact Map: {json.dumps(artifact.allowed_fields_map)}", "Compiler")

    # ----------------------------------------------------------------------
    # Step 5: L7 Enforcement Simulation (Data Plane Phase)
    # ----------------------------------------------------------------------
    log_info("Step 5: L7 Enforcement Simulation (Data Plane Phase)", "Simulator")
    
    # Initialize Filter with Compiled Artifact
    l7_filter = l7_enforcement_simulator.L7EnforcementFilter(artifact.allowed_fields_map)
    
    # Test Payload 1: Legitimate (Should Pass)
    payload_legit = json.dumps({
        "order": {"id": "ORD-999", "amount": 500},
        "user": {"address": {"city": "Jeju", "zip": "99999"}}
    })
    
    res_legit, success_legit = l7_filter.process_payload(payload_legit, action='SCRUB')
    log_info(f"[Test 1] Legitimate Payload -> Success: {success_legit}", "Simulator")
    
    # Test Payload 2: Contains Unauthorized/PII Fields (Should be Scrubbed)
    # 'user.credit_card' is NOT in M (filtered by Intersection with I or Global Rules)
    # 'debug_info' is NOT in M
    payload_dirty = json.dumps({
        "order": {"id": "ORD-888", "amount": 600},
        "user": {"address": {"city": "Daegu", "zip": "12345"}, "credit_card": "4111-xxxx"},
        "debug_info": "dump"
    })
    
    res_dirty, success_dirty = l7_filter.process_payload(payload_dirty, action='SCRUB')
    log_info(f"[Test 2] Dirty Payload -> Success: {success_dirty}", "Simulator")
    log_info(f"Scrubbed Result: {res_dirty}", "Simulator")
    
    # Verify Scrubbing
    scrubbed_json = json.loads(res_dirty)
    if "credit_card" not in scrubbed_json.get("user", {}) and "debug_info" not in scrubbed_json:
        log_info("SUCCESS: PII and Unauthorized fields were correctly scrubbed.", "Simulator")
    else:
        log_info("FAILURE: Scrubbing failed.", "Simulator")

    log_info("Symbiosis Final Integration Simulation Complete.")

if __name__ == "__main__":
    run_simulation()
