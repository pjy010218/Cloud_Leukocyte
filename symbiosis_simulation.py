# -*- coding: utf-8 -*-
#
# Symbiosis Adaptive Security Framework: Autopilot Simulation
# Orchestrates the full lifecycle: Calculation -> Integration -> Verification -> Compilation
# Phase 6: Advanced Research Features (Profiling, Nested Fields, Info Flow, eBPF)

import json
import datetime
import logging
from typing import Set, Dict, Any, List

# Internal Module Imports
import policy_engine
import policy_integrator
import policy_compiler
from schemas import PolicyDraft, MergedPolicy, ExecutionArtifact

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
# Step 0: Setup and Initial Data
# ----------------------------------------------------------------------

def run_simulation():
    log_info("Starting Symbiosis Simulation (Phase 6: Advanced Research Features)")

    # 0.1 Global Forbidden Fields
    GLOBAL_FORBIDDEN_FIELDS: Set[str] = {
        "user.credit_card",    # Nested PII
        "admin_token",
        "private_key_hash"
    }
    
    log_info(f"Global Security Rules: {list(GLOBAL_FORBIDDEN_FIELDS)}")

    TARGET_ENDPOINT = "/api/v1/order/create"
    
    # ----------------------------------------------------------------------
    # Step 1: Dynamic Profiling & Nested Fields (Phase 1 Advanced)
    # ----------------------------------------------------------------------
    log_info("Step 1: Dynamic Profiling & Nested Fields (Phase 1)", "Engine")
    
    # Simulate Raw Traffic Logs (Nested JSON)
    traffic_logs_L1A = [
        {"order": {"id": "101", "amount": 50}, "user": {"address": {"city": "Seoul"}}},
        {"order": {"id": "102", "amount": 60}, "user": {"address": {"city": "Busan"}}}
    ]
    
    traffic_logs_L2B = [
        {"order": {"id": "103", "amount": 50}, "user": {"address": {"city": "Seoul", "zip": "12345"}}}, # Extra field: zip
    ]
    
    traffic_logs_L3C = [
        {"order": {"id": "104", "amount": 50}, "user": {"credit_card": "4111-xxxx", "address": {"city": "Seoul"}}} # PII!
    ]
    
    # Profile Traffic to Extract D (Requester Set)
    D_L1A = policy_engine.profile_traffic(traffic_logs_L1A)
    log_info(f"[L-1A] Profiled D: {D_L1A}", "Engine")
    
    D_L2B = policy_engine.profile_traffic(traffic_logs_L2B)
    log_info(f"[L-2B] Profiled D: {D_L2B}", "Engine")
    
    D_L3C = policy_engine.profile_traffic(traffic_logs_L3C)
    log_info(f"[L-3C] Profiled D: {D_L3C} <--- WARNING: Contains Nested PII", "Engine")
    
    # Define Receiver Schema I (Nested)
    I_Receiver = {
        "order.id", "order.amount", "user.address.city", "user.address.zip"
    }
    log_info(f"Receiver Schema I: {I_Receiver}", "Engine")

    # Calculate Minimum Sets M = D \cap I
    policy_drafts: List[PolicyDraft] = []
    
    for idx, (D, leukocyte_id) in enumerate([(D_L1A, "L-1A"), (D_L2B, "L-2B"), (D_L3C, "L-3C")]):
        M = policy_engine.calculate_minimum_set(D, I_Receiver)
        draft = policy_engine.generate_policy_output(M, TARGET_ENDPOINT, leukocyte_id)
        policy_drafts.append(draft)
        log_info(f"[{leukocyte_id}] Calculated M: {draft.minimum_allowed_fields}", "Engine")

    # ----------------------------------------------------------------------
    # Step 2: Conflict Resolution (Phase 2)
    # ----------------------------------------------------------------------
    log_info("Step 2: Conflict Resolution (Phase 2)", "Integrator")
    merged_policy = policy_integrator.merge_policies(policy_drafts)
    log_info(f"Merged Policy: {merged_policy.minimum_allowed_fields}", "Integrator")

    # ----------------------------------------------------------------------
    # Step 3: Information Flow Verification (Phase 2 Advanced)
    # ----------------------------------------------------------------------
    log_info("Step 3: Information Flow Verification (Phase 2)", "Verifier")
    
    # Verify against Global Rules AND Information Flow (M <= I)
    # Note: In this simulation, M is derived from Intersection with I, so M <= I is naturally true.
    # To demonstrate the check, let's inject a field into Merged Policy that is NOT in I.
    
    # Injecting 'extra_field' to simulate a policy drift or attack
    merged_policy.minimum_allowed_fields.append("malicious.extra_field")
    log_info(f"Injecting 'malicious.extra_field' to test Information Flow Check...", "Verifier")
    
    validated_policy, is_valid = policy_integrator.mock_formal_verification(
        merged_policy, 
        GLOBAL_FORBIDDEN_FIELDS, 
        receiver_schema=I_Receiver # Passing I for Information Flow Check
    )
    
    if is_valid:
        log_info("Verification Passed.", "Verifier")
    else:
        log_info("Verification Failed (Auto-Corrected).", "Verifier")
        log_info(f"Final Validated Policy: {validated_policy.minimum_allowed_fields}", "Verifier")

    # ----------------------------------------------------------------------
    # Step 4: eBPF Artifact Generation (Phase 3 Advanced)
    # ----------------------------------------------------------------------
    log_info("Step 4: eBPF Artifact Generation (Phase 3)", "Compiler")
    
    artifact = policy_compiler.compile_to_data_plane_artifact(validated_policy)
    ebpf_code = policy_compiler.generate_ebpf_map_config(artifact)
    
    log_info("Generated eBPF Map Configuration:", "Compiler")
    print("\n--- eBPF Code Snippet ---")
    print(ebpf_code)
    print("-------------------------\n")
    
    log_info("Symbiosis Advanced Simulation Complete.")

if __name__ == "__main__":
    run_simulation()
