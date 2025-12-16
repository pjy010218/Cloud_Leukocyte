import json
from typing import Dict, Any, Tuple, Optional, List, Set

class L7EnforcementFilter:
    """
    Simulates the Data Plane (Envoy) L7 enforcement filter.
    Focuses on O(1) field lookup performance (Rule P.1).
    """
    def __init__(self, allowed_fields_map: Dict[str, int]):
        """
        Args:
            allowed_fields_map: Hash Map for O(1) lookup of allowed fields.
                                Format: {"field_name": 1, ...}
        """
        # O(1) lookup structure
        self.allowed_fields_map = allowed_fields_map

    def _flatten_keys(self, data: Dict[str, Any], parent_key: str = '') -> Set[str]:
        """Helper to extract all keys in dot notation from the payload."""
        keys = set()
        for k, v in data.items():
            current_key = f"{parent_key}.{k}" if parent_key else k
            keys.add(current_key)
            if isinstance(v, dict):
                keys.update(self._flatten_keys(v, current_key))
        return keys

    def _delete_nested_field(self, data: Dict[str, Any], field_path: str):
        """
        Deletes a field specified by dot notation (e.g., 'user.address.city') from data.
        """
        parts = field_path.split('.')
        current = data
        # Traverse to the parent of the target field
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                return # Path doesn't exist, nothing to delete
        
        # Delete the target field
        target = parts[-1]
        if target in current:
            del current[target]

    def process_payload(self, payload_json: str, action: str = 'SCRUB') -> Tuple[Optional[str], bool]:
        """
        Processes the inbound JSON payload with nested field support.
        """
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            print("[Error] Invalid JSON format.")
            return None, False

        if not isinstance(payload, dict):
            print("[Error] Payload must be a JSON object.")
            return None, False

        # Identify unauthorized fields
        # We flatten the payload keys to check against the allowed map (which uses dot notation)
        input_fields = self._flatten_keys(payload)
        unauthorized_fields = []
        
        for field in input_fields:
            # Rule P.1: O(1) Lookup
            if field not in self.allowed_fields_map:
                unauthorized_fields.append(field)

        # Action: BLOCK
        if action == 'BLOCK':
            if unauthorized_fields:
                print(f"[BLOCK] Unauthorized fields detected: {unauthorized_fields}")
                return None, False
            
            # Check for missing essential fields
            # Note: Checking existence of nested fields in payload is complex without flattening.
            # We reuse input_fields (set of present keys) for efficient checking.
            missing_fields = [f for f in self.allowed_fields_map if f not in input_fields]
            if missing_fields:
                 print(f"[BLOCK] Missing essential fields: {missing_fields}")
                 return None, False
                 
            return json.dumps(payload), True

        # Action: SCRUB
        elif action == 'SCRUB':
            if unauthorized_fields:
                print(f"[SCRUB] Removing unauthorized fields: {unauthorized_fields}")
                # Sort by depth (descending) to delete children before parents if needed, 
                # though _delete_nested_field handles leaf deletion fine.
                # We iterate and delete.
                for field in unauthorized_fields:
                    self._delete_nested_field(payload, field)
            
            # Re-verify essential fields after scrubbing
            remaining_fields = self._flatten_keys(payload)
            missing_fields = [f for f in self.allowed_fields_map if f not in remaining_fields]
            if missing_fields:
                 print(f"[SCRUB FAIL] Missing essential fields after scrubbing: {missing_fields}")
                 return None, False
            
            return json.dumps(payload), True
        
        return None, False

# ----------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- L7 Enforcement Simulator Test ---")
    
    # Simulated Policy (O(1) Hash Map)
    # Policy: Only allow 'order_amount' and 'sku'
    policy_map = {"order_amount": 1, "sku": 1}
    filter_logic = L7EnforcementFilter(policy_map)
    
    # Case 1: Scrub Success
    # Payload has allowed fields + extra 'shipping_address' (unauthorized)
    print("\n[Case 1] Scrubbing Payload with Extra Fields")
    payload_1 = json.dumps({"order_amount": 100, "sku": "ITEM-123", "shipping_address": "123 Main St"})
    result_1, success_1 = filter_logic.process_payload(payload_1, action='SCRUB')
    print(f"Result: {result_1}, Success: {success_1}")
    
    # Case 2: Block Success
    # Payload has unauthorized field 'malicious_code', Action is BLOCK
    print("\n[Case 2] Blocking Payload with Unauthorized Fields")
    payload_2 = json.dumps({"order_amount": 100, "sku": "ITEM-123", "malicious_code": "rm -rf /"})
    result_2, success_2 = filter_logic.process_payload(payload_2, action='BLOCK')
    print(f"Result: {result_2}, Success: {success_2}")
    
    # Case 3: Nested Fields (Challenge)
    print("\n[Case 3] Nested Fields Challenge")
    # Current implementation only checks top-level keys.
    # Nested fields like "user.address" are not flattened here (that's Policy Engine's job to define the map).
    # If the policy map expects "user", and payload has "user": {...}, it passes.
    # But if policy expects "user.address", and payload has "user": {"address": ...}, 
    # the simple key check 'user' vs 'user.address' will fail or behave unexpectedly without flattening.
    # Future Work: Implement recursive checking or flattening at the enforcement layer.
    payload_3 = json.dumps({"order_amount": 100, "sku": "ITEM-123", "user": {"address": "Seoul"}})
    print(f"Payload: {payload_3}")
    print("Note: This simulator currently handles flat keys. Nested field enforcement requires hierarchical set logic or flattening middleware.")
    result_3, success_3 = filter_logic.process_payload(payload_3, action='SCRUB')
    print(f"Result: {result_3}, Success: {success_3}")
