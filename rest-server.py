#!/usr/bin/env python3

import argparse
import base64
import io
import json
import logging

import jsonpickle
import numpy as np
from flask import Flask, Response, request
from PIL import Image

app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/api/add/<int:a>/<int:b>', methods=['GET', 'POST'])
def add(a, b):
    response = {'sum': str(a + b)}
    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


@app.route('/api/rawimage', methods=['POST'])
def rawimage():
    r = request

    try:
        ioBuffer = io.BytesIO(r.data)
        img = Image.open(ioBuffer)

        response = {
            'width': img.size[0],
            'height': img.size[1]
        }
    except Exception:
        response = {'width': 0, 'height': 0}

    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )

@app.route('/api/dotproduct/<a_str>/<b_str>', methods=['POST'])
def dotproduct(a_str, b_str):
    try:
        a = json.loads(a_str)
        b = json.loads(b_str)
        a_numpy, b_numpy = np.array(a), np.array(b)
        response = {'dot product': str(a_numpy @ b_numpy)}
    except Exception as e:
        response = {'error': str(e)}

    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


@app.route('/api/jsonimage', methods=['POST'])
def jsonimage():
    r = request
    ioBuffer = base64.b64encode(r.data)

    response = {
        "image": ioBuffer.decode('utf-8')
    }

    response_pickled = jsonpickle.encode(response)
    return Response(
        response=response_pickled,
        status=200,
        mimetype="application/json"
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask REST server')
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=5000,
        help='Port on which to run the server (default: 5000)'
    )

    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
