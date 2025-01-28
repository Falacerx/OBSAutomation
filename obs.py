import os
import sys
import time

import logging
logging.basicConfig(level=logging.INFO)

sys.path.append('../')

import obsws_python as obs

HOST = os.getenv("OBS_HOST")
PORT = os.getenv("OBS_PORT")
PASSWORD = os.getenv("OBS_PASSWORD")

def test_connection():
    start_recording()
    time.sleep(1)
    p = stop_recording()
    print(p)

def start_recording():
    ws = obs.ReqClient(host=HOST, port=PORT, password=PASSWORD, timeout=3)

    try:
        print("Starting recording")
        ws.start_record()

    except KeyboardInterrupt:
        pass

def stop_recording():
    ws = obs.ReqClient(host=HOST, port=PORT, password=PASSWORD, timeout=3)

    output_path = None
    try:
        print("Stopping recording")
        resp = ws.stop_record()
        output_path = resp.output_path

    except KeyboardInterrupt:
        pass


    return output_path

def main():
    test_connection()

if __name__ == "__main__":
    main()