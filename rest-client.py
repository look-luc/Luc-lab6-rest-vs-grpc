#!/usr/bin/env python3

from __future__ import print_function

import argparse
import base64
import json
import random
import time

import jsonpickle
import requests


def doRawImage(addr, debug=False):

    # prepare headers for http request
    headers = {'content-type': 'image/png'}

    img = open('Flatirons_Winter_Sunrise_edit_2.jpg', 'rb').read()

    # send http request with image and receive response
    image_url = addr + '/api/rawimage'
    response = requests.post(image_url, data=img, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))


def doAdd(addr, debug=False):

    headers = {'content-type': 'application/json'}

    # send http request with image and receive response
    add_url = addr + "/api/add/5/10"
    response = requests.post(add_url, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))


def doDotProduct(addr, debug=False):
    headers = {'content-type': 'application/json'}

    # send http request with image and receive response
    add_url = addr + "/api/dotproduct/[1, 2]/[3, 4]"
    response = requests.post(add_url, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))


def doJsonImage(addr, debug=False):
    headers = {'content-type': 'application/json'}

    # send http request with image and receive response
    add_url = addr + "/api/jsonimage"
    response = requests.post(add_url, headers=headers)

    if debug:
        print("Response is", response)
        print(json.loads(response.text))


# ---------------------------------------------------------
# Parse command-line arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser(
    description='REST client for measuring server operations'
)

parser.add_argument(
    'host',
    help='IP address or hostname of the REST server'
)

parser.add_argument(
    'cmd',
    choices=['add', 'rawImage', 'dotProduct', 'jsonImage'],
    help='Operation to perform'
)

parser.add_argument(
    'reps',
    type=int,
    help='Number of repetitions for measurement'
)

parser.add_argument(
    '-p', '--port',
    type=int,
    default=5000,
    help='Server port (default: 5000)'
)

parser.add_argument(
    '-d', '--debug',
    action='store_true',
    help='Print the response from the server'
)

args = parser.parse_args()


# ---------------------------------------------------------
# Build server address
# ---------------------------------------------------------

addr = f"http://{args.host}:{args.port}"

print(f"Running {args.reps} reps against {addr}")


# ---------------------------------------------------------
# Perform requested operation
# ---------------------------------------------------------

if args.cmd == 'rawImage':

    start = time.perf_counter()

    for x in range(args.reps):
        doRawImage(addr, debug=args.debug)

    delta = ((time.perf_counter() - start) / args.reps) * 1000
    print("Took", delta, "ms per operation")


elif args.cmd == 'add':

    start = time.perf_counter()

    for x in range(args.reps):
        doAdd(addr, debug=args.debug)

    delta = ((time.perf_counter() - start) / args.reps) * 1000
    print("Took", delta, "ms per operation")


elif args.cmd == 'jsonImage':

    start = time.perf_counter()

    for x in range(args.reps):
        doJsonImage(addr, debug=args.debug)

    delta = ((time.perf_counter() - start) / args.reps) * 1000
    print("Took", delta, "ms per operation")


elif args.cmd == 'dotProduct':

    start = time.perf_counter()

    for x in range(args.reps):
        doDotProduct(addr, debug=args.debug)

    delta = ((time.perf_counter() - start) / args.reps) * 1000
    print("Took", delta, "ms per operation")
