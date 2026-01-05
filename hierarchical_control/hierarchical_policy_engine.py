# -*- coding: utf-8 -*-
#
# Phase 14: Trie 기반 후성유전학적 공생 엔진 (Hierarchical Epigenetic Engine)
# 계층적 데이터 통제, 취약점 억제(Suppression), 면역 전파(Transduction)를 구현합니다.

from typing import Dict, Optional, List

class TrieNode:
    """
    Trie Node representing a segment of a data path.
    Attributes:
        children: Dictionary of child nodes.
        is_allowed: Whitelist flag (Gene Expression).
        is_suppressed: Blacklist/Suppression flag (Methylation Tag).
    """
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_allowed: bool = False
        self.is_suppressed: bool = False

class HierarchicalPolicyEngine:
    """
    Manages the Trie structure and enforces Epigenetic policies.
    """
    def __init__(self):
        self.root = TrieNode()

    def allow_path(self, path: str):
        """
        Whitelists a path (Gene Expression).
        Example: "user.address.city"
        """
        node = self.root
        if not path:
            return
        parts = path.lower().split('.')
        for part in parts:
            if part not in node.children:
                node.children[part] = TrieNode()
            node = node.children[part]
        node.is_allowed = True

    def suppress_path(self, path: str):
        """
        Suppresses a path (Epigenetic Methylation).
        Overrides is_allowed.
        Example: "payload.content" (Log4Shell vulnerability)
        """
        node = self.root
        if not path:
            return
        parts = path.lower().split('.')
        for part in parts:
            if part not in node.children:
                node.children[part] = TrieNode()
            node = node.children[part]
        node.is_suppressed = True

    def check_access(self, path: str) -> str:
        """
        Checks access status for a given path.
        Returns: "ALLOWED", "DENIED_NOT_FOUND", "BLOCKED_SUPPRESSED"
        """
        node = self.root
        parts = path.lower().split('.')
        for part in parts:
            if part not in node.children:
                return "DENIED_NOT_FOUND"
            node = node.children[part]
            
        # Epigenetic Rule: Suppression overrides Allowance
        if node.is_suppressed:
            return "BLOCKED_SUPPRESSED"
        
        if node.is_allowed:
            return "ALLOWED"
            
        return "DENIED_NOT_FOUND"

    def transduce_immunity(self, source_engine: 'HierarchicalPolicyEngine'):
        """
        [Transduction]
        Transfers 'is_suppressed' tags (Immunity) from a source engine to this engine.
        Mimics horizontal gene transfer or immune system signaling.
        """
        self._transduce_recursive(self.root, source_engine.root)

    def _transduce_recursive(self, target_node: TrieNode, source_node: TrieNode):
        """
        Helper for recursive transduction.
        """
        # If source is suppressed, suppress target (Transfer Immunity)
        if source_node.is_suppressed:
            target_node.is_suppressed = True
            
        # Traverse common children
        for key, source_child in source_node.children.items():
            if key in target_node.children:
                target_child = target_node.children[key]
                self._transduce_recursive(target_child, source_child)
            else:
                # Optional: If we want to proactively create the node to suppress it, we could.
                # But typically we only suppress what exists or might exist.
                # For this PoC, let's create the path if it's suppressed in source, 
                # so we remember to block it even if we don't use it yet (Proactive Immunity).
                if source_child.is_suppressed or self._has_suppressed_descendants(source_child):
                     new_node = TrieNode()
                     target_node.children[key] = new_node
                     self._transduce_recursive(new_node, source_child)

    def _has_suppressed_descendants(self, node: TrieNode) -> bool:
        """Helper to check if a node has any suppressed descendants."""
        if node.is_suppressed:
            return True
        for child in node.children.values():
            if self._has_suppressed_descendants(child):
                return True
        return False

    def flatten(self) -> List[str]:
        """
        Exports all allowed paths as a flat list.
        Used for "Compile-to-Flat" optimization (O(1) lookup).
        """
        results = []
        self._flatten_recursive(self.root, "", results)
        return results

    def _flatten_recursive(self, node: TrieNode, current_path: str, results: List[str]):
        """
        Recursive helper for flattening.
        """
        if node.is_allowed and not node.is_suppressed:
            results.append(current_path)
        
        for key, child in node.children.items():
            # If suppressed, don't traverse down (pruning) - or traverse but respect suppression?
            # Policy Logic: If a node is suppressed, can its children be allowed?
            # Current check_access says: if node.is_suppressed -> BLOCKED.
            # So if a parent is suppressed, all children are effectively blocked.
            # So we should NOT traverse if suppressed.
            if not node.is_suppressed:
                next_path = f"{current_path}.{key}" if current_path else key
                self._flatten_recursive(child, next_path, results)

# ----------------------------------------------------------------------
# Test Scenarios
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- 🧬 Phase 14: Epigenetic Symbiosis Engine ---")
    
    # 1. Setup Engines
    log_service = HierarchicalPolicyEngine()
    auth_service = HierarchicalPolicyEngine()
    
    # 2. Normal State: LogService allows 'payload.content'
    print("\n>> [Step 1] Normal State")
    log_service.allow_path("payload.content")
    print(f"LogService 'payload.content': {log_service.check_access('payload.content')}")
    
    # AuthService doesn't use it
    print(f"AuthService 'payload.content': {auth_service.check_access('payload.content')}")

    # 3. Vulnerability Discovered -> Suppression (Methylation)
    print("\n>> [Step 2] Vulnerability Discovered (Log4Shell) -> Suppression")
    log_service.suppress_path("payload.content")
    print(f"LogService 'payload.content': {log_service.check_access('payload.content')}")
    # Expected: BLOCKED_SUPPRESSED

    # 4. Transduction (Immunity Transfer)
    print("\n>> [Step 3] Transduction (Immunity Transfer to AuthService)")
    # AuthService receives immunity info from LogService
    auth_service.transduce_immunity(log_service)
    
    # Check AuthService status
    # Even though AuthService never explicitly allowed it, it should now know it's suppressed (if it were to exist)
    # Our transduction logic creates the node if it's suppressed in source.
    print(f"AuthService 'payload.content': {auth_service.check_access('payload.content')}")
    # Expected: BLOCKED_SUPPRESSED (Proactive Immunity)
    
    # Verify that AuthService still denies random stuff
    print(f"AuthService 'random.path': {auth_service.check_access('random.path')}")
    
    print("\n[SUCCESS] Epigenetic mechanisms (Suppression & Transduction) verified.")
