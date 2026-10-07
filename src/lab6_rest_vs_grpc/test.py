import subprocess
import time

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
        disk_params.source_image = "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"

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
    return instance.network_interfaces[0].network_i_p

def execute_ssh_command(vm_name: str, zone: str, command: str) -> str:
    """Executes a shell command on a remote GCP Compute Engine instance via gcloud SSH, streaming stdout line-by-line in real time."""
    ssh_cmd = [
        "gcloud",
        "compute",
        "ssh",
        vm_name,
        f"--zone={zone}",
        "--quiet",  # Suppresses interactive prompts and setup warnings
        "--ssh-flag=-o StrictHostKeyChecking=no",  # Skips key verification prompts
        f"--command={command}",
    ]

    process = subprocess.Popen(
        ssh_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines = []
    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            print(f"  [{vm_name}] {line}", end="", flush=True)
            output_lines.append(line)
        process.stdout.close()

    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, ssh_cmd)

    return "".join(output_lines).strip()

def run_benchmark_remote(
    client_vm_name,
    target_ip,
    endpoint,
    reps,
    protocol,
    zone
):
    if protocol.lower() == "rest":
        cmd = f"uv run -u rest-client.py {target_ip} {endpoint} {reps}"
    elif protocol.lower() == "grpc":
        cmd = f"uv run -u grpc-client.py {target_ip} {endpoint} {reps}"
    else:
        raise ValueError(f"Only REST or gRPC allowed, {protocol} not recognized")

    return execute_ssh_command(client_vm_name, zone, cmd)

def run_test_suite(
    client_vm_name,
    target_ip,
    test_name,
    num_reps,
    zone
):
    running = f"starting {test_name}  against IP: {target_ip}"
    print("="*len(running))
    print(f"|{running}|")
    print("="*len(running))

    endpoints = [
        "add",
        "rawimage",
        "dotproduct",
        "jsonimage"
    ]
    start_time = time.perf_counter()

    for endpoint in endpoints:
        print(f"Running REST benchmark for {endpoint} at zone {zone}")
        run_benchmark_remote(
            client_vm_name=client_vm_name,
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="REST",
            zone=zone
        )

        print(f"Running gRPC benchmark for {endpoint} at zone {zone}")
        run_benchmark_remote(
            client_vm_name=client_vm_name,
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="GRPC",
            zone=zone
        )

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"{test_name} completed in {elapsed_time} seconds\n")
    return elapsed_time

def main():
    PROJECT_ID = "lab-6-510321"
    SNAPSHOT_NAME = None                # e.g., "lab5-snapshot" if available
    MACHINE_TYPE = "e2-standard-2"

    ZONE_US = "us-west1-a"
    ZONE_EU = "europe-west3-a"

    # 1. Provision instances
    provision_start = time.perf_counter()
    create_vm_sdk(PROJECT_ID, "server-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME)
    create_vm_sdk(PROJECT_ID, "client-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME)
    create_vm_sdk(PROJECT_ID, "server-europe-west3", ZONE_EU, MACHINE_TYPE, SNAPSHOT_NAME)
    provision_end = time.perf_counter()
    provision_time = provision_end - provision_start

    # 2. Retrieve IPs
    ip_server_us = get_internal_ip_sdk(PROJECT_ID, "server-us-west1", ZONE_US)
    ip_client_us = get_internal_ip_sdk(PROJECT_ID, "client-us-west1", ZONE_US)
    ip_server_eu = get_internal_ip_sdk(PROJECT_ID, "server-europe-west3", ZONE_EU)

    print("\n--- INSTANCE INTERNAL IP ADDRESSES ---")
    print(f"US Server Internal IP: {ip_server_us}")
    print(f"US Client Internal IP: {ip_client_us}")
    print(f"EU Server Internal IP: {ip_server_eu}")

    reps_Same_zone = 500
    time_test_1 = run_test_suite(
        "client-us-west1",
        ip_server_us,
        "test 1 (same zone)",
        reps_Same_zone,
        "us-west1-a"
    )

    reps_cross_region = 50
    time_test_2 = run_test_suite(
        "client-us-west1",
        ip_server_eu,
        "test 2 (cross region)",
        reps_cross_region,
        "europe-west3-a"
    )

    print("==========================================")
    print("total timing summary")
    print("==========================================")
    print(f"Infrastructure Provisioning Time : {provision_time} s")
    print(f"Test 1 (Same-Zone) Total Duration : {time_test_1} s")
    print(f"Test 2 (Cross-Region) Total Duration: {time_test_2} s")

if __name__ == "__main__":
    main()
