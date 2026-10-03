from google.cloud import compute_v1


def create_vm_sdk(
    project_id: str,
    instance_name: str,
    zone: str,
    machine_type: str = "e2-standard-2",
    snapshot_name: str|None = None
) -> None:
    """Creates a VM instance using the google-cloud-compute SDK."""
    instances_client = compute_v1.InstancesClient()

    # Configure boot disk
    disk_params = compute_v1.AttachedDiskInitializeParams()
    if snapshot_name:
        disk_params.source_snapshot = f"projects/{project_id}/global/snapshots/{snapshot_name}"
    else:
        disk_params.source_image = "projects/debian-cloud/global/images/family/debian-11"

    boot_disk = compute_v1.AttachedDisk(
        boot=True,
        auto_delete=True,
        initialize_params=disk_params
    )

    # Configure default network interface
    network_interface = compute_v1.NetworkInterface(
        network=f"projects/{project_id}/global/networks/default"
    )

    # Build instance resource
    instance_resource = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/{machine_type}",
        disks=[boot_disk],
        network_interfaces=[network_interface]
    )

    request = compute_v1.InsertInstanceRequest(
        project=project_id,
        zone=zone,
        instance_resource=instance_resource
    )

    print(f"Creating instance '{instance_name}' in zone '{zone}'...")
    operation = instances_client.insert(request=request)

    # Block until instance provision is complete
    operation.result()

def get_internal_ip_sdk(project_id: str, instance_name: str, zone: str) -> str:
    """Retrieves the internal IP address of a VM instance using the SDK."""
    instances_client = compute_v1.InstancesClient()
    instance = instances_client.get(project=project_id, zone=zone, instance=instance_name)
    return instance.network_interfaces[0].network_ip

def main():
    PROJECT_ID = "your-gcp-project-id"  # Replace with your GCP project ID
    SNAPSHOT_NAME = None                # e.g., "lab5-snapshot" if available
    MACHINE_TYPE = "e2-standard-2"

    ZONE_US = "us-west1-a"
    ZONE_EU = "europe-west3-a"

    # 1. Provision instances
    create_vm_sdk(PROJECT_ID, "server-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME)
    create_vm_sdk(PROJECT_ID, "client-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME)
    create_vm_sdk(PROJECT_ID, "server-europe-west3", ZONE_EU, MACHINE_TYPE, SNAPSHOT_NAME)

    # 2. Retrieve IPs
    ip_server_us = get_internal_ip_sdk(PROJECT_ID, "server-us-west1", ZONE_US)
    ip_client_us = get_internal_ip_sdk(PROJECT_ID, "client-us-west1", ZONE_US)
    ip_server_eu = get_internal_ip_sdk(PROJECT_ID, "server-europe-west3", ZONE_EU)

    print("\n--- INSTANCE INTERNAL IP ADDRESSES ---")
    print(f"US Server Internal IP: {ip_server_us}")
    print(f"US Client Internal IP: {ip_client_us}")
    print(f"EU Server Internal IP: {ip_server_eu}")

if __name__ == "__main__":
    main()
