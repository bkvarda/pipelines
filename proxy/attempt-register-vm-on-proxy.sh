#!/bin/bash
#
# Copyright 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -ex

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" > /dev/null && pwd)"

function run-proxy-agent {
  # Start the proxy process
  # https://github.com/google/inverting-proxy/blob/master/agent/Dockerfile
  # Connect proxy agent to Kubeflow Pipelines UI
  /opt/bin/proxy-forwarding-agent \
        --debug=${DEBUG} \
        --proxy=${PROXY_URL} \
        --proxy-timeout=${PROXY_TIMEOUT} \
        --backend=${BACKEND_ID} \
        --host=${ML_PIPELINE_UI_SERVICE_HOST}:${ML_PIPELINE_UI_SERVICE_PORT} \
        --shim-websockets=true \
        --shim-path=websocket-shim \
        --health-check-path=${HEALTH_CHECK_PATH} \
        --health-check-interval-seconds=${HEALTH_CHECK_INTERVAL_SECONDS} \
        --health-check-unhealthy-threshold=${HEALTH_CHECK_UNHEALTHY_THRESHOLD}
}

# Don't reuse existing hostname. It means if proxy-agent got restarted,
# it will get a new hostname.
# https://github.com/kubeflow/pipelines/issues/3143
# Another option is that We may try to fix it in InverseProxy server side.

# Activate service account for gcloud SDK first
if [[ ! -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
  gcloud auth activate-service-account --key-file="${GOOGLE_APPLICATION_CREDENTIALS}"
fi

INSTANCE_ZONE="/"$(curl http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google")
INSTANCE_ZONE="${INSTANCE_ZONE##/*/}"

# Get latest Proxy server URL
wget https://storage.googleapis.com/ml-pipeline/proxy-agent-config.json
PROXY_URL=$(python ${DIR}/get_proxy_url.py --config-file-path "proxy-agent-config.json" --location "${INSTANCE_ZONE}" --version "latest")
if [[ -z "${PROXY_URL}" ]]; then
    echo "Proxy URL for the zone ${INSTANCE_ZONE} no found, exiting."
    exit 1
fi
echo "Proxy URL from the config: ${PROXY_URL}"

# Register the proxy agent
VM_ID=$(curl -H 'Metadata-Flavor: Google' "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?format=full&audience=${PROXY_URL}/request-service-account-endpoint"  2>/dev/null)
RESULT_JSON=$(curl -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "X-Inverting-Proxy-VM-ID: ${VM_ID}" -d "" "${PROXY_URL}/request-service-account-endpoint" 2>/dev/null)
echo "Response from the registration server: ${RESULT_JSON}"

HOSTNAME=$(echo "${RESULT_JSON}" | jq -r ".hostname")
BACKEND_ID=$(echo "${RESULT_JSON}" | jq -r ".backendID")
echo "Hostname: ${HOSTNAME}"
echo "Backend id: ${BACKEND_ID}"

# Store the registration information in a ConfigMap
PATCH_TEMP='{"data": {"Hostname":"'${HOSTNAME}'","ProxyUrl":"'${PROXY_URL}'","BackendId":"'${BACKEND_ID}'"}}'
PATCH_JSON=$(printf "${PATCH_TEMP}" "${HOSTNAME}" "${PROXY_URL}" "${BACKEND_ID}")
echo "PACTH_JSON: ${PATCH_JSON}"

kubectl patch configmap/inverse-proxy-config \
    --type merge \
    --patch "${PATCH_JSON}"

echo "Patched configmap/inverse-proxy-config"

run-proxy-agent
