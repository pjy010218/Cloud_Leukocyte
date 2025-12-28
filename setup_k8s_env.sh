#!/bin/bash
set -e

echo "--- 🏗️ Setting up Cloud Leukocyte K8s Environment ---"

# 1. Check Prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl could not be found. Please install it."
    exit 1
fi

if ! command -v istioctl &> /dev/null; then
    echo "⚠️ istioctl not found. Assuming Istio is already installed or skipping install."
else
    echo "✅ Installing Istio (demo profile)..."
    istioctl install --set profile=demo -y
fi

# 2. Build Assets
echo "📦 Building Leukocyte Assets..."

# 2.1 Build WASM Filter
echo "   🦀 Building Rust WASM Filter..."
if ! command -v cargo &> /dev/null; then
    echo "❌ cargo not found. Cannot build WASM."
    exit 1
fi
(cd data_plane/wasm_filter && cargo build --release --target wasm32-unknown-unknown)
WASM_PATH="data_plane/wasm_filter/target/wasm32-unknown-unknown/release/leukocyte_wasm_filter.wasm"

if [ ! -f "$WASM_PATH" ]; then
    echo "❌ WASM build failed. File not found at $WASM_PATH"
    exit 1
fi

# 2.2 Build Controller Image
echo "   🐳 Building Controller Docker Image..."
# Use minikube docker env if available, otherwise just build locally
if command -v minikube &> /dev/null; then
    eval $(minikube -p minikube docker-env)
fi
docker build -t leukocyte/controller:transduction .

# 3. Namespace Setup
echo "🔧 Creating namespace 'online-boutique' with Istio injection..."
kubectl create namespace online-boutique --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace online-boutique istio-injection=enabled --overwrite

# 4. Deploy Online Boutique
echo "🛒 Deploying Google Online Boutique..."
kubectl apply -n online-boutique -f https://raw.githubusercontent.com/GoogleCloudPlatform/microservices-demo/main/release/kubernetes-manifests.yaml

# 5. Deploy Cloud Leukocyte Resources & Patches
echo "🩺 Deploying Cloud Leukocyte Components..."

# 5.1 Create ConfigMap for WASM
echo "   📄 Creating WASM ConfigMap..."
# Delete existing CM to avoid update issues
kubectl -n online-boutique delete configmap leukocyte-wasm --ignore-not-found
kubectl -n online-boutique create configmap leukocyte-wasm \
    --from-file=leukocyte.wasm=$WASM_PATH

# 5.2 Patch adservice to mount the WASM via Istio Annotations
echo "   🩹 Patching adservice to mount WASM (Sidecar Injection)..."
# We use proper JSON escaping for the annotation values
kubectl -n online-boutique patch deployment adservice --type=merge -p '
{
  "spec": {
    "template": {
      "metadata": {
        "annotations": {
          "sidecar.istio.io/userVolume": "[{\"name\":\"wasm-volume\",\"configMap\":{\"name\":\"leukocyte-wasm\"}}]",
          "sidecar.istio.io/userVolumeMount": "[{\"mountPath\":\"/var/local/lib/wasm\",\"name\":\"wasm-volume\"}]"
        }
      }
    }
  }
}'

echo "   🩹 Patching checkoutservice to mount WASM (Sidecar Injection)..."
kubectl -n online-boutique patch deployment checkoutservice --type=merge -p '
{
  "spec": {
    "template": {
      "metadata": {
        "annotations": {
          "sidecar.istio.io/userVolume": "[{\"name\":\"wasm-volume\",\"configMap\":{\"name\":\"leukocyte-wasm\"}}]",
          "sidecar.istio.io/userVolumeMount": "[{\"mountPath\":\"/var/local/lib/wasm\",\"name\":\"wasm-volume\"}]"
        }
      }
    }
  }
}'

# 5.3 Deploy Leukocyte Resources
kubectl apply -f infrastructure/k8s/leukocyte-resources.yaml

echo "--- ⏳ Waiting for Pods to be ready ---"
echo "Run 'kubectl get pods -n online-boutique -w' to monitor progress."
