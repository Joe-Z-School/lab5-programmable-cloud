#!/usr/bin/env python3

import google.auth
from google.cloud import compute_v1


def create_snapshot(compute, project_id, disk_name, snapshot_name, zone):

    print("Creating snapshot...")

    # Configure the snapshot.
    snapshot = compute_v1.Snapshot(
        name=snapshot_name,
    )

    # Create the request.
    request = compute_v1.CreateSnapshotDiskRequest(
        project=project_id,
        zone=zone,
        disk=disk_name,
        snapshot_resource=snapshot,
    )

    # Create the snapshot.
    operation = compute.create_snapshot(
        request=request
    )

    return operation


def wait_for_operation(operation):
    print("Waiting for operation to finish...")

    operation.result()

    if operation.error_code:
        raise Exception(
            f"Operation failed: "
            f"{operation.error_code}: "
            f"{operation.error_message}"
        )

    print("done.")


# Authenticate with Google Cloud.
credentials, project = google.auth.default()

# Create the disk client.
disks_client = compute_v1.DisksClient()

# Assignment configuration.
zone = "us-west1-b"
diskName = "blog"
snapshotName = f"base-snapshot-{diskName}"


# Create the snapshot.
snapshot = create_snapshot(disks_client,project,diskName,snapshotName,zone)

# Wait for the snapshot operation to finish.
wait_for_operation(snapshot)

print(f"Created snapshot {snapshotName}")