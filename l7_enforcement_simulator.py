import json
from typing import Dict, Any, Tuple, Optional, List

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

    def process_payload(self, payload_json: str, action: str = 'SCRUB') -> Tuple[Optional[str], bool]:
        """
        Processes the inbound JSON payload.
        
        Args:
            payload_json: The raw JSON string.
            action: 'SCRUB' (remove unauthorized fields) or 'BLOCK' (deny if unauthorized fields exist).
            
        Returns:
            Tuple[Optional[str], bool]: (Modified JSON string or None, Success/Allowed status)
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
        # Using list(payload.keys()) to iterate safely
        input_fields = list(payload.keys())
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
            
            # Check for missing essential fields (Requirement 3.2)
            # Assuming 'allowed_fields' are treated as 'required' for this simulation context
            missing_fields = [f for f in self.allowed_fields_map if f not in payload]
            if missing_fields:
                 print(f"[BLOCK] Missing essential fields: {missing_fields}")
                 return None, False
                 
            return json.dumps(payload), True

        # Action: SCRUB
        elif action == 'SCRUB':
            if unauthorized_fields:
                print(f"[SCRUB] Removing unauthorized fields: {unauthorized_fields}")
                for field in unauthorized_fields:
                    del payload[field]
            
            # Check for missing essential fields (Requirement 3.2)
            # "만약 필드 제거 후에도 필수 필드(allowed_fields) 중 하나라도 누락되었다면 정책 위반으로 간주합니다."
            missing_fields = [f for f in self.allowed_fields_map if f not in payload]
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
