import collections
from typing import Dict, Any, Set, Tuple, List

class TrafficProfiler:
    """
    Analyzes runtime traffic logs to statistically extract the required field sets (D and I).
    This acts as the 'Learning' phase of the Leukocyte system.
    """
    def __init__(self):
        """
        Initializes the profiler with frequency counters.
        """
        # Frequency counters for fields
        self.requester_field_counts = collections.Counter()
        self.receiver_field_counts = collections.Counter()
        
        # Total number of logs processed
        self.total_logs = 0

    def _extract_all_keys(self, data: Dict[str, Any], parent_key: str = '') -> Set[str]:
        """
        Recursively extracts all keys from a nested dictionary in dot notation.
        Example: {"user": {"address": {"city": "Seoul"}}} -> {"user", "user.address", "user.address.city"}
        
        Note: Whether to include intermediate keys (e.g. "user", "user.address") depends on policy.
        Here we include leaf nodes and intermediate nodes to allow fine-grained control.
        """
        keys = set()
        for k, v in data.items():
            current_key = f"{parent_key}.{k}" if parent_key else k
            keys.add(current_key)
            if isinstance(v, dict):
                keys.update(self._extract_all_keys(v, current_key))
        return keys

    def ingest_traffic_log(self, log_entry: Dict[str, Any]):
        """
        Ingests a single traffic log entry and updates field frequency counts.
        Supports nested fields via recursive extraction.
        
        Args:
            log_entry: A dictionary containing 'requester_payload' and 'receiver_payload'.
        """
        self.total_logs += 1
        
        # Extract fields from requester payload (D candidate)
        if 'requester_payload' in log_entry:
            flattened_keys = self._extract_all_keys(log_entry['requester_payload'])
            for field in flattened_keys:
                self.requester_field_counts[field] += 1
                
        # Extract fields from receiver payload (I candidate)
        if 'receiver_payload' in log_entry:
            flattened_keys = self._extract_all_keys(log_entry['receiver_payload'])
            for field in flattened_keys:
                self.receiver_field_counts[field] += 1

    def generate_field_set(self, threshold: float = 0.95) -> Tuple[Set[str], Set[str]]:
        """
        Generates the dynamic field sets based on statistical frequency.
        
        Args:
            threshold: The percentage (0.0 to 1.0) of traffic a field must appear in to be included.
                       Default is 0.95 (95%).
                       
        Returns:
            Tuple[Set[str], Set[str]]: (Requester Set D, Receiver Set I)
        """
        if self.total_logs == 0:
            return set(), set()
            
        d_set = set()
        i_set = set()
        
        # Calculate D Set (Requester)
        for field, count in self.requester_field_counts.items():
            frequency = count / self.total_logs
            if frequency >= threshold:
                d_set.add(field)
                
        # Calculate I Set (Receiver)
        for field, count in self.receiver_field_counts.items():
            frequency = count / self.total_logs
            if frequency >= threshold:
                i_set.add(field)
                
        return d_set, i_set

# ----------------------------------------------------------------------
# Test / Simulation
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("--- Policy Profiler Simulation (Dynamic Learning) ---")
    
    profiler = TrafficProfiler()
    
    # Mock Traffic Data
    # Scenario: 
    # - 'order_id', 'timestamp': Essential fields (Always present)
    # - 'user_agent': High frequency metadata (90% present)
    # - 'optional_comment': Rare field (10% present)
    # - 'debug_trace': Very rare (1% present)
    
    mock_logs = []
    
    # Generate 100 log entries
    for i in range(100):
        entry = {
            "requester_payload": {
                "order_id": f"ORD-{i}",
                "timestamp": 1234567890 + i
            },
            "receiver_payload": {
                "status": "processing",
                "ack_id": f"ACK-{i}"
            }
        }
        
        # Add 'user_agent' to 90% of logs
        if i < 90:
            entry["requester_payload"]["user_agent"] = "Mozilla/5.0..."
            
        # Add 'optional_comment' to 10% of logs
        if i < 10:
            entry["requester_payload"]["optional_comment"] = "Fast delivery please"
            
        mock_logs.append(entry)
        
    # Ingest logs
    print(f"Ingesting {len(mock_logs)} traffic logs...")
    for log in mock_logs:
        profiler.ingest_traffic_log(log)
        
    # Generate Sets with Threshold 0.95 (Strict)
    print("\n[Analysis 1] Strict Threshold (0.95)")
    D_strict, I_strict = profiler.generate_field_set(threshold=0.95)
    print(f"Dynamic Set D (Requester): {sorted(list(D_strict))}")
    print(f"Dynamic Set I (Receiver):  {sorted(list(I_strict))}")
    
    # Generate Sets with Threshold 0.80 (Lenient)
    print("\n[Analysis 2] Lenient Threshold (0.80)")
    D_lenient, I_lenient = profiler.generate_field_set(threshold=0.80)
    print(f"Dynamic Set D (Requester): {sorted(list(D_lenient))}")
    print(f"Dynamic Set I (Receiver):  {sorted(list(I_lenient))}")
    
    print("\n[Conclusion]")
    print(f"Excluded 'optional_comment' (10% freq) in both cases? {'optional_comment' not in D_lenient}")
    print(f"Included 'user_agent' (90% freq) in Lenient case? {'user_agent' in D_lenient}")
