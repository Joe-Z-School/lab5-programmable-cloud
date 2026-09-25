#!/usr/bin/env python3

import os
import time
import google.auth
from google.cloud import compute_v1


def wait_for_operation(operation):
    print("Waiting for operation to finish...")
    operation.result()

    if operation.error_code:
        raise Exception(
            f"Operation failed: {operation.error_code}: {operation.error_message}"
        )

    print("done.")


def create_instance(compute, project, zone, name, nodeType, fwName):
    # Get the latest image from the Ubuntu 22.04 image family.
    images_client = compute_v1.ImagesClient()

    image_request = compute_v1.GetFromFamilyImageRequest(
        project="ubuntu-os-cloud",
        family="ubuntu-2204-lts",
    )

    image_response = images_client.get_from_family(
        request=image_request
    )

    source_disk_image = image_response.self_link

    # Configure the machine type.
    machine_type = (f"zones/{zone}/machineTypes/{nodeType}")

    # Read the startup script.
    startup_script = open(
        "/srv/vm2-startup-script.sh"
    ).read()

    # Configure the boot disk.
    initialize_params = compute_v1.AttachedDiskInitializeParams(
        source_image=source_disk_image
    )

    boot_disk = compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=initialize_params,
    )

    # Configure the network interface and external IP.
    access_config = compute_v1.AccessConfig(
        name="External NAT",
        type_="ONE_TO_ONE_NAT",
    )

    network_interface = compute_v1.NetworkInterface(
        network="global/networks/default",
        access_configs=[access_config],
    )

    # Configure the network tag.
    tags = compute_v1.Tags(
        items=[fwName]
    )

    # Configure the startup script.
    metadata = compute_v1.Metadata(
        items=[
            compute_v1.Items(
                key="startup-script",
                value=startup_script,
            )
        ]
    )

    # Create the VM configuration.
    instance = compute_v1.Instance(
        name=name,
        machine_type=machine_type,
        disks=[boot_disk],
        network_interfaces=[network_interface],
        tags=tags,
        metadata=metadata,
    )

    # Create the VM.
    request = compute_v1.InsertInstanceRequest(
        project=project,
        zone=zone,
        instance_resource=instance,
    )

    operation = compute.insert(request=request)

    return operation


def create_firewall_rule(compute, project, fwPort, fwName):
    # Configure the firewall rule.
    allowed = compute_v1.Allowed(
        I_p_protocol="tcp",
        ports=[str(fwPort)],
    )

    firewall = compute_v1.Firewall(
        name=fwName,
        network="global/networks/default",
        priority=100,
        allowed=[allowed],
        source_ranges=["0.0.0.0/0"],
        target_tags=[fwName],
    )

    request = compute_v1.InsertFirewallRequest(
        project=project,
        firewall_resource=firewall,
    )

    try:
        operation = compute.insert(request=request)
        operation.result()

        print(f"Created firewall rule {fwName}")

    except Exception as exp:
        # A 409 means the firewall rule already exists.
        if "409" in str(exp):
            print(f"Firewall rule {fwName} already exists")
        else:
            raise


# Authenticate with Google Cloud.
credentials, project = google.auth.default()

# Create the Compute Engine clients.
instances_client = compute_v1.InstancesClient()
firewalls_client = compute_v1.FirewallsClient()

zone = "us-west1-b"
fwPort = 5000
fwName = f"allow-{fwPort}"
instanceName = "blog"
nodeType = "e2-micro"

print("Creating VM2 instance.")

# Create the firewall rule if it does not already exist.
create_firewall_rule(firewalls_client,project,fwPort,fwName)

# Create the VM and wait for creation to finish.
operation = create_instance(instances_client,project,zone,instanceName,nodeType,fwName)
wait_for_operation(operation)


# Retrieve the instance so we can get its external IP address.
try:
    request = compute_v1.GetInstanceRequest(
        project=project,
        zone=zone,
        instance=instanceName,
    )

    instance_response = instances_client.get(
        request=request
    )

    if instance_response:
        instance_ip = (
            instance_response
            .network_interfaces[0]
            .access_configs[0]
            .nat_i_p
        )

        print(
            f"The blog is running at "
            f"http://{instance_ip}:{fwPort}"
        )

except Exception as exp:
    print(
        f"Unable to locate instance "
        f"{instanceName} to get the IP address"
    )
    print(exp)