
|  Method 	| Local  	| Same-Zone  	|  Different Region 	|
|---	|---	|---	|---	|---	|
|   REST add	|   2.72684652199996 ms	|  3.9672635379999974 ms 	|  343.56578162000005 ms	|
|   gRPC add	|   0.8881 ms	|  1.2029ms 	|  168.6736 ms  	|
|   REST rawimg	|   5.581726061999916 ms	|   9.633725732000016 ms	|   1333.4396801799994 ms	|
|   gRPC rawimg	|   7.6662 ms    |   9.6520 ms	|   192.5675 ms	|
|   REST dotproduct	|   3.2745935000000372 ms	|  3.938091269999972 ms 	|  330.5936331800001 ms	|
|   gRPC dotproduct	|  1.0036 ms 	|   1.2723 ms	|  167.6576 ms  	|
|   REST jsonimg	|   57.83057531999998 ms	|   63.90032850000001 ms	|  3018.21246512 ms 	|
|   gRPC jsonimg	|    23.6583 ms   |  26.1729 ms 	|  246.8926 ms 	|
|   PING        |   0.044 ms    |   0.441 ms   |     178.367 ms  |

You should measure the basic latency  using the `ping` command - this can be construed to be the latency without any RPC or python overhead.

You should examine your results and provide a short paragraph with your observations of the performance difference between REST and gRPC. You should explicitly comment on the role that network latency plays -- it's useful to know that REST makes a new TCP connection for each query while gRPC makes a single TCP connection that is used for all the queries.

## Resutlts
Here is the output from the run:

```text
Creating instance 'server-us-west1' in zone 'us-west1-a' (attempt 1/5)...
Creating instance 'client-us-west1' in zone 'us-west1-a' (attempt 1/5)...
Creating instance 'server-europe-west3' in zone 'europe-west3-a' (attempt 1/5)...

--- INSTANCE INTERNAL IP ADDRESSES ---
US Server Internal IP: 10.138.0.63
US Client Internal IP: 10.138.15.192
EU Server Internal IP: 10.156.0.29
Syncing files to 'server-us-west1' (us-west1-a)...
Installing dependencies (jsonpickle flask numpy Pillow grpcio grpcio-tools protobuf>=5.29.0) on 'server-us-west1' (us-west1-a)...
Syncing files to 'client-us-west1' (us-west1-a)...
Installing dependencies (jsonpickle flask numpy Pillow grpcio grpcio-tools protobuf>=5.29.0) on 'client-us-west1' (us-west1-a)...
Syncing files to 'server-europe-west3' (europe-west3-a)...
Installing dependencies (jsonpickle flask numpy Pillow grpcio grpcio-tools protobuf>=5.29.0) on 'server-europe-west3' (europe-west3-a)...
Syncing files to 'server-us-west1' (us-west1-a)...
Syncing files to 'client-us-west1' (us-west1-a)...
Syncing files to 'server-europe-west3' (europe-west3-a)...
Starting REST and gRPC servers on 'server-us-west1' (us-west1-a)...
Starting REST and gRPC servers on 'server-europe-west3' (europe-west3-a)...
===================================================
|starting test 1 (same zone) against IP: 10.138.0.63|
===================================================

--- REST add ---
Running 500 reps against http://10.138.0.63:5000
Took 3.9672635379999974 ms per operation
--- gRPC add ---
Endpoint: add
Iterations: 500
Avg time per query: 1.2029 ms

--- REST rawimage ---
Running 500 reps against http://10.138.0.63:5000
Took 9.633725732000016 ms per operation
--- gRPC rawimage ---
Endpoint: rawimage
Iterations: 500
Avg time per query: 9.6520 ms

--- REST dotproduct ---
Running 500 reps against http://10.138.0.63:5000
Took 3.938091269999972 ms per operation
--- gRPC dotproduct ---
Endpoint: dotproduct
Iterations: 500
Avg time per query: 1.2723 ms

--- REST jsonimage ---
Running 500 reps against http://10.138.0.63:5000
Took 63.90032850000001 ms per operation
--- gRPC jsonimage ---
Endpoint: jsonimage
Iterations: 500
Avg time per query: 26.1729 ms
======================================================
|starting test 2 (cross region) against IP: 10.156.0.29|
======================================================

--- REST add ---
Running 50 reps against http://10.156.0.29:5000
Took 343.56578162000005 ms per operation
--- gRPC add ---
Endpoint: add
Iterations: 50
Avg time per query: 168.6736 ms

--- REST rawimage ---
Running 50 reps against http://10.156.0.29:5000
Took 1333.4396801799994 ms per operation
--- gRPC rawimage ---
Endpoint: rawimage
Iterations: 50
Avg time per query: 192.5675 ms

--- REST dotproduct ---
Running 50 reps against http://10.156.0.29:5000
Took 330.5936331800001 ms per operation
--- gRPC dotproduct ---
Endpoint: dotproduct
Iterations: 50
Avg time per query: 167.6576 ms

--- REST jsonimage ---
Running 50 reps against http://10.156.0.29:5000
Took 3018.21246512 ms per operation
--- gRPC jsonimage ---
Endpoint: jsonimage
Iterations: 50
Avg time per query: 246.8926 ms
==========================================
total timing summary
==========================================
Infrastructure Provisioning Time : 136.2241176330001 s
Test 1 (Same-Zone) Total Duration : {'REST_add': 'Running 500 reps against http://10.138.0.63:5000\nTook 3.9672635379999974 ms per operation', 'GRPC_add': 'Endpoint: add\nIterations: 500\nAvg time per query: 1.2029 ms', 'REST_rawimage': 'Running 500 reps against http://10.138.0.63:5000\nTook 9.633725732000016 ms per operation', 'GRPC_rawimage': 'Endpoint: rawimage\nIterations: 500\nAvg time per query: 9.6520 ms', 'REST_dotproduct': 'Running 500 reps against http://10.138.0.63:5000\nTook 3.938091269999972 ms per operation', 'GRPC_dotproduct': 'Endpoint: dotproduct\nIterations: 500\nAvg time per query: 1.2723 ms', 'REST_jsonimage': 'Running 500 reps against http://10.138.0.63:5000\nTook 63.90032850000001 ms per operation', 'GRPC_jsonimage': 'Endpoint: jsonimage\nIterations: 500\nAvg time per query: 26.1729 ms'} s
Test 2 (Cross-Region) Total Duration: {'REST_add': 'Running 50 reps against http://10.156.0.29:5000\nTook 343.56578162000005 ms per operation', 'GRPC_add': 'Endpoint: add\nIterations: 50\nAvg time per query: 168.6736 ms', 'REST_rawimage': 'Running 50 reps against http://10.156.0.29:5000\nTook 1333.4396801799994 ms per operation', 'GRPC_rawimage': 'Endpoint: rawimage\nIterations: 50\nAvg time per query: 192.5675 ms', 'REST_dotproduct': 'Running 50 reps against http://10.156.0.29:5000\nTook 330.5936331800001 ms per operation', 'GRPC_dotproduct': 'Endpoint: dotproduct\nIterations: 50\nAvg time per query: 167.6576 ms', 'REST_jsonimage': 'Running 50 reps against http://10.156.0.29:5000\nTook 3018.21246512 ms per operation', 'GRPC_jsonimage': 'Endpoint: jsonimage\nIterations: 50\nAvg time per query: 246.8926 ms'} s
Starting REST and gRPC servers on 'client-us-west1' (us-west1-a)...
======================================================
|starting Test 0 (Local Loopback) against IP: 127.0.0.1|
======================================================

--- REST add ---
Running 500 reps against http://127.0.0.1:5000
Took 2.72684652199996 ms per operation
--- gRPC add ---
Endpoint: add
Iterations: 500
Avg time per query: 0.8881 ms

--- REST rawimage ---
Running 500 reps against http://127.0.0.1:5000
Took 5.581726061999916 ms per operation
--- gRPC rawimage ---
Endpoint: rawimage
Iterations: 500
Avg time per query: 7.6662 ms

--- REST dotproduct ---
Running 500 reps against http://127.0.0.1:5000
Took 3.2745935000000372 ms per operation
--- gRPC dotproduct ---
Endpoint: dotproduct
Iterations: 500
Avg time per query: 1.0036 ms

--- REST jsonimage ---
Running 500 reps against http://127.0.0.1:5000
Took 57.83057531999998 ms per operation
--- gRPC jsonimage ---
Endpoint: jsonimage
Iterations: 500
Avg time per query: 23.6583 ms
Local Ping Latency: 0.044 ms
==========================================
Local test: {'REST_add': 'Running 500 reps against http://127.0.0.1:5000\nTook 2.72684652199996 ms per operation', 'GRPC_add': 'Endpoint: add\nIterations: 500\nAvg time per query: 0.8881 ms', 'REST_rawimage': 'Running 500 reps against http://127.0.0.1:5000\nTook 5.581726061999916 ms per operation', 'GRPC_rawimage': 'Endpoint: rawimage\nIterations: 500\nAvg time per query: 7.6662 ms', 'REST_dotproduct': 'Running 500 reps against http://127.0.0.1:5000\nTook 3.2745935000000372 ms per operation', 'GRPC_dotproduct': 'Endpoint: dotproduct\nIterations: 500\nAvg time per query: 1.0036 ms', 'REST_jsonimage': 'Running 500 reps against http://127.0.0.1:5000\nTook 57.83057531999998 ms per operation', 'GRPC_jsonimage': 'Endpoint: jsonimage\nIterations: 500\nAvg time per query: 23.6583 ms'}
ping same zone: 0.441 ms
ping cross zone: 178.367 ms
local ping:  ms
==========================================
```
