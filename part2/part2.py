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

#def list_instances(compute, project, zone):
#    result = compute.instances().list(project=project, zone=zone).execute()
#    return result['items'] if 'items' in result else None

#print("Your running instances are:")
#for instance in list_instances(service, project, 'us-west1-b'):
#    print(instance['name'])

def create_snapshot(compute, project_id, disk_name, snapshot_name, zone):
    
    config = {
        "name": snapshot_name,
        "source_disk": f"projects/{project_id}/zones/{zone}/disks/{disk_name}"
    }

    print("Creating snapshot...")

    return compute.disks().createSnapshot(project=project_id, zone=zone, disk=disk_name, body=config).execute()


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
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
zone = "us-central1-a"
diskName = 'blog'
snapshotName = f'base-snapshot-{diskName}'

snapshot = create_snapshot(service, project, diskName, snapshotName, zone)
wait_for_operation(service, project, zone, snapshot["name"])


print(f"Created snapshot {snapshotName}")