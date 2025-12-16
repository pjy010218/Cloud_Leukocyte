# -*- coding: utf-8 -*-
#
# Phase 23: Cluster Scanner (Immune Surveillance Component 2)
# Analyzes an AttackSignature and cluster metadata to proactively identify vulnerable containers.

import random
from typing import Dict, Tuple, List, Optional, Any

# Mock CVE Database (for simulating static analysis correlation)
MOCK_CVE_DB: Dict[str, Dict] = {
    "CVE-2021-44228": {
        "name": "Log4Shell",
        "library": "log4j",
        "vulnerable_until": "2.17.0"  # 2.17.0 미만은 취약하다고 가정
    },
    "CVE-2022-22965": {
        "name": "Spring4Shell",
        "library": "spring-core",
        "vulnerable_until": "5.3.18" # 5.3.18 미만은 취약하다고 가정
    }
}

# Mock Cluster Metadata (Container Metadata)
MOCK_CLUSTER_METADATA: List[Dict[str, Any]] = [
    {"service_id": "AuthService", "image_name": "auth-v1", "lib_versions": {"log4j": "2.12.0", "spring-core": "5.3.0"}, "exposed_paths": ["user_agent", "login.data"]},
    {"service_id": "BillingService", "image_name": "billing-v2", "lib_versions": {"log4j": "2.16.0", "spring-core": "5.3.15"}, "exposed_paths": ["user_agent", "payload.content", "order.amount"]}, # Log4Shell, Spring4Shell 취약
    {"service_id": "InventoryService", "image_name": "inv-v1", "lib_versions": {"log4j": "2.17.1", "spring-core": "5.2.0"}, "exposed_paths": ["user_agent", "item.sku"]}, # Spring4Shell 취약
    {"service_id": "LogService", "image_name": "log-v3", "lib_versions": {"log4j": "2.12.0"}, "exposed_paths": ["payload.content", "timestamp"]}, # Log4Shell 취약
    {"service_id": "ShippingService", "image_name": "ship-v1", "lib_versions": {"log4j": "2.17.1"}, "exposed_paths": ["tracking.id"]}, # 취약하지 않음
]

class ClusterScanner:
    """
    Immune Surveillance: Analyzes the AttackSignature to find other vulnerable services 
    that might be susceptible to the same threat.
    """
    def __init__(self, cve_db: Dict[str, Dict] = MOCK_CVE_DB, cluster_metadata: List[Dict[str, Any]] = MOCK_CLUSTER_METADATA):
        self.cve_db = cve_db
        self.cluster_metadata = cluster_metadata

    def _parse_version(self, version: str) -> Tuple[int, ...]:
        """Parses version string into a tuple of integers."""
        try:
            return tuple(map(int, version.split('.')))
        except ValueError:
            return (0, 0, 0)

    def _is_version_vulnerable(self, container_libs: Dict[str, str], attack_cve_id: str) -> Optional[str]:
        """
        Static Analysis Mock: Checks if a container's library version is below the safe threshold.
        Returns the library name if vulnerable, otherwise None.
        """
        cve_info = self.cve_db.get(attack_cve_id)
        if not cve_info:
            return None

        lib_name = cve_info["library"]
        vulnerable_until = cve_info["vulnerable_until"]
        
        container_version = container_libs.get(lib_name)
        
        if container_version:
            # Semantic version comparison
            if self._parse_version(container_version) < self._parse_version(vulnerable_until):
                return lib_name
            
        return None

    def scan_cluster(self, attack_signature: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scans the cluster using the AttackSignature to identify containers that need prophylactic hardening.
        """
        vulnerable_containers: List[Dict[str, Any]] = []
        
        # 1. Signature Core: The path the RL Agent determined must be suppressed
        target_path = attack_signature["vulnerable_path"]
        
        # 2. Signature Core: Extract CVE IDs from static indicators (e.g., "CVE-2021-44228")
        cve_ids_found = [ind.split(':')[0] for ind in attack_signature["static_indicators"] if ind.startswith("CVE")]

        if not cve_ids_found:
            print("[SCANNER INFO] No known CVEs associated; Prophylactic Scan aborted.")
            return []

        # 3. Iterate through all containers (Immune Surveillance)
        for container in self.cluster_metadata:
            service_id = container["service_id"]
            reasons = []
            
            # Check Condition A: Is the vulnerable path exposed?
            is_path_exposed = target_path in container["exposed_paths"]
            
            # Check Condition B: Is the container vulnerable to the CVEs found?
            vulnerable_lib = None
            for cve_id in cve_ids_found:
                lib_vulnerable = self._is_version_vulnerable(container["lib_versions"], cve_id)
                if lib_vulnerable:
                    vulnerable_lib = lib_vulnerable
                    reasons.append(f"VULN_VERSION:{cve_id} ({lib_vulnerable} < {self.cve_db[cve_id]['vulnerable_until']})")
                    break # Found one match is enough for hardening

            # 4. Final Decision: Harden if both conditions met
            if is_path_exposed and vulnerable_lib:
                vulnerable_containers.append({
                    "service_id": service_id,
                    "reason": "PROPHYLACTIC_RISK",
                    "path_match": target_path,
                    "vulnerable_lib": vulnerable_lib,
                    "hardening_needed": True
                })
            elif not is_path_exposed and vulnerable_lib:
                 # 취약 버전이지만 경로가 노출 안 된 경우 (잠재적 위험)
                print(f"[SCANNER NOTE] {service_id}: VULN version ({vulnerable_lib}) but safe (Path not exposed).")
                
        return vulnerable_containers

# ----------------------------------------------------------------------
# Simulation Example
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- 🔬 Cluster Scanner (Immune Surveillance) Test ---")

    # Mock Attack Signature (Assumed to be Log4Shell related)
    # The Analyzer found this signature using RL and static checks
    mock_signature = {
        "signature_id": "RL-SIG-9999",
        "threat_level": "CRITICAL",
        "vulnerable_path": "payload.content", # RL Agent가 이 경로를 억제하기로 결정
        "feature_profile": {"anomaly_level": "HIGH"},
        "rl_suppress_q_value": 150.0,
        "static_indicators": ["CVE-2021-44228:ldap://"], # Log4Shell 시그니처 (Fixed Typo)
        "suggested_remediation": "EPIGENETIC_SUPPRESSION"
    }
    
    scanner = ClusterScanner()
    
    # 1. Scan Execution
    print(f"\n[SCANNING] Looking for services vulnerable to: {mock_signature['vulnerable_path']} and Log4Shell.")
    vulnerable_list = scanner.scan_cluster(mock_signature)
    
    # 2. Output Verification
    print(f"\n--- Vulnerable Services Identified ({len(vulnerable_list)} Total) ---")
    
    for service in vulnerable_list:
        print(f"✅ SERVICE: {service['service_id']} (Path: {service['path_match']}, Lib: {service['vulnerable_lib']})")
        
    # Expected Results Verification:
    # - BillingService: VULN (log4j 2.16.0) AND exposed 'payload.content' -> Should be identified.
    # - LogService: VULN (log4j 2.12.0) AND exposed 'payload.content' -> Should be identified.
    # - AuthService: NOT vulnerable version -> Should NOT be identified.
    # - InventoryService: NOT exposed 'payload.content' -> Should NOT be identified (even if vulnerable to Spring4Shell).

    if len(vulnerable_list) == 2 and vulnerable_list[0]['service_id'] == 'BillingService':
        print("\n✅ SUCCESS: Cluster Scan correctly identified susceptible targets for prophylactic hardening.")
    else:
        print("\n❌ FAIL: Cluster Scan missed targets or identified incorrect targets.")