# -*- coding: utf-8 -*-
#
# Phase 3: 정책 컴파일러 및 실행 아티팩트 생성
# Control Plane의 정책을 Data Plane에서 고성능으로 실행하기 위한 아티팩트로 변환합니다.

import json
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# 1. 데이터 모델 (Input: Phase 2에서 검증된 정책)
# ----------------------------------------------------------------------

FINAL_VALIDATED_POLICY = {
    "target_endpoint": "/api/v1/inventory/reserve",
    "minimum_allowed_fields": ["order_amount", "shipping_address", "sku"],
    "verification_status": "VALIDATED_SUCCESS",
    "policy_version": 1,
    "merged_timestamp": "2025-12-01T12:00:00Z"
}

# ----------------------------------------------------------------------
# 2. 핵심 기능: 실행 아티팩트 컴파일 (O(1) Lookup 최적화)
# ----------------------------------------------------------------------

from schemas import MergedPolicy, ExecutionArtifact
import datetime

def compile_to_data_plane_artifact(validated_policy: MergedPolicy) -> ExecutionArtifact:
    """
    검증된 정책을 Data Plane(Envoy/eBPF)에서 즉시 사용할 수 있는 
    고성능 룩업(Lookup) 지향 아티팩트 형태로 변환합니다.
    
    [Rule P.1 준수: Minimize Data Plane Overhead]
    Data Plane은 수많은 패킷을 실시간으로 처리해야 하므로, 필드 검사 로직은
    반드시 O(1) 시간 복잡도를 가져야 합니다. 이를 위해 리스트 형태의 필드 목록을
    해시 맵(Dictionary) 구조로 변환합니다.
    """
    
    # 1. 필드 리스트 추출
    allowed_fields_list = validated_policy.minimum_allowed_fields
    
    # 2. O(1) Lookup을 위한 Hash Map 변환
    # Key: 필드명, Value: 1 (존재 여부만 확인하면 되므로 최소한의 값 사용)
    # Python의 Dictionary는 내부적으로 Hash Table로 구현되어 있어 평균 O(1) 접근 속도를 보장합니다.
    allowed_fields_map = {field: 1 for field in allowed_fields_list}
    
    # 3. 실행 아티팩트 생성
    return ExecutionArtifact(
        artifact_version="1.0",
        target_endpoint=validated_policy.target_endpoint,
        action="ALLOW",
        allowed_fields_map=allowed_fields_map,
        metadata={
            "source_policy_version": validated_policy.policy_version,
            "compiled_at": datetime.datetime.now().isoformat(),
            "optimization_note": "Optimized for O(1) field lookup using Hash Map."
        }
    )

def generate_ebpf_map_config(artifact: ExecutionArtifact) -> str:
    """
    Generates a C-style eBPF Map initialization snippet for the Data Plane.
    This demonstrates the "Realistic Data Plane Artifact" requirement.
    """
    c_code = []
    c_code.append(f"// eBPF Map Update for Endpoint: {artifact.target_endpoint}")
    c_code.append("// Map Type: BPF_MAP_TYPE_HASH")
    c_code.append("// Key: Field Name Hash (u32), Value: Allowed (u8)")
    
    for field_name in artifact.allowed_fields_map.keys():
        # Simulating a hash function for the field name
        field_hash = hash(field_name) & 0xFFFFFFFF
        c_code.append(f"uint32_t key_{field_name.replace('.', '_')} = {field_hash};")
        c_code.append(f"uint8_t value = 1;")
        c_code.append(f"bpf_map_update_elem(&policy_map, &key_{field_name.replace('.', '_')}, &value, BPF_ANY);")
        
    return "\n".join(c_code)

# ----------------------------------------------------------------------
# 3. 테스트 및 실행
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- 🚀 Phase 3: 정책 컴파일러 및 실행 아티팩트 생성 ---")
    print(f"입력 정책 (Validated Policy): {json.dumps(FINAL_VALIDATED_POLICY, indent=2)}")
    
    # 컴파일 실행
    execution_artifact = compile_to_data_plane_artifact(FINAL_VALIDATED_POLICY)
    
    print("\n>> 생성된 실행 아티팩트 (Data Plane Artifact):")
    print(json.dumps(execution_artifact, indent=4))
    
    print("\n[성능 최적화 확인]")
    print(f"Lookup Structure Type: {type(execution_artifact['allowed_fields_map'])}")
    print("-> Dictionary(Hash Map) 구조를 사용하여 O(1) 필드 검사를 보장합니다.")
