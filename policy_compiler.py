# -*- coding: utf-8 -*-
#
# Phase 3: 정책 컴파일러 및 실행 아티팩트 생성
# Control Plane의 정책을 Data Plane에서 고성능으로 실행하기 위한 아티팩트로 변환합니다.

import json
from typing import Dict, Any, List

# ----------------------------------------------------------------------
# 1. 데이터 모델 (Input: Phase 2에서 검증된 정책)
# ----------------------------------------------------------------------

from schemas import MergedPolicy, ExecutionArtifact
import datetime

def compile_to_data_plane_artifact(policy_engine, target_endpoint: str, policy_version: int) -> ExecutionArtifact:
    """
    검증된 정책(HierarchicalPolicyEngine)을 Data Plane(Envoy/eBPF)에서 즉시 사용할 수 있는 
    고성능 룩업(Lookup) 지향 아티팩트 형태로 변환합니다.
    
    [Rule P.1 준수: Minimize Data Plane Overhead]
    Data Plane은 수많은 패킷을 실시간으로 처리해야 하므로, 필드 검사 로직은
    반드시 O(1) 시간 복잡도를 가져야 합니다. 이를 위해 Trie를 Flattening하여
    해시 맵(Dictionary) 구조로 변환합니다.
    """
    
    # 1. Trie Flattening (Compile-to-Flat)
    # HierarchicalPolicyEngine의 flatten() 메서드를 사용하여 모든 허용된 경로를 추출합니다.
    allowed_fields_list = policy_engine.flatten()
    
    # 2. O(1) Lookup을 위한 Hash Map 변환
    # Key: 필드명, Value: 1 (존재 여부만 확인하면 되므로 최소한의 값 사용)
    # Python의 Dictionary는 내부적으로 Hash Table로 구현되어 있어 평균 O(1) 접근 속도를 보장합니다.
    allowed_fields_map = {field: 1 for field in allowed_fields_list}
    
    # 3. 실행 아티팩트 생성
    return ExecutionArtifact(
        artifact_version="1.0",
        target_endpoint=target_endpoint,
        action="ALLOW",
        allowed_fields_map=allowed_fields_map,
        metadata={
            "source_policy_version": policy_version,
            "compiled_at": datetime.datetime.now().isoformat(),
            "optimization_note": "Optimized for O(1) field lookup using Hash Map (Compile-to-Flat)."
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

import urllib.request
import json

def push_to_xds(artifact: ExecutionArtifact, xds_server_url: str = "http://xds-server:8001/update"):
    """
    Converts the artifact into an Envoy Listener configuration and pushes it to the xDS server.
    This closes the loop by dynamically updating the Data Plane.
    """
    # 1. Construct Envoy Listener Config (Simplified)
    # We are creating a listener that uses the 'inventory_service' cluster but adds RBAC or Lua filtering
    # based on the allowed fields. For this PoC, we will just demonstrate pushing the *list* of allowed fields
    # to a hypothetical Lua filter configuration.
    
    allowed_fields_list = list(artifact.allowed_fields_map.keys())
    
    # In a real scenario, this would be a full Listener protobuf structure converted to JSON.
    # Here we construct the JSON structure expected by our mock xds_server.py
    
    envoy_config_update = {
        "version_info": str(int(datetime.datetime.now().timestamp())),
        "resources": [
            {
                "@type": "type.googleapis.com/envoy.config.listener.v3.Listener",
                "name": "listener_0",
                "address": {
                    "socket_address": {
                        "address": "0.0.0.0",
                        "port_value": 10000
                    }
                },
                "filter_chains": [{
                    "filters": [{
                        "name": "envoy.filters.network.http_connection_manager",
                        "typed_config": {
                            "@type": "type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager",
                            "stat_prefix": "ingress_http",
                            "route_config": {
                                "name": "local_route",
                                "virtual_hosts": [{
                                    "name": "local_service",
                                    "domains": ["*"],
                                    "routes": [{
                                        "match": {"prefix": "/"},
                                        "route": {"cluster": "inventory_service"}
                                    }]
                                }]
                            },
                            "http_filters": [
                                {
                                    "name": "envoy.filters.http.lua",
                                    "typed_config": {
                                        "@type": "type.googleapis.com/envoy.extensions.filters.http.lua.v3.Lua",
                                        "inline_code": f"""
                                            function envoy_on_request(request_handle)
                                                -- Symbiosis Enforced Policy
                                                -- Allowed Fields: {allowed_fields_list}
                                                local body = request_handle:body()
                                                if body then
                                                    local body_str = body:getBytes(0, body:length())
                                                    request_handle:logInfo("Inspecting Body: " .. body_str)
                                                    -- In a real implementation, we would parse JSON and check fields here.
                                                    -- For PoC, we just log the active policy.
                                                    request_handle:logInfo("Active Policy Allow List: {', '.join(allowed_fields_list)}")
                                                end
                                            end
                                        """
                                    }
                                },
                                {
                                    "name": "envoy.filters.http.router",
                                    "typed_config": {
                                        "@type": "type.googleapis.com/envoy.extensions.filters.http.router.v3.Router"
                                    }
                                }
                            ]
                        }
                    }]
                }]
            }
        ]
    }
    
    # 2. Push to xDS Server
    try:
        req = urllib.request.Request(
            xds_server_url, 
            data=json.dumps(envoy_config_update).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"Successfully pushed policy to xDS Server. Status: {response.status}")
    except Exception as e:
        print(f"Failed to push to xDS Server: {e}")


# ----------------------------------------------------------------------
# 3. 테스트 및 실행
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# 3. 테스트 및 실행
# ----------------------------------------------------------------------

if __name__ == "__main__":
    import dataclasses
    import sys
    
    # 3.1 모의 입력 데이터 (HierarchicalPolicyEngine)
    try:
        from hierarchical_policy_engine_cython import HierarchicalPolicyEngine
        print("[Info] Using Cython Engine")
    except ImportError:
        from hierarchical_policy_engine import HierarchicalPolicyEngine
        print("[Info] Using Python Engine")

    engine = HierarchicalPolicyEngine()
    engine.allow_path("order_amount")
    engine.allow_path("shipping_address.city")
    engine.allow_path("sku")
    
    # Suppression Test
    engine.allow_path("payload.content")
    engine.suppress_path("payload.content")

    print("--- 🚀 Phase 3: 정책 컴파일러 및 실행 아티팩트 생성 (Compile-to-Flat) ---")
    
    # 컴파일 실행
    execution_artifact = compile_to_data_plane_artifact(engine, "/api/v1/inventory/reserve", 1)
    
    print("\n>> 생성된 실행 아티팩트 (Data Plane Artifact):")
    print(json.dumps(dataclasses.asdict(execution_artifact), indent=4))
    
    print("\n[성능 최적화 확인]")
    print(f"Lookup Structure Type: {type(execution_artifact.allowed_fields_map)}")
    print("-> Dictionary(Hash Map) 구조를 사용하여 O(1) 필드 검사를 보장합니다.")

    # CLI Argument Handling for 'push'
    if len(sys.argv) > 1 and sys.argv[1] == "push":
        print("\n[Action] Pushing to xDS Server...")
        # Use localhost for manual experiment
        push_to_xds(execution_artifact, xds_server_url="http://127.0.0.1:8002/update")
