#!/usr/bin/env bash
# Create or update the identity-based Azure ML datastores in
# pipelines/aml/datastores/*.yml. Idempotent: `az ml datastore create` is a
# create-or-update, so re-running only re-asserts the definition.
#
# Usage (from the project directory, after `az login`):
#   LAKE_STORAGE_ACCOUNT=<stlake...> AZURE_RESOURCE_GROUP=rg-churn-prod-westeurope \
#   AML_WORKSPACE=mlw-churn-prod bash pipelines/aml/scripts/ensure-datastores.sh
set -euo pipefail

: "${LAKE_STORAGE_ACCOUNT:?set LAKE_STORAGE_ACCOUNT (terraform output lake_storage_account_name)}"
: "${AZURE_RESOURCE_GROUP:?set AZURE_RESOURCE_GROUP}"
: "${AML_WORKSPACE:?set AML_WORKSPACE}"

DATASTORE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../datastores" && pwd)"

shopt -s nullglob
files=("$DATASTORE_DIR"/*.yml)
if [ "${#files[@]}" -eq 0 ]; then
  echo "no datastore definitions in $DATASTORE_DIR" >&2
  exit 1
fi

for file in "${files[@]}"; do
  echo "Ensuring datastore from $(basename "$file") on account $LAKE_STORAGE_ACCOUNT"
  az ml datastore create \
    --file "$file" \
    --set account_name="$LAKE_STORAGE_ACCOUNT" \
    --resource-group "$AZURE_RESOURCE_GROUP" \
    --workspace-name "$AML_WORKSPACE" \
    --query "{name:name, account:account_name, filesystem:filesystem, credentials:credentials.type}" \
    -o table
done
