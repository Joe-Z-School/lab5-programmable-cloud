#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
import google.auth
import sys
from google.cloud import compute_v1

def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None


def create_instance(compute, project, zone, name, nodeType, fwName):
    image_response = (
        compute.images()
        .getFromFamily(project="ubuntu-os-cloud", family="ubuntu-2204-lts")
        .execute()
    )
    source_disk_image = image_response["selfLink"]

    # Configure the machine
    machine_type = f"zones/{zone}/machineTypes/{nodeType}"
    startup_script = open(
        os.path.join(os.path.dirname(__file__), "startup-script.sh")
    ).read()

    config = {
        "name": name,
        "machineType": machine_type,
        "properties": {
            "tags": {
                "items": [f"{fwName}"]
            }
        },
        # Specify the boot disk and the image to use as a source.
        "disks": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceImage": source_disk_image,
                },
            }
        ],
        # Specify a network interface with NAT to access the public
        # internet.
        "networkInterfaces": [
            {
                "network": "global/networks/default",
                "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
            }
        ],
        # Allow the instance to access cloud storage and logging.
        "serviceAccounts": [
            {
                "email": "default",
                "scopes": [
                    "https://www.googleapis.com/auth/devstorage.read_write",
                    "https://www.googleapis.com/auth/logging.write",
                ],
            }
        ],
    }
    
    return compute.instances().insert(project=project, zone=zone, body=config).execute()


def wait_for_operation(compute,project,zone,operation):
    print("Waiting for operation to finish...")
    while True:
        result = (
            compute.zoneOperations()
            .get(project=project, zone=zone, operation=operation)
            .execute()
        )

        if result["status"] == "DONE":
            print("done.")
            if "error" in result:
                raise Exception(result["error"])
            return result

        time.sleep(1)


def create_firewall_rule(compute, project, fwPort, fwName):
    firewall_body = {
        "name": fwName,
        "network": "global/networks/default",
        "priority": 100,
        "allowed": [
            {
                "IPProtocol": "tcp",
                "ports": [str(fwPort)],
            }
        ],
        "source_ranges": ["0.0.0.0/0"],
        "target_tags": [fwName]
    }

    try:
        compute.firewalls().insert(project=project, body=firewall_body).execute()
        print(f"Created firewall rule {fwName}")
    except googleapiclient.errors.HttpError as exp:
        if exp.resp.status == 409:
            print(f"Firewall rule {fwName} already exists")


credentials, project = google.auth.default()
compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
zone = "us-west1-b"
fwPort = 5000
fwName = f'allow-{fwPort}'
instanceName = 'blog'
nodeType = 'e2-micro'

print("Creating instance.")

# Create a firewall rule if not already existing
create_firewall_rule(compute, project, fwPort, fwName)

# Create and wait for instance creation
operation = create_instance(compute, project, zone, instanceName, nodeType, fwName)
wait_for_operation(compute, project, zone, operation["name"])


# Print the instance
try:
    instanceResponse = compute.instances().get(project=project, zone=zone, instance=instanceName).execute()
    if instanceResponse:
        instanceIP = instanceResponse['networkInterfaces'][0]['accessConfigs'][0]['natIP']
        print(f"The blog is runnin at http://{instanceIP}:{fwPort}")
except googleapiclient.errors.HttpError as exp:
    print(f"Unable to locate instance {instanceName} to get the IP address")
    print(exp)