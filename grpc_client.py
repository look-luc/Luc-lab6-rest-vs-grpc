import base64
import sys
import time

import grpc

import grpc_pb2
import grpc_pb2_grpc


def run_benckmark(host, endpoint, iterations):
    channel = grpc.insecure_channel(f'{host}:50051')
    stub = grpc_pb2_grpc.grpcServiceStub(channel)

    if endpoint.lower() == "add":
        request_data = grpc_pb2.addMsg(a=5, b=10)
        target_rpc = stub.Add

    elif endpoint.lower() == "dotproduct":
        VEC_A = [1.0, 2.0, 3.0, 4.0, 5.0]
        VEC_B = [5.0, 4.0, 3.0, 2.0, 1.0]
        request_data = grpc_pb2.dotProductMsg(a=VEC_A, b=VEC_B)
        target_rpc = stub.DotProduct

    # FIX: Added missing rawimage RPC handler
    elif endpoint.lower() in ["rawimage", "raw_image"]:
        with open("Flatirons_Winter_Sunrise_edit_2.jpg", "rb") as file:
            raw_bytes = file.read()
        request_data = grpc_pb2.rawImageMsg(img=raw_bytes)
        target_rpc = stub.RawImage

    elif endpoint.lower() in ["jsonimage", "json_image"]:
        with open("Flatirons_Winter_Sunrise_edit_2.jpg", "rb") as file:
            raw_bytes = file.read()

        # FIX: Convert bytes to UTF-8 string properly
        encoded_str = base64.b64encode(raw_bytes).decode('utf-8')
        request_data = grpc_pb2.jsonImageMsg(img=encoded_str)
        target_rpc = stub.JsonImage

    else:
        raise ValueError(f"Unknown endpoint: {endpoint}")

    start_time = time.perf_counter()

    for _ in range(iterations):
        response = target_rpc(request_data)

    end_time = time.perf_counter()

    total_time = end_time - start_time
    time_per_query_ms = (total_time / iterations) * 1000.0

    print(f"Endpoint: {endpoint}\nIterations: {iterations}\nAvg time per query: {time_per_query_ms:.4f} ms")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 grpc_client.py <host> <endpoint> <iterations>")
        sys.exit(1)

    host_arg = sys.argv[1]
    endpoint_arg = sys.argv[2]
    iterations_arg = int(sys.argv[3])

    run_benckmark(host_arg, endpoint_arg, iterations_arg)
