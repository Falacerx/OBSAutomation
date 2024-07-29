import os
import shutil
import time

from database import get_recording_by_id

videos = [x.split("/")[-1].split(".")[0] for x in os.listdir("./edits/Zen")]

for filename in os.listdir("./finished/Zen"):
    recording_id = filename.split("/")[-1].split(".")[0]
    recording = get_recording_by_id(recording_id)
    if recording["video_id"] not in videos:
        shutil.move(f"./finished/Zen/{filename}", f"./recordings/Zen/{filename}")