#!/bin/bash

sudo apt-get update
sudo apt-get install -y python3 python3-pip git curl

pip3 install --upgrade google-cloud-compute

mkdir -p /srv
cd /srv

# Pass the Python program that VM1 will execute
curl "http://metadata/computeMetadata/v1/instance/attributes/vm1-launch-vm2-code" \
    -H "Metadata-Flavor: Google" \
    -o vm1-launch-code.py

# Download the startup script that VM2 will use to start Flask blog
curl "http://metadata/computeMetadata/v1/instance/attributes/vm2-startup-script" \
    -H "Metadata-Flavor: Google" \
    -o vm2-startup-script.sh

# Download the service account credentials
curl "http://metadata/computeMetadata/v1/instance/attributes/service-credentials" \
    -H "Metadata-Flavor: Google" \
    -o service-credentials.json

# Get the project ID from VM1 for VM2 to use
export GOOGLE_CLOUD_PROJECT=$(curl \
    "http://metadata/computeMetadata/v1/instance/attributes/project" \
    -H "Metadata-Flavor: Google")


export GOOGLE_APPLICATION_CREDENTIALS=/srv/service-credentials.json

# VM2 needs the cloud compute libraries in order to work
pip3 install --upgrade google-cloud-compute

# Launch VM2
python3 /srv/vm1-launch-code.py