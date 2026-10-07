#!/bin/bash
set -e

echo "Creating base template VM..."
gcloud compute instances create base-template-vm \
    --zone=us-west1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud

echo "Installing packages on remote VM..."
gcloud compute ssh base-template-vm --zone=us-west1-a --command="
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH=\"\$HOME/.local/bin:\$PATH\"
    uv pip install --system flask jsonpickle numpy pillow grpcio grpcio-tools requests
    python3 -c \"import flask, jsonpickle, numpy, PIL, grpc, requests; print('Dependencies OK')\"
"

echo "Stopping VM and creating snapshot..."
gcloud compute instances stop base-template-vm --zone=us-west1-a

gcloud compute snapshots create lab6-base-snapshot \
    --source-disk=base-template-vm \
    --source-disk-zone=us-west1-a

gcloud compute instances delete base-template-vm --zone=us-west1-a --quiet
