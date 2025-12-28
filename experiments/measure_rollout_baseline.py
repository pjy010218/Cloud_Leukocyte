import time
import subprocess
import json
import statistics

# Configuration
RUNS = 3
NAMESPACE = "online-boutique"
DEPLOYMENT = "frontend"

def run_command(cmd, check=True):
    try:
        # Capture output to avoid spamming console
        subprocess.run(cmd, shell=True, check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def measure_rollout():
    latencies = []
    print(f"--- 🔄 Measuring K8s Rollout Baseline (Runs: {RUNS}) ---")
    
    for i in range(RUNS):
        print(f"   [Run {i+1}/{RUNS}]")
        
        # Trigger Rollout
        print("      Triggering Rollout Restart...")
        t0 = time.time()
        run_command(f"kubectl rollout restart deployment {DEPLOYMENT} -n {NAMESPACE}")
        
        # Wait for Completion
        try:
            # check=True ensures we wait for success
            subprocess.run(f"kubectl rollout status deployment {DEPLOYMENT} -n {NAMESPACE}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            t_end = time.time()
            
            latency = t_end - t0
            latencies.append(latency)
            print(f"      Latency: {latency:.2f}s")
            
        except subprocess.CalledProcessError:
            print("      [Error] Rollout failed.")
            
        # Cool down / Allow stabilization
        time.sleep(5)

    if latencies:
        avg = statistics.mean(latencies)
        print(f"\n✅ Average Rollout Latency: {avg:.2f}s")
        return avg
    return 0

if __name__ == "__main__":
    try:
        avg = measure_rollout()
        result = {"rollout_latency_seconds": avg}
        with open("baseline_measurements.json", "w") as f:
            json.dump(result, f, indent=2)
            
    except KeyboardInterrupt:
        pass
