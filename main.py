import asyncio
from datetime import datetime
import json
import re
import shutil
import sys
import time
import uuid
import requests
import os
from database import add_video, update_recording_with_video_info
import edit
from selenium import webdriver
from selenium.webdriver.common.by import By
import pyautogui
from pywinauto import findwindows
import pywinauto
import threading
from moviepy.editor import VideoFileClip
from itertools import combinations

from dotenv import load_dotenv
from record import process_replays
import upload
load_dotenv()

from rl_ws import RLWebSocketClient

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
BARL_PATH = os.getenv("BARL_PATH")
RL_HOST = os.getenv("RL_HOST")
RL_PORT = os.getenv("RL_PORT")


def setup_recording_directory(player):
    path = f"./recordings/{player}"
    if not os.path.exists(path):
        os.makedirs(path)

    return path

def setup_finished_directory(player):
    path = f"./finished/{player}"
    if not os.path.exists(path):
        os.makedirs(path)

    return path

def get_video_duration(file_path):
    """Returns the duration of a video file in seconds."""
    try:
        clip = VideoFileClip(file_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    
def group_videos(video_paths):
    min_duration = 10 * 60
    max_duration = 15 * 60

    valid_groups = []
    for n in range(2, 4):
        for combo in combinations(video_paths, n):
            total_duration = sum(get_video_duration(f) for f in combo if get_video_duration(f) is not None)
            if min_duration <= total_duration <= max_duration:
                valid_groups.append((combo, total_duration))

    return valid_groups

async def main():
    event_queue = asyncio.Queue()
    rl_client = RLWebSocketClient(f"ws://{RL_HOST}:{RL_PORT}", event_queue)
    asyncio.create_task(rl_client.connect())

    player = sys.argv[1]  
    group_url = sys.argv[2]
    recording_directory = setup_recording_directory(player)
    finished_directory = setup_finished_directory(player)
            
    await process_replays(group_url, player, rl_client)

    video_paths = [f"{recording_directory}/{f}" for f in os.listdir(recording_directory) if f.endswith(".mp4")]
    valid_groups = group_videos(video_paths)

    if not valid_groups:
        print("No valid groups found.")
        return
    else:
        for i, (group, _) in enumerate(valid_groups, 1):
            print(f"Group {i}")
            video_id = str(uuid.uuid4())
            edited_file_path = f"./edits/{player}"
            if not os.path.exists(edited_file_path):
                os.makedirs(edited_file_path)
            edited_video_path = f"{edited_file_path}/{video_id}.mp4"

            video_title = f"{datetime.today().isoformat()} {player} {i}"
            result = edit.edit_videos(group, edited_video_path, player, video_title, video_id)
            
            for seq, recording in enumerate(group):
                shutil.move(recording, f"{finished_directory}/{os.path.basename(recording)}")
                update_recording_with_video_info(recording, video_id, seq)

            if result == "Success":
                upload.upload_video(edited_video_path, player, video_title)


if __name__ == "__main__":
    asyncio.run(main())
