import subprocess
import time
import urllib.request

from google.cloud import compute_v1


def create_vm_sdk(
    project_id: str,
    instance_name: str,
    zone: str,
    startup_script: str | None = None,
    machine_type: str = "e2-standard-2",
    snapshot_name: str | None = None,
) -> None:
    """Creates a VM instance using the google-cloud-compute SDK with optional startup script."""
    instances_client = compute_v1.InstancesClient()

    # Configure boot disk
    disk_params = compute_v1.AttachedDiskInitializeParams()
    if snapshot_name:
        disk_params.source_snapshot = (
            f"projects/{project_id}/global/snapshots/{snapshot_name}"
        )
    else:
        disk_params.source_image = (
            "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
        )

    boot_disk = compute_v1.AttachedDisk(
        boot=True, auto_delete=True, initialize_params=disk_params
    )

    # Configure default network interface
    network_interface = compute_v1.NetworkInterface(
        network=f"projects/{project_id}/global/networks/default"
    )

    # Configure Instance Resource
    instance_resource = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/{machine_type}",
        disks=[boot_disk],
        network_interfaces=[network_interface],
    )

    # Attach startup script if provided
    if startup_script:
        metadata = compute_v1.Metadata(
            items=[compute_v1.Items(key="startup-script", value=startup_script)]
        )
        instance_resource.metadata = metadata

    request = compute_v1.InsertInstanceRequest(
        project=project_id, zone=zone, instance_resource=instance_resource
    )

    print(f"Creating instance '{instance_name}' in zone '{zone}'...")
    operation = instances_client.insert(request=request)

    # Block until instance provision is complete
    operation.result()


def get_internal_ip_sdk(project_id: str, instance_name: str, zone: str) -> str:
    """Retrieves the internal IP address of a VM instance using the SDK."""
    instances_client = compute_v1.InstancesClient()
    instance = instances_client.get(
        project=project_id, zone=zone, instance=instance_name
    )
    return instance.network_interfaces[0].network_i_p


def wait_for_server_health(
    target_ip: str, port: int = 5000, timeout: int = 60, delay: int = 2
) -> None:
    """Polls server over HTTP directly without using SSH until it is responsive."""
    url = f"http://{target_ip}:{port}/"
    print(f"Waiting for server at {url} to become ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status in (200, 404):
                    print(f"Server at {target_ip}:{port} is reachable and online.")
                    return
        except Exception:
            time.sleep(delay)

    print(f"Warning: Timed out waiting for server at {target_ip}:{port}. Proceeding anyway.")


def run_benchmark_local(target_ip: str, endpoint: str, reps: int, protocol: str) -> float:
    """Runs the benchmark client script locally against the target IP and returns execution duration."""
    start_time = time.perf_counter()

    if protocol.lower() == "rest":
        cmd = ["uv", "run", "python", "-u", "rest-client.py", target_ip, endpoint, str(reps)]
    elif protocol.lower() == "grpc":
        cmd = ["uv", "run", "python", "-u", "grpc-client.py", target_ip, endpoint, str(reps)]
    else:
        raise ValueError(f"Only REST or gRPC allowed, {protocol} not recognized")

    subprocess.run(cmd, check=True)
    return time.perf_counter() - start_time


def run_test_suite(target_ip: str, test_name: str, num_reps: int) -> float:
    running = f"starting {test_name} against IP: {target_ip}"
    print("=" * len(running))
    print(f"|{running}|")
    print("=" * len(running))

    endpoints = ["add", "rawimage", "dotproduct", "jsonimage"]
    start_time = time.perf_counter()

    # Ensure backend server is up before starting benchmarks
    wait_for_server_health(target_ip)

    for endpoint in endpoints:
        print(f"Running REST benchmark for {endpoint}...")
        run_benchmark_local(
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="REST",
        )

        print(f"Running gRPC benchmark for {endpoint}...")
        run_benchmark_local(
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="GRPC",
        )

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"{test_name} completed in {elapsed_time:.2f} seconds\n")
    return elapsed_time


def main():
    PROJECT_ID = "lab-6-510321"
    SNAPSHOT_NAME = None  # e.g., "lab5-snapshot" if available
    MACHINE_TYPE = "e2-standard-2"

    ZONE_US = "us-west1-a"
    ZONE_EU = "europe-west3-a"

    # Define Server Startup Script
    server_startup_script = """#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /home/lude4390/Luc-lab6-rest-vs-grpc || true
uv run python server.py > /tmp/server.log 2>&1 &
"""

    # 1. Provision instances with startup scripts (No client VM required if running orchestrator locally)
    provision_start = time.perf_counter()
    create_vm_sdk(
        PROJECT_ID,
        "server-us-west1",
        ZONE_US,
        startup_script=server_startup_script,
        machine_type=MACHINE_TYPE,
        snapshot_name=SNAPSHOT_NAME,
    )
    create_vm_sdk(
        PROJECT_ID,
        "server-europe-west3",
        ZONE_EU,
        startup_script=server_startup_script,
        machine_type=MACHINE_TYPE,
        snapshot_name=SNAPSHOT_NAME,
    )
    provision_end = time.perf_counter()
    provision_time = provision_end - provision_start

    # 2. Retrieve IPs
    ip_server_us = get_internal_ip_sdk(PROJECT_ID, "server-us-west1", ZONE_US)
    ip_server_eu = get_internal_ip_sdk(PROJECT_ID, "server-europe-west3", ZONE_EU)

    print("\n--- INSTANCE INTERNAL IP ADDRESSES ---")
    print(f"US Server Internal IP: {ip_server_us}")
    print(f"EU Server Internal IP: {ip_server_eu}")

    # 3. Execute Benchmarks
    reps_same_zone = 500
    time_test_1 = run_test_suite(
        ip_server_us,
        "test 1 (same zone)",
        reps_same_zone,
    )

    reps_cross_region = 50
    time_test_2 = run_test_suite(
        ip_server_eu,
        "test 2 (cross region)",
        reps_cross_region,
    )

    print("==========================================")
    print("total timing summary")
    print("==========================================")
    print(f"Infrastructure Provisioning Time : {provision_time:.2f} s")
    print(f"Test 1 (Same-Zone) Total Duration : {time_test_1:.2f} s")
    print(f"Test 2 (Cross-Region) Total Duration: {time_test_2:.2f} s")


if __name__ == "__main__":
    main()
