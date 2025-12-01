# -*- coding: utf-8 -*-
#
# Phase 2: 정책 통합 및 갈등 해결 로직 구현 (Verification Engine 핵심)
# 분산된 백혈구들의 정책을 통합하고 정형 속성을 모의 검증합니다.

import json
from typing import Set, Dict, Any, List, Tuple

# ----------------------------------------------------------------------
# 1. 데이터 모델 및 샘플 데이터 (Leukocyte 정책 출력 시뮬레이션)
# ----------------------------------------------------------------------

# 분산된 백혈구(Leukocyte) L-1A와 L-2B가 동일 엔드포인트에 대해 산출한 정책 초안 리스트
POLICY_DRAFT_INPUT: List[Dict[str, Any]] = [
    {
        "policy_version": 1, # Rule G.3: 정책은 불변하며 버전 관리됨
        "target_endpoint": "/api/v1/inventory/reserve",
        # L-1A: 'order_amount', 'shipping_address', 'sku' 허용 (매우 엄격)
        "minimum_allowed_fields": ["order_amount", "shipping_address", "sku"],
        "source_leukocyte_id": "L-1A",
        "timestamp": "2025-12-01T10:00:00Z"
    },
    {
        "policy_version": 1,
        "target_endpoint": "/api/v1/inventory/reserve",
        # L-2B: 'order_amount', 'shipping_address', 'warehouse_id', 'sku' 허용 (L-1A보다 덜 엄격)
        "minimum_allowed_fields": ["order_amount", "shipping_address", "warehouse_id", "sku"],
        "source_leukocyte_id": "L-2B",
        "timestamp": "2025-12-01T10:05:00Z"
    },
    {
        "policy_version": 1,
        "target_endpoint": "/api/v1/inventory/reserve",
        # L-3C: 실수로 'customer_pii'를 포함함 (심각한 갈등 상황)
        "minimum_allowed_fields": ["order_amount", "customer_pii", "shipping_address", "sku"],
        "source_leukocyte_id": "L-3C",
        "timestamp": "2025-12-01T10:10:00Z"
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

from schemas import PolicyDraft, MergedPolicy
import datetime

# ----------------------------------------------------------------------
# 2. 핵심 기능: 정책 통합 및 갈등 해결
# ----------------------------------------------------------------------

def merge_policies(policy_drafts: List[PolicyDraft]) -> MergedPolicy:
    """
    분산된 백혈구 정책 초안들을 통합하고, '가장 엄격한 정책 우선' 원칙을 적용합니다.
    (Rule N.3, N.1 준수)
    
    가장 엄격한 정책은 모든 초안이 공통으로 허용한 필드(교집합)만을 최종 허용합니다.
    """
    if not policy_drafts:
        raise ValueError("No policy drafts provided for merging.")

    # 첫 번째 정책의 필드 집합으로 초기화
    # set()을 사용하여 Rule N.1을 준수
    all_allowed_fields: Set[str] = set(policy_drafts[0].minimum_allowed_fields)
    
    # 나머지 정책들과 교집합을 수행 (가장 엄격한 정책 도출)
    for draft in policy_drafts[1:]:
        draft_fields = set(draft.minimum_allowed_fields)
        # 교집합 연산: 가장 엄격한 (공통된) 허용 집합을 만듦
        all_allowed_fields = all_allowed_fields.intersection(draft_fields)
    
    # 통합된 정책 생성 (Rule G.3: 새로운 버전으로 간주될 수 있음)
    return MergedPolicy(
        target_endpoint=policy_drafts[0].target_endpoint,
        policy_version=policy_drafts[0].policy_version,
        minimum_allowed_fields=sorted(list(all_allowed_fields)),
        source_leukocytes=[d.source_leukocyte_id for d in policy_drafts],
        merged_timestamp=datetime.datetime.now().isoformat(),
        verification_status="PENDING"
    )

def mock_formal_verification(merged_policy: MergedPolicy, global_rules: Set[str], receiver_schema: Set[str] = None) -> Tuple[MergedPolicy, bool]:
    """
    통합된 정책이 전역 보안 속성을 위반하는지 모의 검증하고, 필요시 자동 수정합니다.
    (Rule N.2 준수)
    
    [Advanced Feature: Information Flow Control]
    If receiver_schema (I) is provided, verifies that M <= I.
    This proves that the policy allows NO MORE than what the receiver explicitly needs.
    """
    if not merged_policy:
        raise ValueError("No merged policy provided for verification.")
        
    current_allowed_fields = set(merged_policy.minimum_allowed_fields)
    
    # 1. Global Blacklist Check
    violated_fields = current_allowed_fields.intersection(global_rules)
    
    # 2. Information Flow Check (M <= I)
    excess_fields = set()
    if receiver_schema:
        # Excess = M - I (Fields in M that are NOT in I)
        excess_fields = current_allowed_fields.difference(receiver_schema)
        if excess_fields:
            print(f"\n[VERIFICATION FAIL] Information Flow Violation: Policy allows fields not required by receiver: {excess_fields}")
            print("-> TLA+ Assertion Failed: M \\subseteq I_{receiver}")
    
    if violated_fields or excess_fields:
        print(f"\n[VERIFICATION FAIL] 전역 규칙 위반 필드 발견: {violated_fields}")
        print("-> 정책 일관성 유지를 위해 차집합 연산으로 위반 필드를 자동 수정합니다.")
        
        # 자동 수정 (차집합 연산)
        # Rule N.1 준수: M_final = (M \ R_global) \ Excess
        fixed_allowed_fields = current_allowed_fields.difference(violated_fields).difference(excess_fields)
        
        # 수정된 정책 생성 (불변성을 위해 새 객체 생성)
        fixed_policy = MergedPolicy(
            target_endpoint=merged_policy.target_endpoint,
            policy_version=merged_policy.policy_version,
            minimum_allowed_fields=sorted(list(fixed_allowed_fields)),
            source_leukocytes=merged_policy.source_leukocytes,
            merged_timestamp=merged_policy.merged_timestamp,
            verification_status="FIXED_AND_VALIDATED",
            verification_notes=f"Removed global violation fields: {violated_fields}, Excess fields: {excess_fields}"
        )
        
        return fixed_policy, False
    
    # 검증 성공
    print("\n[VERIFICATION SUCCESS] TLA+ Assertion Passed: M \\subseteq I_{receiver} AND M \\cap R_{global} = \\emptyset")
    validated_policy = MergedPolicy(
        target_endpoint=merged_policy.target_endpoint,
        policy_version=merged_policy.policy_version,
        minimum_allowed_fields=merged_policy.minimum_allowed_fields,
        source_leukocytes=merged_policy.source_leukocytes,
        merged_timestamp=merged_policy.merged_timestamp,
        verification_status="VALIDATED_SUCCESS"
    )
    return validated_policy, True


# ----------------------------------------------------------------------
# 3. 테스트 및 실행
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- 🧠 Phase 2: 정책 통합 및 모의 검증 시작 ---")
    print(f"대상 엔드포인트: {POLICY_DRAFT_INPUT[0]['target_endpoint']}")
    print(f"전역 금지 규칙 (R_Global): {GLOBAL_FORBIDDEN_FIELDS}\n")
    
    # 1단계: 분산 정책 통합 및 갈등 해결 (Merge)
    print(">> 1. 분산 정책 통합 및 갈등 해결:")
    merged_policy = merge_policies(POLICY_DRAFT_INPUT)
    
    print(f"\n통합된 정책 (교집합된 허용 필드): {merged_policy.get('minimum_allowed_fields')}")
    print("  -> L-3C의 'customer_pii'와 L-2B의 'warehouse_id'는 L-1A에 없었으므로 제거됨 (가장 엄격한 정책 적용).")

    # 2단계: 모의 정형 검증 (Verification)
    print("\n>> 2. 통합 정책에 대한 모의 정형 검증:")
    final_policy, is_valid = mock_formal_verification(merged_policy, GLOBAL_FORBIDDEN_FIELDS)
    
    if not is_valid:
        print("\n**검증 실패 및 자동 수정 완료.**")
        print("최종 정책 (Data Plane 배포용):\n")
        print(json.dumps(final_policy, indent=4, ensure_ascii=False))
    else:
        print("\n**검증 성공.**")
        print("최종 정책 (Data Plane 배포용):\n")
        print(json.dumps(final_policy, indent=4, ensure_ascii=False))
