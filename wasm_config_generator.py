# -*- coding: utf-8 -*-
#
# Phase 18: WASM Config Generator
# Converts Trie-based policies into JSON configuration for Envoy WASM filters.

import json
from typing import Dict, Any, List
from hierarchical_policy_engine import HierarchicalPolicyEngine, TrieNode

def serialize_trie_node(node: TrieNode) -> Dict[str, Any]:
    """
    Recursively serializes a TrieNode into a dictionary.
    """
    serialized = {
        "is_allowed": node.is_allowed,
        "is_suppressed": node.is_suppressed,
        "children": {}
    }
    
    for key, child in node.children.items():
        serialized["children"][key] = serialize_trie_node(child)
        
    return serialized

def extract_suppression_paths(node: TrieNode, current_path: str = "") -> List[str]:
    """
    Extracts a list of all suppressed paths for fast lookup in WASM.
    """
    paths = []
    if node.is_suppressed and current_path:
        paths.append(current_path)
        
    for key, child in node.children.items():
        new_path = f"{current_path}.{key}" if current_path else key
        paths.extend(extract_suppression_paths(child, new_path))
        
    return paths

def generate_wasm_filter_config(policy_engine: HierarchicalPolicyEngine) -> str:
    """
    Generates the final JSON configuration for the WASM filter.
    """
    root_node = policy_engine.root
    
    # 1. Serialize Trie Structure
    trie_structure = serialize_trie_node(root_node)
    
    # 2. Extract Suppression List (Optimization for WASM)
    suppression_list = extract_suppression_paths(root_node)
    
    # 3. Construct Final Config Envelope
    config = {
        "policy_id": "symbiosis-v1-epigenetic",
        "timestamp": "2025-12-02T12:00:00Z",
        "features": {
            "hierarchical_enforcement": True,
            "epigenetic_suppression": True
        },
        "suppression_paths": suppression_list, # Fast path for blocking
        "policy_trie": trie_structure          # Full structure for allowed checks
    }
    
    return json.dumps(config, indent=4)

# ----------------------------------------------------------------------
# Main Execution (Scenario)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- ⚙️ Phase 18: WASM Config Generator ---")
    
    # 1. Setup Policy Engine with Scenario
    engine = HierarchicalPolicyEngine()
    
    # Allow normal paths
    engine.allow_path("user.name")
    engine.allow_path("user.id")
    engine.allow_path("order.amount")
    
    # Suppress vulnerability (Log4Shell)
    # Note: Even if we didn't explicitly allow it, suppressing it ensures it's blocked if it matches a wildcard or future allow.
    # Here we simulate a case where it might have been allowed or we just want to block it explicitly.
    engine.suppress_path("payload.content")
    
    # 2. Generate Config
    json_config = generate_wasm_filter_config(engine)
    
    print("\n[Generated WASM Config]")
    print(json_config)
    
    # Save to file
    with open("envoy_wasm_config.json", "w") as f:
        f.write(json_config)
    print("\n[Info] Config saved to 'envoy_wasm_config.json'")
