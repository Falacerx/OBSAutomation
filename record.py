import asyncio
from datetime import datetime
import json
import re
import shutil
import time
import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import pyautogui
from pywinauto import findwindows
import pywinauto
from rl_ws import RLWebSocketClient
import obs
from database import add_recording, get_recording_by_id

from dotenv import load_dotenv
load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
BARL_PATH = os.getenv("BARL_PATH")
RL_HOST = os.getenv("RL_HOST")
RL_PORT = os.getenv("RL_PORT")

def bring_barl_to_foreground():
    windows = findwindows.find_windows()
    for w in windows:
        try:
            window = pywinauto.Application().connect(handle=w).window()
            if window.window_text() == "BARL: Broadcast Assistant for RL":
                window.set_focus()
                break
        except Exception as e:
            continue

def setup_recording_directory(player):
    path = f"./recordings/{player}"
    if not os.path.exists(path):
        os.makedirs(path)

    return path
            
def get_replays(group_id):
    headers = {"Authorization": API_KEY}
    params = {"group": group_id}
    url = f"{API_URL}/replays"
    response = requests.get(url, headers=headers, params=params)
    replays = response.json()['list']

    res = []
    for replay in replays:
        replay_res = {
            "id": replay['id'],
            "link": replay['link'],
            "date": replay['date'],
            "blue": {
                "players": [
                    {
                        "name": p['name'],
                        "platform": p['id']['platform'],
                        "id": p['id']['id']
                    } for p in replay['blue']['players']
                ]
            },
            "orange": {
                "players": [
                    {
                        "name": p['name'],
                        "platform": p['id']['platform'],
                        "id": p['id']['id']
                    } for p in replay['orange']['players']
                ]
            }
        }

        res.append(replay_res)

    return res

def handle_recording(output_path, player, id):
    ext = output_path.split(".")[-1]
    recording_file_name = f"{id}.{ext}"   
    output_directory = setup_recording_directory(player)

    retry = 0
    max_retries = 10
    video_path = f"{output_directory}/{recording_file_name}"
    while retry < max_retries:
        try:
            shutil.move(output_path, video_path)
        except PermissionError as e:
            time.sleep(20)
            print("Recording is still being written, retrying...")
            retry += 1
            continue
        except FileNotFoundError as e:
            break

    if retry == max_retries:
        print("Failed to move recording after 10 retries")

    print(f"Recording saved as {recording_file_name}")

    return video_path

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9 ]', '', name).upper()

async def rl_send_command(client: RLWebSocketClient, command, data={}):
    await client.process_command(command, data)
    await asyncio.sleep(1)

async def wait_for_message(client):
    message = await client.event_queue.get()
    message = json.loads(message)
    client.event_queue.task_done()
    return message

async def process_replays(group_url, player, rl_client):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)

    with open("pros.json", "r") as f:
        players = json.load(f)
    group_id = group_url.split("/")[-1]

    replays = get_replays(group_id)

    with open("replays.json", "w") as f:
        json.dump(replays, f, indent=4)

    video_paths = []

    game_number = 1
    for replay in replays:
        replay_id = replay['id']
        db_replay = get_recording_by_id(replay['id'])
        if db_replay is not None:
            continue
        replay_url = replay['link'].replace("api/replays", "replay")

        team_left = "/".join([sanitize(p['name']) for p in replay['blue']['players']])
        team_right = "/".join([sanitize(p['name']) for p in replay['orange']['players']])

        bring_barl_to_foreground()
        time.sleep(1)
        
        def replace(text):
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('delete')
            pyautogui.write(text, interval=0.05)

        pyautogui.click(x=700, y=510)
        replace(team_left)
        for _ in range(4):
            pyautogui.press('tab', interval=0.05)
        replace(team_right)

        driver.get(replay_url)
        
        play_button = driver.find_element(By.CLASS_NAME, 'replay-watch')
        play_button.click()
        
        message = await wait_for_message(rl_client)
        while message["event"] != "replay:started":
            message = await wait_for_message(rl_client)

        time.sleep(5)
        
        focus_command = {
            "platform": players[player]['platform'],
            "actor_id": players[player]['id']
        }
        await rl_send_command(rl_client, "replay:focus_player", focus_command)
        await rl_send_command(rl_client, "replay:skip_back")
        obs.start_recording()
        
        message = await wait_for_message(rl_client)
        while message["event"] != "replay:ended":
            message = await wait_for_message(rl_client)

        print("Recording ended, saving...")
        output_path = obs.stop_recording()
        video_path = handle_recording(output_path, player, replay_id)

        recording = {
            "id": replay_id,
            "player": player,
            "recording_date": datetime.now().isoformat(),
            "replay_date": replay['date'],
            "url": video_path
        }
        add_recording(recording)

        print("Recording saved")
        game_number += 1

        video_paths.append(video_path)

        with open("video_paths.json", "w") as f:
            json.dump(video_paths, f, indent=4)

    driver.quit()

    return video_paths
