#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
import google.auth

#
# Stub code - just lists all instances
#
# instances will be named: blog-clone-0 , blog-clone-1 , blog-clone-2


def list_instances(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    return result['items'] if 'items' in result else None

def create_instance(compute, project, zone, name, nodeType, fwName):
    machine_type = f"zones/{zone}/machineTypes/{nodeType}"
    startup_script = open(
        os.path.join(os.path.dirname(__file__), "startup-script.sh")
    ).read()

    snapshot_location = f"projects/{project}/global/snapshots/{snapshotName}"

    config = {
        "name": name,
        "machineType": machine_type,
        "properties": {
            "tags": {
                "items": [f"{fwName}"]
            }
        },
        "disk": [
            {
                "boot": True,
                "autoDelete": True,
                "initializeParams": {
                    "sourceSnapshot": snapshot_location,
                },
            }
        ],
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
        "metadata": {
            "items": [
                {
                    "key": "startup-script",
                    "value": startup_script,
                }
            ]
        },
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

credentials, project = google.auth.default()
compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
zone = "us-central1-a"
nodeType = 'e2-micro'
fwPort = 5000
fwName = f'allow-{fwPort}'

snapshotName = 'base-snapshot-blog'

# Print out the instance currently running
for instance in list_instances(compute, project, zone):
    print(f"Currently running instances: {instance['name']}")
    print()

# Create 3 new instances from the snapshot
instanceNames = ['blog-clone-0', 'blog-clone-1', 'blog-clone-2']
for instanceName in instanceNames:
    print(f"Creating instance {instanceName}")

    startTime = time.perf_counter()
    
    operation = create_instance(compute, project, zone, instanceName, nodeType, fwName)
    wait_for_operation(compute, project, zone, operation["name"])

    endTime = time.perf_counter()

    totalTime = endTime - startTime

    print(f"Created instance {instanceName} in {totalTime:.2f} seconds")