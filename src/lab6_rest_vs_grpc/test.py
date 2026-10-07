import subprocess
import time
from pathlib import Path

from google.cloud import compute_v1

ENV_SETUP = "export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$HOME/.astral-uv/bin:$PATH; "
BASE_DIR = Path(__file__).parent.resolve()


def create_vm_sdk(
    project_id: str,
    instance_name: str,
    zone: str,
    machine_type: str = "e2-standard-2",
    snapshot_name: str | None = None,
) -> None:
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

    access_config = compute_v1.AccessConfig(
        name="External NAT",
        type_=compute_v1.AccessConfig.Type.ONE_TO_ONE_NAT.name,
    )

    network_interface = compute_v1.NetworkInterface(
        network=f"projects/{project_id}/global/networks/default",
        access_configs=[access_config],
    )

    instance_resource = compute_v1.Instance(
        name=instance_name,
        machine_type=f"zones/{zone}/machineTypes/{machine_type}",
        disks=[boot_disk],
        network_interfaces=[network_interface],
    )

    request = compute_v1.InsertInstanceRequest(
        project=project_id, zone=zone, instance_resource=instance_resource
    )

    print(f"Creating instance '{instance_name}' in zone '{zone}'...")
    operation = instances_client.insert(request=request)
    operation.result()


def get_internal_ip_sdk(project_id: str, instance_name: str, zone: str) -> str:
    instances_client = compute_v1.InstancesClient()
    instance = instances_client.get(
        project=project_id, zone=zone, instance=instance_name
    )
    return instance.network_interfaces[0].network_i_p


def execute_ssh_command(
    vm_name: str, zone: str, command: str, max_retries: int = 12, delay: int = 5
) -> str:
    ssh_cmd = [
        "gcloud",
        "compute",
        "ssh",
        vm_name,
        f"--zone={zone}",
        "--ssh-flag=-o StrictHostKeyChecking=no",
        "--ssh-flag=-o ConnectTimeout=5",
        f"--command={command}",
    ]

    for attempt in range(1, max_retries + 1):
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()

        print(
            f"[{attempt}/{max_retries}] Waiting for SSH on {vm_name} ({zone})... Retrying in {delay}s"
        )
        time.sleep(delay)

    raise RuntimeError(
        f"Failed to execute SSH command on {vm_name} after {max_retries} attempts.\n"
        f"Stderr: {result.stderr}"
    )


def sync_files_to_vm(vm_name: str, zone: str, files: list[Path]) -> None:
    print(f"Syncing files to '{vm_name}' ({zone})...")
    file_paths = [str(f) for f in files]

    for f in files:
        if not f.exists():
            raise FileNotFoundError(f"Required file does not exist locally: {f}")

    scp_cmd = (
        ["gcloud", "compute", "scp", f"--zone={zone}"]
        + file_paths
        + [f"{vm_name}:~/"]
    )
    result = subprocess.run(scp_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to SCP files to {vm_name} ({zone}). Stderr: {result.stderr}"
        )

    compile_cmd = f"{ENV_SETUP} python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpcService.proto"
    execute_ssh_command(vm_name, zone, compile_cmd)


def start_remote_servers(server_vm_name: str, zone: str) -> None:
    print(f"Starting REST and gRPC servers on '{server_vm_name}' ({zone})...")
    cmd = (
        f"{ENV_SETUP}"
        "nohup python3 rest-server.py > rest_server.log 2>&1 < /dev/null & "
        "nohup python3 grpc_server.py > grpc_server.log 2>&1 < /dev/null &"
    )
    execute_ssh_command(server_vm_name, zone, cmd)
    time.sleep(3)


def run_benchmark_remote(
    client_vm_name,
    target_ip,
    endpoint,
    reps,
    protocol,
    zone
):
    if protocol.lower() == "rest":
        rest_endpoint_map = {
            "add": "add",
            "rawimage": "rawImage",
            "dotproduct": "dotProduct",
            "jsonimage": "jsonImage",
        }
        rest_ep = rest_endpoint_map.get(endpoint.lower(), endpoint)
        cmd = f"{ENV_SETUP} python3 rest-client.py {target_ip} {rest_ep} {reps}"
    elif protocol.lower() == "grpc":
        cmd = f"{ENV_SETUP} python3 grpc_client.py {target_ip} {endpoint} {reps}"
    else:
        raise ValueError(f"Only REST or gRPC allowed, {protocol} not recognized")

    return execute_ssh_command(client_vm_name, zone, cmd)


def run_test_suite(client_vm_name, target_ip, test_name, num_reps, zone):
    running = f"starting {test_name} against IP: {target_ip}"
    print("=" * len(running))
    print(f"|{running}|")
    print("=" * len(running))

    endpoints = ["add", "rawimage", "dotproduct", "jsonimage"]
    start_time = time.perf_counter()

    for endpoint in endpoints:
        print(f"Running REST benchmark for {endpoint} at zone {zone}")
        run_benchmark_remote(
            client_vm_name=client_vm_name,
            target_ip=target_ip,
            endpoint=endpoint,
            reps=num_reps,
            protocol="REST",
            zone=zone,
        )

        print(f"Running gRPC benchmark for {endpoint} at zone {zone}")
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

    print(f"{test_name} completed in {elapsed_time} seconds\n")
    return elapsed_time


def main():
    PROJECT_ID = "lab-6-510321"
    SNAPSHOT_NAME = "lab6-base-snapshot"
    MACHINE_TYPE = "e2-standard-2"

    ZONE_US = "us-west1-a"
    ZONE_EU = "europe-west3-a"

    provision_start = time.perf_counter()
    create_vm_sdk(
        PROJECT_ID, "server-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME
    )
    create_vm_sdk(
        PROJECT_ID, "client-us-west1", ZONE_US, MACHINE_TYPE, SNAPSHOT_NAME
    )
    create_vm_sdk(
        PROJECT_ID,
        "server-europe-west3",
        ZONE_EU,
        MACHINE_TYPE,
        SNAPSHOT_NAME,
    )
    provision_end = time.perf_counter()
    provision_time = provision_end - provision_start

    ip_server_us = get_internal_ip_sdk(PROJECT_ID, "server-us-west1", ZONE_US)
    ip_client_us = get_internal_ip_sdk(PROJECT_ID, "client-us-west1", ZONE_US)
    ip_server_eu = get_internal_ip_sdk(
        PROJECT_ID, "server-europe-west3", ZONE_EU
    )

    print("\n--- INSTANCE INTERNAL IP ADDRESSES ---")
    print(f"US Server Internal IP: {ip_server_us}")
    print(f"US Client Internal IP: {ip_client_us}")
    print(f"EU Server Internal IP: {ip_server_eu}")

    required_files = [
        BASE_DIR / "grpcService.proto",
        BASE_DIR / "rest-server.py",
        BASE_DIR / "grpc_server.py",
        BASE_DIR / "rest-client.py",
        BASE_DIR / "grpc_client.py",
        BASE_DIR / "Flatirons_Winter_Sunrise_edit_2.jpg",
    ]

    vms = [
        ("server-us-west1", ZONE_US),
        ("client-us-west1", ZONE_US),
        ("server-europe-west3", ZONE_EU),
    ]

    for vm_name, zone in vms:
        sync_files_to_vm(vm_name, zone, required_files)

    start_remote_servers("server-us-west1", ZONE_US)
    start_remote_servers("server-europe-west3", ZONE_EU)

    reps_Same_zone = 500
    time_test_1 = run_test_suite(
        "client-us-west1",
        ip_server_us,
        "test 1 (same zone)",
        reps_Same_zone,
        "us-west1-a",
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
    print(f"Infrastructure Provisioning Time : {provision_time} s")
    print(f"Test 1 (Same-Zone) Total Duration : {time_test_1} s")
    print(f"Test 2 (Cross-Region) Total Duration: {time_test_2} s")


if __name__ == "__main__":
    main()
