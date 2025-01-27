import asyncio
from datetime import datetime
import shutil
import sys
import uuid
import os
from database import get_video_by_id, update_recording_with_video_info, update_video_with_uploaded_status
import edit
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

def generate_uuid(key: str):
    namespace = uuid.NAMESPACE_DNS
    return str(uuid.uuid5(namespace, key))

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
    min_duration = 12 * 60
    max_duration = 16 * 60

    durations = [ {"path": p, "duration": get_video_duration(p)} for p in video_paths]
    used_videos = set()

    valid_groups = []
    for n in range(2, 4):
        for combo in combinations(durations, n):

            combo_paths = [f["path"] for f in combo]
            if any(path in used_videos for path in combo_paths):
                continue

            total_duration = sum(f["duration"] for f in combo if f["duration"] is not None)

            if min_duration <= total_duration <= max_duration:
                valid_groups.append((combo, total_duration))
                used_videos.update(combo_paths)

    return valid_groups

async def main():
    event_queue = asyncio.Queue()
    rl_client = RLWebSocketClient(f"ws://{RL_HOST}:{RL_PORT}", event_queue)
    asyncio.create_task(rl_client.connect())

    valid_players = ["Zen", "Dark", "Vatira", "Rw9"]
    # if len(sys.argv) < 2:
    #     print("Please provide a player name.")
    #     return
    
    player = "Zen"
    if player not in valid_players:
        print("Invalid player name.")
        return
    
    recording_directory = setup_recording_directory(player)
    finished_directory = setup_finished_directory(player)
            
    await process_replays(player, rl_client)

    video_paths = [f"{recording_directory}/{f}" for f in os.listdir(recording_directory) if f.endswith(".mp4")]
    valid_groups = group_videos(video_paths)

    if not valid_groups:
        print("No valid groups found.")
        return
    else:
        for i, (group, _) in enumerate(valid_groups, 1):
            print(f"Group {i}")
            video_id = generate_uuid("".join([x["path"].split("/")[-1] for x in group]))
            edited_file_path = f"./edits/{player}"
            if not os.path.exists(edited_file_path):
                os.makedirs(edited_file_path)
            edited_video_path = f"{edited_file_path}/{video_id}.mp4"

            video_title = f"{datetime.today().isoformat()} {player} {i}"
            result, exists = edit.edit_videos(group, edited_video_path, player, video_title, video_id)

            print(f"Result: {result}, Exists: {exists}")
            
            if not exists and result == "Success":
                for seq, recording in enumerate(group):
                    recording_file = os.path.basename(recording["path"])
                    recording_id = recording_file.split(".")[0]
                    shutil.move(recording["path"], f"{finished_directory}/{recording_file}")
                    update_recording_with_video_info(recording_id, video_id, seq)

            uploaded_video = get_video_by_id(video_id)
            is_uploaded = False
            if uploaded_video is not None and uploaded_video.get("uploaded", False):
                is_uploaded = True

            if result == "Success" and not is_uploaded:
                upload.upload_video(edited_video_path, player, video_title)
                update_video_with_uploaded_status(video_id, uploaded=True)



if __name__ == "__main__":
    asyncio.run(main())