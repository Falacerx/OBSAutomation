import os
import sys
import time

import logging
logging.basicConfig(level=logging.INFO)

sys.path.append('../')
from obswebsocket import obsws, requests

HOST = os.getenv("OBS_HOST")
PORT = os.getenv("OBS_PORT")
PASSWORD = os.getenv("OBS_PASSWORD")

def test_connection():
    ws = obsws(HOST, PORT, PASSWORD)
    ws.connect()
    ws.disconnect()

def start_recording():
    ws = obsws(HOST, PORT)
    ws.connect()

    try:
        print("Starting recording")
        resp = ws.call(requests.StartRecord())

    except KeyboardInterrupt:
        pass

    ws.disconnect()

def stop_recording():
    ws = obsws(HOST, PORT, PASSWORD)
    ws.connect()

    output_path = None
    try:
        print("Stopping recording")
        resp = ws.call(requests.StopRecord())
        output_path = resp.datain.get("outputPath", None)

    except KeyboardInterrupt:
        pass

    ws.disconnect()

    return output_path

def main():
    test_connection()

if __name__ == "__main__":
    main()