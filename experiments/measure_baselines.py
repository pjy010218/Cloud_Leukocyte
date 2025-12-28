import time
import subprocess
import json
import statistics
import threading
import sys
import os

# Configuration
RUNS = 5
NAMESPACE = "online-boutique"
TOOL_POD = "tool-pod"
TARGET_URL = "http://frontend"

PROBER_SCRIPT = """
import time
import urllib.request
import urllib.error
import sys
import os

target = "http://frontend"
headers = {"User-Agent": "mozilla-exploit-test"}
req = urllib.request.Request(target, headers=headers)

if os.path.exists("/tmp/blocked"):
    os.remove("/tmp/blocked")

print("Starting Prober...", flush=True)

while True:
    try:
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except urllib.error.HTTPError as e:
        if e.code == 403:
            with open("/tmp/blocked", "w") as f:
                f.write(str(time.time()))
            sys.exit(0)
    except Exception as e:
        pass
    time.sleep(0.005)
"""

AUTH_POLICY_YAML = f"""
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: baseline-deny-exploit
  namespace: {NAMESPACE}
spec:
  selector:
    matchLabels:
      app: frontend
  action: DENY
  rules:
  - to:
    - operation:
        methods: ["GET"]
    when:
    - key: request.headers[User-Agent]
      values: ["*exploit*"]
"""

def run_command(cmd, check=True):
    try:
        subprocess.run(cmd, shell=True, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def setup_environment():
    print("   [Setup] Preparing tool-pod...")
    with open("prober.py", "w") as f:
        f.write(PROBER_SCRIPT)
    
    run_command(f"kubectl cp prober.py {NAMESPACE}/{TOOL_POD}:/prober.py")
    run_command(f"kubectl delete envoyfilter --all -n {NAMESPACE}")
    run_command(f"kubectl delete authorizationpolicy baseline-deny-exploit -n {NAMESPACE}")
    time.sleep(5)

def check_health():
    try:
        cmd = f"kubectl exec -n {NAMESPACE} {TOOL_POD} -- python3 -c \"import urllib.request; print(urllib.request.urlopen('{TARGET_URL}').getcode())\""
        res = subprocess.check_output(cmd, shell=True, text=True).strip()
        if "200" in res:
            return True
    except:
        pass
    return False

def check_blocked_signal():
    try:
        cmd = f"kubectl exec -n {NAMESPACE} {TOOL_POD} -- cat /tmp/blocked 2>/dev/null"
        res = subprocess.check_output(cmd, shell=True, text=True).strip()
        if res:
            return float(res)
    except:
        pass
    return None

def measure_latency():
    latencies = []
    print(f"--- 🛡️ Measuring Istio AuthorizationPolicy Baseline (Runs: {RUNS}) ---")
    
    setup_environment()

    for i in range(RUNS):
        print(f"   [Run {i+1}/{RUNS}]")
        
        # 0. Health Check
        print("      Checking Health (200 OK)...")
        if not check_health():
             print("      [Error] Service not healthy (not 200). Resetting...")
             run_command(f"kubectl delete envoyfilter --all -n {NAMESPACE}")
             time.sleep(5)
             if not check_health():
                 print("      [Error] Still unhealthy. Skipping.")
                 continue

        # 1. Reset Signal
        run_command(f"kubectl exec -n {NAMESPACE} {TOOL_POD} -- rm -f /tmp/blocked")

        # 2. Start Prober Remote
        cmd = ["kubectl", "exec", "-n", NAMESPACE, TOOL_POD, "--", "python3", "-u", "/prober.py"]
        prober_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 3. Apply Policy
        print("      Applying Policy...")
        t_apply = time.time()
        with open("temp_policy.yaml", "w") as f:
            f.write(AUTH_POLICY_YAML)
        run_command(f"kubectl apply -f temp_policy.yaml")
        
        # 4. Poll for File Signal
        t_blocked = None
        start_wait = time.time()
        while (time.time() - start_wait) < 30:
            ts = check_blocked_signal()
            if ts:
                # We use t_apply as start, but ts (from inside pod) as end?
                # Clock skew risk.
                # Better: Use host time of *detection* as approximate end?
                # Or trust pod timestamp?
                # Minikube clock matches host usually.
                # Let's use Host Time of polling success as 'conservative' upper bound.
                # Or calculate skew?
                # Let's use Host Time. Latency = Time(Poll Success) - T(Apply).
                # But Poll interval is e.g. 0.1s.
                # We can optimize poll loop.
                t_blocked = time.time()
                break
            time.sleep(0.5)
        
        if t_blocked:
            latency = t_blocked - t_apply
            # Substrate overhead of `kubectl exec` poll?
            # It's unavoidable.
            latencies.append(latency)
            print(f"      Latency: {latency:.4f}s")
        else:
            print("      [Timeout] Policy did not take effect.")
        
        prober_proc.terminate()
        run_command(f"kubectl delete authorizationpolicy baseline-deny-exploit -n {NAMESPACE}")
        time.sleep(5)

    if latencies:
        avg = statistics.mean(latencies)
        print(f"\n✅ Average Istio Policy Latency: {avg:.4f}s")
        return avg
    return 0

if __name__ == "__main__":
    try:
        avg = measure_latency()
        result = {"istio_policy_latency_seconds": avg}
        with open("baseline_measurements.json", "w") as f:
            json.dump(result, f, indent=2)
            
        run_command("rm temp_policy.yaml prober.py")
    except KeyboardInterrupt:
        pass
