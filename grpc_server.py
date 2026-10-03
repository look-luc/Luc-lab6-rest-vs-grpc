import base64
from concurrent import futures
from io import BytesIO

import grpc
import numpy as np
from PIL import Image

import grpc_pb2
import grpc_pb2_grpc


class grpc_server(grpc_pb2_grpc.grpcServiceServicer):
    def Add(self, request, context):
        result_sum = request.a + request.b
        return grpc_pb2.addReply(sum=result_sum)

    def DotProduct(self, request, context):
        a_numpy, b_numpy = np.array(request.a), np.array(request.b)
        return grpc_pb2.dotProductReply(
            dotproduct=float(a_numpy @ b_numpy)
        )

    def RawImage(self, request, context):
        image_bytes = request.img
        image_obj = Image.open(BytesIO(image_bytes))
        width, height = image_obj.size
        return grpc_pb2.imageReply(width=width, height=height)

    def JsonImage(self, request, context):
        image_bytes = base64.b64decode(request.img)
        image_obj = Image.open(BytesIO(image_bytes))
        width, height = image_obj.size
        return grpc_pb2.imageReply(width=width, height=height)


def serve(port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # FIX: Pass servicer instance `grpc_server()`, not base class `grpcServiceServicer()`
    grpc_pb2_grpc.add_grpcServiceServicer_to_server(
        grpc_server(),
        server
    )

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"gRPC Server listening on port {port}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
