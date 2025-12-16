# -*- coding: utf-8 -*-
#
# Phase 16: WASM Benchmark Driver
# Measures L7 processing latency of Trie-based vs Flat Set-based policies in an Envoy/WASM environment.

import sys
import time
import json
import random
import string
import threading
import http.server
import socketserver
from typing import Dict, Any, List

# Try importing requests, handle if missing (for standard lib compatibility)
try:
    import requests
except ImportError:
    # Minimal mock for requests if not installed
    class MockResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text
            self.elapsed = type('obj', (object,), {'total_seconds': lambda: 0.001})

    class MockRequests:
        def post(self, url, json=None, data=None):
            # For local mock server
            import urllib.request
            import urllib.parse
            
            data_bytes = None
            if json:
                data_bytes = json.dumps(json).encode('utf-8')
                headers = {'Content-Type': 'application/json'}
            elif data:
                data_bytes = data.encode('utf-8')
                headers = {}
            else:
                headers = {}
                
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method='POST')
            try:
                with urllib.request.urlopen(req) as f:
                    return MockResponse(f.status, f.read().decode('utf-8'))
            except Exception as e:
                print(f"Request failed: {e}")
                return MockResponse(500, str(e))

    requests = MockRequests()

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ENVOY_URL = "http://localhost:8000"
XDS_PUSH_URL = "http://localhost:5000/xds/push"

# ----------------------------------------------------------------------
# 1. Policy Generation
# ----------------------------------------------------------------------
def generate_random_string(length=5):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_policy_payload(num_fields: int, max_depth: int) -> Dict[str, Any]:
    """
    Generates a synthetic policy payload with nested fields.
    """
    fields = []
    for _ in range(num_fields):
        depth = random.randint(1, max_depth)
        parts = [generate_random_string() for _ in range(depth)]
        fields.append(".".join(parts))
        
    return {
        "policy_id": f"bench-{num_fields}-{max_depth}",
        "allowed_fields": fields,
        "timestamp": time.time()
    }

# ----------------------------------------------------------------------
# 2. xDS Interaction
# ----------------------------------------------------------------------
def push_policy_to_xds(policy_data: Dict[str, Any], xds_url: str):
    """
    Pushes the policy to the xDS server.
    """
    try:
        resp = requests.post(xds_url, json=policy_data)
        if resp.status_code != 200:
            print(f"[Error] Failed to push policy: {resp.status_code} {resp.text}")
        else:
            # print(f"[Info] Policy pushed successfully.")
            pass
    except Exception as e:
        print(f"[Error] Exception pushing policy: {e}")

# ----------------------------------------------------------------------
# 3. Load Testing
# ----------------------------------------------------------------------
def run_load_test(policy_type: str, num_requests: int) -> float:
    """
    Sends HTTP requests to Envoy and measures average latency.
    """
    latencies = []
    
    # Payload to send to Envoy (Traffic)
    traffic_payload = {
        "user": {"name": "test", "id": 123},
        "order": {"id": "ord-1", "amount": 100}
    }
    
    start_total = time.time()
    
    for _ in range(num_requests):
        req_start = time.time()
        try:
            resp = requests.post(ENVOY_URL, json=traffic_payload)
            # In a real requests lib, resp.elapsed.total_seconds() is available.
            # Here we calculate manually for safety.
            latency = (time.time() - req_start) * 1000 # ms
            latencies.append(latency)
        except Exception as e:
            print(f"[Error] Request failed: {e}")
            
    total_duration = time.time() - start_total
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    
    return avg_latency

# ----------------------------------------------------------------------
# 4. Mock Server (For Verification)
# ----------------------------------------------------------------------
class MockHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        # Simulate processing delay based on endpoint
        delay = 0.0
        if self.path == "/xds/push":
            delay = 0.01 # Fast config update
        else:
            # Simulate Envoy processing (WASM overhead)
            # Randomize slightly
            delay = random.uniform(0.002, 0.005) 
            
        time.sleep(delay)
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        
    def log_message(self, format, *args):
        return # Silence logs

def start_mock_servers():
    """Starts mock Envoy (8000) and xDS (5000) in background threads."""
    
    # Envoy Mock
    envoy_server = socketserver.TCPServer(("localhost", 8000), MockHandler)
    t1 = threading.Thread(target=envoy_server.serve_forever)
    t1.daemon = True
    t1.start()
    
    # xDS Mock
    xds_server = socketserver.TCPServer(("localhost", 5000), MockHandler)
    t2 = threading.Thread(target=xds_server.serve_forever)
    t2.daemon = True
    t2.start()
    
    print("[Mock] Servers started on ports 8000 (Envoy) and 5000 (xDS).")
    time.sleep(1) # Wait for startup

# ----------------------------------------------------------------------
# Main Benchmark Driver
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Check if we need to start mock servers (Argument flag)
    if len(sys.argv) > 1 and sys.argv[1] == "--mock":
        start_mock_servers()
    else:
        print("[Info] Assuming external Envoy/WASM environment is running.")
        print("       Run with '--mock' to use internal mock servers for verification.")

    print("--- 🚀 WASM Benchmark Driver ---")
    print(f"{'Scenario':<15} | {'N (Fields)':<10} | {'Engine':<10} | {'Avg Latency (ms)':<15}")
    print("-" * 60)
    
    # Scenarios
    field_counts = [100, 1000, 5000]
    
    for N in field_counts:
        # 1. Generate Policy
        policy = generate_policy_payload(N, max_depth=5)
        
        # 2. Test Flat Set (Baseline)
        # In real WASM, we'd push a config saying "use flat set mode"
        # Here we simulate it by pushing the policy and tagging it.
        policy["mode"] = "FLAT_SET"
        push_policy_to_xds(policy, XDS_PUSH_URL)
        
        # Warmup
        run_load_test("FLAT_SET", 10)
        
        # Measure
        latency_flat = run_load_test("FLAT_SET", 100)
        print(f"{'Scale-up':<15} | {N:<10} | {'Flat Set':<10} | {latency_flat:<15.4f}")
        
        # 3. Test Trie (Proposed)
        policy["mode"] = "TRIE"
        push_policy_to_xds(policy, XDS_PUSH_URL)
        
        # Warmup
        run_load_test("TRIE", 10)
        
        # Measure
        # Simulate Trie being slightly slower in Mock (or real measurement)
        # If using Mock, the delay is random, so results will be similar.
        # In real WASM, Trie would be slower.
        latency_trie = run_load_test("TRIE", 100)
        print(f"{'Scale-up':<15} | {N:<10} | {'Trie':<10} | {latency_trie:<15.4f}")

    print("\nBenchmark Complete.")
