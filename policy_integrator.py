# -*- coding: utf-8 -*-
#
# Phase 2 & 19: 정책 통합 및 갈등 해결 로직 구현 (Verification Engine 핵심)
# 분산된 백혈구들의 정책을 통합하고 정형 속성을 모의 검증합니다.
# Phase 19 Update: Distributed Leukocytes (Flow-based Integration)

import json
import datetime
from typing import Set, Dict, Any, List, Tuple
from schemas import PolicyDraft, MergedPolicy

# ----------------------------------------------------------------------
# 1. 데이터 모델 및 샘플 데이터 (Leukocyte 정책 출력 시뮬레이션)
# ----------------------------------------------------------------------

# 분산된 백혈구(Leukocyte)들이 제출한 정책 초안 리스트
# Phase 19: Added 'flow_id' to distinguish traffic flows.
POLICY_DRAFT_INPUT: List[Dict[str, Any]] = [
    # Flow A: AuthService -> InventoryService (Minimal Access)
    {
        "flow_id": "AuthService->InventoryService:/api/v1/inventory/reserve",
        "policy_version": 2,
        "target_endpoint": "/api/v1/inventory/reserve",
        "minimum_allowed_fields": ["sku", "order_amount"], # Minimal
        "source_leukocyte_id": "L-Auth-1",
        "timestamp": "2025-12-01T10:00:00Z"
    },
    # Flow B: BillingService -> InventoryService (Rich Access)
    {
        "flow_id": "BillingService->InventoryService:/api/v1/inventory/reserve",
        "policy_version": 2,
        "target_endpoint": "/api/v1/inventory/reserve",
        "minimum_allowed_fields": ["sku", "order_amount", "shipping_address", "billing_code"], # Richer
        "source_leukocyte_id": "L-Billing-1",
        "timestamp": "2025-12-01T10:05:00Z"
    },
    # Flow B Conflict: Another Leukocyte for BillingService proposing stricter rules
    {
        "flow_id": "BillingService->InventoryService:/api/v1/inventory/reserve",
        "policy_version": 2,
        "target_endpoint": "/api/v1/inventory/reserve",
        "minimum_allowed_fields": ["sku", "order_amount", "shipping_address"], # Missing billing_code (Conflict)
        "source_leukocyte_id": "L-Billing-2",
        "timestamp": "2025-12-01T10:06:00Z"
    }
]

# 전역 보안 속성 (Global Security Property - Verification Engine에서 사용)
GLOBAL_FORBIDDEN_FIELDS: Set[str] = {
    "customer_pii",        # PII 데이터는 절대로 이 API를 통과할 수 없음
    "admin_token",         # 관리자 토큰은 데이터 페이로드에 포함 금지
    "private_key_hash"
}

# ----------------------------------------------------------------------
# 2. 핵심 기능: 정책 통합 및 갈등 해결
# ----------------------------------------------------------------------

def merge_policies(policy_drafts: List[PolicyDraft]) -> Dict[str, MergedPolicy]:
    """
    분산된 백혈구 정책 초안들을 Flow ID별로 통합합니다.
    
    Logic:
    1. Group drafts by `flow_id`.
    2. For each flow, apply Version Conflict Resolution (Max Version).
    3. For each flow, apply Intersection Logic (Strict Merge) for conflicts.
    
    Returns:
        Dict[flow_id, MergedPolicy]: A map of merged policies per flow.
    """
    if not policy_drafts:
        raise ValueError("No policy drafts provided for merging.")

    # 1. Group by Flow ID
    grouped_drafts: Dict[str, List[PolicyDraft]] = {}
    for draft in policy_drafts:
        if draft.flow_id not in grouped_drafts:
            grouped_drafts[draft.flow_id] = []
        grouped_drafts[draft.flow_id].append(draft)
        
    merged_results = {}
    
    for flow_id, drafts in grouped_drafts.items():
        # 2. Find Max Version per Flow
        max_version = max(d.policy_version for d in drafts)
        
        # Filter Drafts
        active_drafts = [d for d in drafts if d.policy_version == max_version]
        ignored_drafts = [d for d in drafts if d.policy_version < max_version]
        
        if ignored_drafts:
            print(f"[WARNING] Flow '{flow_id}': Ignoring {len(ignored_drafts)} drafts with older versions.")

        # 3. Intersection Logic (Strict Merge) within Flow
        # Rule N.1: Intersection of allowed fields
        all_allowed_fields: Set[str] = set(active_drafts[0].minimum_allowed_fields)
        
        for draft in active_drafts[1:]:
            draft_fields = set(draft.minimum_allowed_fields)
            all_allowed_fields = all_allowed_fields.intersection(draft_fields)
            
        # Create Merged Policy for this Flow
        merged_results[flow_id] = MergedPolicy(
            flow_id=flow_id,
            target_endpoint=active_drafts[0].target_endpoint,
            policy_version=max_version,
            minimum_allowed_fields=sorted(list(all_allowed_fields)),
            source_leukocytes=[d.source_leukocyte_id for d in active_drafts],
            merged_timestamp=datetime.datetime.now().isoformat(),
            verification_status="PENDING"
        )
        
    return merged_results

def check_policy_non_expansion(old_policy: Dict[str, Any], new_policy: Dict[str, Any]) -> bool:
    """
    [P4] Non-Expansion Property Check.
    M*_new <= M*_old
    """
    old_set = set(old_policy.get("minimum_allowed_fields", []))
    new_set = set(new_policy.get("minimum_allowed_fields", []))
    
    is_subset = new_set.issubset(old_set)
    
    if not is_subset:
        expanded_fields = new_set.difference(old_set)
        print(f"[P4 VIOLATION] Policy Expansion Detected! New fields added: {expanded_fields}")
        return False
        
    return True

def trace_policy_source(merged_policy: MergedPolicy, all_drafts: List[PolicyDraft]) -> Dict[str, List[str]]:
    """
    [P5] Policy Source Tracing.
    """
    trace_map = {}
    
    for field in merged_policy.minimum_allowed_fields:
        sources = []
        for draft in all_drafts:
            # Match Flow ID and Version
            if draft.flow_id == merged_policy.flow_id and draft.policy_version == merged_policy.policy_version:
                if field in draft.minimum_allowed_fields:
                    sources.append(draft.source_leukocyte_id)
        trace_map[field] = sources
        
    return trace_map

def mock_formal_verification(merged_policies: Dict[str, MergedPolicy], global_rules: Set[str]) -> Dict[str, MergedPolicy]:
    """
    Verifies ALL merged policies against global rules.
    """
    validated_policies = {}
    
    for flow_id, policy in merged_policies.items():
        current_allowed_fields = set(policy.minimum_allowed_fields)
        
        # Global Blacklist Check
        violated_fields = current_allowed_fields.intersection(global_rules)
        
        if violated_fields:
            print(f"\n[VERIFICATION FAIL] Flow '{flow_id}': Global Rule Violation: {violated_fields}")
            print("-> Auto-fixing by removing violated fields.")
            
            fixed_allowed_fields = current_allowed_fields.difference(violated_fields)
            
            fixed_policy = MergedPolicy(
                flow_id=policy.flow_id,
                target_endpoint=policy.target_endpoint,
                policy_version=policy.policy_version,
                minimum_allowed_fields=sorted(list(fixed_allowed_fields)),
                source_leukocytes=policy.source_leukocytes,
                merged_timestamp=policy.merged_timestamp,
                verification_status="FIXED_AND_VALIDATED",
                verification_notes=f"Removed global violation fields: {violated_fields}"
            )
            validated_policies[flow_id] = fixed_policy
        else:
            print(f"[VERIFICATION SUCCESS] Flow '{flow_id}': Validated.")
            validated_policy = MergedPolicy(
                flow_id=policy.flow_id,
                target_endpoint=policy.target_endpoint,
                policy_version=policy.policy_version,
                minimum_allowed_fields=policy.minimum_allowed_fields,
                source_leukocytes=policy.source_leukocytes,
                merged_timestamp=policy.merged_timestamp,
                verification_status="VALIDATED_SUCCESS"
            )
            validated_policies[flow_id] = validated_policy
            
    return validated_policies

# ----------------------------------------------------------------------
# 3. 테스트 및 실행
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- 🧠 Phase 19: Distributed Leukocyte Integration ---")
    
    # Convert Dict inputs to PolicyDraft objects
    draft_objects = [PolicyDraft(**d) for d in POLICY_DRAFT_INPUT]
    
    print(f"Total Drafts: {len(draft_objects)}")
    
    # 1. Merge (Flow-based)
    print("\n>> 1. Flow-based Policy Merge:")
    merged_map = merge_policies(draft_objects)
    
    for flow_id, policy in merged_map.items():
        print(f"\n[Flow] {flow_id}")
        print(f"  - Version: {policy.policy_version}")
        print(f"  - Allowed: {policy.minimum_allowed_fields}")
        print(f"  - Sources: {policy.source_leukocytes}")
        
        # Verify Flow Isolation
        if "AuthService" in flow_id:
            assert "billing_code" not in policy.minimum_allowed_fields, "AuthService should NOT see billing_code"
        if "BillingService" in flow_id:
            # Note: L-Billing-2 removed 'billing_code', so intersection should remove it too!
            # Wait, L-Billing-1 has it, L-Billing-2 does NOT. Intersection -> REMOVED.
            # This is correct behavior for "Most Strict Wins".
            pass

    # 2. Verification
    print("\n>> 2. Global Verification:")
    final_policies = mock_formal_verification(merged_map, GLOBAL_FORBIDDEN_FIELDS)
    
    print("\n[Final SSoT Map]")
    print(json.dumps({k: v.to_dict() for k, v in final_policies.items()}, indent=4, default=str))
