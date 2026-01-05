import time
import logging
import signal
import sys
import os
import threading
import json
from flask import Flask, request, jsonify
from kubernetes import client, config

# Cloud Leukocyte Imports
from hierarchical_control.hierarchical_policy_engine import HierarchicalPolicyEngine
from adaptive_security.evolutionary_agent import EvolutionaryAgent
from proactive_remediation.immune_surveillance_system import ImmuneSurveillanceSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Leukocyte Controller] - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global System State
immune_system = None
engine_map = {}

def signal_handler(sig, frame):
    logger.info("Received termination signal. Shutting down...")
    sys.exit(0)

def initialize_system():
    global immune_system, engine_map
    
    logger.info("🧬 Initializing Bio-Inspired Components v3 (Actuation Enabled)...")

    # Initialize Kubernetes Client
    try:
        config.load_incluster_config()
        logger.info("✅ Kubernetes Client Initialized (In-Cluster Config).")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load K8s config (simulated mode?): {e}")
    
    # 1. Initialize Engines (In a real system, these would sync with actual services)
    # For simulation/demo purposes, we create mock engines for known services
    billing_engine = HierarchicalPolicyEngine()
    log_engine = HierarchicalPolicyEngine()
    ad_engine = HierarchicalPolicyEngine()
    cart_engine = HierarchicalPolicyEngine()
    frontend_engine = HierarchicalPolicyEngine()
    
    # Default allowances
    billing_engine.allow_path("payload.content")
    log_engine.allow_path("payload.content")
    ad_engine.allow_path("payload.content")
    cart_engine.allow_path("payload.data")
    frontend_engine.allow_path("proxy_url")
    
    engine_map = {
        "BillingService": billing_engine,
        "LogService": log_engine, # Potentially vulnerable
        "AdService": ad_engine,
        "CartService": cart_engine,
        "Frontend": frontend_engine
    }
    
    # 2. Initialize Evolutionary Agent
    rl_agent = EvolutionaryAgent(log_engine)
    
    # --- DEMO: PARANOID MEMORY ---
    # The AttackPatternAnalyzer accesses .q_table directly (violating encapsulation),
    # so we must override the dictionary itself to always return high threat values.
    class ParanoidDict(dict):
        def __getitem__(self, key):
            # Return [Allow_Q, Suppress_Q]. Suppress_Q=200 > Threshold(100)
            return [-50.0, 200.0]
        def __contains__(self, key):
            return True

    rl_agent.q_table = ParanoidDict()
    logger.info("🧠 Initialized PARANOID MEMORY (Always Detects Threats).")
    
    # 3. Initialize Immune Surveillance System
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://neo4j-service:7687")
    logger.info(f"Connecting to Neo4j at {neo4j_uri}...")
    
    try:
        immune_system = ImmuneSurveillanceSystem(rl_agent, neo4j_uri=neo4j_uri)
        logger.info("✅ Immune Surveillance System is ACTIVE.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Immune System: {e}")

def apply_policy_update(service_name, policy_json):
    """
    Actuation: Updates the EnvoyFilter CRD to enforce the new policy.
    This closes the feedback loop.
    """
    logger.info(f"⚡ [ACTUATION] Applying Policy Update to {service_name}...")
    
    api = client.CustomObjectsApi()
    namespace = "online-boutique"
    # Mapping service names to EnvoyFilter names. 
    # For this prototype, we target a single shared filter or specific ones.
    FILTER_MAP = {
        "AdService": "leukocyte-wasm-filter",
        "BillingService": "leukocyte-wasm-filter-checkoutservice",
        "LogService": "leukocyte-wasm-filter-logservice",
        "CartService": "leukocyte-wasm-filter-cartservice",
        "Frontend": "leukocyte-wasm-filter-frontend"
    }
    
    filter_name = FILTER_MAP.get(service_name)
    if not filter_name:
        # Heuristic fallback
        filter_name = f"leukocyte-wasm-filter-{service_name.lower()}"
    
    # Phase 25: Robust Actuation (Retry Logic)
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            # Get current resource
            resource = api.get_namespaced_custom_object(
                group="networking.istio.io",
                version="v1alpha3",
                namespace=namespace,
                plural="envoyfilters",
                name=filter_name
            )
            
            # Modify the configuration
            # Path: spec -> configPatches[0] -> patch -> value -> typed_config -> config -> configuration
            # We assume the structure matches infrastructure/k8s/leukocyte-resources.yaml (after our update)
            
            # We need to construct the configuration message.
            # Envoy WASM filter expects a google.protobuf.StringValue for configuration.
            new_config_struct = {
                "@type": "type.googleapis.com/google.protobuf.StringValue",
                "value": policy_json
            }
            
            # Navigate and set
            patch_value = resource['spec']['configPatches'][0]['patch']['value']
            
            # Ensure path exists
            if 'typed_config' in patch_value and 'config' in patch_value['typed_config']:
                 patch_value['typed_config']['config']['configuration'] = new_config_struct
                 
                 # Apply Patch
                 api.patch_namespaced_custom_object(
                    group="networking.istio.io",
                    version="v1alpha3",
                    namespace=namespace,
                    plural="envoyfilters",
                    name=filter_name,
                    body=resource
                 )
                 logger.info(f"✅ [ACTUATION] EnvoyFilter '{filter_name}' successfully patched via K8s API.")
                 return # Success
            else:
                logger.error(f"❌ [ACTUATION FAILED] Unexpected EnvoyFilter structure.")
                return # Fatal error, do not retry structure issues
                
        except Exception as e:
            logger.warning(f"⚠️ [ACTUATION RETRY] Attempt {attempt+1}/{MAX_RETRIES} failed for {filter_name}: {e}")
            time.sleep(2) # Backoff
            
    logger.error(f"❌ [ACTUATION FAILED] Could not patch EnvoyFilter {filter_name} after {MAX_RETRIES} attempts.")
            

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "components": "active"}), 200

@app.route('/detect', methods=['POST'])
def detect_attack():
    """
    Endpoint to ingest an attack event (simulated IDS or WAF hook).
    Payload: { "service_id": "LogService", "path": "payload.content", ... }
    """
    data = request.json
    if not data or 'service_id' not in data:
        return jsonify({"error": "Missing service_id"}), 400
        
    service_id = data['service_id']
    logger.warning(f"🚨 [Anti-Body Trigger] Attack detected on {service_id}!")
    
    if not immune_system:
        return jsonify({"error": "Immune system not initialized"}), 500
        
    # Construct attack event object expected by the system
    attack_event = {
        "path": data.get("path", "payload.content"),
        "payload_sample": data.get("payload", "unknown"),
        "features": data.get("features", {"anomaly": 1.0})
    }
    
    try:
        response = immune_system.respond_to_attack(attack_event, service_id, engine_map)
        
        # --- ACTUATION HOOK ---
        # If the response indicates hardening, we must actuate it.
        if "action_flow" in response:
            # --- ACTUATION LOOP (TRANSDUCTION) ---
            # Identify all services that need Actuation: Attacked Host + Prophylactic Targets + Transduced Targets
            services_to_update = set()
            services_to_update.add(service_id) 
            if "hardened_services" in response:
                services_to_update.update(response["hardened_services"])
            if "transduced_services" in response:
                services_to_update.update(response["transduced_services"])
            
            logger.info(f"⚡ [ACTUATION] Triggering Policy Updates for: {services_to_update}")
            
            for target_id in services_to_update:
                target_engine = engine_map.get(target_id)
                if target_engine:
                     # Generate Policy JSON
                     from data_plane.wasm_config_generator import generate_wasm_filter_config
                     # Serialize logic should be quick
                     policy_json = generate_wasm_filter_config(target_engine)
                     
                     # Apply to Infrastructure
                     apply_policy_update(target_id, policy_json)
                     
                     # Throttling to prevent Istiod Webhook overload (Context Deadline Exceeded)
                     time.sleep(1.0)
                else:
                     logger.warning(f"⚠️ Actuation Skipped: No Policy Engine for {target_id}")

        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error during immune response: {e}")
        return jsonify({"error": str(e)}), 500

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    initialize_system()

    logger.info("Starting API Server for Attack Ingestion...")
    # Run Flask in a separate thread so we can do other maintenance tasks if needed
    # Or just run it directly since it blocks.
    run_flask()

if __name__ == "__main__":
    main()
