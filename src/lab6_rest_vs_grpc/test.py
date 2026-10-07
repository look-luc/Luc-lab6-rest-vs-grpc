import subprocess
import time

from google.cloud import compute_v1


def create_vm_sdk(
    project_id: str,
    instance_name: str,
    zone: str,
    startup_script: str | None = None,
    machine_type: str = "e2-standard-2",
    snapshot_name: str | None = None,
) -> None:
    """Creates a VM instance using the google-cloud-compute SDK."""
    instances_client = compute_v1.InstancesClient()

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

    network_interface = compute_v1.NetworkInterface(
        network=f"projects/{project_id}/global/networks/default"
    )

    instance_resource = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/{machine_type}",
        disks=[boot_disk],
        network_interfaces=[network_interface],
    )

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
    operation.result()


def get_internal_ip_sdk(project_id: str, instance_name: str, zone: str) -> str:
    """Retrieves internal IP address of a VM instance."""
    instances_client = compute_v1.InstancesClient()
    instance = instances_client.get(
        project=project_id, zone=zone, instance=instance_name
    )
    return instance.network_interfaces[0].network_i_p


def wait_for_ssh(
    vm_name: str, zone: str, max_retries: int = 30, delay: int = 5
) -> None:
    """Polls remote VM via SSH until port 22 / sshd is ready."""
    print(f"Waiting for SSH to become ready on '{vm_name}'...")
    check_cmd = [
        "gcloud",
        "compute",
        "ssh",
        vm_name,
        f"--zone={zone}",
        "--quiet",
        "--tunnel-through-iap",
        "--ssh-flag=-o StrictHostKeyChecking=no",
        "--ssh-flag=-o ConnectTimeout=5",
        "--command=echo SSH Ready",
    ]

    for attempt in range(1, max_retries + 1):
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SSH connected to '{vm_name}'.")
            return
        time.sleep(delay)

    raise RuntimeError(
        f"Failed SSH connection to '{vm_name}' after {max_retries * delay}s."
    )


def execute_ssh_command(vm_name: str, zone: str, command: str) -> str:
    """Executes command on remote client VM via gcloud compute ssh and IAP."""
    ssh_cmd = [
        "gcloud",
        "compute",
        "ssh",
        vm_name,
        f"--zone={zone}",
        "--quiet",
        "--tunnel-through-iap",
        "--ssh-flag=-o StrictHostKeyChecking=no",
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
    client_vm_name: str,
    target_ip: str,
    endpoint: str,
    reps: int,
    protocol: str,
    zone: str,
) -> str:
    """Runs client script inside client-us-west1 target internal IP."""
    base_dir = "cd ~/Luc-lab6-rest-vs-grpc && export PATH=$HOME/.local/bin:$PATH &&"

    if protocol.lower() == "rest":
        cmd = f"{base_dir} uv run python -u rest-client.py {target_ip} {endpoint} {reps}"
    elif protocol.lower() == "grpc":
        cmd = f"{base_dir} uv run python -u grpc-client.py {target_ip} {endpoint} {reps}"
    else:
        raise ValueError(f"Protocol '{protocol}' not recognized")

    return execute_ssh_command(client_vm_name, zone, cmd)


def run_test_suite(
    client_vm_name: str,
    target_ip: str,
    test_name: str,
    num_reps: int,
    zone: str,
) -> float:
    running = f"starting {test_name} against IP: {target_ip}"
    print("=" * len(running))
    print(f"|{running}|")
    print("=" * len(running))

    endpoints = ["add", "rawimage", "dotproduct", "jsonimage"]
    start_time = time.perf_counter()

    for endpoint in endpoints:
        print(f"Running REST benchmark for {endpoint}...")
        run_benchmark_remote(
            client_vm_name=client_vm_name,
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="REST",
            zone=zone,
        )

        print(f"Running gRPC benchmark for {endpoint}...")
        run_benchmark_remote(
            client_vm_name=client_vm_name,
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="GRPC",
            zone=zone,
        )

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"{test_name} completed in {elapsed_time:.2f} seconds\n")
    return elapsed_time

def sync_code_to_client(client_vm_name: str, zone: str) -> None:
    """Copies the local repository directory to the remote client VM."""
    print(f"Syncing code repository to '{client_vm_name}'...")
    scp_cmd = [
        "gcloud",
        "compute",
        "scp",
        "--recurse",
        "--zone=" + zone,
        "--tunnel-through-iap",
        "--ssh-flag=-o StrictHostKeyChecking=no",
        ".",  # Local repo root
        f"{client_vm_name}:~/Luc-lab6-rest-vs-grpc",
    ]
    subprocess.run(scp_cmd, check=True)

def main():
    PROJECT_ID = "lab-6-510321"
    SNAPSHOT_NAME = None
    MACHINE_TYPE = "e2-standard-2"

    ZONE_US = "us-west1-a"
    ZONE_EU = "europe-west3-a"

    server_startup_script = """#!/bin/bash
export PATH=$HOME/.local/bin:$PATH
cd /home/lude4390/Luc-lab6-rest-vs-grpc || true
uv run python rest-server.py > /tmp/rest_server.log 2>&1 &
uv run python grpc_server.py > /tmp/grpc_server.log 2>&1 &
"""

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
        "client-us-west1",
        ZONE_US,
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

    # Ensure SSH service is accessible on client VM before running tests
    wait_for_ssh("client-us-west1", ZONE_US)
    sync_code_to_client("client-us-west1", ZONE_US)

    ip_server_us = get_internal_ip_sdk(PROJECT_ID, "server-us-west1", ZONE_US)
    ip_client_us = get_internal_ip_sdk(PROJECT_ID, "client-us-west1", ZONE_US)
    ip_server_eu = get_internal_ip_sdk(
        PROJECT_ID, "server-europe-west3", ZONE_EU
    )

    print("\n--- INSTANCE INTERNAL IP ADDRESSES ---")
    print(f"US Server Internal IP: {ip_server_us}")
    print(f"US Client Internal IP: {ip_client_us}")
    print(f"EU Server Internal IP: {ip_server_eu}")

    reps_same_zone = 500
    time_test_1 = run_test_suite(
        "client-us-west1",
        ip_server_us,
        "test 1 (same zone)",
        reps_same_zone,
        ZONE_US,
    )

    reps_cross_region = 50
    time_test_2 = run_test_suite(
        "client-us-west1",
        ip_server_eu,
        "test 2 (cross region)",
        reps_cross_region,
        ZONE_US,
    )

    print("==========================================")
    print("total timing summary")
    print("==========================================")
    print(f"Infrastructure Provisioning Time : {provision_time:.2f} s")
    print(f"Test 1 (Same-Zone) Total Duration : {time_test_1:.2f} s")
    print(f"Test 2 (Cross-Region) Total Duration: {time_test_2:.2f} s")


if __name__ == "__main__":
    main()
