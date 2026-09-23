#!/usr/bin/env python3

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
import google.auth
import sys
from typing import Any

from google.api_core.extended_operation import ExtendedOperation
from google.cloud import compute_v1


#
# Stub code - just lists all instances
#

#def list_instances(compute, project, zone):
#    result = compute.instances().list(project=project, zone=zone).execute()
#    return result['items'] if 'items' in result else None

#print("Your running instances are:")
#for instance in list_instances(service, project, 'us-west1-b'):
#    print(instance['name'])



def wait_for_extended_operation(
    operation: ExtendedOperation, verbose_name: str = "operation", timeout: int = 300
) -> Any:

    result = operation.result(timeout=timeout)

    print("Waiting for operation to finish")

    if operation.error_code:
        print(
            f"Error during {verbose_name}: [Code: {operation.error_code}]: {operation.error_message}",
            file=sys.stderr,
            flush=True,
        )
        print(f"Operation ID: {operation.name}", file=sys.stderr, flush=True)
        raise operation.exception() or RuntimeError(operation.error_message)

    if operation.warnings:
        print(f"Warnings during {verbose_name}:\n", file=sys.stderr, flush=True)
        for warning in operation.warnings:
            print(f" - {warning.code}: {warning.message}", file=sys.stderr, flush=True)

    return result


def create_snapshot(
    project_id: str,
    disk_name: str,
    snapshot_name: str,
    zone: str,
    region: str | None = None,
    location: str | None = None,
    disk_project_id: str | None = None,
) -> compute_v1.Snapshot:
    """
    Create a snapshot of a disk.

    You need to pass `zone` or `region` parameter relevant to the disk you want to
    snapshot, but not both. Pass `zone` parameter for zonal disks and `region` for
    regional disks.

    Args:
        project_id: project ID or project number of the Cloud project you want
            to use to store the snapshot.
        disk_name: name of the disk you want to snapshot.
        snapshot_name: name of the snapshot to be created.
        zone: name of the zone in which is the disk you want to snapshot (for zonal disks).
        region: name of the region in which is the disk you want to snapshot (for regional disks).
        location: The Cloud Storage multi-region or the Cloud Storage region where you
            want to store your snapshot.
            You can specify only one storage location. Available locations:
            https://cloud.google.com/storage/docs/locations#available-locations
        disk_project_id: project ID or project number of the Cloud project that
            hosts the disk you want to snapshot. If not provided, will look for
            the disk in the `project_id` project.

    Returns:
        The new snapshot instance.
    """
    if zone is None and region is None:
        raise RuntimeError(
            "You need to specify `zone` or `region` for this function to work."
        )
    if zone is not None and region is not None:
        raise RuntimeError("You can't set both `zone` and `region` parameters.")

    if disk_project_id is None:
        disk_project_id = project_id

    if zone is not None:
        disk_client = compute_v1.DisksClient()
        disk = disk_client.get(project=disk_project_id, zone=zone, disk=disk_name)
    else:
        regio_disk_client = compute_v1.RegionDisksClient()
        disk = regio_disk_client.get(
            project=disk_project_id, region=region, disk=disk_name
        )

    print("Creating snapshot...")

    snapshot = compute_v1.Snapshot()
    snapshot.source_disk = disk.self_link
    snapshot.name = snapshot_name
    if location:
        snapshot.storage_locations = [location]

    snapshot_client = compute_v1.SnapshotsClient()
    operation = snapshot_client.insert(project=project_id, snapshot_resource=snapshot)

    wait_for_extended_operation(operation, "snapshot creation")

    return snapshot_client.get(project=project_id, snapshot=snapshot_name)

credentials, project = google.auth.default()
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
zone = "us-central1-a"
diskName = 'blog'

snapshot = create_snapshot(project, diskName, f'{diskName}-snapshot', zone)
print(f"Created snapshot {snapshot.name}")