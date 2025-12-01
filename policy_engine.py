import json
from typing import Set, Dict, Any

from schemas import PolicyDraft
import datetime
from typing import List, Dict, Any, Set

def flatten_json(y: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flattens a nested JSON object into a single dictionary with dot-notation keys.
    Example: {"user": {"id": 1}} -> {"user.id": 1}
    """
    out = {}

    def flatten(x: Any, name: str = ''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '.')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '.')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out

def profile_traffic(traffic_logs: List[Dict[str, Any]]) -> Set[str]:
    """
    Analyzes a list of traffic logs (JSON payloads) and extracts the set of 
    fields that appear in the traffic. Handles nested fields via flattening.
    
    This simulates the 'Learning' phase where D (Requester Set) or I (Receiver Set)
    is derived from actual runtime behavior.
    """
    observed_fields = set()
    for log in traffic_logs:
        flattened = flatten_json(log)
        observed_fields.update(flattened.keys())
    return observed_fields

def calculate_minimum_set(requester_fields: Set[str], receiver_fields: Set[str]) -> Set[str]:
    """
    Calculates the Minimum Nutrient Set (M) by taking the intersection of
    the Requester's Desired Set (D) and the Receiver's Required Set (I).
    
    M = D ∩ I
    
    Args:
        requester_fields (Set[str]): The set of fields the sender wants to send (D).
        receiver_fields (Set[str]): The set of fields the receiver needs (I).
        
    Returns:
        Set[str]: The intersection set M.
    """
    return requester_fields.intersection(receiver_fields)

def calculate_forbidden_fields(allowed_set: Set[str], sensitive_set: Set[str]) -> Set[str]:
    """
    Calculates the Final Allowed Set (M') by removing any Forbidden Fields (R)
    from the Minimum Nutrient Set (M).
    
    M' = M \\ R
    
    Args:
        allowed_set (Set[str]): The Minimum Nutrient Set (M).
        sensitive_set (Set[str]): The set of strictly forbidden fields (R).
        
    Returns:
        Set[str]: The final allowed set M' with sensitive fields removed.
    """
    return allowed_set.difference(sensitive_set)

from schemas import PolicyDraft
import datetime

def generate_policy_output(final_set: Set[str], target_endpoint: str, leukocyte_id: str = "L-GENERIC") -> PolicyDraft:
    """
    Generates a PolicyDraft object from the final allowed field set.
    
    Args:
        final_set (Set[str]): The final set of allowed fields (M').
        target_endpoint (str): The target API endpoint.
        leukocyte_id (str): ID of the generating leukocyte.
        
    Returns:
        PolicyDraft: A structured policy draft object.
    """
    return PolicyDraft(
        policy_version=1,
        target_endpoint=target_endpoint,
        minimum_allowed_fields=sorted(list(final_set)),
        source_leukocyte_id=leukocyte_id,
        timestamp=datetime.datetime.now().isoformat()
    )

def main():
    # Sample Data
    
    # OrderService (D): Requester Desired Set
    D_OrderService = {"customer_id", "order_amount", "shipping_address", "internal_tracking_id"}
    
    # InventoryService (I): Receiver Required Set
    I_InventoryService = {"order_amount", "item_sku", "shipping_address", "warehouse_id"}
    
    # Security Policy (R): Forbidden Set
    R_SensitiveData = {"internal_tracking_id", "customer_credit_score", "private_key_hash"}
    
    # Target Endpoint
    Target_Endpoint = "/api/v1/inventory/reserve"
    
    print("--- Symbiosis Policy Engine (Leukocyte) Core Logic ---")
    print(f"Requester Set (D): {D_OrderService}")
    print(f"Receiver Set (I):  {I_InventoryService}")
    print(f"Forbidden Set (R): {R_SensitiveData}")
    print("-" * 50)
    
    # 1. Calculate Minimum Set M = D ∩ I
    M_MinimumSet = calculate_minimum_set(D_OrderService, I_InventoryService)
    print(f"1. Minimum Set (M = D ∩ I): {M_MinimumSet}")
    
    # 2. Calculate Final Set M' = M \ R
    M_Prime_FinalSet = calculate_forbidden_fields(M_MinimumSet, R_SensitiveData)
    print(f"2. Final Allowed Set (M' = M \\ R): {M_Prime_FinalSet}")
    
    # 3. Generate Policy Output
    policy_json = generate_policy_output(M_Prime_FinalSet, Target_Endpoint)
    print("-" * 50)
    print("3. Generated Policy Specification:")
    print(policy_json)

if __name__ == "__main__":
    main()
