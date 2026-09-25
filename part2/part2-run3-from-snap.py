#!/usr/bin/env python3

import time
import google.auth
from google.cloud import compute_v1


def list_instances(compute, project, zone):

    request = compute_v1.ListInstancesRequest(
        project=project,
        zone=zone,
    )

    instances = compute.list(
        request=request
    )

    return list(instances)


def create_instance(
    compute,
    project,
    zone,
    name,
    nodeType,
    fwName,
    snapshotName
):

    # Configure the machine type.
    machine_type = (f"zones/{zone}/machineTypes/{nodeType}")

    # Location of the snapshot.
    snapshot_location = (f"projects/{project}/global/snapshots/{snapshotName}")

    # Configure the boot disk using the snapshot.
    initialize_params = compute_v1.AttachedDiskInitializeParams(
        source_snapshot=snapshot_location
    )

    boot_disk = compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=initialize_params,
    )

    # Configure the external IP address.
    access_config = compute_v1.AccessConfig(
        name="External NAT",
        type_="ONE_TO_ONE_NAT",
    )

    # Configure the network interface.
    network_interface = compute_v1.NetworkInterface(
        network="global/networks/default",
        access_configs=[access_config],
    )

    # Configure the network tag.
    tags = compute_v1.Tags(
        items=[fwName]
    )

    # Create the VM configuration.
    instance = compute_v1.Instance(
        name=name,
        machine_type=machine_type,
        disks=[boot_disk],
        network_interfaces=[network_interface],
        tags=tags,
    )

    # Create the request.
    request = compute_v1.InsertInstanceRequest(project=project, zone=zone, instance_resource=instance,)

    # Create the instance.
    operation = compute.insert(request=request)

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

# Create the Compute Engine client.
compute = compute_v1.InstancesClient()

# Assignment configuration.
zone = "us-west1-b"
nodeType = "e2-micro"

fwPort = 5000
fwName = f"allow-{fwPort}"

snapshotName = "base-snapshot-blog"


# Print the instances currently running.
for instance in list_instances(compute,project,zone):
    print(f"Currently running instance: {instance.name}")
    print()


# Instance names will be in form: 'blog-clone-#'
instanceNames = ["blog-clone-0","blog-clone-1","blog-clone-2"]


for instanceName in instanceNames:

    print(
        f"Creating instance {instanceName}"
    )

    startTime = time.perf_counter()

    operation = create_instance(compute,project,zone,instanceName,nodeType,fwName,snapshotName)

    wait_for_operation(operation)

    endTime = time.perf_counter()

    totalTime = endTime - startTime

    print(
        f"Created instance {instanceName} "
        f"in {totalTime:.2f} seconds"
    )