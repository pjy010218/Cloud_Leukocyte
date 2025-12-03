# -*- coding: utf-8 -*-
#
# Phase 20: Service Identity Policy Generator (IAM Role Policy)
# Aggregates permissions from Flow-Specific SSoT to generate Service Identity PoLP.

import json
from typing import Dict, Set, Any, List
from schemas import PolicyDraft, MergedPolicy
import policy_integrator

def analyze_service_permissions(ssot_map: Dict[str, MergedPolicy]) -> Dict[str, Set[str]]:
    """
    Analyzes the SSoT map to calculate the Union of permissions for each Source Service.
    
    Args:
        ssot_map: Dictionary of {flow_id: MergedPolicy}
        
    Returns:
        Dict[service_id, Set[allowed_fields]]: Map of service ID to its aggregated permissions.
    """
    service_permissions: Dict[str, Set[str]] = {}
    
    # Initialize known services (including those that might not be sources)
    # In a real system, this would come from a service registry.
    # Here we infer from the flows and add known receivers if needed.
    known_services = set()
    
    for flow_id, policy in ssot_map.items():
        # Parse Flow ID: "SourceService->TargetService:/endpoint"
        try:
            services_part = flow_id.split(":")[0] # "Source->Target"
            source_service, target_service = services_part.split("->")
            
            known_services.add(source_service)
            known_services.add(target_service)
            
            if source_service not in service_permissions:
                service_permissions[source_service] = set()
                
            # Union Logic (Rule: Service needs permissions for ALL its outgoing flows)
            service_permissions[source_service].update(policy.minimum_allowed_fields)
            
        except ValueError:
            print(f"[WARN] Invalid Flow ID format: {flow_id}")
            continue
            
    # Ensure all known services exist in the map (Receivers might have empty sets)
    for service in known_services:
        if service not in service_permissions:
            service_permissions[service] = set()
            
    return service_permissions

def generate_mock_iam_policy(service_id: str, required_fields: Set[str]) -> Dict[str, Any]:
    """
    Generates a Mock IAM Policy for a given service.
    """
    policy = {
        "Version": "2025-10-17",
        "Statement": [
            {
                "Sid": f"SymbiosisPoLPFor{service_id}",
                "Effect": "Allow",
                "Action": ["symbiosis:SendPayload"],
                "Resource": "*", # In a real IAM, this might be specific endpoints
                "Condition": {
                    "ForAllValues:StringEquals": {
                        "symbiosis:AllowedFields": sorted(list(required_fields))
                    }
                }
            }
        ]
    }
    
    # Optimization: If no fields are allowed (Receiver only), Deny All or Empty Allow
    if not required_fields:
        policy["Statement"][0]["Effect"] = "Deny"
        policy["Statement"][0]["Action"] = ["symbiosis:*"]
        del policy["Statement"][0]["Condition"]
        policy["Statement"][0]["Resource"] = "*"
        
    return policy

# ----------------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- 🆔 Phase 20: Service Identity Policy Generator ---")
    
    # 1. Generate SSoT from Policy Integrator (Simulate Phase 19)
    print("\n>> 1. Loading SSoT from Policy Integrator...")
    draft_objects = [PolicyDraft(**d) for d in policy_integrator.POLICY_DRAFT_INPUT]
    ssot_map = policy_integrator.merge_policies(draft_objects)
    
    # 2. Analyze Permissions
    print("\n>> 2. Analyzing Service Permissions (Union Logic):")
    service_perms = analyze_service_permissions(ssot_map)
    
    for service, fields in service_perms.items():
        print(f"  - {service}: {sorted(list(fields))}")

    # 3. Generate IAM Policies
    print("\n>> 3. Generating Mock IAM Policies:")
    
    # Scenario A: BillingService (Source)
    billing_policy = generate_mock_iam_policy("BillingService", service_perms.get("BillingService", set()))
    print(f"\n[IAM Policy: BillingService] (Source)")
    print(json.dumps(billing_policy, indent=4))
    
    # Scenario B: InventoryService (Receiver)
    inventory_policy = generate_mock_iam_policy("InventoryService", service_perms.get("InventoryService", set()))
    print(f"\n[IAM Policy: InventoryService] (Receiver Only)")
    print(json.dumps(inventory_policy, indent=4))
    
    # Verify Scenario B
    if inventory_policy["Statement"][0]["Effect"] == "Deny":
        print("\n✅ Verification Passed: InventoryService (Receiver) has DENY policy (No outgoing permissions).")
    else:
        print("\n❌ Verification Failed: InventoryService should have restricted permissions.")
