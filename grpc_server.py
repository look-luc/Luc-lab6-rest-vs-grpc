import numpy as np

import grpc_pb2
import grpc_pb2_grpc


class grpc_server(grpc_pb2_grpc.grpcServiceServicer):
    def add(self, request,context):
        result_sum = request.a + request.b
        return grpc_pb2.addReply(sum=result_sum)

    def dotproduct(self,request,context):
        a_numpy,b_numpy = np.array(request.a),np.array(request.b)
        return grpc_pb2.dotProductReply(
            dotproduct=a_numpy @ b_numpy
        )
