import matplotlib.pyplot as plt
import re
from datetime import datetime

# Load log data
log_file = "k8s_final_results_complete.txt"
with open(log_file, "r") as f:
    logs = f.readlines()

# Patterns to extract timestamps and events
events = []
# Example format: 2025-12-27 10:04:56,559 - [Leukocyte Controller] - ⚡ [ACTUATION] ...
timestamp_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")

# Key events to track
event_map = {
    "Applying Policy Update to BillingService": "BillingService Triggered",
    "Applying Policy Update to AdService": "AdService Triggered",
    "Applying Policy Update to LogService": "LogService Triggered",
    "EnvoyFilter 'leukocyte-wasm-filter-checkoutservice' successfully patched": "BillingService Patched",
    "EnvoyFilter 'leukocyte-wasm-filter' successfully patched": "AdService Patched",
    "Triggering Policy Updates for": "Immune Response Start"
}

parsed_data = []

for line in logs:
    match = timestamp_pattern.search(line)
    if match:
        ts_str = match.group(1)
        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")
        
        for key, description in event_map.items():
            if key in line:
                parsed_data.append((ts, description))
                break

# Sort by time
parsed_data.sort(key=lambda x: x[0])

if not parsed_data:
    print("No events found. Check log format.")
    exit(1)

# Normalize start time
start_time = parsed_data[0][0]
data_points = []
labels = []

print(f"Start Time (T0): {start_time}")

for ts, label in parsed_data:
    latency_ms = (ts - start_time).total_seconds() * 1000
    data_points.append(latency_ms)
    labels.append(f"{label}\n(+{latency_ms:.0f}ms)")
    print(f"{label}: +{latency_ms:.0f}ms")

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(data_points, [1]*len(data_points), "ro-")  # Red line, circle markers

# Annotate points
for i, label in enumerate(labels):
    plt.text(data_points[i], 1.02, label, rotation=45, ha='left', rotation_mode='anchor')

plt.title("Immune Response Latency Timeline (Transduction & Actuation)")
plt.xlabel("Time (milliseconds from Detection)")
plt.yticks([])  # Hide Y axis
plt.grid(axis='x', linestyle='--', alpha=0.7)
plt.tight_layout()

# Save
output_file = "/home/jyp/.gemini/antigravity/brain/964ece5a-f6bc-4b69-9593-3ee2a3b33778/latency_graph.png"
plt.savefig(output_file)
print(f"Graph saved to {output_file}")
