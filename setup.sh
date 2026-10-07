#!/bin/bash
set -e

PROJECT_ID="lab-6-510321"
VM_NAME="base-template-vm"
ZONE="us-west1-a"

echo "Creating base template VM..."
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

echo "Waiting for SSH service to become ready on $VM_NAME..."
MAX_RETRIES=12
RETRY_COUNT=0
until gcloud compute ssh $VM_NAME --zone=$ZONE --command="echo SSH Ready" --ssh-flag="-o ConnectTimeout=5" &>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Timed out waiting for SSH on $VM_NAME."
        exit 1
    fi
    echo "SSH not ready yet... Retrying in 5 seconds ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "Installing packages on remote VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    uv pip install --system flask jsonpickle numpy pillow grpcio grpcio-tools requests
    python3 -c \"import flask, jsonpickle, numpy, PIL, grpc, requests; print('Dependencies OK')\"
"

echo "Stopping VM and creating snapshot..."
gcloud compute instances stop $VM_NAME --zone=$ZONE

gcloud compute snapshots create lab6-base-snapshot \
    --project=$PROJECT_ID \
    --source-disk=$VM_NAME \
    --source-disk-zone=$ZONE

echo "Deleting base template VM..."
gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
