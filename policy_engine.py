import json
from typing import Set, Dict, Any

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

def generate_policy_output(final_set: Set[str], target_endpoint: str) -> str:
    """
    Generates a JSON policy specification from the final allowed field set.
    
    Args:
        final_set (Set[str]): The final set of allowed fields (M').
        target_endpoint (str): The target API endpoint.
        
    Returns:
        str: A JSON string representing the policy.
    """
    policy = {
        "policy_version": "1.0",
        "target_endpoint": target_endpoint,
        "allowed_fields": sorted(list(final_set)),
        "action": "ALLOW" if final_set else "DENY"
    }
    return json.dumps(policy, indent=4)

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
