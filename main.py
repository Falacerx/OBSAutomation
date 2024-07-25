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
import threading

from dotenv import load_dotenv
load_dotenv()

from rl_ws import RLWebSocketClient
import obs

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
            
def get_replays(group_id):
    headers = {"Authorization": API_KEY}
    params = {"group": group_id}
    url = f"{API_URL}/replays"
    response = requests.get(url, headers=headers, params=params)
    replays = response.json()['list']

    print(replays)
    res = []
    for replay in replays:
        replay_res = {
            "link": replay['link'],
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

def sanitize(name):
    return re.sub(r'[^a-zA-Z0-9 ]', '', name).upper()

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

    # replays = get_replays(group_id)

    # with open("replays.json", "w") as f:
    #     json.dump(replays, f, indent=4)

    with open("replays.json", "r") as f:
        replays = json.load(f)

    game_number = 1
    for replay in replays:
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
        handle_recording(output_path, player, game_number)

        print("Recording saved")
        game_number += 1
        break

    driver.quit()

async def rl_send_command(client: RLWebSocketClient, command, data={}):
    await client.process_command(command, data)
    await asyncio.sleep(1)

def setup_recording_directory(player):
    path = f"./recordings/{player}"
    if not os.path.exists(path):
        os.makedirs(path)

    return path

def handle_recording(output_path, player, game_number):
    today = datetime.today().strftime('%Y-%m-%d')
    ext = output_path.split(".")[-1]
    recording_file_name = f"{today}_{player} Game {game_number}.{ext}"   
    output_directory = setup_recording_directory(player)

    retry = 0
    max_retries = 5
    while retry < max_retries:
        try:
            shutil.move(output_path, f"{output_directory}/{recording_file_name}")
        except PermissionError as e:
            time.sleep(5)
            print("Recording is still being written, retrying...")
            retry += 1
            continue
        except FileNotFoundError as e:
            break


async def main():
    event_queue = asyncio.Queue()
    rl_client = RLWebSocketClient(f"ws://{RL_HOST}:{RL_PORT}", event_queue)
    asyncio.create_task(rl_client.connect())

    group_url = "https://ballchasing.com/group/t2407-kcndnkr9f9"
    player = "Zen"  
    setup_recording_directory(player)
            
    await process_replays(group_url, player, rl_client)

if __name__ == "__main__":
    asyncio.run(main())
