#!/usr/bin/env bash
# Remove the shadow InferenceService and its Istio mirror (deploy-shadow on
# failure, shadow-analysis always). Only removes a shadow that belongs to
# MODEL_VERSION, so an older run never tears down a newer run's soak.
#
# Env: ISVC_NAME, KSERVE_NAMESPACE, MODEL_VERSION, ISTIO_INGRESS_GATEWAY,
#      CHURN_API_INGRESS_HOST (to restore virtualservice-api.yaml without mirror)
set -euo pipefail
: "${ISVC_NAME:?}" "${KSERVE_NAMESPACE:?}" "${MODEL_VERSION:?}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

current=$(kubectl get isvc "${ISVC_NAME}-shadow" -n "$KSERVE_NAMESPACE" \
  -o jsonpath='{.metadata.annotations.churn\.ai/model-version}' 2>/dev/null || true)
if [ -n "$current" ] && [ "$current" != "$MODEL_VERSION" ]; then
  echo "Shadow now runs v$current (newer run); leaving it in place."
  exit 0
fi

# Restore the steady-state API route (same VirtualService, no mirror)
if [ -n "${ISTIO_INGRESS_GATEWAY:-}" ] && [ -n "${CHURN_API_INGRESS_HOST:-}" ]; then
  envsubst < "$HERE/virtualservice-api.yaml" | kubectl apply -f -
else
  echo "::warning::ISTIO_INGRESS_GATEWAY/CHURN_API_INGRESS_HOST unset; deleting mirror VirtualService"
  kubectl delete virtualservice -n "$KSERVE_NAMESPACE" \
    -l app=churn-scoring,churn.ai/mirror=on --ignore-not-found
fi
# Pre-6p0 name of the mirror VirtualService
kubectl delete virtualservice "${ISVC_NAME}-mirror" -n "$KSERVE_NAMESPACE" --ignore-not-found
kubectl delete service "${ISVC_NAME}-shadow-mirror" -n "$KSERVE_NAMESPACE" --ignore-not-found
kubectl delete isvc "${ISVC_NAME}-shadow" -n "$KSERVE_NAMESPACE" --ignore-not-found
