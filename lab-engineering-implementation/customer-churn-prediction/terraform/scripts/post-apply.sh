#!/usr/bin/env bash
# =========================================================================
# CUSTOMER CHURN PREDICTION PLATFORM - POST-APPLY APPROVALS
#
# Approves the private endpoint connections that Terraform cannot approve
# itself, using the `post_apply_targets` Terraform output:
#   1. Front Door Premium -> Application Gateway Private Link (one pending
#      connection per region: West Europe, and North Europe when enable_dr).
#   2. Stream Analytics cluster managed private endpoints -> Event Hubs
#      namespace and lake storage account (only when
#      enable_stream_analytics_cluster = true).
#
# Usage (from any directory, after `terraform apply`):
#   scripts/post-apply.sh [--tf-dir <terraform dir>] [--dry-run] [--skip-asa]
#
# Requirements: az CLI (logged in with rights to approve connections on the
# targets, e.g. Network Contributor on the gateways and Contributor on the
# Event Hubs namespace / storage account), terraform, jq.
# The script is idempotent: approved connections are skipped.
# See POST_APPLY.md for the surrounding prerequisites and manual steps.
# =========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$(dirname "${SCRIPT_DIR}")"
DRY_RUN=false
SKIP_ASA=false
APPGW_API_VERSION="2024-05-01"

usage() {
  sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tf-dir)
      TF_DIR="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --skip-asa)
      SKIP_ASA=true
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

log() { printf '[post-apply] %s\n' "$*"; }
die() {
  printf '[post-apply] ERROR: %s\n' "$*" >&2
  exit 1
}

for cmd in az terraform jq; do
  command -v "${cmd}" >/dev/null 2>&1 || die "'${cmd}' is required but not installed."
done

# -------------------------------------------------------------------------
# Read Terraform outputs
# -------------------------------------------------------------------------
TARGETS_JSON="$(terraform -chdir="${TF_DIR}" output -json post_apply_targets)" ||
  die "could not read the post_apply_targets output from ${TF_DIR} (run terraform init/apply first)."

SUBSCRIPTION_ID="$(jq -r '.subscription_id' <<<"${TARGETS_JSON}")"
FD_MESSAGE_PREFIX="$(jq -r '.frontdoor_request_message_prefix' <<<"${TARGETS_JSON}")"
ASA_ENABLED="$(jq -r '.stream_analytics_cluster_enabled' <<<"${TARGETS_JSON}")"

CURRENT_SUB="$(az account show --query id -o tsv)" || die "not logged in: run 'az login' first."
if [[ "${CURRENT_SUB}" != "${SUBSCRIPTION_ID}" ]]; then
  log "Switching az CLI subscription ${CURRENT_SUB} -> ${SUBSCRIPTION_ID}"
  az account set --subscription "${SUBSCRIPTION_ID}"
fi

${DRY_RUN} && log "DRY RUN: pending connections are listed, nothing is approved."

APPROVED=0
PENDING_LEFT=0

# -------------------------------------------------------------------------
# 1. Front Door -> Application Gateway Private Link connections
#    App Gateway private endpoint connections are a child resource of the
#    gateway; az rest is used because the generic
#    `az network private-endpoint-connection` command does not cover
#    Microsoft.Network/applicationGateways in every CLI version.
# -------------------------------------------------------------------------
approve_appgw_connections() {
  local region="$1" agw_id="$2"
  local conns name status description

  log "Application Gateway (${region}): ${agw_id##*/}"
  conns="$(az rest --method get \
    --url "https://management.azure.com${agw_id}?api-version=${APPGW_API_VERSION}" \
    --query "properties.privateEndpointConnections[].{name:name, status:properties.privateLinkServiceConnectionState.status, description:properties.privateLinkServiceConnectionState.description}" \
    -o json)"

  if [[ "$(jq 'length' <<<"${conns}")" -eq 0 ]]; then
    log "  no private endpoint connections yet (Front Door origin not created?)"
    PENDING_LEFT=$((PENDING_LEFT + 1))
    return
  fi

  while IFS=$'\t' read -r name status description; do
    if [[ "${status}" != "Pending" ]]; then
      log "  ${name}: ${status} (skipped)"
      continue
    fi
    if [[ "${description}" != "${FD_MESSAGE_PREFIX}"* ]]; then
      log "  ${name}: Pending but not requested by this Front Door profile ('${description}'), left for manual review"
      PENDING_LEFT=$((PENDING_LEFT + 1))
      continue
    fi
    if ${DRY_RUN}; then
      log "  ${name}: Pending -> would approve"
      continue
    fi
    az rest --method put \
      --url "https://management.azure.com${agw_id}/privateEndpointConnections/${name}?api-version=${APPGW_API_VERSION}" \
      --body "$(jq -n --arg n "${name}" '{name: $n, properties: {privateLinkServiceConnectionState: {status: "Approved", description: "Approved by post-apply.sh (Front Door private origin)"}}}')" \
      --output none
    log "  ${name}: approved"
    APPROVED=$((APPROVED + 1))
  done < <(jq -r '.[] | [.name, .status, (.description // "")] | @tsv' <<<"${conns}")
}

while IFS=$'\t' read -r region agw_id; do
  approve_appgw_connections "${region}" "${agw_id}"
done < <(jq -r '.application_gateway_ids | to_entries[] | [.key, .value] | @tsv' <<<"${TARGETS_JSON}")

# -------------------------------------------------------------------------
# 2. Stream Analytics cluster managed private endpoints
#    The managed endpoints live in a Microsoft-managed VNet, so they always
#    arrive as Pending on the target. All other endpoints on these targets
#    are auto-approved by Terraform, so only Pending ones are touched.
# -------------------------------------------------------------------------
if [[ "${ASA_ENABLED}" == "true" && "${SKIP_ASA}" == "false" ]]; then
  while IFS= read -r target_id; do
    log "Stream Analytics target: ${target_id##*/}"
    while IFS=$'\t' read -r conn_id status pe_id; do
      [[ -z "${conn_id}" ]] && continue
      if [[ "${status}" != "Pending" ]]; then
        continue
      fi
      if ${DRY_RUN}; then
        log "  ${conn_id##*/}: Pending (endpoint ${pe_id##*/}) -> would approve"
        continue
      fi
      az network private-endpoint-connection approve --id "${conn_id}" \
        --description "Approved by post-apply.sh (Stream Analytics cluster managed private endpoint)" \
        --output none
      log "  ${conn_id##*/}: approved"
      APPROVED=$((APPROVED + 1))
    done < <(az network private-endpoint-connection list --id "${target_id}" \
      --query "[].[id, properties.privateLinkServiceConnectionState.status, properties.privateEndpoint.id]" -o tsv)
  done < <(jq -r '.stream_analytics_private_link_ids[]' <<<"${TARGETS_JSON}")

  ASA_JOB="$(jq -r '.stream_analytics_job_name' <<<"${TARGETS_JSON}")"
  ASA_RG="$(jq -r '.resource_group_name' <<<"${TARGETS_JSON}")"
  log "Stream Analytics job ${ASA_JOB} is not started by this script; start it from the platform runbook once the endpoints show Approved:"
  log "  az stream-analytics job start --resource-group ${ASA_RG} --job-name ${ASA_JOB} --output-start-mode JobStartTime"
else
  log "Stream Analytics cluster disabled (or --skip-asa): no managed private endpoints to approve."
fi

log "Done: ${APPROVED} connection(s) approved, ${PENDING_LEFT} item(s) need attention."
if [[ "${PENDING_LEFT}" -gt 0 ]]; then
  exit 3
fi
